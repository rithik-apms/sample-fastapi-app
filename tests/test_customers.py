from dataclasses import replace

from fastapi.testclient import TestClient

from app.main import create_app


def test_order_history_is_newest_first_and_per_customer(client, make_order):
    first = make_order([("MUG", 1)], email="bob@example.com")
    second = make_order([("TSHIRT", 1)], email="bob@example.com")
    make_order([("MUG", 1)], email="carol@example.com")

    history = client.get("/api/customers/Bob@example.com/orders").json()

    assert [o["id"] for o in history] == [second["id"], first["id"]]


def test_reorder_repeats_latest_order(client, make_order):
    make_order([("TSHIRT", 1)], email="bob@example.com")
    latest = make_order([("MUG", 2), ("TSHIRT", 1)], email="bob@example.com", delivery_method="express", country="GB",
                        coupon_code="SAVE5")

    response = client.post("/api/customers/bob@example.com/reorder")

    assert response.status_code == 201
    order = response.json()
    assert order["id"] != latest["id"]
    assert order["status"] == "pending"
    assert [(i["sku"], i["quantity"]) for i in order["items"]] == [("MUG", 2), ("TSHIRT", 1)]
    assert (order["delivery_method"], order["country"]) == ("express", "GB")
    assert order["coupon_code"] is None


def test_reorder_with_invalid_email_is_rejected(client):
    assert client.post("/api/customers/not-an-email/reorder").status_code == 400


def test_demo_data_is_seeded(settings):
    with TestClient(create_app(replace(settings, seed_demo_data=True))) as client:
        history = client.get("/api/customers/demo@example.com/orders").json()
        assert [o["status"] for o in history] == ["paid", "paid"]
        assert client.post("/api/customers/demo@example.com/reorder").status_code == 201
