import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.data_loader import load_asset_allocation, load_asset_prices
from src.utils.metrics import get_transaction_table, get_cash_series
from config import WEIGHTS_PATH, PRICES_PATH

def info(texto):
    return f"<span style='color:#888;font-size:1.1em;vertical-align:middle' title='{texto}'>❓</span>"

def resultado_icon(retorno):
    """Devuelve solo el icono resultado: 🟢/🟡/🔴 según rentabilidad."""
    if retorno > 0.1:
        icon = "🟢"
    elif retorno < -0.1:
        icon = "🔴"
    else:
        icon = "🟡"
    # Solo icono, sin badge ni fondo
    return f"<span style='font-size:1.35em;' title='Rentabilidad de la operación'>{icon}</span>"

def kpi_badge(valor, umbral, tipo="low"):
    if (tipo == "low" and valor < umbral) or (tipo == "high" and valor > umbral):
        return " <span style='color:#d33;font-weight:bold;font-size:1.1em'>⚠️</span>"
    return ""

def resumen_ejecutivo(df_trans, rotacion, min_cash, mejor_op):
    n_trans = len(df_trans)
    resumen = (
        f"En el periodo analizado se realizaron <b>{n_trans}</b> transacciones, "
        f"la <b>rotación</b> total fue del <b>{rotacion:.1f}%</b>{kpi_badge(rotacion, 50, 'high')}, "
        f"el saldo de caja mínimo fue <b>{min_cash:.2%}</b>{kpi_badge(min_cash, 0.05, 'low')}. "
    )
    if mejor_op is not None:
        tipo, act, ret = mejor_op
        resumen += f"La operación más rentable fue una <b>{tipo}</b> en <b>{act}</b> con un <b>{ret:+.2f}%</b>."
    else:
        resumen += "No hay operaciones rentables destacadas."
    return resumen

def vista_transacciones():
    st.title("Transacciones y rotación de cartera")

    # 1. Cargar datos
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    df_prices = load_asset_prices(PRICES_PATH)
    df_trans = get_transaction_table(df_alloc, df_prices)
    df_cash = get_cash_series(df_alloc)

    # 2. KPIs clave y resumen ejecutivo
    n_trans = len(df_trans)
    rot = df_trans["cambio_peso"].abs().sum() if n_trans > 0 else 0
    min_cash = df_cash["CASH"].min() if len(df_cash) > 0 else 0
    mejor_op = None
    if n_trans > 0 and (df_trans["retorno_op"].abs() > 0).any():
        idx = df_trans["retorno_op"].abs().idxmax()
        mejor = df_trans.loc[idx]
        mejor_op = (mejor["acción"], mejor["activo"], mejor["retorno_op"] * 100)

    st.markdown("#### Resumen ejecutivo")
    st.markdown(
        f"<div style='padding:0.7em 1em;background:#f7f8fb;border-radius:10px;margin-bottom:1.2em;font-size:1.13em;'>"
        f"{resumen_ejecutivo(df_trans, rot, min_cash, mejor_op)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # KPIs visuales + sparkline de caja
    k1, k2, k3, k4 = st.columns([1.2, 1, 1, 2.2])
    k1.metric("Transacciones", n_trans, help="Número de operaciones detectadas en el periodo")
    k2.metric("Rotación", f"{rot:.2f}%", help="Suma de compras y ventas absolutas en porcentaje")
    if rot > 50:
        k2.markdown('<span style="color:#d33;font-weight:bold;font-size:1.15em">⚠️ Rotación alta</span>', unsafe_allow_html=True)
    k3.metric("Cash mín.", f"{min_cash:.2%}", help="Mínimo porcentaje de caja disponible")
    if min_cash < 0.05:
        k3.markdown('<span style="color:#d33;font-weight:bold;font-size:1.15em">⚠️ Bajo cash</span>', unsafe_allow_html=True)
    with k4:
        st.markdown("Evolución caja")
        if len(df_cash) > 0:
            fig = px.line(df_cash, x="date", y="CASH")
            fig.update_layout(
                height=90, width=310, margin=dict(l=8, r=8, t=10, b=8),
                xaxis=dict(
                    showgrid=False, tickmode="array",
                    tickvals=[df_cash["date"].iloc[0], df_cash["date"].iloc[-1]],
                    ticktext=[df_cash["date"].dt.strftime("%b-%y").iloc[0], df_cash["date"].dt.strftime("%b-%y").iloc[-1]],
                    visible=True, title=None, ticks='outside', ticklen=4
                ),
                yaxis=dict(showgrid=False, visible=True)
            )
            fig.update_traces(line=dict(width=2, color="#1180f0"))
            st.plotly_chart(fig, use_container_width=False)
        else:
            st.write("Sin datos de caja")

    # 3. Tabla de transacciones: solo icono resultado tras acción y antes de cambio_peso
    st.markdown(
        f"#### Tabla de transacciones {info('Cada fila es una operación real: compra o venta, precio y rendimiento inmediato')}",
        unsafe_allow_html=True,
    )
    if n_trans == 0:
        st.info("No se detectan transacciones en los datos.")
    else:
        mostrar = df_trans.copy().sort_values(by="fecha", ascending=False)
        mostrar["fecha"] = mostrar["fecha"].dt.strftime("%Y-%m-%d")
        mostrar["cambio_peso_str"] = (mostrar["cambio_peso"] * 100).round(2).astype(str) + "%"
        mostrar["resultado"] = mostrar["retorno_op"].apply(lambda x: resultado_icon(x * 100))
        mostrar["retorno_op"] = (mostrar["retorno_op"] * 100).round(2).astype(str) + "%"

        # Solo icono en columna resultado, sin modificar nada más
        mostrar = mostrar[["fecha", "activo", "acción", "resultado", "cambio_peso_str", "precio_entrada", "precio_salida", "retorno_op"]]

        # Renombrar columnas a nombres bonitos
        mostrar = mostrar.rename(columns={
            "fecha": "Fecha",
            "activo": "Activo",
            "acción": "Acción",
            "resultado": "Resultado",
            "cambio_peso_str": "Cambio Peso",
            "precio_entrada": "Precio Inicio",
            "precio_salida": "Precio Fin",
            "retorno_op": "Retorno"
        })

        # Mostrar tabla con resultado como HTML para icono y resto normal
        st.write(
            mostrar.to_html(escape=False, index=False),
            unsafe_allow_html=True,
        )


    st.markdown("---")

def show():
    vista_transacciones()
