"""Expiry calculation service for MEDSAFE.

Provides pure business logic to calculate days remaining until expiry
and determine organizational expiry statuses ('valid', 'expiring_soon', 'expired').

IMPORTANT SAFETY NOTICE:
    An expiry status of 'valid' indicates strictly that the user-recorded expiry date
    has not yet reached the warning threshold according to the system calendar.
    It does NOT guarantee or claim that a medicine is safe to consume or use.
"""

from datetime import date
from typing import Optional, Union

from backend.utils.date_utils import ensure_date_object, get_today

# Status string constants
STATUS_VALID: str = "valid"
STATUS_EXPIRING_SOON: str = "expiring_soon"
STATUS_EXPIRED: str = "expired"

DEFAULT_EXPIRING_SOON_DAYS: int = 30


def days_until_expiry(
    expiry_date: Union[str, date],
    today: Optional[date] = None,
) -> int:
    """Calculate the signed number of days between today and the expiry date.

    Args:
        expiry_date: Target expiry date as ISO string ('YYYY-MM-DD') or datetime.date.
        today: Optional reference date (defaults to the current system date).

    Returns:
        Integer number of days:
        - Negative integer: The date has passed (e.g. -5 means expired 5 days ago).
        - 0: Expires today.
        - Positive integer: Days remaining until expiry.

    Raises:
        ValueError: If expiry_date is malformed or invalid.
    """
    target_date = ensure_date_object(expiry_date)
    ref_date = today if today is not None else get_today()

    return (target_date - ref_date).days


def get_expiry_status(
    expiry_date: Union[str, date],
    today: Optional[date] = None,
    expiring_soon_days: int = DEFAULT_EXPIRING_SOON_DAYS,
) -> str:
    """Determine the organizational expiry status for a given date.

    Status determination rules:
        - days < 0: 'expired' (the date is in the past)
        - 0 <= days <= expiring_soon_days: 'expiring_soon' (expires today or within threshold)
        - days > expiring_soon_days: 'valid' (expiry is beyond warning threshold)

    Args:
        expiry_date: Target expiry date as ISO string ('YYYY-MM-DD') or datetime.date.
        today: Optional reference date (defaults to the current system date).
        expiring_soon_days: Number of days before expiry considered 'expiring soon' (default: 30).

    Returns:
        One of STATUS_EXPIRED ('expired'), STATUS_EXPIRING_SOON ('expiring_soon'), or STATUS_VALID ('valid').

    Raises:
        ValueError: If expiry_date is malformed or expiring_soon_days is negative.
    """
    if expiring_soon_days < 0:
        raise ValueError(
            f"expiring_soon_days threshold must be non-negative. Received: {expiring_soon_days}"
        )

    days_left = days_until_expiry(expiry_date, today=today)

    if days_left < 0:
        return STATUS_EXPIRED
    elif days_left <= expiring_soon_days:
        return STATUS_EXPIRING_SOON
    else:
        return STATUS_VALID


def format_expiry_human_label(days: int) -> str:
    """Return a plain-English, accessible description of remaining expiry time.

    Examples:
        -5  -> 'Expired 5 days ago'
        -1  -> 'Expired yesterday'
        0   -> 'Expires today'
        1   -> 'Expires in 1 day'
        7   -> 'Expires in 7 days'
    """
    if days < -1:
        return f"Expired {abs(days)} days ago"
    elif days == -1:
        return "Expired yesterday"
    elif days == 0:
        return "Expires today"
    elif days == 1:
        return "Expires in 1 day"
    else:
        return f"Expires in {days} days"
