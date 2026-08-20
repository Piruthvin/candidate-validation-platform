import contextvars
import logging
import sys
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import starlette.requests
import starlette.responses

correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")


class CorrelationMiddleware:
    def __init__(self, app: Callable[[starlette.requests.Request], Awaitable[starlette.responses.Response]]) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = starlette.requests.Request(scope, receive)
        cid = request.headers.get("X-Correlation-ID", uuid.uuid4().hex[:16])
        correlation_id.set(cid)

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = starlette.datastructures.MutableHeaders(scope=message)
                headers.append("X-Correlation-ID", cid)
            await send(message)

        await self.app(scope, receive, send_wrapper)


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        cid = correlation_id.get()
        cid_part = f" [{cid}]" if cid else ""
        return f"{timestamp} | {record.levelname:7s} | {record.name:30s}{cid_part} | {record.getMessage()}"


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
