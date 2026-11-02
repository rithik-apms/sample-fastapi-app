from datetime import datetime, timezone
from decimal import Decimal

from app.models import Order, OrderCreate, OrderItem
from app.services.errors import InvalidOrder, OrderNotFound
from app.services.pricing import CENT, subtotal
from app.store import CATALOG, store

# code -> (kind, value)
COUPONS: dict[str, tuple[str, Decimal]] = {
    "WELCOME10": ("percent_off", Decimal("10")),
    "SAVE5": ("amount_off", Decimal("5.00")),
    "DOUBLEPTS": ("points_multiplier", Decimal("2")),
}


def create_order(data: OrderCreate) -> Order:
    items = []
    for line in data.items:
        product = CATALOG.get(line.sku)
        if product is None:
            raise InvalidOrder(f"Unknown product: {line.sku}")
        items.append(
            OrderItem(
                sku=product.sku,
                name=product.name,
                quantity=line.quantity,
                unit_price=product.unit_price,
                weight_kg=product.weight_kg,
            )
        )

    coupon_code = (data.coupon_code or "").strip().upper() or None
    discount = None
    points_multiplier = None
    if coupon_code is not None:
        if coupon_code not in COUPONS:
            raise InvalidOrder(f"Unknown coupon: {coupon_code}")
        kind, value = COUPONS[coupon_code]
        if kind == "percent_off":
            discount = (subtotal(items) * value / 100).quantize(CENT)
        elif kind == "amount_off":
            discount = min(value, subtotal(items))
        else:
            points_multiplier = value

    order = Order(
        id=store.next_id(),
        items=items,
        coupon_code=coupon_code,
        discount=discount,
        points_multiplier=points_multiplier,
        created_at=datetime.now(timezone.utc),
    )
    return store.save(order)


def get_order(order_id: str) -> Order:
    order = store.get(order_id)
    if order is None:
        raise OrderNotFound(order_id)
    return order
