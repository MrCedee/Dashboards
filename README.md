# Dashboards

> **Experimental dashboards for investment portfolio analytics and decision support, integrating Big Data and Visual Analytics.**

## Overview

This repository contains an experimental pilot for interactive financial dashboards, aimed at demonstrating how advanced data handling and visualization techniques can enhance investment portfolio analysis and decision-making. The pilot allows users to explore portfolio allocations, historical market data, and key financial indicators through a set of interactive panels—without requiring complex setup or model training.

## Features

* **Preloaded financial datasets**: All necessary CSV files are included in `/data` (no external downloads required).
* **Ready-to-use dashboards**: Explore portfolio weights, transactions, performance, market indicators, and scenario analysis.
* **Modular app structure**: Each dashboard is implemented as an independent, reusable view.
* **Comparison with benchmarks**: Instantly compare your portfolio with indices such as S\&P 500 and other financial metrics.
* **No machine learning models required**: All features are data-driven and focus on interpretability and transparency.

## Project Structure

```
/
├── data/                # All datasets: historical prices, weights, benchmarks, macro indicators (CSV)
├── notebooks/           # Jupyter/Colab notebooks for auxiliary data preparation (optional)
├── src/
│   ├── views/           # Streamlit dashboard views (e.g. portfolio, transactions, market overview)
│   └── utils/           # Data loading, metrics, helpers
├── requirements.txt     # Python dependencies
├── config.py            # Configuration (paths, settings)
├── LICENSE
└── README.md
```

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/MrCedee/Dashboards.git
   cd Dashboards
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Check/adjust `config.py`**
   Ensure the paths to your `/data` directory are correct.

5. **Launch the dashboards**

   ```bash
   streamlit run src/dashboards/portfolio_dashboard.py
   ```

## Technologies

* **Streamlit** – Fast web app framework for interactive dashboards.
* **Pandas / NumPy** – Data manipulation and analysis.
* **Plotly** – High-quality interactive charts.
* **Python** – Unified data pipeline.

## Limitations

* Offline use only (no real-time updates or external data connections).
* No user management or trading functionality.
* Dataset limited to included CSVs (29 assets, equities only).
* Designed as a demo/prototype for research and educational purposes.

## License

MIT License – see `LICENSE` for details.

## Author

[Marcos Cedenilla Bonet](https://github.com/MrCedee)
