import logging
from datetime import datetime
from dateutil import parser

logger = logging.getLogger(__name__)

def parse_flexible(date_str: str):
    """Parse a date string in a flexible manner.
    Supports ISO, YYYY-MM-DD, DD-MM-YYYY, MM-YYYY, YYYY.
    Returns a datetime object (timezone‑aware if present) or None.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    # Try ISO first
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except Exception:
        pass
    # Try common formats
    formats = ["%d-%m-%Y", "%m-%Y", "%Y-%m-%d", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    # Fallback to dateutil parser (handles many cases)
    try:
        return parser.parse(date_str, dayfirst=True)
    except Exception as e:
        logger.debug(f"Failed to parse date '{date_str}': {e}")
        return None
