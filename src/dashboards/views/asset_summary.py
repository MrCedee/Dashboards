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

# ----- Diccionarios para nombres y descripciones -----
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
    "high": ("High", "Precio máximo sesión/día."),
    "low": ("Low", "Precio mínimo sesión/día."),
}

# ----- Helper visual/tooltip -----
def info(texto):
    return f"<span style='color:#888;font-size:1.0em;vertical-align:middle' title='{texto}'>❓</span>"

def badge_alert(valor, key):
    # Simple lógica de alertas para TFM (ajusta a tu criterio)
    if key == "Current_Ratio":
        if valor < 1: return "🔴"
        elif valor < 1.5: return "🟡"
        else: return "🟢"
    elif key == "Debt_to_Equity":
        if valor > 2: return "🔴"
        elif valor > 1: return "🟡"
        else: return "🟢"
    elif key == "ROE_Adj":
        if valor < 0: return "🔴"
        elif valor < 10: return "🟡"
        else: return "🟢"
    elif key == "PER":
        if valor is None: return ""
        if valor < 10: return "🟡"  # barato, pero puede ser por baja expectativa
        elif valor > 30: return "🔴"
        else: return "🟢"
    else:
        return ""

def resumen_ejecutivo(last_fund, last_tech, price, weight, per):
    # Resumen arriba del todo (puedes personalizar el mensaje)
    resumen = []
    if per is not None:
        if per > 30:
            resumen.append("PER alto")
        elif per < 10:
            resumen.append("PER bajo")
    if last_fund["Current_Ratio"] < 1.5:
        resumen.append("liquidez baja")
    if last_fund["Debt_to_Equity"] > 2:
        resumen.append("endeudamiento alto")
    if last_fund["ROE_Adj"] > 20:
        resumen.append("ROE excelente")
    elif last_fund["ROE_Adj"] < 0:
        resumen.append("ROE negativo")
    if weight > 10:
        resumen.append("peso alto en cartera")
    if last_tech['rsi'] > 70:
        resumen.append("sobrecompra técnica")
    if last_tech['rsi'] < 30:
        resumen.append("sobreventa técnica")
    if len(resumen) == 0:
        resumen_txt = "Todo en parámetros normales."
    else:
        resumen_txt = " • ".join(resumen).capitalize()
    return f"**Resumen ejecutivo:** {resumen_txt}"

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

