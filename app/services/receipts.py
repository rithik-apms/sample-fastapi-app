import csv
import io
from decimal import Decimal

from app.models import Order
from app.services.errors import OrderConflict
from app.services.pricing import CENT, subtotal

# VAT included in the price, by destination country
VAT_RATES = {
    "US": Decimal("0"),
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "IN": Decimal("0.18"),
}


def receipt_csv(order: Order) -> str:
    if order.status != "paid":
        raise OrderConflict("A receipt is only available for paid orders")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["order_id", order.id])
    writer.writerow(["customer_email", order.customer_email])
    writer.writerow(["paid_at", order.paid_at.isoformat(timespec="seconds")])
    writer.writerow([])
    writer.writerow(["item", "quantity", "unit_price", "line_total"])
    for item in order.items:
        writer.writerow([item.name, item.quantity, item.unit_price, item.unit_price * item.quantity])
    writer.writerow([])
    writer.writerow(["subtotal", subtotal(order.items)])
    writer.writerow(["delivery", f"{order.delivery_method} to {order.country}", order.shipping_fee])
    if order.coupon_code:
        writer.writerow(["coupon", order.coupon_code])
    writer.writerow(["total_paid", order.amount_paid])
    rate = VAT_RATES[order.country]
    writer.writerow(["vat_included", f"{rate:.0%}", (order.amount_paid * rate / (1 + rate)).quantize(CENT)])
    return buffer.getvalue()
