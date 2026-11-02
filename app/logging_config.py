"""Structured JSON logging with per-request context."""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone

from app.config import Settings

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)

_base_record_factory = logging.getLogRecordFactory()


def _record_with_request_context(*args, **kwargs) -> logging.LogRecord:
    """Stamp request context on each record when it is created, in the caller's context."""
    record = _base_record_factory(*args, **kwargs)
    record.request_id = request_id_var.get()
    record.trace_id = trace_id_var.get()
    return record


class JsonFormatter(logging.Formatter):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "service_name": self.settings.service_name,
            "environment": self.settings.environment,
            "release_sha": self.settings.release_sha,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "trace_id": getattr(record, "trace_id", None),
        }
        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc, tb = record.exc_info
            event["exception_type"] = exc_type.__name__
            event["stack_trace"] = "".join(traceback.format_exception(exc_type, exc, tb))
        event.update(getattr(record, "fields", {}))
        return json.dumps({k: v for k, v in event.items() if v is not None}, default=str)


def configure_logging(settings: Settings) -> None:
    logging.setLogRecordFactory(_record_with_request_context)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(settings))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # Route uvicorn's own logs through the JSON handler; requests are logged by our middleware.
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
