import logging
from datetime import datetime, timezone

from app import db, repository
from app.models import Order
from app.services.errors import OrderConflict
from app.services.orders import load_order
from app.services.pricing import amount_due

logger = logging.getLogger(__name__)


def pay_order(order_id: str) -> Order:
    with db.transaction() as conn:
        order = load_order(conn, order_id)
        if order.status != "pending":
            raise OrderConflict(f"Order is already {order.status}")
        for item in order.items:
            product = repository.get_product(conn, item.sku)
            if product.stock < item.quantity:
                raise OrderConflict(f"{item.name} is out of stock")

        amount = amount_due(order)
        for item in order.items:
            repository.change_stock(conn, item.sku, -item.quantity)
        repository.update_order(
            conn, order_id, status="paid", amount_paid=amount, paid_at=datetime.now(timezone.utc)
        )
        paid = load_order(conn, order_id)

    logger.info("payment captured", extra={"fields": {"order_id": order_id, "amount": str(amount)}})
    return paid
