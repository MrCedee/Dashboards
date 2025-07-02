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
    return actual_weights.astype(float), recommended_weights.astype(float)

# ---------- BLOQUE: KPIs de activos top ----------
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
    # Icono info discreto, alineado y pequeño
    info_icon = "<span style='color:#888; font-size:1.2em; vertical-align:middle;' title='La IA recomienda con más peso este activo'>❓</span>"
    badge_ia = "<span style='background:#E6F0FA; color:#1956A6; font-size:0.8em; border-radius:6px; padding:2px 7px; margin-left:8px; vertical-align:middle;'>IA</span>"
    badge_actual = "<span style='background:#EEE; color:#222; font-size:0.8em; border-radius:6px; padding:2px 7px; margin-left:8px; vertical-align:middle;'>Actual</span>"
    info_icon2 = "<span style='color:#888; font-size:1.2em; vertical-align:middle;' title='Actualmente en la cartera este activo tiene más peso'>❓</span>"
    with col1:
        st.markdown(f"**Activo más recomendado** {badge_ia} {info_icon}", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:2.9em; font-weight:bold'>{activo_rec} <span style='font-size:1.2em; font-weight:600;'>({peso_rec:.1f}%)</span></span>", unsafe_allow_html=True)
        # Diferencia, flecha, color y posible icono
        if diff_rec > 0.1:
            st.markdown(f"<span style='color:green; font-size:1.15em'>🟢 ↗ Se recomienda <b>COMPRAR</b> {diff_rec:.1f}%</span>", unsafe_allow_html=True)
        elif diff_rec < -0.1:
            st.markdown(f"<span style='color:#E00; font-size:1.15em'>🔴 ↘ Se recomienda <b>VENDER</b> {-diff_rec:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:gray; font-size:1.1em'>= Peso casi igual al actual</span>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Activo más ponderado actualmente** {badge_actual} {info_icon2}", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:2.9em; font-weight:bold'>{activo_act} <span style='font-size:1.2em; font-weight:600;'>({peso_act:.1f}%)</span></span>", unsafe_allow_html=True)
        if diff_act > 0.1:
            st.markdown(f"<span style='color:green; font-size:1.15em'>🟢 ↗ Se recomienda <b>COMPRAR</b> {diff_act:.1f}%</span>", unsafe_allow_html=True)
        elif diff_act < -0.1:
            st.markdown(f"<span style='color:#E00; font-size:1.15em'>🔴 ↘ Se recomienda <b>VENDER</b> {-diff_act:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:gray; font-size:1.1em'>= Peso casi igual al recomendado</span>", unsafe_allow_html=True)

# ---------- BLOQUE: Gráfico de cambios de pesos ----------
def plot_changed_weights(actual_weights, recommended_weights):
    actual_weights = actual_weights.astype(float)
    recommended_weights = recommended_weights.astype(float)
    cambios = (actual_weights != recommended_weights)
    activos_cambiados = actual_weights.index[cambios]

    if len(activos_cambiados) == 0:
        st.info("No hay cambios de pesos recomendados respecto a los actuales.")
        return

    df = pd.DataFrame({
        "Activo": activos_cambiados,
        "Peso actual": (actual_weights[activos_cambiados].fillna(0) * 100).round(1),
        "Peso recomendado": (recommended_weights[activos_cambiados].fillna(0) * 100).round(1)
    })

    # Mejora visual: barras más anchas, pegadas, colores con más contraste, leyenda arriba derecha
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Activo"],
        y=df["Peso actual"],
        name="Peso actual",
        offsetgroup=0,
        width=0.38,
        marker_color="rgba(70,130,180,0.8)",  # azul neutro
        hovertemplate="Peso actual: %{y:.1f}%<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=df["Activo"],
        y=df["Peso recomendado"],
        name="Peso recomendado",
        offsetgroup=1,
        width=0.38,
        marker_color="rgba(34,139,34,0.92)",  # verde más oscuro
        hovertemplate="Peso recomendado: %{y:.1f}%<extra></extra>"
    ))

    # Resalta cambios >10%
    for i, row in df.iterrows():
        diff = abs(row["Peso actual"] - row["Peso recomendado"])
        if diff > 10:
            fig.add_vrect(
                x0=i-0.4, x1=i+0.4,
                fillcolor="rgba(255, 230, 0, 0.15)", layer="below", line_width=0
            )

    fig.update_layout(
        barmode='group',
        title="<b>Activos con cambio de peso: Actual vs Recomendado</b>",
        xaxis_title="Activo",
        yaxis_title="Peso (%)",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.05,
            xanchor="right", x=1
        ),
        margin=dict(l=10, r=10, t=50, b=40),
        height=390,
        bargap=0.20,
        bargroupgap=0.04
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- BLOQUE PRINCIPAL DE LA VISTA ----------
def vista_siguiente_movimiento():
    st.title("Siguiente Movimiento")
    st.caption("Comparativa de pesos actuales vs recomendados por IA")
    df_alloc = load_data()
    actual_weights, recommended_weights = get_weights(df_alloc)
    show_top_assets(actual_weights, recommended_weights)
    st.markdown("<hr style='border:0.5px solid #EEE; margin-top:18px; margin-bottom:18px;'>", unsafe_allow_html=True)
    plot_changed_weights(actual_weights, recommended_weights)

# ---- Para router principal:
def show():
    vista_siguiente_movimiento()
