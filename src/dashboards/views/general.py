import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils.data_loader import load_portfolio_history, load_benchmarks, load_asset_allocation
from src.utils.metrics import get_total_return, get_var
from config import FECHA_CORTE, PORTFOLIO_HISTORY_PATH, BENCHMARKS_PATH, WEIGHTS_PATH

# ---------- Header + periodo ----------
def show_header_and_periodo(periodos, default):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 style='margin-bottom:0.2rem;'>Resumen General de la Cartera</h2>", unsafe_allow_html=True)
    with col2:
        periodo = st.selectbox("Periodo", list(periodos.keys()), index=default)
    return periodo, periodos[periodo]

# ---------- Resumen textual ----------
def show_resumen(df_period, df_benchmarks_period):
    ret_cartera = get_total_return(df_period)
    best = None
    max_bench = -1
    for nombre, df_bench in df_benchmarks_period.items():
        ret = (1 + df_bench['retorno']).prod() - 1
        if ret > max_bench:
            max_bench = ret
            best = nombre
    text = f"📊 <b>Tu cartera ha subido un <span style='color:#2ecc71'>{ret_cartera:.2%}</span> en el periodo seleccionado.</b> "
    if best and ret_cartera > max_bench:
        text += f"¡Has batido a todos los benchmarks! 🥇"
    elif best:
        text += f"El benchmark con mejor rentabilidad ha sido <b>{best}</b> ({max_bench:.2%})."
    st.markdown(text, unsafe_allow_html=True)

# ---------- KPIs rentabilidad ----------
def show_kpis(df_period, df_benchmarks_period, max_benchmarks=3):
    st.markdown("<b>Rentabilidad acumulada</b>", unsafe_allow_html=True)
    all_cols = st.columns(1 + min(len(df_benchmarks_period), max_benchmarks))
    # Cartera principal
    ret = get_total_return(df_period)
    color = "green" if ret >= 0 else "red"
    all_cols[0].markdown(f"""
        <div style="background:#F9F9F9;border-radius:8px;padding:18px 10px;text-align:center;box-shadow:0 2px 8px #ddd;">
            <span style='font-size:20px;color:{color};font-weight:700'>{ret:.2%}</span><br>
            <span style='font-size:13px;opacity:0.8'>Cartera</span>
        </div>
        """, unsafe_allow_html=True)
    # Benchmarks destacados
    for i, (nombre, df_bench) in enumerate(df_benchmarks_period.items()):
        if i >= max_benchmarks:
            break
        ret_bench = (1 + df_bench['retorno']).prod() - 1
        color = "green" if ret_bench >= 0 else "red"
        all_cols[i+1].markdown(f"""
            <div style="background:#F9F9F9;border-radius:8px;padding:18px 10px;text-align:center;box-shadow:0 2px 8px #ddd;">
                <span style='font-size:20px;color:{color};font-weight:700'>{ret_bench:.2%}</span><br>
                <span style='font-size:13px;opacity:0.8'>{nombre}</span>
            </div>
            """, unsafe_allow_html=True)
    # Botón para ver todos si hay más
    if len(df_benchmarks_period) > max_benchmarks:
        if st.button("Ver todos los benchmarks"):
            extra_cols = st.columns(len(df_benchmarks_period) - max_benchmarks)
            for i, (nombre, df_bench) in enumerate(list(df_benchmarks_period.items())[max_benchmarks:]):
                ret_bench = (1 + df_bench['retorno']).prod() - 1
                color = "green" if ret_bench >= 0 else "red"
                extra_cols[i].markdown(f"""
                    <div style="background:#F9F9F9;border-radius:8px;padding:18px 10px;text-align:center;box-shadow:0 2px 8px #ddd;">
                        <span style='font-size:20px;color:{color};font-weight:700'>{ret_bench:.2%}</span><br>
                        <span style='font-size:13px;opacity:0.8'>{nombre}</span>
                    </div>
                    """, unsafe_allow_html=True)

# ---------- Valor histórico (card) ----------
def show_valor_historico(df_period, df_benchmarks_period, n_dias):
    if n_dias == 1:
        return
    titulos = {
        None: "Histórico de valor: Cartera vs Benchmarks",
        365: "Valor último año: Cartera vs Benchmarks",
        30: "Valor último mes: Cartera vs Benchmarks",
    }
    titulo = titulos.get(n_dias, "Histórico de valor: Cartera vs Benchmarks")
    with st.container():
        st.markdown(f"<div style='margin-bottom:-1rem;'><b>{titulo}</b></div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_period["date"], y=df_period["portfolio_value"],
            mode="lines", name="Cartera", line=dict(width=2, color="#0050b3")
        ))
        for nombre, df_bench in df_benchmarks_period.items():
            if "value" in df_bench.columns:
                fig.add_trace(go.Scatter(
                    x=df_bench["date"], y=df_bench["value"],
                    mode="lines", name=nombre
                ))
        fig.update_layout(
            xaxis_title="Fecha", yaxis_title="Valor cartera",
            legend=dict(orientation="h", x=0.01, y=1.12, font=dict(size=13)),
            margin=dict(l=20, r=20, t=40, b=20), height=370,
            plot_bgcolor="#FAFAFA"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_var_gauge(df_portfolio):
    returns_hist = df_portfolio[df_portfolio['date'] <= FECHA_CORTE]['portfolio_value'].pct_change().dropna()
    var_95_d = abs(get_var(returns_hist, alpha=0.05)) * 100
    var_95_m = abs(var_95_d * (21 ** 0.5))
    var_95_y = abs(var_95_d * (252 ** 0.5))
    periodos = {"1 día": var_95_d, "1 mes": var_95_m, "1 año": var_95_y}
    periodo = st.selectbox("Periodo VaR", list(periodos.keys()), key="periodo_var")
    valor = periodos[periodo]
    # Badge
    if valor < 3:
        badge = "🟢"
        color_gauge = "#2ecc71"
    elif valor < 7:
        badge = "🟡"
        color_gauge = "#f1c40f"
    else:
        badge = "🔴"
        color_gauge = "#e74c3c"
    # Gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={'suffix': '%', "font": {"size": 38}},
        title={'text': f"VaR {periodo}", "font": {"size": 18}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1.2},
            'bar': {'color': "black", 'thickness': 0.23},
            'steps': [
                {'range': [0, 100], 'color': 'black'},
                {'range': [0, 3], 'color': "#2ecc71"},
                {'range': [3, 7], 'color': "#f1c40f"},
                {'range': [7, 100], 'color': "#e74c3c"},
            ],
            'threshold': {
                'line': {'color': "black", 'width': 5},
                'thickness': 0.95,
                'value': valor
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(t=14, b=0, l=2, r=2))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f"<div style='font-size:2rem;display:flex;align-items:center;justify-content:center;'><b>{valor:.2f}%</b> {badge}</div>",
        unsafe_allow_html=True)
    st.caption(
        f"El semicírculo representa la cartera. VaR ({badge}) indica la pérdida máxima esperada ({periodo}).\n"
        "🟢 bajo, 🟡 moderado, 🔴 alto.")

