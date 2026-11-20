import csv
import io


def test_receipt_for_gb_order_includes_uk_vat(client, make_order, pay):
    order = pay(make_order([("MUG", 1)], delivery_method="express", country="GB")["id"])

    response = client.get(f"/api/orders/{order['id']}/receipt.csv")

    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.text)))
    assert ["vat_included", "20%", "4.92"] in rows
