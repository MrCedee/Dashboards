import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.data_loader import (
    load_fundamentals,
    load_technicals,
    load_asset_allocation
)
from src.utils.metrics import get_max_drawdown
from config import FUNDAMENTALS_PATH, TECNICALS_PATH, WEIGHTS_PATH, FECHA_CORTE, FECHA_INICIO

FUNDAMENTALS_VARS = {
    "Current_Ratio": (
        "Current Ratio", 
        "Liquidez: capacidad de cubrir deudas a corto plazo (>1.5 suele ser seguro)."
    ),
    "Debt_to_Equity": (
        "Deuda/Equity", 
        "Nivel de endeudamiento respecto a fondos propios. Menos es menos riesgo."
    ),
    "ROE_Adj": (
        "ROE ajustado", 
        "Rentabilidad neta sobre fondos propios. Más alto es mejor."
    ),
}

TECHNICALS_VARS = {
    "rsi": ("RSI 14", "Índice de fuerza relativa. Sobrecompra >70, sobreventa <30."),
    "macd": ("MACD", "Momentum/trend. Señales positivas/negativas de tendencia."),
    "atr": ("ATR 14", "Rango promedio de movimiento en 14 días."),
    "adx": ("ADX", "Fuerza de tendencia. >25 = fuerte tendencia."),
    "high": ("High", "Precio máximo de la sesión/día."),
    "low": ("Low", "Precio mínimo de la sesión/día."),
}

def info(texto):
    return f"<span style='color:#888;font-size:1.1em;vertical-align:middle' title='{texto}'>❓</span>"

def select_asset():
    import os
    fundamentals_files = os.listdir(FUNDAMENTALS_PATH)
    tickers = [f.split("_")[0] for f in fundamentals_files if f.endswith(".csv")]
    ticker = st.selectbox("Selecciona activo", sorted(tickers))
    return ticker

def load_data(ticker):
    df_fund = load_fundamentals(FUNDAMENTALS_PATH, ticker)
    df_tech = load_technicals(TECNICALS_PATH, ticker)
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    return df_fund, df_tech, df_alloc

def get_current_weight(ticker, df_alloc):
    if "asset" in df_alloc.columns and "weight" in df_alloc.columns:
        df_alloc_ticker = df_alloc[df_alloc['asset'] == ticker].copy()
        df_alloc_ticker = df_alloc_ticker.sort_values("date")
        if len(df_alloc_ticker) == 0:
            return None
        current_weight = df_alloc_ticker.iloc[-1]["weight"] * 100
    else:
        df_alloc_copy = df_alloc.copy()
        df_alloc_copy["date"] = pd.to_datetime(df_alloc_copy["date"])
        if ticker not in df_alloc_copy.columns:
            return None
        current_weight = df_alloc_copy[ticker].iloc[-1] * 100
    return current_weight

def show_price_and_weight(df_tech, ticker, df_alloc):
    precio = df_tech['close'].iloc[-1] if 'close' in df_tech.columns else None
    weight = get_current_weight(ticker, df_alloc)
    col1, col2 = st.columns(2)
    col1.metric("Precio actual", f"{precio:.2f}" if precio is not None else "N/A")
    col2.metric("Peso actual en cartera", f"{weight:.2f}%" if weight is not None else "N/A")

def show_fundamentals(df_fund, precio_actual):
    st.markdown("#### Principales métricas fundamentales")
    last = df_fund.iloc[-1]
    prev = df_fund.iloc[-2] if len(df_fund) > 1 else None

    # ---- P/E manual ----
    try:
        eps = last["EPS"]
        pe = precio_actual / eps if eps and eps != 0 else None
    except Exception:
        pe = None

    pretty_pe = "PER (Price/Earnings)"
    desc_pe = "Precio de cierre actual dividido por el beneficio por acción (EPS). Cuánto pagas por $1 de beneficio."
    val_fmt_pe = f"{pe:.2f}" if pe is not None else "N/A"
    badge_pe = ""
    col_pe = st.columns(len(FUNDAMENTALS_VARS) + 1)[0]
    col_pe.markdown(
        f"<div style='font-weight:bold'>{pretty_pe} {info(desc_pe)}</div>"
        f"<span style='font-size:1.5em'>{val_fmt_pe} {badge_pe}</span>",
        unsafe_allow_html=True
    )

    # ---- Resto de fundamentales ----
    cols = st.columns(len(FUNDAMENTALS_VARS))
    for i, (colname, (pretty, desc)) in enumerate(FUNDAMENTALS_VARS.items()):
        valor = last.get(colname, None)
        diff = None
        if prev is not None and colname in prev.index and valor is not None:
            try:
                diff = (valor - prev[colname]) / abs(prev[colname]) * 100 if prev[colname] else None
            except Exception:
                diff = None
        val_fmt = f"{valor:.2f}" if valor is not None and pd.notnull(valor) else "N/A"
        badge = ""
        if diff is not None:
            badge = f"<span style='color:{'green' if diff>0 else 'red'};font-size:0.9em'>({'+' if diff>0 else ''}{diff:.1f}%)</span>"
        col = cols[i]
        col.markdown(
            f"<div style='font-weight:bold'>{pretty} {info(desc)}</div>"
            f"<span style='font-size:1.5em'>{val_fmt} {badge}</span>",
            unsafe_allow_html=True
        )

