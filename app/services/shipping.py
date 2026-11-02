from decimal import Decimal

from app.models import Order
from app.services.pricing import CENT

BASE_FEE = Decimal("4.99")
FEE_PER_KG = Decimal("2.00")


def shipping_quote(order: Order) -> Decimal:
    weight = sum((item.weight_kg * item.quantity for item in order.items), Decimal("0"))
    return (BASE_FEE + weight * FEE_PER_KG).quantize(CENT)
