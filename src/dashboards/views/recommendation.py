import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.utils.data_loader import load_asset_allocation
from config import WEIGHTS_PATH, FECHA_CORTE

# ---------- BLOQUE: Cargar y preparar datos ----------
def load_data():
    df_alloc = load_asset_allocation(WEIGHTS_PATH)
    df_alloc['date'] = pd.to_datetime(df_alloc['date'])
    return df_alloc

def get_weights(df_alloc):
    last_actual = df_alloc[df_alloc['date'] <= FECHA_CORTE].sort_values('date').iloc[-1]
    actual_weights = last_actual.drop('date')
    target_date = FECHA_CORTE + pd.Timedelta(days=1)
    future_alloc = df_alloc[df_alloc['date'] >= target_date].sort_values('date')
    if not future_alloc.empty:
        recommended = future_alloc.iloc[0]
        recommended_weights = recommended.drop('date')
    else:
        recommended_weights = actual_weights  # fallback
    return actual_weights, recommended_weights

# ---------- BLOQUE: KPIs de activos top ----------
import streamlit as st

def show_top_assets(actual_weights, recommended_weights):
    # Top recomendado
    activo_rec = recommended_weights.idxmax()
    peso_rec = recommended_weights.max() * 100
    actual_rec = actual_weights.get(activo_rec, 0) * 100
    diff_rec = peso_rec - actual_rec

    # Top actual
    activo_act = actual_weights.idxmax()
    peso_act = actual_weights.max() * 100
    rec_act = recommended_weights.get(activo_act, 0) * 100
    diff_act = rec_act - peso_act

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Activo más recomendado** &nbsp; <span title='El activo al que la IA asigna mayor peso recomendado para la próxima revisión.'>❓</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:2.5em; font-weight:bold'>{activo_rec} ({peso_rec:.1f}%)</span>", unsafe_allow_html=True)
        # Mostramos compra/venta
        if diff_rec > 0.1:
            st.markdown(f"<span style='color:green'>↗ Se recomienda <b>COMPRAR</b> {diff_rec:.1f}%</span>", unsafe_allow_html=True)
        elif diff_rec < -0.1:
            st.markdown(f"<span style='color:red'>↘ Se recomienda <b>VENDER</b> {-diff_rec:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:gray'>= Peso casi igual al actual</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("**Activo más ponderado actualmente** &nbsp; <span title='El activo con mayor peso en la cartera ahora mismo.'>❓</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:2.5em; font-weight:bold'>{activo_act} ({peso_act:.1f}%)</span>", unsafe_allow_html=True)
        # Mostramos compra/venta según lo que la IA pide ajustar respecto al actual
        if diff_act > 0.1:
            st.markdown(f"<span style='color:green'>↗ Se recomienda <b>COMPRAR</b> {diff_act:.1f}%</span>", unsafe_allow_html=True)
        elif diff_act < -0.1:
            st.markdown(f"<span style='color:red'>↘ Se recomienda <b>VENDER</b> {-diff_act:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:gray'>= Peso casi igual al recomendado</span>", unsafe_allow_html=True)


# ---------- BLOQUE: Gráfico de cambios de pesos ----------
def plot_changed_weights(actual_weights, recommended_weights):
    # Nos aseguramos de que ambos sean float, si no, los convertimos
    actual_weights = actual_weights.astype(float)
    recommended_weights = recommended_weights.astype(float)

    cambios = (actual_weights != recommended_weights)
    activos_cambiados = actual_weights.index[cambios]
    if len(activos_cambiados) == 0:
        st.info("No hay cambios de pesos recomendados respecto a los actuales.")
        return

    # Crea el dataframe y convierte NaN a 0, redondea ya convertido
    df = pd.DataFrame({
        "Activo": activos_cambiados,
        "Peso actual": (actual_weights[activos_cambiados].fillna(0) * 100).round(1),
        "Peso recomendado": (recommended_weights[activos_cambiados].fillna(0) * 100).round(1)
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Activo"],
        y=df["Peso actual"],
        name="Peso actual",
        offsetgroup=0,
        marker_color="rgba(0,123,255,0.7)"
    ))
    fig.add_trace(go.Bar(
        x=df["Activo"],
        y=df["Peso recomendado"],
        name="Peso recomendado",
        offsetgroup=1,
        marker_color="rgba(40,167,69,0.7)"
    ))
    fig.update_layout(
        barmode='group',
        title="Activos con cambio de peso: Actual vs Recomendado",
        xaxis_title="Activo",
        yaxis_title="Peso (%)",
        legend_title="Tipo de peso",
        margin=dict(l=10, r=10, t=40, b=40),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- BLOQUE PRINCIPAL DE LA VISTA ----------
def vista_siguiente_movimiento():
    st.title("Siguiente Movimiento")
    st.caption("Comparativa de pesos actuales vs recomendados por IA")
    df_alloc = load_data()
    actual_weights, recommended_weights = get_weights(df_alloc)

    show_top_assets(actual_weights, recommended_weights)
    st.markdown("---")
    plot_changed_weights(actual_weights, recommended_weights)

# ---- Para router principal:
def show():
    vista_siguiente_movimiento()
