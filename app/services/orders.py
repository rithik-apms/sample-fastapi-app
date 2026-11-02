import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

from app import db, repository
from app.models import Order, OrderCreate, OrderItem
from app.services.errors import InvalidOrder, OrderNotFound
from app.services.pricing import CENT, subtotal
from app.services.shipping import COUNTRIES, delivery_fee

# code -> (kind, value)
COUPONS: dict[str, tuple[str, Decimal]] = {
    "WELCOME10": ("percent_off", Decimal("10")),
    "SAVE5": ("amount_off", Decimal("5.00")),
    "DOUBLEPTS": ("points_multiplier", Decimal("2")),
    "FREESHIP": ("free_shipping", Decimal("0")),
}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_order(data: OrderCreate) -> Order:
    with db.transaction() as conn:
        items = []
        for line in data.items:
            product = repository.get_product(conn, line.sku)
            if product is None:
                raise InvalidOrder(f"Unknown product: {line.sku}")
            if any(item.sku == product.sku for item in items):
                raise InvalidOrder(f"{product.name} is listed more than once")
            if line.quantity > product.stock:
                raise InvalidOrder(f"Not enough stock for {product.name} (available: {product.stock})")
            items.append(
                OrderItem(
                    sku=product.sku,
                    name=product.name,
                    quantity=line.quantity,
                    unit_price=product.unit_price,
                    weight_kg=product.weight_kg,
                )
            )

        country = data.country.upper()
        if country not in COUNTRIES:
            raise InvalidOrder(f"Unsupported country: {country}")

        coupon_code = (data.coupon_code or "").strip().upper() or None
        discount = None
        points_multiplier = None
        free_shipping = False
        if coupon_code is not None:
            if coupon_code not in COUPONS:
                raise InvalidOrder(f"Unknown coupon: {coupon_code}")
            kind, value = COUPONS[coupon_code]
            if kind == "percent_off":
                discount = (subtotal(items) * value / 100).quantize(CENT)
            elif kind == "amount_off":
                discount = min(value, subtotal(items))
            elif kind == "points_multiplier":
                discount = Decimal("0.00")
                points_multiplier = value
            elif kind == "free_shipping":
                free_shipping = True

        shipping_fee = Decimal("0.00") if free_shipping else delivery_fee(data.delivery_method, country)

        order_id = repository.insert_order(
            conn,
            customer_email=normalize_email(data.customer_email),
            items=items,
            coupon_code=coupon_code,
            discount=discount,
            points_multiplier=points_multiplier,
            free_shipping=free_shipping,
            delivery_method=data.delivery_method,
            country=country,
            shipping_fee=shipping_fee,
            created_at=datetime.now(timezone.utc),
        )
        return load_order(conn, order_id)


def load_order(conn: sqlite3.Connection, order_id: str) -> Order:
    order = repository.get_order(conn, order_id)
    if order is None:
        raise OrderNotFound(order_id)
    return order


def get_order(order_id: str) -> Order:
    with db.read() as conn:
        return load_order(conn, order_id)


def list_orders(status: str | None = None, customer_email: str | None = None) -> list[Order]:
    email = normalize_email(customer_email) if customer_email else None
    with db.read() as conn:
        return repository.list_orders(conn, status=status, customer_email=email)
