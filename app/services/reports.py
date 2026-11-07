from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from app import db, repository
from app.models import SalesReport
from app.services.errors import InvalidReportRange
from app.services.pricing import CENT

MAX_RANGE_DAYS = 366


def sales_report(start: date, end: date) -> SalesReport:
    if end < start:
        raise InvalidReportRange("End date must be on or after the start date")
    if (end - start).days > MAX_RANGE_DAYS:
        raise InvalidReportRange(f"Date range can be at most {MAX_RANGE_DAYS} days")

    range_start = datetime.combine(start, time.min, tzinfo=timezone.utc)
    range_end = datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc)
    with db.read() as conn:
        orders = repository.paid_orders_between(conn, range_start, range_end)

    revenue = sum((order.amount_paid for order in orders), Decimal(0))
    average = revenue / len(orders) if orders else Decimal(0)
    return SalesReport(
        start=start,
        end=end,
        paid_orders=len(orders),
        items_sold=sum(item.quantity for order in orders for item in order.items),
        revenue=revenue.quantize(CENT),
        average_order_value=average.quantize(CENT),
    )
