import pandas as pd
import os

def load_portfolio_history(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date")
    return df

def load_asset_allocation(path):
    df = pd.read_csv(path)
    return df

def load_benchmarks(folder_path):
    """
    Devuelve un dict nombre -> df, con cada benchmark (csv) ya con su columna date parseada.
    """
    dfs = {}
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            key = os.path.splitext(file)[0]
            full_path = os.path.join(folder_path, file)
            dfs[key] = pd.read_csv(full_path, parse_dates=["date"])
    return dfs

# --- Función para cargar todo lo necesario para la vista general ---
def load_dashboard_general_data(portfolio_path, benchmarks_folder, allocation_path):
    portfolio = load_portfolio_history(portfolio_path)
    allocation = load_asset_allocation(allocation_path)
    benchmarks = load_benchmarks(benchmarks_folder)
    return portfolio, benchmarks, allocation
