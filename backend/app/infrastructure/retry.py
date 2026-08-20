import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    RETRYABLE = "retryable"
    USER_INPUT = "user_input_required"
    SYSTEM_FAILURE = "system_failure"


class RetryableError(Exception):
    pass


class UserInputError(Exception):
    pass


class SystemFailureError(Exception):
    pass


def classify_error(exc: Exception) -> ErrorCategory:
    msg = str(exc).lower()
    if isinstance(exc, RetryableError):
        return ErrorCategory.RETRYABLE
    if isinstance(exc, UserInputError):
        return ErrorCategory.USER_INPUT
    if isinstance(exc, SystemFailureError):
        return ErrorCategory.SYSTEM_FAILURE
    if any(kw in msg for kw in ("timeout", "connection", "unavailable", "rate limit", "too many requests", "server error", "500", "502", "503", "504")):
        return ErrorCategory.RETRYABLE
    if any(kw in msg for kw in ("not found", "invalid", "bad request", "400", "401", "403", "404")):
        return ErrorCategory.USER_INPUT
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return ErrorCategory.RETRYABLE
    return ErrorCategory.SYSTEM_FAILURE


async def retry_async(coro_factory, max_retries: int = 2, retry_delay: float = 1.0, backoff: float = 2.0, name: str = "operation"):
    last_exc = None
    for attempt in range(1 + max_retries):
        try:
            return await coro_factory()
        except Exception as e:
            last_exc = e
            category = classify_error(e)
            if attempt < max_retries and category == ErrorCategory.RETRYABLE:
                delay = retry_delay * (backoff ** attempt)
                logger.warning("%s attempt %d/%d failed (%s), retrying in %.1fs: %s", name, attempt + 1, max_retries, category.value, delay, e)
                await asyncio.sleep(delay)
            else:
                logger.error("%s failed after %d attempt(s): %s (category=%s)", name, attempt + 1, e, category.value)
                return {"error": str(e), "category": category.value, "attempts": attempt + 1}
    return {"error": str(last_exc), "category": classify_error(last_exc).value, "attempts": max_retries + 1}
