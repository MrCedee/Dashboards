import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.data_loader import load_portfolio_history, load_benchmarks, load_asset_allocation
from src.utils.metrics import (
    get_daily_returns, get_sharpe_ratio, get_sortino_ratio, get_max_drawdown,
    get_annualized_return, get_alpha_beta, get_effective_n, get_turnover
)
from config import PORTFOLIO_HISTORY_PATH, BENCHMARKS_PATH, WEIGHTS_PATH, RF

# ----- METAINFORMACIÓN -----
METRIC_INFO = {
    "Sharpe Ratio":      {"help": "Sharpe mide la rentabilidad ajustada al riesgo. >1 bueno, <0.5 pobre.", "icon": "📈"},
    "Sortino Ratio":     {"help": "Como Sharpe, pero solo penaliza caídas. >1 muy bueno.", "icon": "📉"},
    "Max Drawdown (%)":  {"help": "Mayor caída desde un máximo. Más negativo = peor. <10% poco riesgo, >30% mucho riesgo.", "icon": "📉"},
    "ARR (%)":           {"help": "Rentabilidad anualizada de la cartera.", "icon": "💸"},
    "Effective N":       {"help": "Nivel de diversificación. Máximo=número de activos.", "icon": "🔢"},
    "Turnover (%)":      {"help": "Rotación anual. <100% normal, >200% trading excesivo.", "icon": "🔁"},
    "Alpha (anual, vs SP500)": {"help": "Diferencial de rentabilidad anualizada respecto a SP500. >0 mejor.", "icon": "✨"},
    "Beta (vs SP500)":   {"help": "Sensibilidad al mercado SP500. 1=igual, >1 más volátil.", "icon": "🧭"},
}

# SOLO METRICAS CLAVE EN RESUMEN
KPI_MAIN = ["Sharpe Ratio", "ARR (%)", "Max Drawdown (%)", "Effective N"]
# MÉTRICAS SECUNDARIAS (incluye Sortino ahora)
KPI_SEC = ["Sortino Ratio", "Turnover (%)", "Alpha (anual, vs SP500)", "Beta (vs SP500)"]

def metric_color(metric, value):
    if metric in ["Sharpe Ratio", "Sortino Ratio"]:
        if value >= 1: return "#b9f6ca"
        elif value < 0.5: return "#ffcdd2"
        else: return "#fff9c4"
    if metric == "ARR (%)":
        if value >= 8: return "#b9f6ca"
        elif value <= 2: return "#ffcdd2"
        else: return "#fff9c4"
    if metric == "Max Drawdown (%)":
        if value > -10: return "#b9f6ca"
        elif value < -30: return "#ffcdd2"
        else: return "#fff9c4"
    if metric == "Effective N":
        if value > 0.66: return "#b9f6ca"
        elif value < 0.33: return "#ffcdd2"
        else: return "#fff9c4"
    if metric == "Turnover (%)":
        if value <= 100: return "#b9f6ca"
        elif value <= 200: return "#fff9c4"
        else: return "#ffcdd2"
    if metric == "Alpha (anual, vs SP500)":
        if value > 0: return "#b9f6ca"
        elif value < -0.05: return "#ffcdd2"
        else: return "#fff9c4"
    if metric == "Beta (vs SP500)":
        if 0.9 <= value <= 1.1: return "#b9f6ca"
        elif value < 0.7 or value > 1.3: return "#ffcdd2"
        else: return "#fff9c4"
    return "#f6f6fa"

def format_metric(metric, value, n_assets=None):
    if value is None:
        return "—"
    if metric in ["ARR (%)", "Turnover (%)", "Max Drawdown (%)"]:
        return f"{value:.1f}%"
    if metric == "Effective N":
        return f"{value:.1f} / {n_assets}"
    if metric.startswith("Alpha"):
        return f"{value:.2f}"
    return f"{value:.2f}"

def get_metrics(df, df_alloc, n_assets, is_port=True, sp500=None):
    col = "portfolio_value" if is_port else "value"
    metrics = {
        "Sharpe Ratio": get_sharpe_ratio(df, col, rf=RF),
        "Sortino Ratio": get_sortino_ratio(df, col, rf=RF),
        "ARR (%)": 100 * get_annualized_return(df, col),
        "Max Drawdown (%)": 100 * get_max_drawdown(df, col),
        "Effective N": get_effective_n(df_alloc.iloc[-1].drop('date').values),
        "Turnover (%)": get_turnover(df_alloc, df["date"].max()) if is_port else None,
    }
    # Alpha y beta solo vs sp500
    if sp500 is not None:
        alpha, beta = get_alpha_beta(df, sp500, col_port=col, col_bench="value")
        metrics["Alpha (anual, vs SP500)"] = alpha
        metrics["Beta (vs SP500)"] = beta
    else:
        metrics["Alpha (anual, vs SP500)"] = None
        metrics["Beta (vs SP500)"] = None
    return metrics

def get_sp500_bench(benchmarks):
    for k in benchmarks:
        if k.lower() == "sp500":
            return benchmarks[k]
    return next(iter(benchmarks.values()))

