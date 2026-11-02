import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def empty_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_order(client):
    def _make(items, coupon_code=None):
        body = {"items": [{"sku": sku, "quantity": qty} for sku, qty in items]}
        if coupon_code is not None:
            body["coupon_code"] = coupon_code
        response = client.post("/api/orders", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
