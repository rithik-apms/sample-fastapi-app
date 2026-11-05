from decimal import Decimal

from app import db


def test_pay_order_without_coupon(make_order, pay):
    paid = pay(make_order([("MUG", 2)])["id"])

    assert paid["status"] == "paid"
    assert Decimal(paid["amount_paid"]) == Decimal("29.99")
    assert paid["paid_at"] is not None


def test_pay_order_with_percent_coupon(make_order, pay):
    paid = pay(make_order([("MUG", 2), ("TSHIRT", 1)], coupon_code="WELCOME10")["id"])
    assert Decimal(paid["amount_paid"]) == Decimal("45.49")


def test_pay_order_with_amount_coupon(make_order, pay):
    paid = pay(make_order([("TSHIRT", 2)], coupon_code="SAVE5")["id"])
    assert Decimal(paid["amount_paid"]) == Decimal("39.99")


def test_pay_order_with_points_coupon(make_order, pay):
    paid = pay(make_order([("TSHIRT", 1)], coupon_code="DOUBLEPTS")["id"])
    assert Decimal(paid["amount_paid"]) == Decimal("24.99")


def test_pay_order_with_express_delivery(make_order, pay):
    paid = pay(make_order([("MUG", 1)], delivery_method="express", country="GB")["id"])
    assert Decimal(paid["amount_paid"]) == Decimal("29.49")


def test_payment_reduces_stock(make_order, pay, stock_of):
    pay(make_order([("MUG", 2)])["id"])
    assert stock_of("MUG") == 48


def test_paying_twice_is_rejected(client, make_order, pay):
    order = make_order([("MUG", 1)])
    pay(order["id"])
    assert client.post(f"/api/orders/{order['id']}/pay").status_code == 409


def test_paying_when_stock_ran_out_is_rejected(client, make_order, pay):
    orders = [make_order([("TSHIRT", 10)]) for _ in range(4)]
    for order in orders[:3]:
        pay(order["id"])

    response = client.post(f"/api/orders/{orders[3]['id']}/pay")

    assert response.status_code == 409
    assert "out of stock" in response.json()["detail"]


def test_paying_missing_order_returns_404(client):
    assert client.post("/api/orders/ord-9999/pay").status_code == 404


def test_pay_order_with_free_shipping_coupon(make_order, pay):
    paid = pay(make_order([("MUG", 2)], coupon_code="FREESHIP")["id"])

    assert paid["status"] == "paid"
    assert Decimal(paid["amount_paid"]) == Decimal("25.00")


def test_free_shipping_order_saved_without_a_discount_can_be_paid(make_order, pay):
    order = make_order([("MUG", 2)], coupon_code="FREESHIP")
    with db.transaction() as conn:  # as orders were saved before the 0.00 discount was recorded
        conn.execute("UPDATE orders SET discount = NULL WHERE id = ?", (int(order["id"].removeprefix("ord-")),))

    paid = pay(order["id"])

    assert paid["status"] == "paid"
    assert Decimal(paid["amount_paid"]) == Decimal("25.00")
