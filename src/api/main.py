from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os

from src.common.db import get_db
from src.common.models import Product

# --- FastAPI app init ---
app = FastAPI(
    title="SupplyChain AI Backend",
    version=os.getenv("APP_VERSION", "0.0.1")
)

# --- Routers ---
from src.api import upload, analytics
app.include_router(upload.router)
app.include_router(analytics.router)

# --- Product schema ---
class ProductIn(BaseModel):
    sku: str
    name: str
    category: str | None = None

class ProductOut(ProductIn):
    product_id: int

# --- Product endpoints ---
@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductIn, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    p = Product(sku=payload.sku, name=payload.name, category=payload.category or "")
    db.add(p)
    db.commit()
    db.refresh(p)
    return ProductOut(product_id=p.product_id, sku=p.sku, name=p.name, category=p.category)

@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.product_id.desc()).all()
    return [ProductOut(product_id=p.product_id, sku=p.sku, name=p.name, category=p.category) for p in products]

# --- Health routes ---
@app.get("/health")
def health():
    return {"status": "ok", "env": os.getenv("APP_ENV", "dev")}

# --- Mount Dash Dashboard ---
from src.api.dashboard import create_dash_app
from starlette.middleware.wsgi import WSGIMiddleware

dash_app = create_dash_app()
app.mount("/dashboard", WSGIMiddleware(dash_app.server))

# --- Root route ---
@app.get("/")
def root():
    return {
        "msg": "SupplyChain AI running",
        "dashboard": "/dashboard",
        "docs": "/docs"
    }
