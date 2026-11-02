from collections.abc import Iterable
from decimal import Decimal

from app.models import Order, OrderItem

CENT = Decimal("0.01")


def subtotal(items: Iterable[OrderItem]) -> Decimal:
    return sum((item.unit_price * item.quantity for item in items), Decimal("0")).quantize(CENT)


def amount_due(order: Order) -> Decimal:
    return (subtotal(order.items) - order.discount).quantize(CENT)
