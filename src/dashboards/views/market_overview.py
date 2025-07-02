import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from src.utils.data_loader import load_benchmarks
from config import MARKETS_PATH
from datetime import timedelta

# Define aquí si más es mejor (True) o peor (False) para cada KPI
METRIC_POSITIVE_TREND = {
    "GDP": True,          # PIB: más es mejor
    "GDPC1": True,        # PIB real: más es mejor
    "TASADES": False,     # Desempleo: menos es mejor
    "CPI": False,         # Inflación: menos es mejor
    "M2": None,           # Liquidez: depende
    "OIL": None,          # Petróleo: neutral/depende
    "DJ": True,
    "NASDAQ100": True,
    "VIXCLS": False,      # Volatilidad: menos es mejor
    "DXY": None,          # Dólar: neutral/depende
    "INTRATE": None,     # Tipo interés: depende
    "yield_curve": True,  # Curva: depende
}

TOOLTIPS_EXPLICATIVOS = {
    "GDP": "Producto Interior Bruto: mide el valor total de bienes y servicios producidos. Más es mejor.",
    "GDPC1": "PIB real: ajustado por inflación. Más es mejor.",
    "TASADES": "Tasa de desempleo: porcentaje de población sin trabajo. Menos es mejor.",
    "CPI": "Índice de precios al consumo: mide la inflación. Menos es mejor.",
    "M2": "Liquidez monetaria: cantidad de dinero en circulación. El impacto depende del contexto",
    "OIL": "Precio del petróleo. El impacto depende del contexto.",
    "DJ": "Índice Dow Jones: referencia bursátil. Más es mejor.",
    "NASDAQ100": "Índice Nasdaq 100. Más es mejor.",
    "VIXCLS": "Índice VIX: mide la volatilidad esperada. Menos es mejor.",
    "DXY": "Índice dólar. El impacto depende del contexto.",
    "INTRATE": "Tasa de interés: coste del dinero. Menos es mejor para el crecimiento económico, pero puede traer inflación",
    "yield_curve": "Curva de tipos: diferencia entre tipos largos y cortos. Más es mejor (curva positiva)."
}


def info(texto):
    return f"<span style='color:#aaa;font-size:1em;vertical-align:middle;margin-left:5px' title='{texto}'>●</span>"

def get_last_and_yoy(df, col_value=None):
    col = col_value or [c for c in df.columns if c != "date"][0]
    vals = df.sort_values("date")[["date", col]].dropna()
    if len(vals) < 2:
        return None, None, None
    last_row = vals.iloc[-1]
    last = last_row[col]
    last_date = last_row["date"]
    prev = vals.iloc[-2][col]
    # YoY: busca dato 12 meses antes
    vals["date"] = pd.to_datetime(vals["date"])
    this_date = vals.iloc[-1]["date"]
    prior = vals[vals["date"] <= this_date - timedelta(days=365)]
    if len(prior) > 0:
        yoy_val = prior.iloc[-1][col]
        yoy = (last - yoy_val) / abs(yoy_val) * 100 if yoy_val != 0 else None
    else:
        yoy = None
    return last, prev, yoy

def trend_icon(val, key=None):
    sentido_positivo = METRIC_POSITIVE_TREND.get(key, True)
    color_positive = "#3cb371"  # verde
    color_negative = "#d33"     # rojo
    color_neutro = "#888"       # gris neutro

    if val is None:
        return f'<span style="color:{color_neutro};font-size:1.05em;margin-left:5px" title="Sin cambio relevante">→</span>'

    if sentido_positivo is None:
        # Neutro: arriba/abajo según signo, pero siempre gris
        if val > 1:
            return f'<span style="color:{color_neutro};font-size:1.05em;margin-left:5px" title="Arriba (neutro)">🡅</span>'
        elif val < -1:
            return f'<span style="color:{color_neutro};font-size:1.05em;margin-left:5px" title="Abajo (neutro)">🡇</span>'
        else:
            return f'<span style="color:{color_neutro};font-size:1.05em;margin-left:5px" title="Sin cambio relevante">→</span>'
    if val > 1:
        if sentido_positivo:
            return f'<span style="color:{color_positive};font-size:1.05em;margin-left:5px" title="Mejora">🡅</span>'
        else:
            return f'<span style="color:{color_negative};font-size:1.05em;margin-left:5px" title="Empeora">🡅</span>'
    elif val < -1:
        if sentido_positivo:
            return f'<span style="color:{color_negative};font-size:1.05em;margin-left:5px" title="Empeora">🡇</span>'
        else:
            return f'<span style="color:{color_positive};font-size:1.05em;margin-left:5px" title="Mejora">🡇</span>'
    else:
        return f'<span style="color:{color_neutro};font-size:1.05em;margin-left:5px" title="Sin cambio relevante">→</span>'

def question_tooltip(texto):
    return f"""<span style="color:#2196f3;font-size:1.13em;vertical-align:middle;margin-left:7px;cursor:pointer;" title="{texto}">❔</span>"""

