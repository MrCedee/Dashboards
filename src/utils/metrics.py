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
