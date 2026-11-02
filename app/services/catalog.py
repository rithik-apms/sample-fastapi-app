from app import db, repository
from app.models import Product


def list_products() -> list[Product]:
    with db.read() as conn:
        return repository.list_products(conn)
