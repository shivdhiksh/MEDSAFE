"""Tests for packaged Windows notification identity.

Verifies that NotificationService dispatches toasts using the application identifier
(app_id="MedSafe") to ensure Windows Action Center attributes alerts correctly to MedSafe.
"""

from unittest.mock import patch
import pytest

from backend.config import APP_ID
from backend.services.notification_service import NotificationService


def test_notification_service_uses_medsafe_app_id() -> None:
    """Verify NotificationService initializes with APP_ID and passes it to win11toast."""
    assert APP_ID == "MedSafe"

    service = NotificationService()
    assert service.app_id == "MedSafe"

    with patch("backend.services.notification_service.win11toast.toast") as mock_toast:
        service._dispatch_toast("Test Title", "Test Body")
        mock_toast.assert_called_once_with("Test Title", "Test Body", app_id="MedSafe")


def test_notification_service_custom_app_id_override() -> None:
    """Verify custom app_id can be passed to NotificationService if needed."""
    service = NotificationService(app_id="CustomMedSafeID")
    assert service.app_id == "CustomMedSafeID"

    with patch("backend.services.notification_service.win11toast.toast") as mock_toast:
        service._dispatch_toast("Custom Title", "Custom Body")
        mock_toast.assert_called_once_with("Custom Title", "Custom Body", app_id="CustomMedSafeID")
