"""Mapping between SQLite rows and the domain models."""

import re
import sqlite3
from datetime import datetime
from decimal import Decimal

from app.models import Order, OrderItem, Product

ORDER_ID = re.compile(r"^ord-(\d{1,9})$")
UPDATABLE_ORDER_COLUMNS = {"status", "amount_paid", "refund_amount", "paid_at", "cancelled_at"}


def public_order_id(row_id: int) -> str:
    return f"ord-{row_id:04d}"


def parse_order_id(order_id: str) -> int | None:
    match = ORDER_ID.match(order_id)
    return int(match.group(1)) if match else None


def _decimal(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


def _to_db(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat(timespec="microseconds")
    return value


def _product(row: sqlite3.Row) -> Product:
    return Product(
        sku=row["sku"],
        name=row["name"],
        unit_price=Decimal(row["unit_price"]),
        weight_kg=_decimal(row["weight_kg"]),
        stock=row["stock"],
    )


def list_products(conn: sqlite3.Connection) -> list[Product]:
    return [_product(row) for row in conn.execute("SELECT * FROM products ORDER BY rowid")]


def get_product(conn: sqlite3.Connection, sku: str) -> Product | None:
    row = conn.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
    return _product(row) if row else None


def insert_product(conn: sqlite3.Connection, product: Product) -> None:
    conn.execute(
        "INSERT INTO products (sku, name, unit_price, weight_kg, stock) VALUES (?, ?, ?, ?, ?)",
        (product.sku, product.name, _to_db(product.unit_price), _to_db(product.weight_kg), product.stock),
    )


def change_stock(conn: sqlite3.Connection, sku: str, delta: int) -> None:
    conn.execute("UPDATE products SET stock = stock + ? WHERE sku = ?", (delta, sku))


def insert_order(
    conn: sqlite3.Connection,
    *,
    customer_email: str,
    items: list[OrderItem],
    coupon_code: str | None,
    discount: Decimal | None,
    points_multiplier: Decimal | None,
    free_shipping: bool,
    delivery_method: str,
    country: str,
    shipping_fee: Decimal,
    created_at: datetime,
    status: str = "pending",
    amount_paid: Decimal | None = None,
    paid_at: datetime | None = None,
) -> str:
    cursor = conn.execute(
        """
        INSERT INTO orders (customer_email, coupon_code, discount, points_multiplier, free_shipping,
                            delivery_method, country, shipping_fee, status, amount_paid, created_at, paid_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_email, coupon_code, _to_db(discount), _to_db(points_multiplier), int(free_shipping),
            delivery_method, country, _to_db(shipping_fee), status, _to_db(amount_paid),
            _to_db(created_at), _to_db(paid_at),
        ),
    )
    row_id = cursor.lastrowid
    conn.executemany(
        """
        INSERT INTO order_items (order_id, line_no, sku, name, quantity, unit_price, weight_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (row_id, line_no, item.sku, item.name, item.quantity, _to_db(item.unit_price), _to_db(item.weight_kg))
            for line_no, item in enumerate(items, start=1)
        ],
    )
    return public_order_id(row_id)


def _order(conn: sqlite3.Connection, row: sqlite3.Row) -> Order:
    items = [
        OrderItem(
            sku=item["sku"],
            name=item["name"],
            quantity=item["quantity"],
            unit_price=Decimal(item["unit_price"]),
            weight_kg=_decimal(item["weight_kg"]),
        )
        for item in conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY line_no", (row["id"],))
    ]
    return Order(
        id=public_order_id(row["id"]),
        customer_email=row["customer_email"],
        items=items,
        coupon_code=row["coupon_code"],
        discount=_decimal(row["discount"]),
        points_multiplier=_decimal(row["points_multiplier"]),
        free_shipping=bool(row["free_shipping"]),
        delivery_method=row["delivery_method"],
        country=row["country"],
        shipping_fee=Decimal(row["shipping_fee"]),
        status=row["status"],
        amount_paid=_decimal(row["amount_paid"]),
        refund_amount=_decimal(row["refund_amount"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        paid_at=_datetime(row["paid_at"]),
        cancelled_at=_datetime(row["cancelled_at"]),
    )


def get_order(conn: sqlite3.Connection, order_id: str) -> Order | None:
    row_id = parse_order_id(order_id)
    if row_id is None:
        return None
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (row_id,)).fetchone()
    return _order(conn, row) if row else None


def list_orders(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    customer_email: str | None = None,
    limit: int = 200,
) -> list[Order]:
    sql = "SELECT * FROM orders WHERE 1 = 1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if customer_email:
        sql += " AND customer_email = ?"
        params.append(customer_email)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return [_order(conn, row) for row in conn.execute(sql, params).fetchall()]


def paid_orders_between(conn: sqlite3.Connection, start: datetime, end: datetime) -> list[Order]:
    rows = conn.execute(
        "SELECT * FROM orders WHERE status = 'paid' AND paid_at >= ? AND paid_at < ? ORDER BY paid_at",
        (_to_db(start), _to_db(end)),
    ).fetchall()
    return [_order(conn, row) for row in rows]


def update_order(conn: sqlite3.Connection, order_id: str, **fields) -> None:
    unknown = set(fields) - UPDATABLE_ORDER_COLUMNS
    if unknown:
        raise ValueError(f"Cannot update columns: {sorted(unknown)}")
    assignments = ", ".join(f"{column} = ?" for column in fields)
    conn.execute(
        f"UPDATE orders SET {assignments} WHERE id = ?",
        [*(_to_db(value) for value in fields.values()), parse_order_id(order_id)],
    )
