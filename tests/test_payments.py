from decimal import Decimal


def test_pay_order_with_percent_coupon(client, make_order):
    order = make_order([("MUG", 2), ("TSHIRT", 1)], coupon_code="WELCOME10")

    response = client.post(f"/api/orders/{order['id']}/pay")

    assert response.status_code == 200
    paid = response.json()
    assert paid["status"] == "paid"
    assert Decimal(paid["amount_paid"]) == Decimal("40.50")
    assert paid["paid_at"] is not None


def test_pay_order_with_amount_coupon(client, make_order):
    order = make_order([("TSHIRT", 2)], coupon_code="SAVE5")
    paid = client.post(f"/api/orders/{order['id']}/pay").json()
    assert Decimal(paid["amount_paid"]) == Decimal("35.00")


def test_paying_twice_is_rejected(client, make_order):
    order = make_order([("MUG", 1)], coupon_code="WELCOME10")
    client.post(f"/api/orders/{order['id']}/pay")
    assert client.post(f"/api/orders/{order['id']}/pay").status_code == 409


def test_paying_missing_order_returns_404(client):
    assert client.post("/api/orders/ord-9999/pay").status_code == 404


def test_refund_quote_for_paid_order(client, make_order):
    order = make_order([("TSHIRT", 1)], coupon_code="SAVE5")
    client.post(f"/api/orders/{order['id']}/pay")

    refund = client.get(f"/api/orders/{order['id']}/refund-quote").json()

    assert Decimal(refund["refund_amount"]) == Decimal("13.00")


def test_refund_quote_for_unpaid_order_is_zero(client, make_order):
    order = make_order([("MUG", 1)])
    refund = client.get(f"/api/orders/{order['id']}/refund-quote").json()
    assert Decimal(refund["refund_amount"]) == Decimal("0.00")
