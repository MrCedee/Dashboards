# src/dashboards/portfolio_dashboard.py

import streamlit as st
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]  # Ajusta el número si cambias la profundidad
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from config import FECHA_CORTE
# --- Importa las vistas correctamente ---
from src.dashboards.views import general, performance, recommendation, asset_summary
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
st.caption(f"FECHA: {FECHA_CORTE.strftime('%d/%m/%Y')}")


# --- Router principal ---
if selected_view == "Resumen General":
    general.show()  # Llama a la función principal de la vista General
elif selected_view == "Rendimiento & Métricas":
    performance.show()
elif selected_view == "Siguiente Movimiento":
    recommendation.show()
elif selected_view == "Resumen por Activo":
    asset_summary.show()
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
