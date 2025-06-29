import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.data_loader import load_asset_allocation, load_asset_prices
from src.utils.metrics import get_transaction_table, get_cash_series
from config import WEIGHTS_PATH, PRICES_PATH

# ----------- Helper tooltips
def info(texto):
    return f"<span style='color:#888;font-size:1.1em;vertical-align:middle' title='{texto}'>❓</span>"

# ----------- Vista principal
def vista_transacciones():
    st.title("Transacciones y rotación de cartera")

    # 1. Cargar datos
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    df_prices = load_asset_prices(PRICES_PATH)

    # 2. Tabla de transacciones
    st.markdown(f"#### Tabla de transacciones {info('Cada fila es una operación real: compra o venta, precio y rendimiento inmediato')}", unsafe_allow_html=True)
    df_trans = get_transaction_table(df_alloc, df_prices)

    if len(df_trans) == 0:
        st.info("No se detectan transacciones en los datos.")
    else:
        # Tabla visual, solo para mostrar
        mostrar = df_trans.copy()
        mostrar["fecha"] = mostrar["fecha"].dt.strftime("%Y-%m-%d")
        mostrar["retorno_op"] = (mostrar["retorno_op"] * 100).round(2).astype(str) + "%"
        mostrar["cambio_peso_str"] = (mostrar["cambio_peso"] * 100).round(2).astype(str) + "%"

        st.dataframe(
            mostrar[["fecha", "activo", "acción", "cambio_peso_str", "precio_entrada", "precio_salida", "retorno_op"]],
            hide_index=True, use_container_width=True
        )

    # 3. Gráfico de caja
    st.markdown(f"#### Evolución del saldo de caja {info('El saldo de caja disponible tras cada operación')}", unsafe_allow_html=True)
    df_cash = get_cash_series(df_alloc)
    if len(df_cash) > 0:
        fig = px.line(df_cash, x="date", y="CASH", title="Evolución de caja")
        fig.update_traces(line=dict(width=3, color="#004080"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay columna 'CASH' en los datos de pesos.")

    # 4. Rotación de cartera (suma de compras y ventas absolutas)
    st.markdown(f"#### Rotación de cartera {info('Suma absoluta de cambios de peso, refleja actividad operativa')}", unsafe_allow_html=True)
    if len(df_trans) > 0:
        rot = df_trans["cambio_peso"].astype("string").str.replace("%", "").astype(float).abs().sum()
        st.metric("Rotación total", f"{rot:.2f}%")
    else:
        st.metric("Rotación total", "0%")

def show():
    vista_transacciones()
