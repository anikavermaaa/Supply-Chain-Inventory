import requests
import pandas as pd
from dash import Dash, html, dcc
import plotly.express as px

API_BASE = "http://127.0.0.1:8000"   # your running FastAPI URL

# Fetch data from FastAPI
products = requests.get(f"{API_BASE}/products").json()
forecast = requests.get(f"{API_BASE}/analytics/demand_forecast").json()
low_stock = requests.get(f"{API_BASE}/analytics/low_stock").json()

forecast_df = pd.DataFrame(forecast)
low_df = pd.DataFrame(low_stock)

# Initialize Dash app
app = Dash(__name__, title="SupplyChain AI Dashboard")

# Figures
forecast_fig = px.bar(
    forecast_df, x="sku", y="predicted_next_day_units",
    color="sku", title="📦 Predicted Next-Day Demand per SKU"
)

if not low_df.empty:
    low_fig = px.bar(
        low_df, x="sku", y="on_hand",
        color="location_id", title="⚠️ Low Stock Levels by Location"
    )
else:
    low_fig = px.bar(title="✅ No Low Stock Detected")

# Layout
app.layout = html.Div([
    html.H1("SupplyChain AI Dashboard", style={"textAlign": "center"}),
    html.H3("Demand Forecast"),
    dcc.Graph(figure=forecast_fig),
    html.H3("Inventory Alerts", style={"marginTop": "40px"}),
    dcc.Graph(figure=low_fig)
])

if __name__ == "__main__":
    app.run(debug=True, port=8050)

