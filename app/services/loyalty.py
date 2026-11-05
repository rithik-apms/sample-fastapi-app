from app.models import Order
from app.services.pricing import subtotal


def points_preview(order: Order) -> int:
    """Loyalty points the customer earns for this order."""
    return int(subtotal(order.items) * (order.points_multiplier or 1))
