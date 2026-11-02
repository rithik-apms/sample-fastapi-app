from decimal import Decimal


def test_cancel_pending_order(client, make_order, stock_of):
    order = make_order([("MUG", 2)])

    cancelled = client.post(f"/api/orders/{order['id']}/cancel").json()

    assert cancelled["status"] == "cancelled"
    assert cancelled["refund_amount"] is None
    assert cancelled["cancelled_at"] is not None
    assert stock_of("MUG") == 50


def test_cancel_paid_order_refunds_and_restocks(client, make_order, pay, stock_of):
    order = make_order([("MUG", 2)])
    pay(order["id"])

    cancelled = client.post(f"/api/orders/{order['id']}/cancel").json()

    assert cancelled["status"] == "cancelled"
    assert Decimal(cancelled["refund_amount"]) == Decimal("27.99")
    assert stock_of("MUG") == 50


def test_cancelling_twice_is_rejected(client, make_order):
    order = make_order([("MUG", 1)])
    client.post(f"/api/orders/{order['id']}/cancel")
    assert client.post(f"/api/orders/{order['id']}/cancel").status_code == 409


def test_refund_quote_for_paid_order(client, make_order, pay):
    order = make_order([("TSHIRT", 1)], coupon_code="SAVE5")
    pay(order["id"])

    refund = client.get(f"/api/orders/{order['id']}/refund-quote").json()

    assert Decimal(refund["refund_amount"]) == Decimal("17.99")


def test_refund_quote_for_unpaid_order_is_zero(client, make_order):
    order = make_order([("MUG", 1)])
    refund = client.get(f"/api/orders/{order['id']}/refund-quote").json()
    assert Decimal(refund["refund_amount"]) == Decimal("0.00")
