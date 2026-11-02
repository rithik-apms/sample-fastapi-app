from decimal import Decimal


def test_shipping_quote_uses_weight(client, make_order):
    order = make_order([("MUG", 2), ("TSHIRT", 2)])

    quote = client.get(f"/api/orders/{order['id']}/shipping-quote").json()

    # 4.99 base + (0.80 + 0.50) kg * 2.00
    assert Decimal(quote["shipping_fee"]) == Decimal("7.59")


def test_loyalty_points_with_points_promotion(client, make_order):
    order = make_order([("TSHIRT", 2)], coupon_code="DOUBLEPTS")

    points = client.get(f"/api/orders/{order['id']}/loyalty-points").json()

    assert points["points"] == 80
