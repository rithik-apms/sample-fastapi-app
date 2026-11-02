"""Initial catalog and optional demo data, inserted only into an empty database."""

import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import repository
from app.models import OrderItem, Product
from app.services.pricing import CENT, subtotal
from app.services.shipping import delivery_fee

PRODUCTS = [
    Product(sku="MUG", name="Coffee mug", unit_price=Decimal("12.50"), weight_kg=Decimal("0.40"), stock=50),
    Product(sku="TSHIRT", name="T-shirt", unit_price=Decimal("20.00"), weight_kg=Decimal("0.25"), stock=30),
    Product(sku="GIFTCARD", name="Gift card (e-mail delivery)", unit_price=Decimal("25.00"), stock=1000),
]

DEMO_EMAIL = "demo@example.com"
# (days ago, [(sku, quantity), ...])
DEMO_ORDERS = [
    (10, [("MUG", 2)]),
    (3, [("TSHIRT", 1), ("MUG", 1)]),
]


def seed(conn: sqlite3.Connection, demo: bool) -> None:
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        for product in PRODUCTS:
            repository.insert_product(conn, product)

    if not demo or conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] > 0:
        return

    catalog = {product.sku: product for product in PRODUCTS}
    now = datetime.now(timezone.utc)
    for days_ago, lines in DEMO_ORDERS:
        items = [
            OrderItem(
                sku=sku,
                name=catalog[sku].name,
                quantity=quantity,
                unit_price=catalog[sku].unit_price,
                weight_kg=catalog[sku].weight_kg,
            )
            for sku, quantity in lines
        ]
        fee = delivery_fee("standard", "US")
        placed_at = now - timedelta(days=days_ago)
        repository.insert_order(
            conn,
            customer_email=DEMO_EMAIL,
            items=items,
            coupon_code=None,
            discount=None,
            points_multiplier=None,
            free_shipping=False,
            delivery_method="standard",
            country="US",
            shipping_fee=fee,
            created_at=placed_at,
            status="paid",
            amount_paid=(subtotal(items) + fee).quantize(CENT),
            paid_at=placed_at,
        )
