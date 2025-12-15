# src/api/dashboard.py

import os
import requests
import pandas as pd
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# backend API base address
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# ------------------------ Data Fetchers ------------------------

def _fetch_forecast():
    """Fetch demand forecast data from backend API."""
    try:
        return pd.DataFrame(
            requests.get(f"{API_BASE}/analytics/demand_forecast").json()
        )
    except Exception:
        return pd.DataFrame(columns=["sku", "predicted_next_day_units"])


def _fetch_low_stock():
    """Fetch low-stock alerts from backend API."""
    try:
        return pd.DataFrame(
            requests.get(f"{API_BASE}/analytics/low_stock").json()
        )
    except Exception:
        return pd.DataFrame(columns=["sku", "on_hand", "location_id"])

# ------------------------ Dash App ------------------------

def create_dash_app(prefix: str = "/dashboard/") -> Dash:
    """Create the Dash dashboard embedded in FastAPI."""
    app = Dash(__name__, requests_pathname_prefix=prefix, title="SupplyChain AI Dashboard")

    # --- Graph builder functions ---
    def forecast_fig(df):
        if df.empty:
            return px.bar(title="No forecast data (upload sales first)")
        return px.bar(
            df,
            x="sku",
            y="predicted_next_day_units",
            color="sku",
            title="📦 Predicted Next-Day Demand per SKU",
        )

    def low_fig(df):
        if df.empty:
            return px.bar(title="✅ No Low Stock Detected")
        return px.bar(
            df,
            x="sku",
            y="on_hand",
            color="location_id",
            title="⚠️ Low Stock Levels by Location",
        )

    # Initial data
    df_forecast = _fetch_forecast()
    df_low = _fetch_low_stock()

    # --- Dashboard Layout ---
    app.layout = html.Div(
        style={"width": "90%", "margin": "auto"},
        children=[
            html.H1("SupplyChain AI Dashboard", style={"textAlign": "center"}),
            html.H3("Demand Forecast"),
            dcc.Graph(id="forecast-graph", figure=forecast_fig(df_forecast)),

            html.H3("Inventory Alerts", style={"marginTop": "40px"}),
            dcc.Graph(id="low-graph", figure=low_fig(df_low)),

            # auto-refresh every 15 seconds
            dcc.Interval(id="refresh", interval=15_000, n_intervals=0),
        ],
    )

    # --- Callbacks for live updates ---
    @app.callback(Output("forecast-graph", "figure"), Input("refresh", "n_intervals"))
    def update_forecast(_):
        return forecast_fig(_fetch_forecast())

    @app.callback(Output("low-graph", "figure"), Input("refresh", "n_intervals"))
    def update_low(_):
        return low_fig(_fetch_low_stock())

    return app
