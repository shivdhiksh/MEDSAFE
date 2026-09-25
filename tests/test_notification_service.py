"""Tests for MEDSAFE Notification Service and Alert Repository.

Validates threshold detection, toast dispatching, deduplication rules,
settings integration, and alert history persistence using an isolated temporary SQLite database.
Mocking win11toast ensures no real Windows notifications fire during automated runs.
"""

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.database import init_db
from backend.models import Batch, Medicine
from backend.repositories.alert_repository import AlertRepository
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.repositories.settings_repository import SettingsRepository, parse_alert_days
from backend.services.notification_service import (
    ALERT_TYPE_EXPIRED,
    TITLE_EXPIRY_ALERT,
    TITLE_TEST_NOTIFICATION,
    NotificationService,
    determine_alert_type,
    format_expiry_notification_message,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture to create and initialize a clean, temporary SQLite database."""
    db_file = tmp_path / "test_medsafe.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def notif_service(temp_db: Path) -> NotificationService:
    """Fixture providing NotificationService connected to a temporary database."""
    return NotificationService(db_path=temp_db)


@pytest.fixture
def sample_medicine(temp_db: Path) -> Medicine:
    """Fixture creating a baseline medicine record."""
    med_repo = MedicineRepository(temp_db)
    med = Medicine(
        name="Paracetamol",
        strength="500 mg",
        medicine_type="Tablet",
        manufacturer="Acme Pharma",
        created_at="2026-09-01T10:00:00",
    )
    return med_repo.create(med)


def test_determine_alert_type() -> None:
    """Verify alert type assignment for exact thresholds and expired states."""
    thresholds = [30, 7, 1]

    assert determine_alert_type(30, thresholds) == "expiry_30"
    assert determine_alert_type(7, thresholds) == "expiry_7"
    assert determine_alert_type(1, thresholds) == "expiry_1"
    assert determine_alert_type(-1, thresholds) == "expired"
    assert determine_alert_type(-10, thresholds) == "expired"

    # Non-threshold boundaries must NOT trigger alerts
    assert determine_alert_type(29, thresholds) is None
    assert determine_alert_type(15, thresholds) is None
    assert determine_alert_type(2, thresholds) is None
    assert determine_alert_type(0, thresholds) is None


def test_correct_30_day_alert_type(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """1. Verify 30-day alert type produces correct notification."""
    ref_date = date(2026, 9, 25)
    exp_date = ref_date + timedelta(days=30)  # 2026-10-25

    batch_repo = BatchRepository(temp_db)
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT30",
        expiry_date=exp_date.isoformat(),
        quantity=20,
        storage_location="Cabinet A",
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_sent == 1
        assert res.duplicates_suppressed == 0
        mock_toast.assert_called_once()
        title, body = mock_toast.call_args[0]
        assert title == TITLE_EXPIRY_ALERT
        assert "Paracetamol 500 mg expires in 30 days." in body
        assert "Location: Cabinet A." in body

        # Verify alert history
        history = notif_service.alert_repo.list_all()
        assert len(history) == 1
        assert history[0].alert_type == "expiry_30"


def test_correct_7_day_alert_type(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """2. Verify 7-day alert type produces correct notification."""
    ref_date = date(2026, 9, 25)
    exp_date = ref_date + timedelta(days=7)  # 2026-10-02

    batch_repo = BatchRepository(temp_db)
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT7",
        expiry_date=exp_date.isoformat(),
        quantity=10,
        storage_location="First Aid Kit",
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_sent == 1
        mock_toast.assert_called_once()
        title, body = mock_toast.call_args[0]
        assert title == TITLE_EXPIRY_ALERT
        assert "Paracetamol 500 mg expires in 7 days." in body
        assert "Location: First Aid Kit." in body

        history = notif_service.alert_repo.list_all()
        assert len(history) == 1
        assert history[0].alert_type == "expiry_7"


def test_correct_1_day_alert_type(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """3. Verify 1-day alert type produces correct notification."""
    ref_date = date(2026, 9, 25)
    exp_date = ref_date + timedelta(days=1)  # 2026-09-26

    batch_repo = BatchRepository(temp_db)
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT1",
        expiry_date=exp_date.isoformat(),
        quantity=5,
        storage_location=None,  # Location cleanly omitted
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_sent == 1
        mock_toast.assert_called_once()
        title, body = mock_toast.call_args[0]
        assert title == TITLE_EXPIRY_ALERT
        assert "Paracetamol 500 mg expires in 1 day." in body
        assert "Location:" not in body

        history = notif_service.alert_repo.list_all()
        assert len(history) == 1
        assert history[0].alert_type == "expiry_1"


def test_correct_expired_alert_type(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """4. Verify expired batch produces correct expired notification with pharmacist disclaimer."""
    ref_date = date(2026, 9, 25)
    exp_date = ref_date - timedelta(days=3)  # Expired 3 days ago

    batch_repo = BatchRepository(temp_db)
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT_EXP",
        expiry_date=exp_date.isoformat(),
        quantity=2,
        storage_location="Drawer",
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_sent == 1
        mock_toast.assert_called_once()
        title, body = mock_toast.call_args[0]
        assert title == TITLE_EXPIRY_ALERT
        assert "Paracetamol 500 mg expired 3 days ago." in body
        assert "consult a pharmacist or healthcare professional" in body
        assert "Location: Drawer." in body

        history = notif_service.alert_repo.list_all()
        assert len(history) == 1
        assert history[0].alert_type == "expired"


def test_no_alert_when_notifications_disabled(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """5. Verify no alerts are sent when notifications_enabled is set to 0."""
    ref_date = date(2026, 9, 25)
    batch_repo = BatchRepository(temp_db)
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT7",
        expiry_date=(ref_date + timedelta(days=7)).isoformat(),
        quantity=10,
        created_at="2026-09-01T10:00:00",
    ))

    # Disable notifications in settings
    notif_service.settings_repo.update_notifications_enabled(False)

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_enabled is False
        assert res.notifications_sent == 0
        mock_toast.assert_not_called()
        assert len(notif_service.alert_repo.list_all()) == 0


def test_duplicate_alert_suppressed_on_same_day(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """6. Verify duplicate alert is suppressed on the same day for same batch/alert_type."""
    ref_date = date(2026, 9, 25)
    batch_repo = BatchRepository(temp_db)
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT30",
        expiry_date=(ref_date + timedelta(days=30)).isoformat(),
        quantity=15,
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        # First check on 2026-09-25: should send
        res1 = notif_service.check_and_notify_expiring_batches(today=ref_date)
        assert res1.notifications_sent == 1
        assert res1.duplicates_suppressed == 0
        assert mock_toast.call_count == 1

        # Second check on same day 2026-09-25: must be suppressed
        res2 = notif_service.check_and_notify_expiring_batches(today=ref_date)
        assert res2.notifications_sent == 0
        assert res2.duplicates_suppressed == 1
        assert mock_toast.call_count == 1  # No additional toast dispatched

        # Alert history still has only 1 row
        assert len(notif_service.alert_repo.list_all()) == 1


def test_same_alert_may_be_sent_on_different_day_according_to_policy(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """7. Verify expired alert may be sent on a different day according to daily policy."""
    day1 = date(2026, 9, 25)
    day2 = date(2026, 9, 26)

    batch_repo = BatchRepository(temp_db)
    batch = batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT_EXP",
        expiry_date="2026-09-20",  # Expired
        quantity=5,
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        # Day 1: sends notification
        res1 = notif_service.check_and_notify_expiring_batches(today=day1, expired_policy="daily")
        assert res1.notifications_sent == 1
        assert mock_toast.call_count == 1

        # Day 1 second run: suppressed
        res1_dup = notif_service.check_and_notify_expiring_batches(today=day1, expired_policy="daily")
        assert res1_dup.duplicates_suppressed == 1
        assert mock_toast.call_count == 1

        # Day 2: sends under daily policy
        res2 = notif_service.check_and_notify_expiring_batches(today=day2, expired_policy="daily")
        assert res2.notifications_sent == 1
        assert mock_toast.call_count == 2

        # Verify alert history has two records with different dates
        history = notif_service.alert_repo.list_all()
        assert len(history) == 2


def test_alert_history_recorded_after_successful_notification(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """8. Verify alert history is recorded after successful notification."""
    ref_date = date(2026, 9, 25)
    batch_repo = BatchRepository(temp_db)
    batch = batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT7",
        expiry_date=(ref_date + timedelta(days=7)).isoformat(),
        quantity=10,
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast", return_value=True):
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)
        assert res.notifications_sent == 1

        history = notif_service.alert_repo.get_alert_history(batch.id)
        assert len(history) == 1
        assert history[0].batch_id == batch.id
        assert history[0].alert_type == "expiry_7"
        assert history[0].sent_at.startswith("2026-09-25")


def test_alert_history_not_recorded_when_notification_fails(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """9. Verify alert history is NOT recorded when notification dispatch throws an exception."""
    ref_date = date(2026, 9, 25)
    batch_repo = BatchRepository(temp_db)
    batch = batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT7",
        expiry_date=(ref_date + timedelta(days=7)).isoformat(),
        quantity=10,
        created_at="2026-09-01T10:00:00",
    ))

    # Simulate win11toast failure
    with patch.object(notif_service, "_dispatch_toast", side_effect=RuntimeError("Windows Notification API failed")):
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_sent == 0
        assert res.errors_count == 1

        # Must NOT record alert history on failure
        history = notif_service.alert_repo.get_alert_history(batch.id)
        assert len(history) == 0


def test_test_notification_does_not_create_alert_history(
    notif_service: NotificationService,
) -> None:
    """10. Verify test notification dispatches test toast but creates NO alert_history."""
    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        success, msg = notif_service.send_test_notification()

        assert success is True
        assert "successfully" in msg
        mock_toast.assert_called_once_with(TITLE_TEST_NOTIFICATION, "MEDSAFE notifications are working.")

        # Crucial requirement: alert history remains empty
        assert len(notif_service.alert_repo.list_all()) == 0


def test_multiple_batches_processed_independently(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """11. Verify multiple batches are evaluated independently."""
    ref_date = date(2026, 9, 25)
    batch_repo = BatchRepository(temp_db)

    # Batch 1: at 30-day threshold -> alerts
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT30",
        expiry_date=(ref_date + timedelta(days=30)).isoformat(),
        quantity=10,
        created_at="2026-09-01T10:00:00",
    ))

    # Batch 2: at 7-day threshold -> alerts
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT7",
        expiry_date=(ref_date + timedelta(days=7)).isoformat(),
        quantity=15,
        created_at="2026-09-01T10:00:00",
    ))

    # Batch 3: at 15 days -> NOT a threshold, must be skipped
    batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="LOT15",
        expiry_date=(ref_date + timedelta(days=15)).isoformat(),
        quantity=5,
        created_at="2026-09-01T10:00:00",
    ))

    with patch.object(notif_service, "_dispatch_toast") as mock_toast:
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.checked_count == 3
        assert res.notifications_sent == 2
        assert mock_toast.call_count == 2


def test_one_failed_notification_does_not_prevent_other_batches(
    temp_db: Path,
    notif_service: NotificationService,
    sample_medicine: Medicine,
) -> None:
    """12. Verify one failed notification does not abort checking subsequent batches."""
    ref_date = date(2026, 9, 25)
    batch_repo = BatchRepository(temp_db)

    b1 = batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="FAIL_LOT",
        expiry_date=(ref_date + timedelta(days=1)).isoformat(),
        quantity=10,
        created_at="2026-09-01T10:00:00",
    ))

    b2 = batch_repo.create(Batch(
        medicine_id=sample_medicine.id,
        batch_number="SUCCESS_LOT",
        expiry_date=(ref_date + timedelta(days=7)).isoformat(),
        quantity=10,
        created_at="2026-09-01T10:00:00",
    ))

    # Fail on first call, succeed on second call
    with patch.object(
        notif_service,
        "_dispatch_toast",
        side_effect=[RuntimeError("API glitch"), True],
    ):
        res = notif_service.check_and_notify_expiring_batches(today=ref_date)

        assert res.notifications_sent == 1
        assert res.errors_count == 1

        # Only the successful batch has an alert_history record
        history = notif_service.alert_repo.list_all()
        assert len(history) == 1
        assert history[0].batch_id == b2.id
        assert history[0].alert_type == "expiry_7"


def test_parse_alert_days_robustness() -> None:
    """Verify parse_alert_days handles malformed, whitespace, and negative values safely."""
    assert parse_alert_days("30,7,1") == [30, 7, 1]
    assert parse_alert_days(" 14 , 3 , 1 ") == [14, 3, 1]
    assert parse_alert_days("invalid,bad") == [30, 7, 1]
    assert parse_alert_days("") == [30, 7, 1]
    assert parse_alert_days(None) == [30, 7, 1]
    # Ignores negative numbers and keeps positive valid ones
    assert parse_alert_days("-5, 60, abc, 15") == [60, 15]


def test_format_notification_message_safety_compliance() -> None:
    """Verify formatted messages follow MEDSAFE safety requirements."""
    msg = format_expiry_notification_message(
        medicine_name="Amoxicillin",
        strength="250 mg",
        days_left=7,
        storage_location="Medicine Box",
    )
    assert "Amoxicillin 250 mg expires in 7 days." in msg
    assert "Location: Medicine Box." in msg

    # Prohibited words check
    prohibited = ["safe", "unsafe", "okay to consume", "take this medicine", "recommended dosage"]
    for word in prohibited:
        assert word not in msg.lower()
