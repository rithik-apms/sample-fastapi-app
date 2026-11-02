from datetime import date

from fastapi import APIRouter
from fastapi.responses import Response

from app.models import Order, OrderCreate, OrderStatus, Product, SalesReport
from app.services.cancellations import cancel_order
from app.services.catalog import list_products
from app.services.customers import order_history, reorder
from app.services.loyalty import points_preview
from app.services.orders import create_order, get_order, list_orders
from app.services.payments import pay_order
from app.services.receipts import receipt_csv
from app.services.refunds import refund_quote
from app.services.reports import sales_report
from app.services.shipping import shipping_quote

router = APIRouter(prefix="/api")


@router.get("/products")
def products() -> list[Product]:
    return list_products()


@router.post("/orders", status_code=201)
def create(data: OrderCreate) -> Order:
    return create_order(data)


@router.get("/orders")
def orders(status: OrderStatus | None = None, email: str | None = None) -> list[Order]:
    return list_orders(status=status, customer_email=email)


@router.get("/orders/{order_id}")
def read(order_id: str) -> Order:
    return get_order(order_id)


@router.post("/orders/{order_id}/pay")
def pay(order_id: str) -> Order:
    return pay_order(order_id)


@router.post("/orders/{order_id}/cancel")
def cancel(order_id: str) -> Order:
    return cancel_order(order_id)


@router.get("/orders/{order_id}/shipping-quote")
def shipping(order_id: str) -> dict:
    return {"order_id": order_id, "shipping_fee": shipping_quote(get_order(order_id))}


@router.get("/orders/{order_id}/loyalty-points")
def loyalty(order_id: str) -> dict:
    return {"order_id": order_id, "points": points_preview(get_order(order_id))}


@router.get("/orders/{order_id}/refund-quote")
def refund(order_id: str) -> dict:
    return {"order_id": order_id, "refund_amount": refund_quote(get_order(order_id))}


@router.get("/orders/{order_id}/receipt.csv")
def receipt(order_id: str) -> Response:
    return Response(
        receipt_csv(get_order(order_id)),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="receipt-{order_id}.csv"'},
    )


@router.get("/customers/{email}/orders")
def customer_orders(email: str) -> list[Order]:
    return order_history(email)


@router.post("/customers/{email}/reorder", status_code=201)
def customer_reorder(email: str) -> Order:
    return reorder(email)


@router.get("/reports/sales")
def sales(start: date, end: date) -> SalesReport:
    return sales_report(start, end)
