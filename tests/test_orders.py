from decimal import Decimal


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["release_sha"] == "test-sha"


def test_list_products_with_stock(client):
    stock = {p["sku"]: p["stock"] for p in client.get("/api/products").json()}
    assert stock == {"MUG": 50, "TSHIRT": 30, "GIFTCARD": 1000}


def test_create_and_read_order(client, make_order):
    order = make_order([("MUG", 2), ("TSHIRT", 1)], coupon_code="welcome10", email="Alice@Example.com")

    assert order["id"] == "ord-0001"
    assert order["customer_email"] == "alice@example.com"
    assert order["status"] == "pending"
    assert order["coupon_code"] == "WELCOME10"
    assert Decimal(order["discount"]) == Decimal("4.50")
    assert order["delivery_method"] == "standard"
    assert order["country"] == "US"
    assert Decimal(order["shipping_fee"]) == Decimal("4.99")
    assert client.get(f"/api/orders/{order['id']}").json() == order


def test_amount_off_coupon(make_order):
    order = make_order([("MUG", 1)], coupon_code="SAVE5")
    assert Decimal(order["discount"]) == Decimal("5.00")


def test_free_shipping_coupon_sets_fee_to_zero(make_order):
    order = make_order([("MUG", 1)], coupon_code="FREESHIP", delivery_method="express", country="GB")
    assert order["free_shipping"] is True
    assert Decimal(order["shipping_fee"]) == Decimal("0.00")


def test_delivery_fees(make_order):
    cases = [("standard", "US", "4.99"), ("standard", "GB", "5.99"), ("standard", "IN", "7.99"),
             ("express", "US", "14.99"), ("express", "DE", "16.99")]
    for method, country, fee in cases:
        order = make_order([("TSHIRT", 1)], delivery_method=method, country=country)
        assert Decimal(order["shipping_fee"]) == Decimal(fee), (method, country)


def test_unsupported_country_is_rejected(client):
    response = client.post(
        "/api/orders",
        json={"customer_email": "a@example.com", "items": [{"sku": "MUG", "quantity": 1}], "country": "JP"},
    )
    assert response.status_code == 400
    assert "Unsupported country" in response.json()["detail"]


def test_invalid_email_is_rejected(client):
    response = client.post("/api/orders", json={"customer_email": "not-an-email", "items": [{"sku": "MUG", "quantity": 1}]})
    assert response.status_code == 422


def test_unknown_product_is_rejected(client):
    response = client.post("/api/orders", json={"customer_email": "a@example.com", "items": [{"sku": "NOPE", "quantity": 1}]})
    assert response.status_code == 400
    assert "Unknown product" in response.json()["detail"]


def test_duplicate_product_lines_are_rejected(client):
    items = [{"sku": "MUG", "quantity": 1}, {"sku": "MUG", "quantity": 2}]
    response = client.post("/api/orders", json={"customer_email": "a@example.com", "items": items})
    assert response.status_code == 400


def test_unknown_coupon_is_rejected(client):
    response = client.post(
        "/api/orders",
        json={"customer_email": "a@example.com", "items": [{"sku": "MUG", "quantity": 1}], "coupon_code": "FREE"},
    )
    assert response.status_code == 400


def test_quantity_bounds(client):
    for quantity in (0, 11):
        response = client.post(
            "/api/orders", json={"customer_email": "a@example.com", "items": [{"sku": "MUG", "quantity": quantity}]}
        )
        assert response.status_code == 422


def test_empty_order_is_rejected(client):
    assert client.post("/api/orders", json={"customer_email": "a@example.com", "items": []}).status_code == 422


def test_order_beyond_stock_is_rejected(client, make_order, pay):
    for _ in range(3):
        pay(make_order([("TSHIRT", 10)])["id"])

    response = client.post("/api/orders", json={"customer_email": "a@example.com", "items": [{"sku": "TSHIRT", "quantity": 1}]})

    assert response.status_code == 400
    assert "Not enough stock" in response.json()["detail"]


def test_filter_orders_by_status_and_email(client, make_order, pay):
    first = make_order([("MUG", 1)], email="alice@example.com")
    make_order([("MUG", 1)], email="bob@example.com")
    pay(first["id"])

    paid = client.get("/api/orders", params={"status": "paid"}).json()
    bobs = client.get("/api/orders", params={"email": "BOB@example.com"}).json()

    assert [o["id"] for o in paid] == [first["id"]]
    assert [o["customer_email"] for o in bobs] == ["bob@example.com"]


def test_missing_order_returns_404(client):
    assert client.get("/api/orders/ord-9999").status_code == 404
    assert client.get("/api/orders/not-an-id").status_code == 404


def test_loyalty_points_without_multiplier_coupon_use_base_points(client, make_order):
    order = make_order([("MUG", 2), ("TSHIRT", 1)])
    expected = int(sum(float(i["unit_price"]) * i["quantity"] for i in order["items"]))

    response = client.get(f"/api/orders/{order['id']}/loyalty-points")

    assert response.status_code == 200
    assert response.json() == {"order_id": order["id"], "points": expected}
    assert expected > 0
