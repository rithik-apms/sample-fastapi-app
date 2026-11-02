from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import ValidationError

from app.models import OrderCreate, OrderItemIn
from app.services.cancellations import cancel_order
from app.services.catalog import list_products
from app.services.customers import order_history, reorder
from app.services.errors import InvalidOrder, InvalidReportRange
from app.services.orders import create_order, get_order, list_orders, normalize_email
from app.services.payments import pay_order
from app.services.pricing import subtotal
from app.services.receipts import receipt_csv
from app.services.refunds import refund_quote
from app.services.reports import sales_report
from app.services.shipping import COUNTRIES
from app.templating import templates

router = APIRouter(include_in_schema=False)

STATUSES = ("pending", "paid", "cancelled")


def render_index(request: Request, error: str | None = None, status_code: int = 200):
    status = request.query_params.get("status")
    status = status if status in STATUSES else None
    email = request.query_params.get("email", "").strip()
    orders = list_orders(status=status, customer_email=email or None)
    context = {
        "products": list_products(),
        "countries": COUNTRIES,
        "orders": [(order, subtotal(order.items)) for order in orders],
        "statuses": STATUSES,
        "filter_status": status,
        "filter_email": email,
        "error": error,
    }
    return templates.TemplateResponse(request, "index.html", context, status_code=status_code)


@router.get("/")
def index(request: Request):
    return render_index(request)


@router.post("/orders")
async def create(request: Request):
    form = await request.form()
    try:
        quantities = {p.sku: int(form.get(f"qty_{p.sku}") or 0) for p in list_products()}
        order = create_order(
            OrderCreate(
                customer_email=form.get("customer_email", ""),
                items=[OrderItemIn(sku=sku, quantity=qty) for sku, qty in quantities.items() if qty > 0],
                coupon_code=form.get("coupon_code") or None,
                delivery_method=form.get("delivery_method") or "standard",
                country=form.get("country") or "US",
            )
        )
    except InvalidOrder as exc:
        return render_index(request, error=str(exc), status_code=400)
    except (ValueError, ValidationError):
        return render_index(
            request, error="Enter a valid email and choose 1 to 10 of at least one product.", status_code=400
        )
    return RedirectResponse(f"/orders/{order.id}", status_code=303)


@router.get("/orders/{order_id}")
def detail(request: Request, order_id: str):
    order = get_order(order_id)
    context = {
        "order": order,
        "subtotal": subtotal(order.items),
        "country_name": COUNTRIES.get(order.country, order.country),
        "refund": refund_quote(order) if order.status == "paid" else None,
    }
    return templates.TemplateResponse(request, "order.html", context)


@router.post("/orders/{order_id}/pay")
def pay(order_id: str):
    pay_order(order_id)
    return RedirectResponse(f"/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/cancel")
def cancel(order_id: str):
    cancel_order(order_id)
    return RedirectResponse(f"/orders/{order_id}", status_code=303)


@router.get("/orders/{order_id}/receipt.csv")
def receipt(order_id: str):
    return Response(
        receipt_csv(get_order(order_id)),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="receipt-{order_id}.csv"'},
    )


@router.get("/customers/{email}")
def customer(request: Request, email: str):
    email = normalize_email(email)
    orders = [(order, subtotal(order.items)) for order in order_history(email)]
    return templates.TemplateResponse(request, "customer.html", {"email": email, "orders": orders})


@router.post("/reorder")
async def reorder_last(request: Request):
    form = await request.form()
    order = reorder(form.get("customer_email", ""))
    return RedirectResponse(f"/orders/{order.id}", status_code=303)


@router.get("/products")
def products(request: Request):
    return templates.TemplateResponse(request, "products.html", {"products": list_products()})


@router.get("/reports/sales")
def sales(request: Request, start: str = "", end: str = ""):
    context = {"start": start, "end": end, "report": None, "error": None}
    status_code = 200
    if start and end:
        try:
            context["report"] = sales_report(date.fromisoformat(start), date.fromisoformat(end))
        except (ValueError, InvalidReportRange) as exc:
            context["error"] = str(exc) if isinstance(exc, InvalidReportRange) else "Enter dates as YYYY-MM-DD."
            status_code = 400
    return templates.TemplateResponse(request, "report.html", context, status_code=status_code)
