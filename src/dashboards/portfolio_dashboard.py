# src/dashboards/portfolio_dashboard.py

import streamlit as st
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]  # Ajusta el número si cambias la profundidad
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Importa las vistas correctamente ---
from src.dashboards.views import general
# --- Sidebar navegación ---
st.sidebar.title("Menú de navegación")

VIEWS = [
    "Resumen General",
    "Rendimiento & Métricas",
    "Siguiente Movimiento",
    "Resumen por Activo",
    "Riesgo",
    "Transacciones",
    "Situación de Mercado"
]

selected_view = st.sidebar.selectbox("Selecciona una vista:", VIEWS)

# --- Cabecera general ---
st.title("Portfolio Manager Demo")
st.caption("TFM • Marcos Cedenilla Bonet")



# --- Router principal ---
if selected_view == "Resumen General":
    general.show()  # Llama a la función principal de la vista General
elif selected_view == "Rendimiento & Métricas":
    st.header("Vista: Rendimiento & Métricas")
    st.info("Comparativa de retornos, métricas de riesgo, Sharpe, Sortino, drawdown, etc.")
elif selected_view == "Siguiente Movimiento":
    st.header("Vista: Siguiente Movimiento")
    st.info("Recomendación IA, sentimiento de mercado y comparación de pesos recomendados.")
elif selected_view == "Resumen por Activo":
    st.header("Vista: Resumen por Activo")
    st.info("KPIs fundamentales, gráfico histórico de peso y detalle por activo.")
elif selected_view == "Riesgo":
    st.header("Vista: Riesgo")
    st.info("Correlaciones, volatilidad, betas, matriz de covarianza y diversificación.")
elif selected_view == "Transacciones":
    st.header("Vista: Transacciones")
    st.info("Tabla con todas las transacciones, filtros y KPIs de actividad.")
elif selected_view == "Situación de Mercado":
    st.header("Vista: Situación de Mercado")
    st.info("Indicadores macro, mercados globales y gráficos contextuales.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Desarrollado por [Marcos Cedenilla Bonet](mailto:marcos.cedenilla.bonet@unir.net)"
)
