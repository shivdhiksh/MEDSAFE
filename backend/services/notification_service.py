"""Notification service for MEDSAFE.

Manages local Windows toast notifications for expiring and expired medicine batches
using win11toast, enforces threshold rules and deduplication, and records alert history.

IMPORTANT CONSTRAINTS:
- Does NOT import CustomTkinter or access UI widgets.
- Does NOT run raw SQL; uses AlertRepository, BatchRepository, and SettingsRepository.
- Safe offline execution with robust failure handling.
- Follows MEDSAFE safety guidelines:
  Never states or implies medicines are 'safe', 'unsafe', or 'okay to consume'.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import win11toast

from backend.config import APP_ID
from backend.models import AlertHistory, Settings
from backend.repositories.alert_repository import AlertRepository
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.settings_repository import SettingsRepository, parse_alert_days
from backend.services.expiry_service import days_until_expiry
from backend.utils.date_utils import get_now_iso, get_today
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Standard notification titles and alert types
TITLE_EXPIRY_ALERT: str = "Medicine expiry alert"
TITLE_TEST_NOTIFICATION: str = "MEDSAFE Test Notification"

ALERT_TYPE_EXPIRED: str = "expired"


def determine_alert_type(days_left: int, thresholds: List[int]) -> Optional[str]:
    """Determine the alert type string matching days_left against thresholds.

    Rules:
        - days_left < 0: 'expired'
        - days_left in thresholds: 'expiry_{days_left}' (e.g. 'expiry_30', 'expiry_7', 'expiry_1')
        - Otherwise: None (no alert boundary reached)

    Args:
        days_left: Signed number of days remaining until batch expiry.
        thresholds: List of configured warning thresholds (e.g. [30, 7, 1]).

    Returns:
        String alert type or None if no threshold is met.
    """
    if days_left < 0:
        return ALERT_TYPE_EXPIRED
    if days_left in thresholds:
        return f"expiry_{days_left}"
    return None


def format_expiry_notification_message(
    medicine_name: str,
    strength: Optional[str] = None,
    days_left: int = 0,
    storage_location: Optional[str] = None,
) -> str:
    """Format an informative, strictly organizational medicine expiry reminder.

    Adheres strictly to MEDSAFE safety standards:
    - Never uses words: safe, unsafe, okay to consume, take this medicine, recommended dosage.
    - Omit strength cleanly if missing or empty.
    - Omit storage location cleanly if missing or empty.

    Examples:
        - "Paracetamol 500 mg expires in 7 days. Location: Home Cabinet."
        - "Paracetamol 500 mg expired 3 days ago. Verify the packaging and consult a pharmacist or healthcare professional if unsure."
        - "Ibuprofen expires in 1 day."
    """
    clean_name = medicine_name.strip()
    clean_strength = strength.strip() if strength and strength.strip() else ""

    if clean_strength:
        med_display = f"{clean_name} {clean_strength}"
    else:
        med_display = clean_name

    clean_location = (
        storage_location.strip()
        if storage_location and storage_location.strip()
        else ""
    )

    if days_left < 0:
        abs_days = abs(days_left)
        day_str = f"{abs_days} day{'s' if abs_days != 1 else ''} ago"
        msg = (
            f"{med_display} expired {day_str}. "
            "Verify the packaging and consult a pharmacist or healthcare professional if unsure."
        )
    elif days_left == 0:
        msg = f"{med_display} expires today."
    elif days_left == 1:
        msg = f"{med_display} expires in 1 day."
    else:
        msg = f"{med_display} expires in {days_left} days."

    if clean_location:
        msg += f" Location: {clean_location}."

    return msg


@dataclass
class ExpiryCheckResult:
    """Summary of batch checking and notification execution."""

    checked_count: int = 0
    notifications_sent: int = 0
    duplicates_suppressed: int = 0
    errors_count: int = 0
    notifications_enabled: bool = True
    details: List[Dict[str, Any]] = field(default_factory=list)


class NotificationService:
    """Handles local Windows notifications and batch expiry auditing."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        alert_repository: Optional[AlertRepository] = None,
        batch_repository: Optional[BatchRepository] = None,
        settings_repository: Optional[SettingsRepository] = None,
        app_id: Optional[str] = None,
    ) -> None:
        self.db_path = db_path
        self.alert_repo = alert_repository or AlertRepository(db_path)
        self.batch_repo = batch_repository or BatchRepository(db_path)
        self.settings_repo = settings_repository or SettingsRepository(db_path)
        self.app_id = app_id or APP_ID
        self.logger = logger

    def _dispatch_toast(self, title: str, body: str) -> Any:
        """Low-level dispatch of Windows toast via win11toast.

        Isolated for clean unit test mocking.
        """
        try:
            return win11toast.toast(title, body, app_id=self.app_id)
        except TypeError:
            return win11toast.toast(title, body)

    def send_test_notification(self) -> Tuple[bool, str]:
        """Send a harmless local test toast notification.

        Does NOT create an alert_history record.
        Returns:
            Tuple of (success: bool, status_message: str).
        """
        title = TITLE_TEST_NOTIFICATION
        body = "MEDSAFE notifications are working."
        try:
            self.logger.info("Attempting to send test notification")
            self._dispatch_toast(title, body)
            self.logger.info("Test notification delivered successfully")
            return True, "Test notification sent successfully."
        except Exception as exc:
            self.logger.error("Failed to deliver test notification: %s", exc)
            return False, f"Delivery failed: {exc}"

    def send_expiry_notification(
        self,
        medicine_name: str,
        strength: Optional[str] = None,
        batch_number: Optional[str] = None,
        days_left: int = 0,
        storage_location: Optional[str] = None,
        alert_type: str = "expiry_alert",
    ) -> bool:
        """Format and dispatch a single medicine expiry toast notification.

        Args:
            medicine_name: Name of the drug.
            strength: Optional strength string (e.g. '500 mg').
            batch_number: Optional batch lot identifier.
            days_left: Signed days remaining until expiry.
            storage_location: Optional storage location.
            alert_type: Internal alert type identifier.

        Returns:
            True if delivered successfully, False if delivery failed.
        """
        title = TITLE_EXPIRY_ALERT
        body = format_expiry_notification_message(
            medicine_name=medicine_name,
            strength=strength,
            days_left=days_left,
            storage_location=storage_location,
        )
        try:
            self.logger.info(
                "Attempting notification for '%s' (%s, %d days left)",
                medicine_name,
                alert_type,
                days_left,
            )
            self._dispatch_toast(title, body)
            self.logger.info(
                "Notification successfully dispatched for '%s' (%s)",
                medicine_name,
                alert_type,
            )
            return True
        except Exception as exc:
            self.logger.error(
                "Failed to send notification for '%s' (%s): %s",
                medicine_name,
                alert_type,
                exc,
            )
            return False

    def check_and_notify_expiring_batches(
        self,
        today: Optional[date] = None,
        expired_policy: str = "daily",
    ) -> ExpiryCheckResult:
        """Inspect all active inventory batches and dispatch eligible expiry notifications.

        Execution algorithm:
        1. Load notification settings.
        2. If notifications_enabled == 0, abort without sending.
        3. Parse alert thresholds (e.g. 30, 7, 1).
        4. Load active batches joined with medicine details.
        5. For each batch, calculate days_until_expiry.
        6. Determine matching alert_type.
        7. Check AlertRepository to see if this alert_type was already sent today.
           - For 'expired': If expired_policy == 'once', suppress if sent ever;
             if expired_policy == 'daily', suppress if sent today.
        8. If not sent, attempt Windows toast notification.
        9. On success, record entry in alert_history.
        10. On failure, log error without creating an alert_history entry.
        11. Continue processing remaining batches without halting on errors.

        Args:
            today: Optional reference date (defaults to current system date).
            expired_policy: Policy for expired alerts ('daily' or 'once').

        Returns:
            ExpiryCheckResult summarizing the outcome.
        """
        result = ExpiryCheckResult()
        ref_date = today if today is not None else get_today()
        ref_date_iso = ref_date.isoformat()

        # 1. Load settings
        settings: Settings = self.settings_repo.get_settings()
        if not settings.notifications_enabled:
            self.logger.info("Notifications are disabled in settings. Skipping check.")
            result.notifications_enabled = False
            return result

        thresholds = parse_alert_days(settings.alert_days)
        self.logger.info("Running expiry notification check for %s (thresholds: %s)", ref_date_iso, thresholds)

        # 2. Load active batches
        batches = self.batch_repo.get_all_batches_with_medicine()

        for row in batches:
            # Check only active batches
            if row["status"] != "active":
                continue

            result.checked_count += 1
            batch_id = row["batch_id"]
            med_name = row["medicine_name"]
            expiry_str = row["expiry_date"]

            try:
                days_left = days_until_expiry(expiry_str, today=ref_date)
            except ValueError as val_err:
                self.logger.warning("Skipping batch %d due to invalid expiry date '%s': %s", batch_id, expiry_str, val_err)
                continue

            alert_type = determine_alert_type(days_left, thresholds)
            if alert_type is None:
                continue

            # 3. Duplicate check
            already_sent_today = self.alert_repo.has_alert_for_day(
                batch_id=batch_id,
                alert_type=alert_type,
                local_date=ref_date,
            )

            is_duplicate = already_sent_today
            if alert_type == ALERT_TYPE_EXPIRED and expired_policy == "once":
                already_sent_ever = self.alert_repo.has_alert_ever(batch_id=batch_id, alert_type=alert_type)
                is_duplicate = is_duplicate or already_sent_ever

            if is_duplicate:
                result.duplicates_suppressed += 1
                self.logger.info(
                    "Duplicate alert suppressed for batch %d ('%s', %s) on %s",
                    batch_id,
                    med_name,
                    alert_type,
                    ref_date_iso,
                )
                continue

            # 4. Attempt notification delivery
            sent_ok = self.send_expiry_notification(
                medicine_name=med_name,
                strength=row["strength"],
                batch_number=row["batch_number"],
                days_left=days_left,
                storage_location=row["storage_location"],
                alert_type=alert_type,
            )

            # 5. Record history strictly on successful delivery
            if sent_ok:
                sent_at_timestamp = get_now_iso() if today is None else f"{ref_date_iso}T12:00:00"
                self.alert_repo.record_alert(
                    batch_id=batch_id,
                    alert_type=alert_type,
                    sent_at=sent_at_timestamp,
                )
                result.notifications_sent += 1
                result.details.append({
                    "batch_id": batch_id,
                    "medicine_name": med_name,
                    "alert_type": alert_type,
                    "days_left": days_left,
                    "status": "sent",
                })
            else:
                result.errors_count += 1
                result.details.append({
                    "batch_id": batch_id,
                    "medicine_name": med_name,
                    "alert_type": alert_type,
                    "days_left": days_left,
                    "status": "failed",
                })

        self.logger.info(
            "Expiry check completed: %d checked, %d sent, %d duplicates suppressed, %d errors",
            result.checked_count,
            result.notifications_sent,
            result.duplicates_suppressed,
            result.errors_count,
        )
        return result


if __name__ == "__main__":
    import sys
    from backend.database import init_db

    init_db()
    service = NotificationService()
    res = service.check_and_notify_expiring_batches()
    print(
        f"Expiry check completed: {res.notifications_sent} sent, "
        f"{res.duplicates_suppressed} suppressed, {res.errors_count} errors, "
        f"{res.checked_count} checked."
    )
    sys.exit(0)
