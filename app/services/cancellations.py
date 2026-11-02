import logging
from datetime import datetime, timezone

from app import db, repository
from app.models import Order
from app.services.errors import OrderConflict
from app.services.orders import load_order
from app.services.refunds import refund_quote

logger = logging.getLogger(__name__)


def cancel_order(order_id: str) -> Order:
    with db.transaction() as conn:
        order = load_order(conn, order_id)
        if order.status == "cancelled":
            raise OrderConflict("Order is already cancelled")

        refund = None
        if order.status == "paid":
            refund = refund_quote(order)
            for item in order.items:
                repository.change_stock(conn, item.sku, item.quantity)
        repository.update_order(
            conn, order_id, status="cancelled", refund_amount=refund, cancelled_at=datetime.now(timezone.utc)
        )
        cancelled = load_order(conn, order_id)

    logger.info("order cancelled", extra={"fields": {"order_id": order_id, "refund": str(refund)}})
    return cancelled
