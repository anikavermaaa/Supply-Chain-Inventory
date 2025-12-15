from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from src.common.db import get_db
from src.common.models import Product, SalesFact, InventorySnapshot
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/sales")
def upload_sales(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    data = pd.read_csv(BytesIO(file.file.read()))
    required_cols = {"date_key", "sku", "location_id", "units", "revenue"}
    if not required_cols.issubset(data.columns):
        raise HTTPException(status_code=400, detail=f"Missing required columns {required_cols}")

    inserted = 0
    for _, row in data.iterrows():
        product = db.query(Product).filter(Product.sku == row["sku"]).first()
        if not product:
            continue  # skip unknown SKUs
        db.add(SalesFact(
            date_key=pd.to_datetime(row["date_key"]).date(),
            product_id=product.product_id,
            location_id=int(row["location_id"]),
            units=float(row["units"]),
            revenue=float(row["revenue"])
        ))
        inserted += 1
    db.commit()
    return {"status": "ok", "rows_inserted": inserted}

@router.post("/inventory")
def upload_inventory(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    data = pd.read_csv(BytesIO(file.file.read()))
    required_cols = {"ts", "sku", "location_id", "on_hand", "on_order", "backorder"}
    if not required_cols.issubset(data.columns):
        raise HTTPException(status_code=400, detail=f"Missing required columns {required_cols}")

    inserted = 0
    for _, row in data.iterrows():
        product = db.query(Product).filter(Product.sku == row["sku"]).first()
        if not product:
            continue
        db.add(InventorySnapshot(
            ts=pd.to_datetime(row["ts"]),
            product_id=product.product_id,
            location_id=int(row["location_id"]),
            on_hand=float(row["on_hand"]),
            on_order=float(row["on_order"]),
            backorder=float(row["backorder"])
        ))
        inserted += 1
    db.commit()
    return {"status": "ok", "rows_inserted": inserted}
