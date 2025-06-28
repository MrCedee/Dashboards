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

# --- Helper para tooltip de métricas ---
def info(texto):
    return f"<span style='color:#888;font-size:1.2em;vertical-align:middle' title='{texto}'>❓</span>"

# --- Selección de activo ---
def select_asset():
    import os
    fundamentals_files = os.listdir(FUNDAMENTALS_PATH)
    tickers = [f.split("_")[0] for f in fundamentals_files if f.endswith(".csv")]
    ticker = st.selectbox("Selecciona activo", sorted(tickers))
    return ticker

# --- Carga de datos ---
def load_data(ticker):
    df_fund = load_fundamentals(FUNDAMENTALS_PATH, ticker)
    df_tech = load_technicals(TECNICALS_PATH, ticker)
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    return df_fund, df_tech, df_alloc

# --- Mostrar TODOS los fundamentales (con comparación % anterior) ---
def show_fundamentals(df_fund):
    st.markdown("#### Principales métricas fundamentales")
    last = df_fund.iloc[-1]
    prev = df_fund.iloc[-2] if len(df_fund) > 1 else None

    exclude = ["date"]  # ignora columna fecha
    cols = st.columns(4)
    metricas = [c for c in df_fund.columns if c not in exclude]
    for i, colname in enumerate(metricas):
        valor = last[colname]
        # Calcular diferencia con anterior
        diff = None
        if prev is not None and colname in prev.index:
            try:
                diff = (valor - prev[colname]) / abs(prev[colname]) * 100 if prev[colname] != 0 else None
            except Exception:
                diff = None
        # Formateo
        if abs(valor) > 1e6:
            val_fmt = f"{valor:,.0f}"
        elif isinstance(valor, float):
            val_fmt = f"{valor:,.2f}"
        else:
            val_fmt = str(valor)
        # Badge cambio
        badge = ""
        if diff is not None:
            badge = f"<span style='color:{'green' if diff>0 else 'red'};font-size:0.9em'>({'+' if diff>0 else ''}{diff:.1f}%)</span>"
        desc = colname.replace("_", " ").upper()
        col = cols[i % 4]
        col.markdown(f"<div style='font-weight:bold'>{desc} {info('Últimos valores de '+desc)}</div>", unsafe_allow_html=True)
        col.markdown(f"<span style='font-size:1.5em'>{val_fmt} {badge}</span>", unsafe_allow_html=True)

# --- Mostrar técnicos clave y todos los que hay ---
def show_technical_kpis(df_tech):
    st.markdown("#### Métricas técnicas clave")
    last = df_tech.iloc[-1]
    prev = df_tech.iloc[-2] if len(df_tech) > 1 else None

    exclude = ["date"]
    cols = st.columns(4)
    metricas = [c for c in df_tech.columns if c not in exclude]
    for i, colname in enumerate(metricas):
        valor = last[colname]
        diff = None
        if prev is not None and colname in prev.index:
            try:
                diff = (valor - prev[colname]) / abs(prev[colname]) * 100 if prev[colname] != 0 else None
            except Exception:
                diff = None
        # Formatos: si es retorno o rsi se muestra como porcentaje
        if "ret" in colname.lower() or "drawdown" in colname.lower():
            val_fmt = f"{valor*100:.2f}%" if abs(valor) < 5 else f"{valor:.2f}"
        elif "rsi" in colname.lower():
            val_fmt = f"{valor:.2f}"
        elif isinstance(valor, float):
            val_fmt = f"{valor:,.2f}"
        else:
            val_fmt = str(valor)
        badge = ""
        if diff is not None:
            badge = f"<span style='color:{'green' if diff>0 else 'red'};font-size:0.9em'>({'+' if diff>0 else ''}{diff:.1f}%)</span>"
        desc = colname.replace("_", " ").upper()
        col = cols[i % 4]
        col.markdown(f"<div style='font-weight:bold'>{desc} {info('Últimos valores de '+desc)}</div>", unsafe_allow_html=True)
        col.markdown(f"<span style='font-size:1.5em'>{val_fmt} {badge}</span>", unsafe_allow_html=True)

    # Histórico de precio
    st.markdown("##### Histórico de precio de cierre")
    fig = px.line(df_tech, x="date", y="close", title="Evolución del precio de cierre")
    st.plotly_chart(fig, use_container_width=True)

# --- Peso actual e histórico ---
def show_weight_and_history(ticker, df_alloc):
    # Si la columna es el ticker (wide) o 'asset' (long)
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

# --- KPIs de rendimiento: rentabilidad desde inicio y MDD ---
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

# --- Vista principal ---
def vista_resumen_activo():
    st.title("Resumen por activo")
    ticker = select_asset()
    df_fund, df_tech, df_alloc = load_data(ticker)
    show_fundamentals(df_fund)
    st.markdown("---")
    show_technical_kpis(df_tech)
    st.markdown("---")
    show_weight_and_history(ticker, df_alloc)
    st.markdown("---")
    show_performance_kpis(df_tech)

def show():
    vista_resumen_activo()
