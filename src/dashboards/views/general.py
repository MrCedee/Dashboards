import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils.data_loader import load_portfolio_history, load_benchmarks, load_asset_allocation
from src.utils.metrics import get_total_return, get_var

# --- Configuración global ---
FECHA_CORTE = pd.Timestamp("2025-03-26")
portfolio_history_path = "C:/Users/marco/Desktop/Cede/estudios/UNIR/TFM/Desarrollo/dashboards/data/raw/portfolio_history.csv"
benchmarks_path = "C:/Users/marco/Desktop/Cede/estudios/UNIR/TFM/Desarrollo/dashboards/data/raw/benchmarks"
weights_path = "C:/Users/marco/Desktop/Cede/estudios/UNIR/TFM/Desarrollo/dashboards/data/raw/asset_allocation.csv"

# --- BLOQUE: KPIs de rentabilidad acumulada ---
def show_kpis(df_period, df_benchmarks_period):
    st.markdown("#### Rentabilidad acumulada")
    columns = st.columns(1 + len(df_benchmarks_period))
    columns[0].metric("Cartera", f"{get_total_return(df_period):.2%}")
    for col, (nombre, df_bench) in zip(columns[1:], df_benchmarks_period.items()):
        ret_bench = (1 + df_bench['retorno']).prod() - 1
        col.metric(nombre, f"{ret_bench:.2%}")

# --- BLOQUE: Gráfico histórico de valor ---
def show_valor_historico(df_period, df_benchmarks_period, n_dias):
    if n_dias == 1:
        return
    titulos = {
        None: "Histórico de valor: Cartera vs Benchmarks",
        365: "Valor último año: Cartera vs Benchmarks",
        30: "Valor último mes: Cartera vs Benchmarks",
    }
    titulo = titulos.get(n_dias, "Histórico de valor: Cartera vs Benchmarks")
    st.subheader(titulo)
    fig = go.Figure()
    # Línea cartera
    fig.add_trace(go.Scatter(
        x=df_period["date"],
        y=df_period["portfolio_value"],
        mode="lines",
        name="Cartera",
        line=dict(width=2, color="#0050b3")
    ))
    # Benchmarks
    for nombre, df_bench in df_benchmarks_period.items():
        if "value" in df_bench.columns:
            fig.add_trace(go.Scatter(
                x=df_bench["date"],
                y=df_bench["value"],
                mode="lines",
                name=nombre
            ))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Valor cartera",
        legend=dict(orientation="v", x=1.05, y=1),
        margin=dict(l=20, r=20, t=50, b=40),
        height=450,
        title=dict(text="Valor histórico de la cartera", x=0.01, xanchor='left')
    )
    st.plotly_chart(fig, use_container_width=True)

