"""Automated tests for expiry calculation and organizational status logic.
"""

from datetime import date, timedelta
import pytest

from backend.services.expiry_service import (
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
    days_until_expiry,
    get_expiry_status,
)


def test_expired_dates():
    """Verify past dates return negative days and STATUS_EXPIRED ('expired')."""
    today = date(2026, 6, 1)

    # Yesterday
    yesterday = today - timedelta(days=1)
    assert days_until_expiry(yesterday, today=today) == -1
    assert get_expiry_status(yesterday, today=today) == STATUS_EXPIRED

    # 10 days ago
    ten_days_ago = today - timedelta(days=10)
    assert days_until_expiry(ten_days_ago.isoformat(), today=today) == -10
    assert get_expiry_status(ten_days_ago.isoformat(), today=today) == STATUS_EXPIRED


def test_today_expiry():
    """Verify that a medicine expiring today returns 0 days and STATUS_EXPIRING_SOON."""
    today = date(2026, 6, 1)
    assert days_until_expiry(today, today=today) == 0
    assert get_expiry_status(today, today=today) == STATUS_EXPIRING_SOON
    assert get_expiry_status(today.isoformat(), today=today) == STATUS_EXPIRING_SOON


def test_expiry_in_1_day():
    """Verify that expiry in 1 day returns 1 day and STATUS_EXPIRING_SOON."""
    today = date(2026, 6, 1)
    tomorrow = today + timedelta(days=1)
    assert days_until_expiry(tomorrow, today=today) == 1
    assert get_expiry_status(tomorrow, today=today) == STATUS_EXPIRING_SOON


def test_expiry_in_7_days():
    """Verify that expiry in 7 days returns 7 days and STATUS_EXPIRING_SOON."""
    today = date(2026, 6, 1)
    seven_days = today + timedelta(days=7)
    assert days_until_expiry(seven_days, today=today) == 7
    assert get_expiry_status(seven_days, today=today) == STATUS_EXPIRING_SOON


def test_expiry_on_30_day_boundary():
    """Verify that an expiry exactly on the 30-day boundary returns STATUS_EXPIRING_SOON."""
    today = date(2026, 6, 1)
    boundary_day = today + timedelta(days=30)
    assert days_until_expiry(boundary_day, today=today) == 30
    assert get_expiry_status(boundary_day, today=today, expiring_soon_days=30) == STATUS_EXPIRING_SOON


def test_expiry_beyond_30_days():
    """Verify that expiry beyond the threshold returns STATUS_VALID ('valid')."""
    today = date(2026, 6, 1)

    # 31 days out
    day_31 = today + timedelta(days=31)
    assert days_until_expiry(day_31, today=today) == 31
    assert get_expiry_status(day_31, today=today, expiring_soon_days=30) == STATUS_VALID

    # 180 days out
    day_180 = today + timedelta(days=180)
    assert days_until_expiry(day_180.isoformat(), today=today) == 180
    assert get_expiry_status(day_180.isoformat(), today=today) == STATUS_VALID


def test_custom_threshold():
    """Verify that customizable warning thresholds are respected."""
    today = date(2026, 6, 1)
    day_20 = today + timedelta(days=20)

    # With default 30-day threshold -> expiring_soon
    assert get_expiry_status(day_20, today=today, expiring_soon_days=30) == STATUS_EXPIRING_SOON

    # With custom 14-day threshold -> valid
    assert get_expiry_status(day_20, today=today, expiring_soon_days=14) == STATUS_VALID


def test_invalid_date_formats():
    """Verify that malformed or non-ISO date strings raise descriptive ValueErrors."""
    with pytest.raises(ValueError, match="Expiry date cannot be empty"):
        days_until_expiry("")

    with pytest.raises(ValueError, match="Expiry date cannot be empty"):
        days_until_expiry("   ")

    with pytest.raises(ValueError, match="Invalid date format"):
        days_until_expiry("2026/12/31")

    with pytest.raises(ValueError, match="Invalid date format"):
        days_until_expiry("31-12-2026")

    with pytest.raises(ValueError, match="Invalid date format"):
        days_until_expiry("not-a-date")

    with pytest.raises(ValueError, match="Invalid date format"):
        days_until_expiry("2026-02-31")  # Invalid calendar day