def vista_performance():
    st.title("Rendimiento y Métricas")

    df_portfolio = load_portfolio_history(PORTFOLIO_HISTORY_PATH)
    benchmarks = load_benchmarks(BENCHMARKS_PATH)
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    df_alloc['date'] = pd.to_datetime(df_alloc['date'])
    n_assets = len(df_alloc.sort_values('date').iloc[-1].drop("date"))

    df_sp500 = get_sp500_bench(benchmarks)

    # --- KPIs cartera principales y secundarios
    metrics = get_metrics(df_portfolio, df_alloc, n_assets, True, df_sp500)

    # --- RESUMEN EJECUTIVO
    mejor_kpi = sum([metrics["Sharpe Ratio"] > 1, metrics["ARR (%)"] > 8])
    badge = "🥇" if mejor_kpi >= 2 else ("🟢" if mejor_kpi == 1 else "🟠")
    st.markdown(
        f"<div style='font-size:1.2em;font-weight:bold;background:#eef8ed;padding:10px 20px;border-radius:12px;display:inline-block'>"
        f"{badge} Tu cartera tiene un Sharpe de <b>{metrics['Sharpe Ratio']:.2f}</b> y una rentabilidad anualizada de <b>{metrics['ARR (%)']:.1f}%</b>. "
        f"Diversificación: <b>{metrics['Effective N']:.1f}/{n_assets}</b>. "
        f"MDD: <b>{metrics['Max Drawdown (%)']:.1f}%</b>."
        "</div>", unsafe_allow_html=True
    )

    # --- KPIs principales en GRID tipo tabla ---
    # (Eliminado st.markdown("#### Métricas clave de la cartera"))

    # --- KPIs secundarios en una sola fila (ahora incluye Sortino) ---
    st.markdown("#### Métricas avanzadas")
    cols = st.columns(len(KPI_SEC))
    for i, m in enumerate(KPI_SEC):
        cols[i].markdown(
            f"<div style='background:{metric_color(m, metrics[m] if metrics[m] is not None else 0)};border-radius:10px;padding:10px 8px 4px 8px;margin:0 4px;min-height:86px;text-align:center'>"
            f"<span title='{METRIC_INFO[m]['help']}'>{METRIC_INFO[m]['icon']} <b>{m}</b></span><br>"
            f"<span style='font-size:1.4em'>{format_metric(m, metrics[m], n_assets)}</span>"
            "</div>", unsafe_allow_html=True
        )

    # --- TAB COMPARATIVA ---
    tabs = st.tabs(["Retornos diarios", "Comparar métricas"])
    with tabs[0]:
        st.markdown("##### Histórico de retornos diarios")
        r_port = get_daily_returns(df_portfolio, col="portfolio_value")
        df_plot = pd.DataFrame({"Fecha": df_portfolio['date'].iloc[-len(r_port):], "Cartera": r_port.values})
        for name, df_bench in benchmarks.items():
            r_bmk = get_daily_returns(df_bench, col="value")
            df_plot[name] = r_bmk.values
        fig = px.line(df_plot, x="Fecha", y=df_plot.columns[1:], title="Retorno diario: Cartera vs Benchmarks")
        fig.update_layout(
            legend=dict(orientation="h", x=0.5, xanchor="center"),
            yaxis_title="Retorno diario",
            xaxis_title="Fecha"
        )
        # Cartera destacado
        fig.update_traces(line=dict(width=3), selector=dict(name="Cartera"))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.markdown("##### Comparativa con benchmark")
        bench_names = list(benchmarks.keys())
        bench_sel = st.selectbox("Selecciona benchmark", bench_names)
        df_bench = benchmarks[bench_sel]
        met_port = get_metrics(df_portfolio, df_alloc, n_assets, True, df_sp500)
        met_bench = get_metrics(df_bench, df_alloc, n_assets, False, df_sp500)

        # Tabla comparativa
        rows = list(met_port.keys())
        tabla = []
        for m in rows:
            port_v = met_port[m] if met_port[m] is not None else 0
            bench_v = met_bench[m] if met_bench[m] is not None else 0
            diff = port_v - bench_v if (port_v is not None and bench_v is not None) else 0
            mejor = "🔼" if (m not in ["Max Drawdown (%)", "Turnover (%)", "Beta (vs SP500)"] and diff > 0) or (m in ["Max Drawdown (%)"] and diff > 0) else "🔽"
            color_p = metric_color(m, port_v)
            color_b = metric_color(m, bench_v)
            tabla.append({
                "Métrica": f"{METRIC_INFO[m]['icon']} {m}",
                "Cartera": f"<div style='background:{color_p};border-radius:6px;padding:2px 8px'>{format_metric(m, port_v, n_assets)}</div>",
                "Benchmark": f"<div style='background:{color_b};border-radius:6px;padding:2px 8px'>{format_metric(m, bench_v, n_assets)}</div>",
                "": mejor
            })
        df_tabla = pd.DataFrame(tabla)
        st.markdown(df_tabla.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Mini barras solo para KPIs principales
        st.markdown("###### Comparativa visual de KPIs principales")
        kpi_show = KPI_MAIN
        df_barras = pd.DataFrame({
            "Métrica": kpi_show,
            "Cartera": [met_port[m] if met_port[m] is not None else 0 for m in kpi_show],
            "Benchmark": [met_bench[m] if met_bench[m] is not None else 0 for m in kpi_show],
        })
        fig = px.bar(df_barras, x="Métrica", y=["Cartera", "Benchmark"], barmode="group")
        st.plotly_chart(fig, use_container_width=True)

def show():
    vista_performance()
