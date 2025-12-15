from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.common.db import get_db
from src.common.models import Product, SalesFact, InventorySnapshot
from datetime import date, timedelta
from sqlalchemy import func

# import optimization helper
from src.ai.optimizer import optimize_inventory

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ----------------- SUMMARY -----------------
@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    rows = (
        db.query(Product.sku, func.sum(SalesFact.units), func.sum(SalesFact.revenue))
        .join(SalesFact, Product.product_id == SalesFact.product_id)
        .group_by(Product.sku)
        .all()
    )
    return [
        {"sku": sku, "total_units": int(units or 0), "total_revenue": float(revenue or 0)}
        for sku, units, revenue in rows
    ]

# ----------------- LOW STOCK ALERTS -----------------
@router.get("/low_stock")
def low_stock(db: Session = Depends(get_db)):
    subq = (
        db.query(
            InventorySnapshot.product_id,
            func.max(InventorySnapshot.ts).label("latest_ts")
        )
        .group_by(InventorySnapshot.product_id)
        .subquery()
    )
    q = (
        db.query(Product.sku, InventorySnapshot.on_hand)
        .join(subq, (subq.c.product_id == InventorySnapshot.product_id) &
                    (subq.c.latest_ts == InventorySnapshot.ts))
        .join(Product, Product.product_id == InventorySnapshot.product_id)
        .filter(InventorySnapshot.on_hand < 10)
        .all()
    )
    return [{"sku": sku, "on_hand": float(on_hand)} for sku, on_hand in q]

# ----------------- DEMAND FORECAST -----------------
@router.get("/demand_forecast")
def demand_forecast(db: Session = Depends(get_db)):
    today = date.today()
    start = today - timedelta(days=7)
    data = (
        db.query(Product.sku, func.avg(SalesFact.units).label("avg_units"))
        .join(SalesFact, Product.product_id == SalesFact.product_id)
        .filter(SalesFact.date_key >= start)
        .group_by(Product.sku)
        .all()
    )
    return [
        {"sku": sku, "predicted_next_day_units": round(avg_units or 0, 2)}
        for sku, avg_units in data
    ]

# ----------------- OPTIMIZE INVENTORY -----------------
@router.get("/optimize_inventory")
def optimize_inventory_route(db: Session = Depends(get_db)):
    """
    Suggests how many units to reorder per SKU
    based on forecasted demand and current stock.
    """
    # 1️⃣ Get forecasted demand
    forecast_data = (
        db.query(Product.sku, func.avg(SalesFact.units))
        .join(SalesFact, Product.product_id == SalesFact.product_id)
        .group_by(Product.sku)
        .all()
    )
    forecasts = {sku: float(avg or 0) for sku, avg in forecast_data}

    # 2️⃣ Get latest inventory snapshot
    subq = (
        db.query(
            InventorySnapshot.product_id,
            func.max(InventorySnapshot.ts).label("latest_ts")
        )
        .group_by(InventorySnapshot.product_id)
        .subquery()
    )
    stock_data = (
        db.query(Product.sku, InventorySnapshot.on_hand)
        .join(subq, (subq.c.product_id == InventorySnapshot.product_id) &
                    (subq.c.latest_ts == InventorySnapshot.ts))
        .join(Product, Product.product_id == InventorySnapshot.product_id)
        .all()
    )
    stock = {sku: float(on_hand or 0) for sku, on_hand in stock_data}

    # 3️⃣ Assume reorder cost per unit = 1 for now
    reorder_cost = {sku: 1.0 for sku in forecasts}

    # 4️⃣ Run optimizer
    if not forecasts or not stock:
        return {"message": "No data available for optimization."}

    result = optimize_inventory(forecasts, stock, reorder_cost)

    return {"suggested_orders": result}
