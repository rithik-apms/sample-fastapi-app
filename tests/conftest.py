from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(
        service_name="sample-fastapi",
        environment="test",
        release_sha="test-sha",
        database_path=str(tmp_path / "app.db"),
        seed_demo_data=False,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def make_order(client):
    def _make(items, coupon_code=None, email="alice@example.com", delivery_method="standard", country="US"):
        body = {
            "customer_email": email,
            "items": [{"sku": sku, "quantity": qty} for sku, qty in items],
            "delivery_method": delivery_method,
            "country": country,
        }
        if coupon_code is not None:
            body["coupon_code"] = coupon_code
        response = client.post("/api/orders", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def pay(client):
    def _pay(order_id):
        response = client.post(f"/api/orders/{order_id}/pay")
        assert response.status_code == 200, response.text
        return response.json()

    return _pay


@pytest.fixture
def today():
    return datetime.now(timezone.utc).date().isoformat()


@pytest.fixture
def stock_of(client):
    def _stock(sku):
        return next(p["stock"] for p in client.get("/api/products").json() if p["sku"] == sku)

    return _stock
