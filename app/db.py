"""SQLite connections and schema."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku         TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    unit_price  TEXT NOT NULL,
    weight_kg   TEXT,
    stock       INTEGER NOT NULL CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_email    TEXT NOT NULL,
    coupon_code       TEXT,
    discount          TEXT,
    points_multiplier TEXT,
    free_shipping     INTEGER NOT NULL DEFAULT 0,
    delivery_method   TEXT NOT NULL,
    country           TEXT NOT NULL,
    shipping_fee      TEXT NOT NULL,
    status            TEXT NOT NULL,
    amount_paid       TEXT,
    refund_amount     TEXT,
    created_at        TEXT NOT NULL,
    paid_at           TEXT,
    cancelled_at      TEXT
);
CREATE INDEX IF NOT EXISTS orders_customer_email ON orders (customer_email);
CREATE INDEX IF NOT EXISTS orders_paid_at ON orders (paid_at);

CREATE TABLE IF NOT EXISTS order_items (
    order_id    INTEGER NOT NULL REFERENCES orders (id),
    line_no     INTEGER NOT NULL,
    sku         TEXT NOT NULL REFERENCES products (sku),
    name        TEXT NOT NULL,
    quantity    INTEGER NOT NULL,
    unit_price  TEXT NOT NULL,
    weight_kg   TEXT,
    PRIMARY KEY (order_id, line_no)
);
"""

_database_path: Path | None = None


def init(path: str) -> None:
    """Point the app at a database file and create the schema if needed."""
    global _database_path
    _database_path = Path(path)
    _database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def _connect() -> sqlite3.Connection:
    if _database_path is None:
        raise RuntimeError("Database is not initialised")
    conn = sqlite3.connect(_database_path, timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Write transaction; takes the write lock up front so read-check-write sequences are atomic."""
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


@contextmanager
def read() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()
