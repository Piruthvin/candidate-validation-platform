import logging
import asyncio
import re
from datetime import datetime
from typing import Tuple, Optional, Any

import dns.resolver

# Optional import of dateutil parser; if unavailable, fallback to built‑in parsing only
try:
    from dateutil import parser  # type: ignore
except Exception:  # pragma: no cover
    parser = None

logger = logging.getLogger(__name__)


def parse_flexible(date_str: Any) -> Optional[datetime]:
    """Parse a date string in a flexible manner.

    Supports formats:
    - Present / Current / Now / Ongoing
    - YYYY-MM-DD, YYYY-MM, YYYY
    - MM/YYYY, DD/MM/YYYY, MM-YYYY, YYYY/MM/DD, YYYY/MM
    - Month Year (e.g. Jan 2020, January 2020)
    Returns a ``datetime`` object or ``None`` if parsing fails.
    """
    if date_str is None:
        return None
    if isinstance(date_str, (int, float)):
        date_str = str(int(date_str))
    if not isinstance(date_str, str):
        return None
    
    clean_str = date_str.strip()
    if not clean_str:
        return None

    # Handle ongoing / present
    if clean_str.lower() in ("present", "current", "now", "ongoing", "till date", "today"):
        return datetime.now()

    # Try ISO format first
    try:
        return datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
    except Exception:
        pass

    # Try known patterns
    patterns = (
        "%Y-%m-%d", "%Y-%m", "%Y",
        "%m/%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%Y/%m/%d", "%Y/%m",
        "%b %Y", "%B %Y",
        "%b-%Y", "%B-%Y",
        "%m-%Y", "%d-%m-%Y"
    )
    for fmt in patterns:
        try:
            return datetime.strptime(clean_str, fmt)
        except Exception:
            continue

    # Fallback to dateutil parser if available
    if parser is not None:
        try:
            return parser.parse(clean_str, dayfirst=True)
        except Exception as e:
            logger.debug(f"Failed to parse date '{clean_str}': {e}")

    # Fallback: extract 4-digit year if present
    m = re.search(r"\b(19\d\d|20\d\d)\b", clean_str)
    if m:
        try:
            return datetime(int(m.group(1)), 1, 1)
        except Exception:
            pass

    return None


def validate_email(email: str) -> bool:
    """Simple syntactic email validation."""
    if not email or not isinstance(email, str):
        return False
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(email_regex, email) is not None


def check_dns_mx(domain: str) -> Tuple[bool, bool]:
    """Check DNS A record and MX record existence for a domain.

    Returns a tuple ``(dns_exists, mx_exists)``. ``gmail.com`` is treated as
    always having both records to satisfy the special requirement.
    """
    if not domain or not isinstance(domain, str):
        return (False, False)
    domain = domain.lower().strip()
    if domain == "gmail.com":
        return (True, True)
    dns_exists = False
    mx_exists = False
    try:
        answers = dns.resolver.resolve(domain, "A")
        dns_exists = any(True for _ in answers)
    except Exception as e:
        logger.debug(f"DNS A lookup failed for {domain}: {e}")
    try:
        mx_answers = dns.resolver.resolve(domain, "MX")
        mx_exists = any(True for _ in mx_answers)
    except Exception as e:
        logger.debug(f"MX lookup failed for {domain}: {e}")
    return (dns_exists, mx_exists)


def parse_phone(phone_str: str) -> Optional[str]:
    """Very lightweight phone normalisation to E.164 style if possible.

    This implementation strips non‑digit characters and adds a leading '+'
    when the number looks plausible. It does **not** perform full validation.
    """
    if not phone_str or not isinstance(phone_str, str):
        return None
    digits = re.sub(r"\D", "", phone_str)
    if len(digits) == 0:
        return None
    if digits.startswith("0"):
        digits = digits.lstrip("0")
    if not digits.startswith("+"):
        digits = f"+{digits}"
    return digits


async def retry_async(coro_callable, attempts: int = 3, timeout: int = 5):
    """Retry an awaitable ``coro_callable`` up to ``attempts`` times with a timeout.

    ``coro_callable`` should be a *callable* that returns an awaitable, e.g.
    ``lambda: httpx.get(url)``. If all attempts fail, the last exception is raised.
    """
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return await asyncio.wait_for(coro_callable(), timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("Attempt %s/%s failed with %s", attempt, attempts, exc)
    raise last_exc
