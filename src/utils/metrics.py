import pandas as pd
import numpy as np

def get_last_value(df, col="portfolio_value"):
    """Devuelve el último valor de la cartera (o columna especificada)."""
    return df[col].iloc[-1]

def get_total_return(df, col="portfolio_value"):
    """Rentabilidad total entre primer y último valor."""
    return df[col].iloc[-1] / df[col].iloc[0] - 1

def get_daily_returns(df, col="portfolio_value"):
    """Serie de retornos diarios."""
    return df[col].pct_change().dropna()

def get_cumulative_return_series(df, col="portfolio_value"):
    """Serie de rentabilidad acumulada."""
    daily_ret = get_daily_returns(df, col)
    return (1 + daily_ret).cumprod() - 1

def get_var(returns, alpha=0.05):
    """Value at Risk (VaR) al 5% sobre una Serie de retornos diarios."""
    import numpy as np
    returns = pd.Series(returns).dropna()
    return np.percentile(returns, 100 * alpha)


# --- KPIs por activo ---
def get_best_and_worst_asset(df, value_col="asset_value", asset_col="asset"):
    """
    Devuelve el nombre y return del mejor y peor activo (según rentabilidad total).
    Espera un df con columnas 'asset', 'date', 'asset_value'.
    """
    res = {}
    grouped = df.groupby(asset_col)
    returns = grouped.apply(lambda x: x[value_col].iloc[-1] / x[value_col].iloc[0] - 1)
    best = returns.idxmax()
    worst = returns.idxmin()
    return {
        "best_asset": best,
        "best_return": returns.loc[best],
        "worst_asset": worst,
        "worst_return": returns.loc[worst],
    }


def get_annualized_return(df, col="portfolio_value", periods_per_year=252):
    """Annualized Return"""
    returns = get_daily_returns(df, col)
    n = returns.shape[0]
    total_ret = df[col].iloc[-1] / df[col].iloc[0]
    return total_ret ** (periods_per_year / n) - 1

def get_sharpe_ratio(df, col="portfolio_value", rf=0.0, periods_per_year=252):
    """Sharpe Ratio anualizado (asume retornos diarios, rf anualizado)"""
    returns = get_daily_returns(df, col)
    excess = returns - (rf / periods_per_year)
    return np.sqrt(periods_per_year) * excess.mean() / excess.std(ddof=1)

def get_sortino_ratio(df, col="portfolio_value", rf=0.0, periods_per_year=252):
    """Sortino Ratio anualizado"""
    returns = get_daily_returns(df, col)
    excess = returns - (rf / periods_per_year)
    downside = excess[excess < 0]
    denom = np.sqrt((downside ** 2).mean())
    if denom == 0:
        return np.nan
    return np.sqrt(periods_per_year) * excess.mean() / denom

def get_max_drawdown(df, col="portfolio_value"):
    """Máximo Drawdown"""
    series = df[col].cummax()
    drawdown = df[col] / series - 1
    return drawdown.min()

def get_alpha_beta(df_portfolio, df_bench, col_port="portfolio_value", col_bench="value"):
    """
    Alpha y Beta de la cartera frente a un benchmark.
    Espera dos dataframes con fechas alineadas.
    """
    ret_port = get_daily_returns(df_portfolio, col_port)
    ret_bench = get_daily_returns(df_bench, col_bench)
    min_len = min(len(ret_port), len(ret_bench))
    ret_port = ret_port[-min_len:]
    ret_bench = ret_bench[-min_len:]
    cov = np.cov(ret_port, ret_bench)
    beta = cov[0, 1] / cov[1, 1]
    alpha = ret_port.mean() - beta * ret_bench.mean()
    return alpha * 252, beta  # anualiza el alpha

def get_turnover(df_alloc, fecha_corte):
    """
    Calcula el turnover de la cartera: suma de los cambios absolutos en los pesos de los activos.
    df_alloc debe tener columnas: 'date', resto = activos (un activo por columna)
    """
    df_alloc = df_alloc.copy()
    df_alloc['date'] = pd.to_datetime(df_alloc['date'])
    df_alloc = df_alloc[df_alloc['date'] <= fecha_corte]
    df_alloc = df_alloc.sort_values('date')
    # Solo columnas de activos
    activos = [c for c in df_alloc.columns if c not in ['date']]
    df_activos = df_alloc[activos]
    turnover = df_activos.diff().abs().sum(axis=1).mean()
    return turnover


def get_effective_n(weights):
    """
    Diversificación efectiva: 1 / sum(weights**2).
    weights debe ser un array-like con los pesos de cada activo en el periodo.
    """
    weights = np.array(weights)
    return 1 / np.sum(weights ** 2)

def get_kpis(df, col="portfolio_value", rf=0.0, periods_per_year=252):
    """Devuelve todos los KPIs principales en un dict."""
    return {
        "total_return": get_total_return(df, col),
        "annualized_return": get_annualized_return(df, col, periods_per_year),
        "sharpe": get_sharpe_ratio(df, col, rf, periods_per_year),
        "sortino": get_sortino_ratio(df, col, rf, periods_per_year),
        "max_drawdown": get_max_drawdown(df, col),
        "var": get_var(get_daily_returns(df, col)),
    }

