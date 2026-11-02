# Sample Orders

A small FastAPI order and payment application with a minimal web UI.

## Run locally

```bash
uv sync
RELEASE_SHA=$(git rev-parse HEAD) ENVIRONMENT=local uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs are at `/docs`.

## Run with Docker

```bash
docker build --build-arg RELEASE_SHA=$(git rev-parse HEAD) -t sample-fastapi .
docker run --rm -p 8000:8000 sample-fastapi
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SERVICE_NAME` | `sample-fastapi` | Service name in logs |
| `ENVIRONMENT` | `local` (`poc` in the image) | Environment name in logs |
| `RELEASE_SHA` | `unknown` | Git commit of the running build; set at build time |

Logs are JSON lines on stdout. Each request gets an `X-Request-ID` (taken from the request header when valid, otherwise generated), which is included in every log line and in error responses.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health and build info |
| GET | `/api/products` | Product catalog |
| POST | `/api/orders` | Create an order: `{"items": [{"sku": "MUG", "quantity": 1}], "coupon_code": "WELCOME10"}` |
| GET | `/api/orders` | List orders |
| GET | `/api/orders/{id}` | Order details |
| POST | `/api/orders/{id}/pay` | Pay for an order |
| GET | `/api/orders/{id}/shipping-quote` | Shipping fee for an order |
| GET | `/api/orders/{id}/loyalty-points` | Loyalty points earned by an order |
| GET | `/api/orders/{id}/refund-quote` | Refund amount if the order is cancelled |

Coupons: `WELCOME10` (10% off), `SAVE5` (5.00 off), `DOUBLEPTS` (double loyalty points).

## Tests

```bash
uv run pytest
```
