from decimal import Decimal


def test_sales_report_for_range_with_paid_orders(client, make_order, pay, today):
    pay(make_order([("MUG", 2)])["id"])
    pay(make_order([("TSHIRT", 1)])["id"])
    make_order([("MUG", 1)])  # pending, not counted

    report = client.get("/api/reports/sales", params={"start": today, "end": today}).json()

    assert report["paid_orders"] == 2
    assert report["items_sold"] == 3
    assert Decimal(report["revenue"]) == Decimal("54.98")
    assert Decimal(report["average_order_value"]) == Decimal("27.49")


def test_cancelled_orders_are_excluded(client, make_order, pay, today):
    kept = make_order([("MUG", 1)])
    refunded = make_order([("TSHIRT", 1)])
    pay(kept["id"])
    pay(refunded["id"])
    client.post(f"/api/orders/{refunded['id']}/cancel")

    report = client.get("/api/reports/sales", params={"start": today, "end": today}).json()

    assert report["paid_orders"] == 1


def test_report_rejects_end_before_start(client):
    response = client.get("/api/reports/sales", params={"start": "2026-02-01", "end": "2026-01-01"})
    assert response.status_code == 400


def test_report_rejects_ranges_over_a_year(client):
    response = client.get("/api/reports/sales", params={"start": "2024-01-01", "end": "2026-01-01"})
    assert response.status_code == 400


def test_receipt_csv_for_paid_order(client, make_order, pay):
    order = make_order([("MUG", 2)], coupon_code="WELCOME10")
    pay(order["id"])

    response = client.get(f"/api/orders/{order['id']}/receipt.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "total_paid,27.49" in response.text


def test_receipt_for_unpaid_order_is_rejected(client, make_order):
    order = make_order([("MUG", 1)])
    assert client.get(f"/api/orders/{order['id']}/receipt.csv").status_code == 409
