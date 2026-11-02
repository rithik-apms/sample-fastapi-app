# Sample Orders

A small FastAPI order and payment application with a minimal web UI and a SQLite database.

Features: customer orders with stock checks, coupons, standard/express delivery to several countries, payment, cancellation with refunds, customer order history and "buy again", CSV receipts, a products page and a sales report.

## Run locally

```bash
uv sync
RELEASE_SHA=$(git rev-parse HEAD) ENVIRONMENT=local uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs are at `/docs`. The database is created at `data/app.db`.

## Run with Docker

```bash
docker build --build-arg RELEASE_SHA=$(git rev-parse HEAD) -t sample-fastapi .
docker run -d --name sample-fastapi -p 127.0.0.1:8000:8000 -v sample-data:/data sample-fastapi
```

The `sample-data` volume keeps the database across container restarts and rebuilds. Remove it with `docker volume rm sample-data` to start fresh.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SERVICE_NAME` | `sample-fastapi` | Service name in logs |
| `ENVIRONMENT` | `local` (`poc` in the image) | Environment name in logs |
| `RELEASE_SHA` | `unknown` | Git commit of the running build; set at build time |
| `DATABASE_PATH` | `data/app.db` (`/data/app.db` in the image) | SQLite database file |
| `SEED_DEMO_DATA` | `true` | Add a demo customer (`demo@example.com`) with two past orders to an empty database |

Logs are JSON lines on stdout. Each request gets an `X-Request-ID` (taken from the request header when valid, otherwise generated), which is included in every log line and in error responses.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health and build info |
| GET | `/api/products` | Product catalog with stock |
| POST | `/api/orders` | Create an order (see below) |
| GET | `/api/orders?status=&email=` | List orders, optionally filtered |
| GET | `/api/orders/{id}` | Order details |
| POST | `/api/orders/{id}/pay` | Pay for an order |
| POST | `/api/orders/{id}/cancel` | Cancel an order (paid orders are refunded minus a 2.00 fee) |
| GET | `/api/orders/{id}/receipt.csv` | Receipt for a paid order |
| GET | `/api/orders/{id}/shipping-quote` | Carrier cost estimate by parcel weight |
| GET | `/api/orders/{id}/loyalty-points` | Loyalty points earned by an order |
| GET | `/api/orders/{id}/refund-quote` | Refund amount if the order is cancelled now |
| GET | `/api/customers/{email}/orders` | A customer's orders, newest first |
| POST | `/api/customers/{email}/reorder` | Repeat the customer's latest order |
| GET | `/api/reports/sales?start=YYYY-MM-DD&end=YYYY-MM-DD` | Paid orders, revenue and average order value |

Create an order:

```json
{
  "customer_email": "alice@example.com",
  "items": [{"sku": "MUG", "quantity": 2}],
  "coupon_code": "WELCOME10",
  "delivery_method": "standard",
  "country": "US"
}
```

- Coupons: `WELCOME10` (10% off), `SAVE5` (5.00 off), `DOUBLEPTS` (double loyalty points), `FREESHIP` (free delivery).
- Countries: `US`, `GB`, `DE`, `FR`, `IN`. Delivery: `standard` or `express`.

## Tests

```bash
uv run pytest
```
