from collections.abc import Iterable
from decimal import Decimal

from app.models import Order, OrderItem

CENT = Decimal("0.01")


def subtotal(items: Iterable[OrderItem]) -> Decimal:
    return sum((item.unit_price * item.quantity for item in items), Decimal("0")).quantize(CENT)


def amount_due(order: Order) -> Decimal:
    total = subtotal(order.items) + order.shipping_fee
    if order.coupon_code:
        total -= coupon_discount(order)
    return total.quantize(CENT)


def coupon_discount(order: Order) -> Decimal:
    # Free-shipping coupons waive the fee and take nothing off. Orders saved before that was recorded as 0.00
    # have no discount; any other coupon without a discount is still an error.
    if order.discount is None and order.free_shipping:
        return Decimal("0.00")
    return order.discount
