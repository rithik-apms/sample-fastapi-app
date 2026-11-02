import logging
from datetime import datetime, timezone

from app.models import Order
from app.services.errors import OrderAlreadyPaid
from app.services.orders import get_order
from app.services.pricing import amount_due
from app.store import store

logger = logging.getLogger(__name__)


def pay_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status == "paid":
        raise OrderAlreadyPaid(order_id)

    amount = amount_due(order)
    paid = order.model_copy(
        update={"status": "paid", "amount_paid": amount, "paid_at": datetime.now(timezone.utc)}
    )
    store.save(paid)
    logger.info("payment captured", extra={"fields": {"order_id": order_id, "amount": str(amount)}})
    return paid
