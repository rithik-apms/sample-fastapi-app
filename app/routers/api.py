from fastapi import APIRouter

from app.models import Order, OrderCreate, Product
from app.services.loyalty import points_preview
from app.services.orders import create_order, get_order
from app.services.payments import pay_order
from app.services.refunds import refund_quote
from app.services.shipping import shipping_quote
from app.store import CATALOG, store

router = APIRouter(prefix="/api")


@router.get("/products")
def list_products() -> list[Product]:
    return list(CATALOG.values())


@router.post("/orders", status_code=201)
def create(data: OrderCreate) -> Order:
    return create_order(data)


@router.get("/orders")
def list_orders() -> list[Order]:
    return store.list()


@router.get("/orders/{order_id}")
def read(order_id: str) -> Order:
    return get_order(order_id)


@router.post("/orders/{order_id}/pay")
def pay(order_id: str) -> Order:
    return pay_order(order_id)


@router.get("/orders/{order_id}/shipping-quote")
def shipping(order_id: str) -> dict:
    return {"order_id": order_id, "shipping_fee": shipping_quote(get_order(order_id))}


@router.get("/orders/{order_id}/loyalty-points")
def loyalty(order_id: str) -> dict:
    return {"order_id": order_id, "points": points_preview(get_order(order_id))}


@router.get("/orders/{order_id}/refund-quote")
def refund(order_id: str) -> dict:
    return {"order_id": order_id, "refund_amount": refund_quote(get_order(order_id))}
