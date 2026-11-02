from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Product(BaseModel):
    sku: str
    name: str
    unit_price: Decimal
    weight_kg: Decimal | None = None


class OrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    weight_kg: Decimal | None = None


class Order(BaseModel):
    id: str
    items: list[OrderItem]
    coupon_code: str | None = None
    discount: Decimal | None = None
    points_multiplier: Decimal | None = None
    status: Literal["pending", "paid"] = "pending"
    amount_paid: Decimal | None = None
    created_at: datetime
    paid_at: datetime | None = None


class OrderItemIn(BaseModel):
    sku: str
    quantity: int = Field(ge=1, le=10)


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=10)
    coupon_code: str | None = Field(default=None, max_length=32)