def show_main_megacard(last_fund, last_tech, price, weight, per, ret, mdd):
    # Formatea todos los valores antes de meterlos en el f-string
    price_fmt   = f"{price:.2f}"     if price is not None else "N/A"
    weight_fmt  = f"{weight:.2f}%"   if weight is not None else "N/A"
    per_fmt     = f"{per:.2f}"       if per is not None else "N/A"
    cr_fmt      = f"{last_fund['Current_Ratio']:.2f}" if last_fund['Current_Ratio'] is not None else "N/A"
    de_fmt      = f"{last_fund['Debt_to_Equity']:.2f}" if last_fund['Debt_to_Equity'] is not None else "N/A"
    roe_fmt     = f"{last_fund['ROE_Adj']:.2f}" if last_fund['ROE_Adj'] is not None else "N/A"
    ret_fmt     = f"{ret*100:.2f}%"  if ret is not None else "N/A"
    mdd_fmt     = f"{mdd*100:.2f}%"  if mdd is not None else "N/A"

    st.markdown(
        """
        <style>
        .megagrid {display:grid;grid-template-columns:repeat(3,1fr);gap:1em;align-items:center;}
        .megaitem {background:#f9f9fa;padding:16px 8px;border-radius:10px;text-align:center;box-shadow:0 2px 8px #0001;}
        .badge {font-size:1.1em;}
        .kpinum {font-size:1.7em;font-weight:700;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='megagrid'>"
        f"<div class='megaitem'>Precio actual<br><span class='kpinum'>{price_fmt}</span></div>"
        f"<div class='megaitem'>Peso actual<br><span class='kpinum'>{weight_fmt}</span></div>"
        f"<div class='megaitem'>PER<br><span class='kpinum'>{per_fmt}</span> <span class='badge'>{badge_alert(per,'PER')}</span></div>"
        f"<div class='megaitem'>Current Ratio<br><span class='kpinum'>{cr_fmt}</span> <span class='badge'>{badge_alert(last_fund['Current_Ratio'],'Current_Ratio')}</span></div>"
        f"<div class='megaitem'>Deuda/Equity<br><span class='kpinum'>{de_fmt}</span> <span class='badge'>{badge_alert(last_fund['Debt_to_Equity'],'Debt_to_Equity')}</span></div>"
        f"<div class='megaitem'>ROE ajustado<br><span class='kpinum'>{roe_fmt}</span> <span class='badge'>{badge_alert(last_fund['ROE_Adj'],'ROE_Adj')}</span></div>"
        f"<div class='megaitem'>Rent. inicio<br><span class='kpinum'>{ret_fmt}</span></div>"
        f"<div class='megaitem'>Max Drawdown<br><span class='kpinum'>{mdd_fmt}</span></div>"
        "</div>", unsafe_allow_html=True
    )


def show_technical_kpis(last_tech, prev_tech):
    st.markdown("#### Técnicas clave")
    cols = st.columns(4)
    for i, (colname, (pretty, desc)) in enumerate(list(TECHNICALS_VARS.items())[:4]):
        valor = last_tech.get(colname, None)
        prev = prev_tech.get(colname, None) if prev_tech is not None else None
        diff = None
        if prev is not None and valor is not None:
            try:
                diff = (valor - prev) / abs(prev) * 100 if prev else None
            except Exception:
                diff = None
        val_fmt = f"{valor:.2f}" if valor is not None and pd.notnull(valor) else "N/A"
        badge = ""
        if diff is not None:
            badge = f"<span style='color:{'green' if diff>0 else 'red'};font-size:0.9em'>({'+' if diff>0 else ''}{diff:.1f}%)</span>"
        col = cols[i]
        col.markdown(
            f"<div style='font-weight:bold'>{pretty} {info(desc)}</div>"
            f"<span style='font-size:1.4em'>{val_fmt} {badge}</span>",
            unsafe_allow_html=True
        )

def show_graphs(df_tech, ticker, df_alloc):
    # Sparkline precio cierre (gráfico bajo)
    st.markdown("##### Histórico de precio de cierre")
    fig_price = px.line(df_tech, x="date", y="close", title="", height=160)
    fig_price.update_traces(line=dict(width=2))
    fig_price.update_layout(margin=dict(l=10, r=10, t=10, b=30), xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig_price, use_container_width=True)

    # Sparkline peso en cartera
    if "asset" in df_alloc.columns and "weight" in df_alloc.columns:
        df_alloc_ticker = df_alloc[df_alloc['asset'] == ticker].copy()
        df_alloc_ticker = df_alloc_ticker.sort_values("date")
    else:
        df_alloc_ticker = df_alloc[["date", ticker]].rename(columns={ticker: "weight"})
    st.markdown("##### Histórico de peso en cartera")
    fig_weight = px.line(df_alloc_ticker, x="date", y="weight", title="", height=120)
    fig_weight.update_traces(line=dict(width=2, color="#bbb"))
    fig_weight.update_layout(margin=dict(l=10, r=10, t=10, b=20), xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig_weight, use_container_width=True)

def vista_resumen_activo():
    st.title("Resumen por activo")
    ticker = select_asset()
    df_fund, df_tech, df_alloc = load_data(ticker)
    last_fund = df_fund.iloc[-1]
    prev_fund = df_fund.iloc[-2] if len(df_fund) > 1 else None
    last_tech = df_tech.iloc[-1]
    prev_tech = df_tech.iloc[-2] if len(df_tech) > 1 else None
    price = last_tech['close']
    weight = get_current_weight(ticker, df_alloc)
    eps = last_fund['EPS'] if 'EPS' in last_fund else None
    per = price / eps if eps and eps != 0 else None
    # KPIs performance
    precios = df_tech[['date', 'close']].copy()
    precios['date'] = pd.to_datetime(precios['date'])
    precios = precios[precios['date'] >= pd.to_datetime(FECHA_INICIO)]
    precios = precios[precios['date'] <= pd.to_datetime(FECHA_CORTE)]
    precios = precios.sort_values('date')
    if len(precios) >= 2:
        ret = (precios['close'].iloc[-1] / precios['close'].iloc[0]) - 1
        mdd = get_max_drawdown(precios, col="close")
    else:
        ret, mdd = None, None
    # ----------- Resumen ejecutivo arriba del todo ------------
    st.info(resumen_ejecutivo(last_fund, last_tech, price, weight, per))
    # ----------- Mega-card y métricas clave -------------------
    show_main_megacard(last_fund, last_tech, price, weight, per, ret, mdd)
    st.markdown("#### Técnicos clave y gráficos")
    cols = st.columns([2, 1])
    with cols[0]:
        show_technical_kpis(last_tech, prev_tech)
    with cols[1]:
        show_graphs(df_tech, ticker, df_alloc)

def show():
    vista_resumen_activo()