def show_technical_kpis(df_tech):
    st.markdown("#### Métricas técnicas clave")
    last = df_tech.iloc[-1]
    prev = df_tech.iloc[-2] if len(df_tech) > 1 else None
    cols = st.columns(len(TECHNICALS_VARS))
    for i, (colname, (pretty, desc)) in enumerate(TECHNICALS_VARS.items()):
        valor = last.get(colname, None)
        diff = None
        if prev is not None and colname in prev.index and valor is not None:
            try:
                diff = (valor - prev[colname]) / abs(prev[colname]) * 100 if prev[colname] else None
            except Exception:
                diff = None
        val_fmt = f"{valor:.2f}" if valor is not None and pd.notnull(valor) else "N/A"
        badge = ""
        if diff is not None:
            badge = f"<span style='color:{'green' if diff>0 else 'red'};font-size:0.9em'>({'+' if diff>0 else ''}{diff:.1f}%)</span>"
        col = cols[i]
        col.markdown(
            f"<div style='font-weight:bold'>{pretty} {info(desc)}</div>"
            f"<span style='font-size:1.5em'>{val_fmt} {badge}</span>",
            unsafe_allow_html=True
        )
    # Histórico de precio
    st.markdown("##### Histórico de precio de cierre")
    fig = px.line(df_tech, x="date", y="close", title="Evolución del precio de cierre")
    st.plotly_chart(fig, use_container_width=True)

def show_weight_and_history(ticker, df_alloc):
    if "asset" in df_alloc.columns and "weight" in df_alloc.columns:
        df_alloc_ticker = df_alloc[df_alloc['asset'] == ticker].copy()
        df_alloc_ticker = df_alloc_ticker.sort_values("date")
        current_weight = df_alloc_ticker.iloc[-1]["weight"] * 100
    else:
        df_alloc_copy = df_alloc.copy()
        df_alloc_copy["date"] = pd.to_datetime(df_alloc_copy["date"])
        if ticker not in df_alloc_copy.columns:
            st.warning(f"No hay pesos para {ticker}.")
            return
        df_alloc_ticker = df_alloc_copy[["date", ticker]].rename(columns={ticker: "weight"})
        current_weight = df_alloc_ticker["weight"].iloc[-1] * 100

    st.metric("Peso actual en cartera", f"{current_weight:.2f}%")
    fig = px.line(df_alloc_ticker, x="date", y="weight", labels={"weight": "Peso"}, title="Evolución histórica del peso")
    st.plotly_chart(fig, use_container_width=True)

def show_performance_kpis(df_tech):
    st.markdown("#### KPIs de rendimiento")
    precios = df_tech[['date', 'close']].copy()
    precios['date'] = pd.to_datetime(precios['date'])
    precios = precios[precios['date'] >= pd.to_datetime(FECHA_INICIO)]
    precios = precios[precios['date'] <= pd.to_datetime(FECHA_CORTE)]
    precios = precios.sort_values('date')
    if len(precios) < 2:
        st.warning("No hay suficientes datos históricos para este activo.")
        return
    ret = (precios['close'].iloc[-1] / precios['close'].iloc[0]) - 1
    mdd = get_max_drawdown(precios, col="close")
    col1, col2 = st.columns(2)
    col1.metric("Rentabilidad desde inicio", f"{ret*100:.2f}%")
    col2.metric("Max Drawdown", f"{mdd*100:.2f}%")

def vista_resumen_activo():
    st.title("Resumen por activo")
    ticker = select_asset()
    df_fund, df_tech, df_alloc = load_data(ticker)
    show_price_and_weight(df_tech, ticker, df_alloc)
    st.markdown("---")
    show_fundamentals(df_fund, df_tech['close'].iloc[-1])
    st.markdown("---")
    show_technical_kpis(df_tech)
    st.markdown("---")
    show_weight_and_history(ticker, df_alloc)
    st.markdown("---")
    show_performance_kpis(df_tech)

def show():
    vista_resumen_activo()
