import json
import logging
import sys

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.logging_config import JsonFormatter, request_id_var
from app.main import create_app

SETTINGS = Settings(service_name="sample-fastapi", environment="test", release_sha="abc123")


def test_formatter_emits_required_fields():
    try:
        raise ValueError("boom")
    except ValueError:
        exc_info = sys.exc_info()

    token = request_id_var.set("req-1")
    try:
        record = logging.getLogger("t").makeRecord("t", logging.ERROR, __file__, 1, "boom", None, exc_info)
    finally:
        request_id_var.reset(token)
    event = json.loads(JsonFormatter(SETTINGS).format(record))

    assert event["service_name"] == "sample-fastapi"
    assert event["environment"] == "test"
    assert event["release_sha"] == "abc123"
    assert event["level"] == "ERROR"
    assert event["request_id"] == "req-1"
    assert event["exception_type"] == "ValueError"
    assert "Traceback" in event["stack_trace"]
    assert event["timestamp"].endswith("Z")


@pytest.fixture
def failing_client():
    app = create_app()

    @app.get("/api/explode")
    def explode():
        raise RuntimeError("internal detail that must not leak")

    @app.get("/explode")
    def explode_page():
        raise RuntimeError("internal detail that must not leak")

    with TestClient(app) as client:
        yield client


def test_unhandled_api_error_hides_internals(failing_client):
    response = failing_client.get("/api/explode", headers={"X-Request-ID": "req-test-1"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error", "request_id": "req-test-1"}
    assert response.headers["X-Request-ID"] == "req-test-1"


def test_unhandled_page_error_hides_internals(failing_client):
    response = failing_client.get("/explode")

    assert response.status_code == 500
    assert "Something went wrong" in response.text
    assert "must not leak" not in response.text
    assert "Traceback" not in response.text


def test_unhandled_error_is_logged_with_stack_trace(failing_client, caplog):
    failing_client.get("/api/explode", headers={"traceparent": "00-" + "a" * 32 + "-" + "b" * 16 + "-01"})

    record = next(r for r in caplog.records if getattr(r, "fields", {}).get("event") == "unhandled_exception")
    error = json.loads(JsonFormatter(SETTINGS).format(record))
    assert error["exception_type"] == "RuntimeError"
    assert error["path"] == "/api/explode"
    assert error["trace_id"] == "a" * 32
    assert error["request_id"].startswith("req-")
    assert "explode" in error["stack_trace"]


def test_invalid_request_id_is_replaced(client):
    response = client.get("/health", headers={"X-Request-ID": "bad id with spaces"})
    assert response.headers["X-Request-ID"].startswith("req-")
