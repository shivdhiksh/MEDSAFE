"""Date handling utilities for MEDSAFE.

Provides strict ISO 8601 (YYYY-MM-DD) date parsing, validation,
formatting, and system date retrieval using Python's standard datetime module.
"""

from datetime import date, datetime
from typing import Union

ISO_DATE_FORMAT: str = "%Y-%m-%d"
ISO_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def get_today() -> date:
    """Return the current local system date."""
    return date.today()


def get_today_iso() -> str:
    """Return today's date formatted as an ISO YYYY-MM-DD string."""
    return format_iso_date(get_today())


def get_now_iso() -> str:
    """Return the current local system date and time as a standard ISO string."""
    return datetime.now().strftime(ISO_DATETIME_FORMAT)


def parse_iso_date(date_str: str) -> date:
    """Safely parse a date string in strict YYYY-MM-DD format.

    Args:
        date_str: Date string expected in 'YYYY-MM-DD' format.

    Returns:
        datetime.date instance.

    Raises:
        ValueError: If date_str is empty, malformed, or represents an invalid calendar date.
    """
    if not isinstance(date_str, str) or not date_str.strip():
        raise ValueError("Expiry date cannot be empty. Expected format: YYYY-MM-DD.")

    cleaned_str = date_str.strip()
    try:
        return datetime.strptime(cleaned_str, ISO_DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(
            f"Invalid date format: '{cleaned_str}'. Expiry dates must strictly follow YYYY-MM-DD (e.g. 2026-12-31)."
        ) from exc


def format_iso_date(d: date) -> str:
    """Format a datetime.date object into a standard YYYY-MM-DD string."""
    if not isinstance(d, date):
        raise ValueError(f"Expected datetime.date object, received: {type(d)}")
    return d.strftime(ISO_DATE_FORMAT)


def ensure_date_object(d: Union[str, date]) -> date:
    """Convert input string or date to a validated datetime.date object."""
    if isinstance(d, date):
        return d
    return parse_iso_date(d)