# --- BLOQUE: Pesos actual con toggle top 10/todos y barras mejoradas ---
def show_pesos_actuales(df_alloc):
    st.markdown("<b>Pesos (%) actuales de la cartera</b>", unsafe_allow_html=True)
    df_alloc['date'] = pd.to_datetime(df_alloc['date'])
    last_alloc = df_alloc[df_alloc['date'] <= FECHA_CORTE].sort_values('date').iloc[-1]
    pesos = last_alloc.drop('date').astype(float) * 100
    df_pesos = pd.DataFrame({"Activo": pesos.index, "Peso (%)": pesos.values.round(1)})
    df_pesos = df_pesos.sort_values("Peso (%)", ascending=False)
    top_n = 10
    # Toggle botón
    if "show_all" not in st.session_state:
        st.session_state["show_all"] = False
    if st.button("Mostrar todos los activos" if not st.session_state["show_all"] else "Ocultar activos"):
        st.session_state["show_all"] = not st.session_state["show_all"]
    show_all = st.session_state["show_all"]
    if not show_all:
        df_show = df_pesos.head(top_n)
        height = 45 * top_n
    else:
        df_show = df_pesos
        height = 45 * len(df_pesos)
    # Mejorar colores: solo top el más fuerte, el resto más claro
    colors = ["#0a2463"] + ["#dbeafe"] * (len(df_show) - 1)
    fig_bar = go.Figure()
    for i, row in df_show.iterrows():
        fig_bar.add_trace(go.Bar(
            y=[row["Activo"]],
            x=[row["Peso (%)"]],
            orientation='h',
            marker_color=colors[i] if i < len(colors) else "#dbeafe",
            text=f"{row['Peso (%)']:.1f}%",
            textposition='outside',
            hovertemplate=f"<b>{row['Activo']}</b>: {row['Peso (%)']:.1f}%<extra></extra>",
            showlegend=False,
        ))
    fig_bar.update_layout(
        yaxis_title="Activo", xaxis_title="Peso (%)",
        margin=dict(l=80, r=20, t=10, b=20), height=height,
        xaxis=dict(range=[0, df_show["Peso (%)"].max() * 1.15])
    )
    st.plotly_chart(fig_bar, use_container_width=True)
# ---------- FUNCIÓN PRINCIPAL ----------

def vista_general():
    # --- Layout compacto y grid ---
    periodos = {"1 día": 1, "1 mes": 30, "1 año": 365, "Histórico": None}
    periodo, n_dias = show_header_and_periodo(periodos, default=3)
    df_portfolio = load_portfolio_history(PORTFOLIO_HISTORY_PATH)
    benchmarks = load_benchmarks(BENCHMARKS_PATH)
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    df_portfolio['date'] = pd.to_datetime(df_portfolio['date'])
    df_period = df_portfolio[df_portfolio['date'] <= FECHA_CORTE].copy()
    if n_dias is not None:
        df_period = df_period.tail(n_dias)
    df_period.reset_index(drop=True, inplace=True)
    # Benchmarks
    df_benchmarks_period = {}
    for nombre, df_bench in benchmarks.items():
        df_bench['date'] = pd.to_datetime(df_bench['date'])
        bench_period = df_bench[df_bench['date'] <= FECHA_CORTE].copy()
        if n_dias is not None:
            bench_period = bench_period.tail(n_dias)
        bench_period.reset_index(drop=True, inplace=True)
        df_benchmarks_period[nombre] = bench_period

    # --------- GRID LAYOUT PRINCIPAL -------------
    show_resumen(df_period, df_benchmarks_period)
    show_kpis(df_period, df_benchmarks_period)
    st.markdown("<hr style='margin:10px 0 15px 0;'/>", unsafe_allow_html=True)
    cols = st.columns([2, 1])  # Izq: histórico+VaR, Der: pesos
    with cols[0]:
        show_valor_historico(df_period, df_benchmarks_period, n_dias)
        show_var_gauge(df_portfolio)
    with cols[1]:
        show_pesos_actuales(df_alloc)

def show():
    vista_general()
