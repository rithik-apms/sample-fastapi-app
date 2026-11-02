from decimal import Decimal

from app.models import Order
from app.services.pricing import CENT

CANCELLATION_FEE = Decimal("2.00")


def refund_quote(order: Order) -> Decimal:
    """Amount returned to the customer if the order is cancelled now."""
    paid = order.amount_paid or Decimal("0")
    return max(paid - CANCELLATION_FEE, Decimal("0")).quantize(CENT)
