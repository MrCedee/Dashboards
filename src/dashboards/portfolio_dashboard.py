# src/dashboards/portfolio_dashboard.py

import streamlit as st
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]  # Ajusta el número si cambias la profundidad
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from config import FECHA_CORTE
# --- Importa las vistas correctamente ---
from src.dashboards.views import general, performance, recommendation, asset_summary, transactions, market_overview
# --- Sidebar navegación ---
st.sidebar.title("Portfolio Manager Demo")
st.sidebar.caption("TFM • Marcos Cedenilla Bonet")
st.sidebar.caption(f"FECHA: {FECHA_CORTE.strftime('%d/%m/%Y')}")
st.sidebar.title("Menú de navegación")

VIEWS = [
    "Resumen General",
    "Rendimiento & Métricas",
    "Siguiente Movimiento",
    "Resumen por Activo",
    "Transacciones",
    "Situación de Mercado"
]

selected_view = st.sidebar.selectbox("Selecciona una vista:", VIEWS)




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
    transactions.show()
elif selected_view == "Situación de Mercado":
    market_overview.show()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Desarrollado por [Marcos Cedenilla Bonet](mailto:marcos.cedenilla.bonet@unir.net)"
)
