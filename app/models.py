from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

DeliveryMethod = Literal["standard", "express"]
OrderStatus = Literal["pending", "paid", "cancelled"]


class Product(BaseModel):
    sku: str
    name: str
    unit_price: Decimal
    weight_kg: Decimal | None = None
    stock: int


class OrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    weight_kg: Decimal | None = None


class Order(BaseModel):
    id: str
    customer_email: str
    items: list[OrderItem]
    coupon_code: str | None = None
    discount: Decimal | None = None
    points_multiplier: Decimal | None = None
    free_shipping: bool = False
    delivery_method: DeliveryMethod
    country: str
    shipping_fee: Decimal
    status: OrderStatus = "pending"
    amount_paid: Decimal | None = None
    refund_amount: Decimal | None = None
    created_at: datetime
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None


class OrderItemIn(BaseModel):
    sku: str
    quantity: int = Field(ge=1, le=10)


class OrderCreate(BaseModel):
    customer_email: str = Field(pattern=EMAIL_PATTERN, max_length=254)
    items: list[OrderItemIn] = Field(min_length=1, max_length=10)
    coupon_code: str | None = Field(default=None, max_length=32)
    delivery_method: DeliveryMethod = "standard"
    country: str = Field(default="US", min_length=2, max_length=2)


class SalesReport(BaseModel):
    start: date
    end: date
    paid_orders: int
    items_sold: int
    revenue: Decimal
    average_order_value: Decimal
