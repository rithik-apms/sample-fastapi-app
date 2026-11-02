import logging
import re

from app.models import EMAIL_PATTERN, Order, OrderCreate, OrderItemIn
from app.services.errors import InvalidOrder
from app.services.orders import create_order, list_orders, normalize_email

logger = logging.getLogger(__name__)


def order_history(email: str) -> list[Order]:
    """The customer's orders, newest first."""
    return list_orders(customer_email=email)


def reorder(email: str) -> Order:
    """Place a new order with the same items and delivery as the customer's latest order."""
    email = normalize_email(email)
    if not re.match(EMAIL_PATTERN, email):
        raise InvalidOrder("Invalid email address")

    latest = order_history(email)[0]
    order = create_order(
        OrderCreate(
            customer_email=email,
            items=[OrderItemIn(sku=item.sku, quantity=item.quantity) for item in latest.items],
            delivery_method=latest.delivery_method,
            country=latest.country,
        )
    )
    logger.info("reorder placed", extra={"fields": {"order_id": order.id, "from_order_id": latest.id}})
    return order
