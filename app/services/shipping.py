from decimal import Decimal

from app.models import Order
from app.services.pricing import CENT

COUNTRIES = {
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "IN": "India",
}

STANDARD_FEES = {
    "US": Decimal("4.99"),
    "GB": Decimal("5.99"),
    "DE": Decimal("5.99"),
    "FR": Decimal("5.99"),
    "IN": Decimal("7.99"),
}
EXPRESS_FEES = {
    "US": Decimal("14.99"),
    "GB": Decimal("16.99"),
    "DE": Decimal("16.99"),
    "FR": Decimal("16.99"),
}

# Carrier cost estimate by parcel weight
BASE_FEE = Decimal("4.99")
FEE_PER_KG = Decimal("2.00")


def delivery_fee(method: str, country: str) -> Decimal:
    fees = EXPRESS_FEES if method == "express" else STANDARD_FEES
    return fees[country]


def shipping_quote(order: Order) -> Decimal:
    weight = sum((item.weight_kg * item.quantity for item in order.items), Decimal("0"))
    return (BASE_FEE + weight * FEE_PER_KG).quantize(CENT)
