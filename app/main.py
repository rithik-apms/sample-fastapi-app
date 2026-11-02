import logging
import re
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import db
from app.config import Settings, get_settings
from app.logging_config import configure_logging, request_id_var, trace_id_var
from app.routers import api, web
from app.seed import seed
from app.services.errors import InvalidOrder, InvalidReportRange, OrderConflict, OrderNotFound
from app.templating import templates

logger = logging.getLogger("app")

REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
TRACEPARENT = re.compile(r"^[0-9a-f]{2}-([0-9a-f]{32})-[0-9a-f]{16}-[0-9a-f]{2}$")

# Expected business errors -> (HTTP status, message shown to the client)
DOMAIN_ERRORS = {
    OrderNotFound: (404, lambda exc: "Order not found"),
    InvalidOrder: (400, str),
    InvalidReportRange: (400, str),
    OrderConflict: (409, str),
}


def is_api(request: Request) -> bool:
    return request.url.path.startswith("/api/")


def error_response(request: Request, request_id: str):
    if is_api(request):
        return JSONResponse({"detail": "Internal server error", "request_id": request_id}, status_code=500)
    return templates.TemplateResponse(request, "error.html", {"request_id": request_id}, status_code=500)


async def domain_error(request: Request, exc: Exception):
    status_code, describe = DOMAIN_ERRORS[type(exc)]
    message = describe(exc)
    if is_api(request):
        return JSONResponse({"detail": message}, status_code=status_code)
    return templates.TemplateResponse(
        request, "message.html", {"status_code": status_code, "message": message}, status_code=status_code
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.release_sha == "unknown":
            logger.warning("RELEASE_SHA is not set; logs cannot be matched to a deployed commit")
        db.init(settings.database_path)
        with db.transaction() as conn:
            seed(conn, demo=settings.seed_demo_data)
        logger.info("service started", extra={"fields": {"event": "startup"}})
        yield

    app = FastAPI(title="Sample Orders", lifespan=lifespan)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if REQUEST_ID.match(incoming) else f"req-{uuid4().hex[:12]}"
        trace = TRACEPARENT.match(request.headers.get("traceparent", ""))
        request_token = request_id_var.set(request_id)
        trace_token = trace_id_var.set(trace.group(1) if trace else None)
        started = time.perf_counter()
        http_fields = {"method": request.method, "path": request.url.path}
        try:
            try:
                response = await call_next(request)
            except Exception as exc:
                logger.error(
                    str(exc) or type(exc).__name__,
                    exc_info=exc,
                    extra={"fields": {"event": "unhandled_exception", **http_fields, "status_code": 500}},
                )
                response = error_response(request, request_id)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request completed",
                extra={
                    "fields": {
                        "event": "http_request",
                        **http_fields,
                        "status_code": response.status_code,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    }
                },
            )
            return response
        finally:
            request_id_var.reset(request_token)
            trace_id_var.reset(trace_token)

    for error_type in DOMAIN_ERRORS:
        app.add_exception_handler(error_type, domain_error)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "service": settings.service_name,
            "environment": settings.environment,
            "release_sha": settings.release_sha,
        }

    app.include_router(api.router)
    app.include_router(web.router)
    return app


app = create_app()
