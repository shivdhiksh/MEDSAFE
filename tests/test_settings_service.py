"""Tests for MEDSAFE SettingsService and SettingsRepository.

Verifies notifications toggles, threshold normalization, theme preferences,
error handling, and persistent SQLite storage across instances.
"""

from pathlib import Path
import pytest

from backend.database import init_db
from backend.repositories.settings_repository import SettingsRepository
from backend.services.settings_service import SettingsService


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture providing a clean temporary SQLite database."""
    db_file = tmp_path / "test_settings.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def settings_service(temp_db: Path) -> SettingsService:
    """Fixture providing SettingsService instance."""
    return SettingsService(db_path=temp_db)


def test_notifications_can_be_enabled_and_disabled(settings_service: SettingsService) -> None:
    """1 & 2. Verify notifications can be toggled on and off."""
    # Default is enabled (1)
    s0 = settings_service.get_settings()
    assert s0.notifications_enabled == 1

    # Disable notifications
    res_dis = settings_service.update_notifications_enabled(False)
    assert res_dis is True
    assert settings_service.get_settings().notifications_enabled == 0

    # Re-enable notifications
    res_en = settings_service.update_notifications_enabled(True)
    assert res_en is True
    assert settings_service.get_settings().notifications_enabled == 1


def test_alert_thresholds_can_be_updated(settings_service: SettingsService) -> None:
    """3. Verify alert thresholds can be updated with valid comma-separated values."""
    success, msg = settings_service.update_alert_thresholds("14, 7, 2")
    assert success is True
    assert "successfully" in msg

    s = settings_service.get_settings()
    assert s.alert_days == "14,7,2"


def test_invalid_thresholds_are_handled_safely(settings_service: SettingsService) -> None:
    """4. Verify invalid threshold strings are safely rejected with clear error feedback."""
    # Non-numeric text
    ok1, msg1 = settings_service.update_alert_thresholds("invalid,text")
    assert ok1 is False
    assert "Please enter notification thresholds" in msg1

    # Negative numbers
    ok2, msg2 = settings_service.update_alert_thresholds("-5, 10")
    assert ok2 is False
    assert "cannot be negative" in msg2

    # Empty string
    ok3, msg3 = settings_service.update_alert_thresholds("   ")
    assert ok3 is False
    assert "Please enter notification thresholds" in msg3

    # Ensure previous valid settings were NOT corrupted
    s = settings_service.get_settings()
    assert s.alert_days == "30,7,1"


def test_thresholds_whitespace_and_deduplication(settings_service: SettingsService) -> None:
    """Verify threshold strings trim whitespace and remove duplicate values."""
    ok, msg = settings_service.update_alert_thresholds("  30 , 7 , 30 , 1  ")
    assert ok is True
    s = settings_service.get_settings()
    assert s.alert_days == "30,7,1"


def test_theme_can_be_updated(settings_service: SettingsService) -> None:
    """5. Verify theme preferences can be updated to valid options and rejects invalid ones."""
    # Update to Dark
    ok_dark, _ = settings_service.update_theme("Dark")
    assert ok_dark is True
    assert settings_service.get_settings().theme == "dark"

    # Update to Light
    ok_light, _ = settings_service.update_theme("light")
    assert ok_light is True
    assert settings_service.get_settings().theme == "light"

    # Update to System
    ok_sys, _ = settings_service.update_theme("System")
    assert ok_sys is True
    assert settings_service.get_settings().theme == "system"

    # Reject invalid theme
    ok_bad, msg_bad = settings_service.update_theme("neon_cyberpunk")
    assert ok_bad is False
    assert "Invalid theme" in msg_bad


def test_save_all_settings_coordinated(settings_service: SettingsService) -> None:
    """Verify coordinated save_settings updates notifications, thresholds, and theme."""
    success, msg = settings_service.save_settings(
        notifications_enabled=False,
        thresholds_str="60, 15, 3",
        theme="dark",
    )
    assert success is True
    assert "successfully" in msg

    s = settings_service.get_settings()
    assert s.notifications_enabled == 0
    assert s.alert_days == "60,15,3"
    assert s.theme == "dark"


def test_settings_persist_after_restart(temp_db: Path) -> None:
    """6. Verify settings persist across new service and repository instances (simulating app restart)."""
    # 1. First session modifies settings
    svc1 = SettingsService(db_path=temp_db)
    svc1.save_settings(notifications_enabled=False, thresholds_str="45, 10", theme="light")

    # 2. Simulate application restart with a completely fresh service instance
    svc2 = SettingsService(db_path=temp_db)
    s = svc2.get_settings()

    assert s.notifications_enabled == 0
    assert s.alert_days == "45,10"
    assert s.theme == "light"
