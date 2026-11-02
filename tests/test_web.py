def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "New order" in response.text


def test_create_and_pay_through_ui(client):
    response = client.post(
        "/orders",
        data={"qty_MUG": "1", "qty_TSHIRT": "0", "qty_GIFTCARD": "0", "coupon_code": "SAVE5"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    order_url = response.headers["location"]

    page = client.get(order_url)
    assert page.status_code == 200
    assert "Pay now" in page.text

    paid = client.post(f"{order_url}/pay", follow_redirects=True)
    assert paid.status_code == 200
    assert "Refund if cancelled now" in paid.text


def test_ui_rejects_empty_order(client):
    response = client.post("/orders", data={"qty_MUG": "0", "coupon_code": ""})
    assert response.status_code == 400
    assert "at least one product" in response.text


def test_ui_rejects_unknown_coupon(client):
    response = client.post("/orders", data={"qty_MUG": "1", "coupon_code": "FREE"})
    assert response.status_code == 400
    assert "Unknown coupon" in response.text
