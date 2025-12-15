from sqlalchemy import String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Product(Base):
    __tablename__ = "product_dim"
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=True)

class Location(Base):
    __tablename__ = "location_dim"
    location_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(16))  # store/wh/dc
    city: Mapped[str] = mapped_column(String(64))
    region: Mapped[str] = mapped_column(String(64))

class SalesFact(Base):
    __tablename__ = "sales_fact"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_key: Mapped[Date] = mapped_column(Date, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product_dim.product_id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("location_dim.location_id"), index=True)
    units: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshot"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[DateTime] = mapped_column(DateTime, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product_dim.product_id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("location_dim.location_id"), index=True)
    on_hand: Mapped[float] = mapped_column(Float, default=0.0)
    on_order: Mapped[float] = mapped_column(Float, default=0.0)
    backorder: Mapped[float] = mapped_column(Float, default=0.0)
