import streamlit as st
import plotly.express as px
from src.utils.data_loader import load_benchmarks
from config import MARKETS_PATH
from datetime import timedelta

def get_last_and_change(df, col_value=None):
    col = col_value or [c for c in df.columns if c != "date"][0]
    vals = df.sort_values("date")[col].dropna()
    if len(vals) < 2:
        return None, None
    last = vals.iloc[-1]
    prev = vals.iloc[-2]
    pct = (last - prev) / abs(prev) * 100 if prev != 0 else None
    return last, pct

def badge(change):
    if change is None:
        return ""
    if change > 1:
        return "<span style='color:#3cb371;font-size:1.1em'>🡅</span>"
    elif change < -1:
        return "<span style='color:#d33;font-size:1.1em'>🡇</span>"
    else:
        return "<span style='color:#f5bb00;font-size:1.1em'>→</span>"

def info(texto):
    return f"<span style='color:#888;font-size:1.1em;vertical-align:middle' title='{texto}'>❓</span>"

MACRO_KPIS = {
    "PIB": ("PIB (nominal)", "Producto Interior Bruto nominal.", None),
    "REALPIB": ("PIB real", "PIB ajustado por inflación, mide crecimiento real.", None),
    "TASADES": ("Desempleo (%)", "Tasa de desempleo USA.", None),
    "CPI": ("IPC", "Índice de precios al consumo, proxy de inflación.", None),
    "CONFIDENCE": ("Confianza consumidor", "Expectativas/optimismo de los hogares.", None),
    "M2": ("M2", "Liquidez monetaria, dinero en circulación.", None),
    "VIXCLS": ("VIX (Volatilidad)", "Índice de volatilidad esperado S&P 500.", None),
    "DXY": ("Dólar (DXY)", "Índice del dólar frente a divisas.", None),
    "yield_curve": ("Curva de tipos", "Diferencial bonos USA 10y-2y, <0 suele anticipar recesión.", None),
    "INTRATE": ("Tasa interés", "Tipo de la Fed (DFF)", None),
    "DJ": ("Dow Jones", "Índice Dow Jones (industriales USA).", None),
    "NASDAQ100": ("Nasdaq 100", "Índice Nasdaq 100 (tecnología USA).", None),
    "OIL": ("Petróleo", "Precio del barril (CL=F).", None),
}

def market_summary(macro_dict):
    try:
        gdp, chg_gdp = get_last_and_change(macro_dict["PIB"])
        cpi, chg_cpi = get_last_and_change(macro_dict["CPI"])
        unemp, chg_unemp = get_last_and_change(macro_dict.get("UNRATE", macro_dict.get("TASADES")))
        vix, chg_vix = get_last_and_change(macro_dict["VIXCLS"])
        oil, chg_oil = get_last_and_change(macro_dict["OIL"])
        resumen = (
            f"El PIB actual es <b>{gdp:,.0f}</b> ({chg_gdp:+.2f}%) y la inflación está en <b>{cpi:.2f}</b> ({chg_cpi:+.2f}%). "
            f"La tasa de desempleo es <b>{unemp:.2f}%</b> ({chg_unemp:+.2f}%). "
            f"El VIX se sitúa en <b>{vix:.1f}</b> y el precio del petróleo es <b>{oil:.2f}</b> ({chg_oil:+.2f}%)."
        )
    except Exception:
        resumen = "No hay suficientes datos recientes para mostrar el resumen ejecutivo."
    return resumen

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

def vista_market():
    st.title("Situación y evolución del mercado")

    macro_dict = load_benchmarks(MARKETS_PATH)

    # Resumen ejecutivo arriba
    st.markdown(
        f"<div style='padding:0.7em 1em;background:#f7f8fb;border-radius:10px;margin-bottom:1.2em;font-size:1.13em;'>"
        f"{market_summary(macro_dict)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # KPIs principales en grid compacta
    kpi_cols = st.columns(4)
    macro_keys = list(MACRO_KPIS.keys())
    for i, key in enumerate(macro_keys):
        if key not in macro_dict:
            continue
        if key == "REALPIB":
            continue  # No mostrar KPI extra para PIB real
        df = macro_dict[key]
        pretty, tooltip, col_val = MACRO_KPIS[key]
        val, pct = get_last_and_change(df, col_val)
        badge_html = badge(pct)
        val_fmt = f"{val:,.2f}" if val is not None else "N/A"
        diff_fmt = f" <span style='color:gray;font-size:0.99em'>({pct:+.2f}%)</span>" if pct is not None else ""
        col = kpi_cols[i % 4]
        col.markdown(
            f"<div style='font-weight:bold'>{pretty} {info(tooltip)}</div>"
            f"<span style='font-size:1.5em'>{val_fmt}{diff_fmt} {badge_html}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    # Selector de periodo para gráficos históricos
    periodo = st.radio(
        "Selecciona periodo para los gráficos históricos:",
        ["Histórico completo", "Último año", "Últimos 5 años", "Últimos 10 años"],
        horizontal=True,
        help="Filtra los gráficos de evolución por periodo temporal."
    )

    with st.expander("Ver evolución histórica de los indicadores clave"):
        tab_names = []
        tab_keys = []
        if "PIB" in macro_dict and "REALPIB" in macro_dict:
            tab_names.append("PIB y PIB real")
            tab_keys.append("PIB_REALPIB")
        for k in macro_keys:
            if k in ("PIB", "REALPIB"):
                continue
            if k in macro_dict:
                tab_names.append(MACRO_KPIS[k][0])
                tab_keys.append(k)
        if "INTRATE" in macro_dict and "INTRATE" not in tab_keys:
            tab_names.append(MACRO_KPIS["INTRATE"][0])
            tab_keys.append("INTRATE")
        tabs = st.tabs(tab_names)
        for i, key in enumerate(tab_keys):
            if key == "PIB_REALPIB":
                df_pib = macro_dict["PIB"][["date", "GDP"]]       # Solo 'date' y 'GDP'
                df_real = macro_dict["REALPIB"][["date", "GDPC1"]] # Solo 'date' y 'GDPC1'
                df_merged = df_pib.merge(df_real, on="date", how="outer").sort_values("date")
                y_cols = []
                if "GDP" in df_merged.columns:
                    y_cols.append("GDP")
                if "GDPC1" in df_merged.columns:
                    y_cols.append("GDPC1")
                # Solo elimina filas donde ambos sean nan
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
                        # Renombrar leyendas de las líneas
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
                df = macro_dict[key].dropna()  # Aquí sí eliminamos nan
                pretty, tooltip, col_val = MACRO_KPIS[key]
                col_val = col_val or [c for c in df.columns if c != "date"][0]
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
