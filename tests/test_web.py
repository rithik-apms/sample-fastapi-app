def create_via_form(client, **fields):
    data = {"customer_email": "alice@example.com", "qty_MUG": "0", "qty_TSHIRT": "0", "qty_GIFTCARD": "0",
            "delivery_method": "standard", "country": "US", "coupon_code": ""}
    data.update(fields)
    return client.post("/orders", data=data, follow_redirects=False)


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "New order" in response.text
    assert "Buy again" in response.text


def test_products_page_shows_stock(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert "Coffee mug" in response.text


def test_create_pay_and_download_receipt_through_ui(client):
    response = create_via_form(client, qty_MUG="1", delivery_method="express", country="DE")
    assert response.status_code == 303
    order_url = response.headers["location"]

    page = client.get(order_url)
    assert "Pay now" in page.text
    assert "Express to Germany" in page.text

    paid = client.post(f"{order_url}/pay", follow_redirects=True)
    assert paid.status_code == 200
    assert "Refund if cancelled now" in paid.text

    receipt = client.get(f"{order_url}/receipt.csv")
    assert receipt.status_code == 200


def test_cancel_through_ui(client):
    order_url = create_via_form(client, qty_TSHIRT="1").headers["location"]
    page = client.post(f"{order_url}/cancel", follow_redirects=True)
    assert "Cancelled on" in page.text


def test_customer_page_and_reorder(client):
    create_via_form(client, qty_MUG="2", customer_email="bob@example.com")

    page = client.get("/customers/bob@example.com")
    assert page.status_code == 200
    assert "Repeat last order" in page.text

    response = client.post("/reorder", data={"customer_email": "bob@example.com"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/orders/ord-0002"


def test_customer_page_without_orders_has_no_reorder_button(client):
    page = client.get("/customers/nobody@example.com")
    assert "No orders yet" in page.text
    assert "Repeat last order" not in page.text


def test_report_page_shows_form_only_until_dates_are_given(client):
    response = client.get("/reports/sales")
    assert response.status_code == 200
    assert "Average order value" not in response.text


def test_report_page_with_results(client, today):
    order_url = create_via_form(client, qty_MUG="1").headers["location"]
    client.post(f"{order_url}/pay")

    response = client.get("/reports/sales", params={"start": today, "end": today})

    assert response.status_code == 200
    assert "Average order value" in response.text


def test_report_page_rejects_bad_dates(client):
    response = client.get("/reports/sales", params={"start": "2026-02-01", "end": "2026-01-01"})
    assert response.status_code == 400


def test_ui_rejects_empty_order(client):
    response = create_via_form(client)
    assert response.status_code == 400
    assert "at least one product" in response.text


def test_ui_rejects_invalid_email(client):
    response = create_via_form(client, qty_MUG="1", customer_email="nope")
    assert response.status_code == 400


def test_ui_rejects_unknown_coupon(client):
    response = create_via_form(client, qty_MUG="1", coupon_code="FREE")
    assert response.status_code == 400
    assert "Unknown coupon" in response.text


def test_ui_missing_order_shows_page(client):
    response = client.get("/orders/ord-9999")
    assert response.status_code == 404
    assert "Order not found" in response.text
    assert "<html" in response.text
