"""In-memory catalog and order storage."""

from decimal import Decimal
from threading import Lock

from app.models import Order, Product

CATALOG: dict[str, Product] = {
    p.sku: p
    for p in (
        Product(sku="MUG", name="Coffee mug", unit_price=Decimal("12.50"), weight_kg=Decimal("0.40")),
        Product(sku="TSHIRT", name="T-shirt", unit_price=Decimal("20.00"), weight_kg=Decimal("0.25")),
        Product(sku="GIFTCARD", name="Gift card (e-mail delivery)", unit_price=Decimal("25.00")),
    )
}


class OrderStore:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._next_id = 1
        self._lock = Lock()

    def next_id(self) -> str:
        with self._lock:
            order_id = f"ord-{self._next_id:04d}"
            self._next_id += 1
            return order_id

    def save(self, order: Order) -> Order:
        with self._lock:
            self._orders[order.id] = order
        return order

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def list(self) -> list[Order]:
        return sorted(self._orders.values(), key=lambda o: o.created_at, reverse=True)

    def reset(self) -> None:
        with self._lock:
            self._orders.clear()
            self._next_id = 1


store = OrderStore()
