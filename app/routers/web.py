from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.models import OrderCreate, OrderItemIn
from app.services.errors import InvalidOrder, OrderAlreadyPaid, OrderNotFound
from app.services.orders import create_order, get_order
from app.services.payments import pay_order
from app.services.pricing import subtotal
from app.services.refunds import refund_quote
from app.store import CATALOG, store
from app.templating import templates

router = APIRouter(include_in_schema=False)


def render_index(request: Request, error: str | None = None, status_code: int = 200):
    orders = [(order, subtotal(order.items)) for order in store.list()]
    return templates.TemplateResponse(
        request,
        "index.html",
        {"products": CATALOG.values(), "orders": orders, "error": error},
        status_code=status_code,
    )


@router.get("/")
def index(request: Request):
    return render_index(request)


@router.post("/orders")
async def create(request: Request):
    form = await request.form()
    try:
        items = [
            OrderItemIn(sku=sku, quantity=int(form.get(f"qty_{sku}") or 0))
            for sku in CATALOG
            if int(form.get(f"qty_{sku}") or 0) > 0
        ]
        order = create_order(OrderCreate(items=items, coupon_code=form.get("coupon_code") or None))
    except (ValueError, ValidationError, InvalidOrder) as exc:
        message = str(exc) if isinstance(exc, InvalidOrder) else "Choose 1 to 10 of at least one product."
        return render_index(request, error=message, status_code=400)
    return RedirectResponse(f"/orders/{order.id}", status_code=303)


@router.get("/orders/{order_id}")
def detail(request: Request, order_id: str):
    try:
        order = get_order(order_id)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Order not found")
    context = {
        "order": order,
        "subtotal": subtotal(order.items),
        "refund": refund_quote(order) if order.status == "paid" else None,
    }
    return templates.TemplateResponse(request, "order.html", context)


@router.post("/orders/{order_id}/pay")
def pay(order_id: str):
    try:
        pay_order(order_id)
    except OrderNotFound:
        raise HTTPException(status_code=404, detail="Order not found")
    except OrderAlreadyPaid:
        pass
    return RedirectResponse(f"/orders/{order_id}", status_code=303)
