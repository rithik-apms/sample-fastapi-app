from app import db


def add_order(conn, coupon_code, discount, free_shipping):
    conn.execute(
        """
        INSERT INTO orders (customer_email, coupon_code, discount, free_shipping, delivery_method, country,
                            shipping_fee, status, created_at)
        VALUES ('alice@example.com', ?, ?, ?, 'standard', 'US', '0.00', 'pending', '2026-11-03T10:00:00+00:00')
        """,
        (coupon_code, discount, free_shipping),
    )


def test_start_up_gives_old_free_shipping_orders_a_zero_discount(tmp_path):
    path = str(tmp_path / "app.db")
    db.init(path)
    with db.transaction() as conn:
        add_order(conn, "FREESHIP", None, 1)    # saved before the 0.00 discount was recorded
        add_order(conn, None, None, 0)          # no coupon: no discount is correct
        add_order(conn, "WELCOME10", "2.50", 0)

    db.init(path)
    db.init(path)  # every start runs it again; nothing more changes

    with db.transaction() as conn:
        rows = [tuple(row) for row in conn.execute("SELECT coupon_code, discount FROM orders ORDER BY id")]
    assert rows == [("FREESHIP", "0.00"), (None, None), ("WELCOME10", "2.50")]
