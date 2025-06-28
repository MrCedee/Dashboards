import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.data_loader import load_portfolio_history, load_benchmarks, load_asset_allocation
from src.utils.metrics import (
    get_daily_returns, get_sharpe_ratio, get_sortino_ratio, get_max_drawdown,
    get_annualized_return, get_alpha_beta, get_effective_n, get_turnover
)
from config import PORTFOLIO_HISTORY_PATH, BENCHMARKS_PATH, WEIGHTS_PATH, RF

# ---- AYUDA Y COLORES REVISADOS ----
METRIC_INFO = {
    "Sharpe Ratio": {
        "help": "Sharpe mide la rentabilidad ajustada al riesgo. >1 bueno, <0.5 pobre.",
        "good": 1.0, "bad": 0.5, "icon": "📈"
    },
    "Sortino Ratio": {
        "help": "Sortino es como Sharpe pero solo penaliza las caídas. >1 muy bueno.",
        "good": 1.0, "bad": 0.5, "icon": "📉"
    },
    "Max Drawdown (%)": {
        "help": "Mayor caída desde un máximo. Más negativo = peor. <10% poco riesgo, >30% mucho riesgo.",
        "good": -10, "bad": -30, "icon": "📉"
    },
    "ARR (Anualiz., %)": {
        "help": "Rentabilidad anualizada de la cartera.",
        "good": 8, "bad": 2, "icon": "💸"
    },
    "Beta (vs SP500)": {
        "help": "Sensibilidad al mercado SP500. 1=igual, >1 más volátil.",
        "good": 1.0, "bad": 1.2, "icon": "🧭"
    },
    "Alpha (anual, vs SP500)": {
        "help": "Diferencial de rentabilidad anualizada respecto al SP500. >0 mejor.",
        "good": 0.0, "bad": -0.05, "icon": "✨"
    },
    "Effective N": {
        "help": "Nivel de diversificación. El máximo es el número de activos en cartera.",
        "good": 5, "bad": 2, "icon": "🔢"
    },
    "Turnover (%)": {
        "help": "Rotación anual de la cartera. 0-100% normal. >200% = trading excesivo.",
        "good": 100, "bad": 200, "icon": "🔁"
    }
}

def color_metric(metric, value):
    info = METRIC_INFO.get(metric, {})
    # --- Porcentajes: Max Drawdown, ARR, Turnover
    if metric == "Max Drawdown (%)":
        # Aquí: valor más cercano a 0 es mejor, más negativo es peor
        if value > info["good"]:
            return "#b9f6ca"  # verde
        elif value <= info["bad"]:
            return "#ffcdd2"  # rojo
        else:
            return "#fff9c4"  # amarillo
    elif metric == "ARR (Anualiz., %)":
        if value >= info["good"]:
            return "#b9f6ca"
        elif value <= info["bad"]:
            return "#ffcdd2"
        else:
            return "#fff9c4"
    elif metric == "Turnover (%)":
        # 0-100% verde, 100-200% amarillo, >200% rojo
        if value <= info["good"]:
            return "#b9f6ca"
        elif value <= info["bad"]:
            return "#fff9c4"
        else:
            return "#ffcdd2"
    elif metric == "Alpha (anual, vs SP500)":
        # >0 verde, <-5% rojo
        if value > info["good"]:
            return "#b9f6ca"
        elif value <= info["bad"]:
            return "#ffcdd2"
        else:
            return "#fff9c4"
    elif metric == "Beta (vs SP500)":
        # 0.9-1.1 verde, fuera de ese rango amarillo o rojo
        if 0.9 <= value <= 1.1:
            return "#b9f6ca"
        elif value < 0.7 or value > 1.3:
            return "#ffcdd2"
        else:
            return "#fff9c4"
    elif metric == "Effective N":
        if value >= info["good"]:
            return "#b9f6ca"
        elif value <= info["bad"]:
            return "#ffcdd2"
        else:
            return "#fff9c4"
    else:
        # Ratios generales (Sharpe, Sortino...)
        if value >= info.get("good", 0):
            return "#b9f6ca"
        elif value <= info.get("bad", 0):
            return "#ffcdd2"
        else:
            return "#fff9c4"


def metric_card(label, value, fmt=":.2f", icon=None, help_text=None, color=None, suffix=""):
    color = color or "#F6F6FA"
    try:
        if "(%)" in label:
            value_disp = f"{100*float(value):.1f}%"
        elif "Effective N" in label:
            value_disp = f"{value}{suffix}"
        else:
            value_disp = f"{float(value):.2f}{suffix}"
    except Exception:
        value_disp = "—"
    st.markdown(
        f"<div style='padding:10px 16px;background:{color};border-radius:8px;display:inline-block;width:170px'>"
        f"<span style='font-size:1.6em'>{icon or ''}</span>"
        f"<b style='font-size:1em'>{label}</b><br>"
        f"<span style='color:#0b7285;font-size:1.5em'>{value_disp}</span>"
        f"</div>", unsafe_allow_html=True
    )
    if help_text:
        st.caption(f"ℹ️ {help_text}")

def get_sp500_bench(benchmarks):
    # Busca SP500 en keys sin importar mayúsculas, si no el primero
    for k in benchmarks.keys():
        if k.lower() == "sp500":
            return benchmarks[k]
    # Si no hay, devuelve el primero por orden
    return next(iter(benchmarks.values()))