def badge_color(val, bad_high=None, bad_low=None):
    if val is None:
        return ""
    # Valores demo, ajusta thresholds a cada KPI si quieres
    if bad_high is not None and val > bad_high:
        return "background:#f7c7c7;"  # rojo suave
    if bad_low is not None and val < bad_low:
        return "background:#ffe89b;"  # amarillo suave
    return ""

MACRO_BLOCKS = [
    {
        "title": "Crecimiento",
        "kpis": [
            ("PIB", "GDP", "PIB (nominal)", "Producto Interior Bruto nominal.", {"bad_low": 0}),
            ("REALPIB", "GDPC1", "PIB real", "PIB ajustado por inflación.", {"bad_low": 0}),
            ("TASADES", None, "Desempleo (%)", "Tasa de desempleo USA.", {"bad_high": 8}),
        ],
    },
    {
        "title": "Inflación y Liquidez",
        "kpis": [
            ("CPI", None, "IPC", "Índice de precios al consumo.", {"bad_high": 5}),
            ("M2", None, "M2", "Liquidez monetaria.", {}),
            ("OIL", None, "Petróleo", "Precio del barril.", {}),
        ],
    },
    {
        "title": "Mercado",
        "kpis": [
            ("DJ", None, "Dow Jones", "Índice Dow Jones.", {}),
            ("NASDAQ100", None, "Nasdaq 100", "Índice Nasdaq 100.", {}),
            ("VIXCLS", None, "VIX", "Volatilidad esperada S&P 500.", {"bad_high": 30}),
            ("DXY", None, "Dólar (DXY)", "Índice del dólar.", {}),
        ],
    },
    {
        "title": "Monetario",
        "kpis": [
            ("INTRATE", None, "Tasa interés", "Tipo de la Fed.", {"bad_high": 5}),
            ("yield_curve", None, "Curva de tipos", "Diferencial 10y-2y.", {"bad_low": 0}),
        ],
    },
]

def filtra_periodo(df, periodo):
    """Filtra el DataFrame por el periodo seleccionado."""
    if periodo == "Histórico completo":
        return df
    hoy = df["date"].max()
    if periodo == "Último año":
        fecha_ini = hoy - timedelta(days=365)
    elif periodo == "Últimos 5 años":
        fecha_ini = hoy - timedelta(days=5 * 365)
    elif periodo == "Últimos 10 años":
        fecha_ini = hoy - timedelta(days=10 * 365)
    else:
        return df
    return df[df["date"] >= fecha_ini]

def market_summary_yoy(macro_dict):
    # Breve resumen ejecutivo con valores YoY principales (ejemplo)
    try:
        gdp, _, yoy_gdp = get_last_and_yoy(macro_dict["PIB"], "GDP")
        cpi, _, yoy_cpi = get_last_and_yoy(macro_dict["CPI"])
        unemp, _, yoy_unemp = get_last_and_yoy(macro_dict.get("UNRATE", macro_dict.get("TASADES")))
        vix, _, yoy_vix = get_last_and_yoy(macro_dict["VIXCLS"])
        oil, _, yoy_oil = get_last_and_yoy(macro_dict["OIL"])
        resumen = (
            "<b>YoY = Cambio Anual</b><br> "
            f"<b>PIB</b> {gdp:,.0f} (<b>{yoy_gdp:+.2f}%</b> YoY), "
            f"<b>Inflación (IPC)</b> {cpi:.2f} (<b>{yoy_cpi:+.2f}%</b> YoY), "
            f"<b>Desempleo</b> {unemp:.2f}% (<b>{yoy_unemp:+.2f}%</b> YoY), "
            f"<b>VIX (Volatilidad)</b> {vix:.1f} (<b>{yoy_vix:+.2f}%</b> YoY), "
            f"<b>Petróleo</b> {oil:.2f} (<b>{yoy_oil:+.2f}%</b> YoY)."
        )
    except Exception:
        resumen = "No hay suficientes datos recientes para mostrar el resumen ejecutivo."
    return resumen
# Añade aquí el diccionario de nombres "bonitos" para tabs:
PRETTY_TABS = {
    "TASADES": "Desempleo (%)",
    "CPI": "IPC",
    "M2": "M2",
    "OIL": "Petróleo",
    "DJ": "Dow Jones",
    "NASDAQ100": "Nasdaq 100",
    "VIXCLS": "VIX",
    "DXY": "Dólar (DXY)",
    "INTRATE": "Tasa interés",
    "yield_curve": "Curva de tipos",
    "CONFIDENCE": "Confianza consumidor",
}

