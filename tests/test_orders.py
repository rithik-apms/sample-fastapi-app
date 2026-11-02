from decimal import Decimal


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert {"service", "environment", "release_sha"} <= body.keys()


def test_list_products(client):
    skus = {p["sku"] for p in client.get("/api/products").json()}
    assert skus == {"MUG", "TSHIRT", "GIFTCARD"}


def test_create_and_read_order(client, make_order):
    order = make_order([("MUG", 2), ("TSHIRT", 1)], coupon_code="welcome10")

    assert order["id"] == "ord-0001"
    assert order["status"] == "pending"
    assert order["coupon_code"] == "WELCOME10"
    assert Decimal(order["discount"]) == Decimal("4.50")
    assert client.get(f"/api/orders/{order['id']}").json() == order


def test_amount_off_coupon_never_exceeds_subtotal(make_order):
    order = make_order([("MUG", 1)], coupon_code="SAVE5")
    assert Decimal(order["discount"]) == Decimal("5.00")


def test_unknown_product_is_rejected(client):
    response = client.post("/api/orders", json={"items": [{"sku": "NOPE", "quantity": 1}]})
    assert response.status_code == 400
    assert "Unknown product" in response.json()["detail"]


def test_unknown_coupon_is_rejected(client):
    response = client.post(
        "/api/orders", json={"items": [{"sku": "MUG", "quantity": 1}], "coupon_code": "FREE"}
    )
    assert response.status_code == 400


def test_quantity_bounds(client):
    for quantity in (0, 11):
        response = client.post("/api/orders", json={"items": [{"sku": "MUG", "quantity": quantity}]})
        assert response.status_code == 422


def test_empty_order_is_rejected(client):
    assert client.post("/api/orders", json={"items": []}).status_code == 422


def test_missing_order_returns_404(client):
    assert client.get("/api/orders/ord-9999").status_code == 404
