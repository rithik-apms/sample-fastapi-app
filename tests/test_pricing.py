from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models import Order, OrderItem
from app.services.pricing import amount_due


def order(**fields) -> Order:
    return Order(
        id="ord-0001",
        customer_email="alice@example.com",
        items=[OrderItem(sku="MUG", name="Coffee mug", quantity=2, unit_price=Decimal("12.50"))],
        delivery_method="standard",
        country="US",
        shipping_fee=Decimal("0.00"),
        created_at=datetime(2026, 11, 5, tzinfo=timezone.utc),
        **fields,
    )


def test_free_shipping_without_a_recorded_discount_takes_nothing_off():
    assert amount_due(order(coupon_code="FREESHIP", free_shipping=True)) == Decimal("25.00")


def test_other_coupon_without_a_discount_still_fails():
    with pytest.raises(TypeError):
        amount_due(order(coupon_code="WELCOME10"))