def vista_market():
    st.title("Situación y evolución del mercado")
    macro_dict = load_benchmarks(MARKETS_PATH)

    # --- RESUMEN EJECUTIVO ---
    st.markdown(
        f"<div style='padding:0.7em 1em;background:#f7f8fb;border-radius:10px;margin-bottom:1.2em;font-size:1.13em;'>"
        f"{market_summary_yoy(macro_dict)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- KPIs AGRUPADOS ---
    for block in MACRO_BLOCKS:
        st.markdown(f"#### {block['title']}")
        cols = st.columns(len(block["kpis"]))
        for i, (key, col_value, pretty, tooltip, thresholds) in enumerate(block["kpis"]):
            if key not in macro_dict:
                cols[i].markdown(f"<span style='color:#888'>{pretty}</span>", unsafe_allow_html=True)
                continue
            df = macro_dict[key]
            last, prev, yoy = get_last_and_yoy(df, col_value)
            if last is None:
                cols[i].markdown(f"<span style='color:#888'>{pretty}</span>", unsafe_allow_html=True)
                continue

            # Destacar solo si es negativo/positivo, no en neutros
            sentido = METRIC_POSITIVE_TREND.get(key, True)
            highlight = ""
            if sentido is not None:
                highlight = badge_color(yoy, bad_high=thresholds.get("bad_high"), bad_low=thresholds.get("bad_low"))

            # Valor y cambio
            val_fmt = f"{last:,.2f}" if abs(last) > 1 else f"{last:.2%}"
            yoy_fmt = f"{yoy:+.2f}%" if yoy is not None else "N/A"
            icon = trend_icon(yoy, key)
            tooltip_icon = question_tooltip(TOOLTIPS_EXPLICATIVOS.get(key, tooltip))

            cols[i].markdown(
                f"<div style='font-weight:bold'>{pretty}{tooltip_icon}</div>"
                f"<div style='font-size:1.6em;{highlight}display:flex;align-items:center;gap:7px'>"
                f"{val_fmt}{icon}"
                f"</div>"
                f"<div style='font-size:1.05em;color:gray;margin-top:-3px'>YoY: <b>{yoy_fmt}</b></div>",
                unsafe_allow_html=True
            )
        st.markdown("---")

    # Selector de periodo para los gráficos históricos (no tocado)
    periodo = st.radio(
        "Selecciona periodo para los gráficos históricos:",
        ["Histórico completo", "Último año", "Últimos 5 años", "Últimos 10 años"],
        horizontal=True,
        help="Filtra los gráficos de evolución por periodo temporal."
    )

    # ----- GRAFICOS HISTÓRICOS -----
    with st.expander("Ver evolución histórica de los indicadores clave"):
        tab_names = []
        tab_keys = []
        # Añade el tab combinado de PIB+PIBreal primero
        if "PIB" in macro_dict and "REALPIB" in macro_dict:
            tab_names.append("PIB y PIB real")
            tab_keys.append("PIB_REALPIB")
        # Recorre macro_blocks para mantener orden y legibilidad
        macro_keys = [k for block in MACRO_BLOCKS for k, *_ in block["kpis"]]
        for k in macro_keys:
            if k in ("PIB", "REALPIB"):
                continue
            if k in macro_dict and k in PRETTY_TABS:
                tab_names.append(PRETTY_TABS[k])
                tab_keys.append(k)
        # (Opcional, por si alguna clave extra: asegúrate de no duplicar)
        if "INTRATE" in macro_dict and "INTRATE" not in tab_keys:
            tab_names.append(PRETTY_TABS["INTRATE"])
            tab_keys.append("INTRATE")
        tabs = st.tabs(tab_names)
        for i, key in enumerate(tab_keys):
            if key == "PIB_REALPIB":
                df_pib = macro_dict["PIB"][["date", "GDP"]]
                df_real = macro_dict["REALPIB"][["date", "GDPC1"]]
                df_merged = df_pib.merge(df_real, on="date", how="outer").sort_values("date")
                y_cols = []
                if "GDP" in df_merged.columns:
                    y_cols.append("GDP")
                if "GDPC1" in df_merged.columns:
                    y_cols.append("GDPC1")
                df_merged = df_merged.dropna(subset=y_cols, how='all')
                df_merged = filtra_periodo(df_merged, periodo)
                with tabs[i]:
                    if len(y_cols) > 0 and not df_merged.empty:
                        legend_map = {
                            "GDP": "PIB (nominal)",
                            "GDPC1": "PIB real"
                        }
                        fig = px.line(
                            df_merged, x="date", y=y_cols,
                            labels={"value": "PIB", "variable": "Indicador"},
                            title="Evolución PIB nominal y real"
                        )
                        for t in fig.data:
                            if t.name in legend_map:
                                t.name = legend_map[t.name]
                        fig.update_layout(height=270, margin=dict(l=5, r=5, t=35, b=18))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay datos suficientes para mostrar el PIB y PIB real.")
            else:
                if key not in macro_dict:
                    continue
                df = macro_dict[key].dropna()
                pretty = PRETTY_TABS.get(key, key)
                col_val = [c for c in df.columns if c != "date"][0]
                df_filtrado = filtra_periodo(df, periodo)
                df_filtrado = df_filtrado.dropna(subset=[col_val])
                with tabs[i]:
                    if not df_filtrado.empty:
                        fig = px.line(df_filtrado, x="date", y=col_val, title=f"Evolución de {pretty}")
                        fig.update_layout(height=270, margin=dict(l=5, r=5, t=35, b=18))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No hay datos suficientes para mostrar {pretty}.")

def show():
    vista_market()