def calc_metrics(df, df_alloc, num_assets, is_portfolio=True, sp500_bench=None):
    metrics = {}
    col = "portfolio_value" if is_portfolio else "value"
    metrics["Sharpe Ratio"] = get_sharpe_ratio(df, col=col, rf=RF)
    metrics["Sortino Ratio"] = get_sortino_ratio(df, col=col, rf=RF)
    metrics["Max Drawdown (%)"] = get_max_drawdown(df, col=col) 
    metrics["ARR (Anualiz., %)"] = get_annualized_return(df, col=col) * 100
    metrics["Effective N"] = f"{get_effective_n(df_alloc.iloc[-1].drop('date').values):.1f}"
    metrics["Turnover (%)"] = get_turnover(df_alloc, df["date"].max())  if is_portfolio else None
    # Alpha y Beta SIEMPRE frente a SP500
    if sp500_bench is not None:
        alpha, beta = get_alpha_beta(df, sp500_bench, col_port=col, col_bench="value")
        metrics["Alpha (anual, vs SP500)"] = alpha
        metrics["Beta (vs SP500)"] = beta
    else:
        metrics["Alpha (anual, vs SP500)"] = None
        metrics["Beta (vs SP500)"] = None
    return metrics

# -------------------------------
# VISTA PRINCIPAL
# -------------------------------
def vista_performance():
    st.title("Rendimiento y Métricas")
    df_portfolio = load_portfolio_history(PORTFOLIO_HISTORY_PATH)
    benchmarks = load_benchmarks(BENCHMARKS_PATH)
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    bench_names = list(benchmarks.keys())

    # Encuentra el benchmark SP500 para cálculos de alpha/beta
    df_sp500 = get_sp500_bench(benchmarks)

    # Número de activos actuales
    df_alloc['date'] = pd.to_datetime(df_alloc['date'])
    num_assets = len(df_alloc.sort_values('date').iloc[-1].drop("date"))

    # KPIs cartera
    st.markdown("#### Métricas clave de la cartera")
    metrics = calc_metrics(df_portfolio, df_alloc, num_assets, is_portfolio=True, sp500_bench=df_sp500)
    col1, col2, col3, col4 = st.columns(4)
    cards = list(metrics.items())
    for i, (metric, value) in enumerate(cards):
        color = color_metric(metric, float(str(value).split()[0]) if value not in [None, "None", "—"] else 0)
        icon = METRIC_INFO.get(metric, {}).get("icon", "")
        help_text = METRIC_INFO.get(metric, {}).get("help", "")
        suffix = "" if "Effective N" not in metric else f" / {num_assets}"
        col = [col1, col2, col3, col4][i % 4]
        metric_card(metric, value if value is not None else "—", icon=icon, help_text=help_text, color=color, suffix=suffix)
    st.markdown("---")

    # Tabs: Comparar con benchmark
    tabs = st.tabs(["Retornos diarios", "Comparar métricas con benchmark"])
    with tabs[0]:
        st.markdown("##### Histórico de retornos diarios")
        r_port = get_daily_returns(df_portfolio, col="portfolio_value")
        df_plot = pd.DataFrame({"Fecha": df_portfolio['date'].iloc[-len(r_port):], "Cartera": r_port.values})
        for name, df_bench in benchmarks.items():
            r_bmk = get_daily_returns(df_bench, col="value")
            df_plot[name] = r_bmk.values
        fig = px.line(df_plot, x="Fecha", y=df_plot.columns[1:], title="Retorno diario: Cartera vs Benchmarks")
        fig.update_layout(legend=dict(orientation="h", x=0.5, xanchor="center"))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.markdown("##### Comparativa con benchmark")
        bench_sel = st.selectbox("Selecciona benchmark", bench_names, key="bench2")
        df_bench = benchmarks[bench_sel]
        met_port = calc_metrics(df_portfolio, df_alloc, num_assets, is_portfolio=True, sp500_bench=df_sp500)
        met_bench = calc_metrics(df_bench, df_alloc, num_assets, is_portfolio=False, sp500_bench=df_sp500)

        # Visual: tarjetas lado a lado
        st.markdown("###### Comparativa de métricas")
        rows = list(met_port.keys())
        col_port, col_bench = st.columns(2)
        with col_port:
            st.markdown("**Cartera**")
            for m in rows:
                color = color_metric(m, float(str(met_port[m]).split()[0]) if met_port[m] not in [None, "None", "—"] else 0)
                icon = METRIC_INFO.get(m, {}).get("icon", "")
                metric_card(m, met_port[m] if met_port[m] is not None else "—", icon=icon, help_text=None, color=color)
        with col_bench:
            st.markdown("**Benchmark**")
            for m in rows:
                color = color_metric(m, float(str(met_bench[m]).split()[0]) if met_bench[m] not in [None, "None", "—"] else 0)
                icon = METRIC_INFO.get(m, {}).get("icon", "")
                metric_card(m, met_bench[m] if met_bench[m] is not None else "—", icon=icon, help_text=None, color=color)

        # Visual: gráfico de barras lado a lado
        st.markdown("###### Diferencias visuales")
        df_compare = pd.DataFrame({
            "Métrica": rows,
            "Cartera": [float(str(met_port[m]).split()[0]) if met_port[m] not in [None, "None", "—"] else 0 for m in rows],
            "Benchmark": [float(str(met_bench[m]).split()[0]) if met_bench[m] not in [None, "None", "—"] else 0 for m in rows],
        })
        fig = px.bar(df_compare, x="Métrica", y=["Cartera", "Benchmark"], barmode="group")
        st.plotly_chart(fig, use_container_width=True)

def show():
    vista_performance()