# --- BLOQUE: Pesos actuales ---
def show_pesos_actuales(df_alloc):
    st.subheader("Pesos (%) actuales de la cartera")
    df_alloc['date'] = pd.to_datetime(df_alloc['date'])
    last_alloc = df_alloc[df_alloc['date'] <= FECHA_CORTE].sort_values('date').iloc[-1]
    pesos = last_alloc.drop('date').astype(float) * 100
    df_pesos = pd.DataFrame({"Activo": pesos.index, "Peso (%)": pesos.values.round(1)})
    df_pesos = df_pesos.sort_values("Peso (%)", ascending=True)
    # Ajusta la altura según el número de barras
    altura = max(300, 20 * len(df_pesos))  # 24 px por barra, mínimo 300
    fig_bar = px.bar(
        df_pesos, 
        y="Activo", x="Peso (%)", 
        orientation="h", 
        title="Pesos (%) actuales de la cartera",
        text="Peso (%)"
    )
    fig_bar.update_traces(texttemplate='%{x:.1f}%', textposition='outside')
    fig_bar.update_layout(
        yaxis_title="Activo",
        xaxis_title="Peso (%)",
        margin=dict(l=100, r=40, t=50, b=40),  # margen izq aumentado
        height=altura
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# --- BLOQUE: VaR (Value at Risk) ---
def show_var(df_portfolio):
    st.subheader("Riesgo (Value at Risk al 95% de confianza)")
    returns_hist = df_portfolio[df_portfolio['date'] <= FECHA_CORTE]['portfolio_value'].pct_change().dropna()
    var_95_d = abs(get_var(returns_hist, alpha=0.05)) * 100
    var_95_m = abs(var_95_d * (21**0.5))
    var_95_y = abs(var_95_d * (252**0.5))
    periodos = ["1 día", "1 mes", "1 año"]
    valores = [var_95_d, var_95_m, var_95_y]

    max_gauge = 100
    # Steps debajo de la barra negra
    risk_steps = [
        {'range': [0, 3], 'color': "#2ecc71"},
        {'range': [3, 7], 'color': "#f1c40f"},
        {'range': [7, max_gauge], 'color': "#e74c3c"},
    ]

    cols = st.columns(3)
    for col, periodo, valor in zip(cols, periodos, valores):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=valor,
            number={'suffix': '%', "font": {"size": 44}},
            title={'text': f"VaR {periodo}", "font": {"size": 22}},
            gauge={
                'axis': {'range': [0, max_gauge], 'tickwidth': 2, 'tickcolor': "black"},
                # Fondo total negro
                'bgcolor': 'white',  # color de fondo fuera de la barra
                # --- Barra negra para el valor actual (no roja)
                'bar': {'color': "black", 'thickness': 0.23},
                # Steps debajo para zonas de color, la barra negra lo cubre
                'steps': [
                    {'range': [0, max_gauge], 'color': 'black'},
                    *risk_steps
                ],
                # Aguja/umbral en negro
                'threshold': {
                    'line': {'color': "black", 'width': 5},
                    'thickness': 0.95,
                    'value': valor
                }
            }
        ))
        fig.update_layout(
            height=260, 
            margin=dict(t=30, b=0, l=5, r=5),
            font=dict(family="Arial"),
        )
        col.plotly_chart(fig, use_container_width=True)
        col.caption(f"VaR en {periodo}: {valor:.2f}% del valor de la cartera")

    st.info(
        "El semicírculo representa la cartera de inversión\n"
        "El VaR (Barra negra) indica la pérdida máxima esperada en condiciones normales (al 95% de confianza), comparada visualmente con el valor total.\n"
        "Zonas:  Verde riesgo bajo y ssumible, amarillo riesgo moderado, rojo riesgo excesivo"
    )


# --- FUNCIÓN PRINCIPAL ---
def vista_general():
    st.title(f"Resumen General de la Cartera {FECHA_CORTE.strftime('%d/%m/%Y')}")
    opciones = {
        "1 día": 1,
        "1 mes": 30,
        "1 año": 365,
        "Histórico": None,
    }
    periodo = st.selectbox("Periodo", list(opciones.keys()), index=3)
    n_dias = opciones[periodo]
    # --- Cargar datos ---
    df_portfolio = load_portfolio_history(portfolio_history_path)
    benchmarks = load_benchmarks(benchmarks_path)
    df_alloc = load_asset_allocation(weights_path)
    # --- Filtrar fechas ---
    df_portfolio['date'] = pd.to_datetime(df_portfolio['date'])
    df_period = df_portfolio[df_portfolio['date'] <= FECHA_CORTE].copy()
    if n_dias is not None:
        df_period = df_period.tail(n_dias)
    df_period.reset_index(drop=True, inplace=True)
    # --- Benchmarks ---
    df_benchmarks_period = {}
    for nombre, df_bench in benchmarks.items():
        df_bench['date'] = pd.to_datetime(df_bench['date'])
        bench_period = df_bench[df_bench['date'] <= FECHA_CORTE].copy()
        if n_dias is not None:
            bench_period = bench_period.tail(n_dias)
        bench_period.reset_index(drop=True, inplace=True)
        df_benchmarks_period[nombre] = bench_period

    # --- Mostrar bloques ---
    show_kpis(df_period, df_benchmarks_period)
    st.markdown("---")
    show_valor_historico(df_period, df_benchmarks_period, n_dias)
    show_pesos_actuales(df_alloc)
    show_var(df_portfolio)

def show():
    vista_general()
