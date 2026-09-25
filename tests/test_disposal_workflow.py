"""Tests for MEDSAFE batch disposal and restoration workflow.

Validates that:
- Batches can be marked as disposed with timestamps.
- Disposed batches are excluded from active dashboard metrics and notifications.
- Disposed batches remain searchable through the 'Disposed' inventory filter.
- Permanent deletion does NOT occur during disposal.
- Batches can be restored to active status safely.
"""

from datetime import date, timedelta
from pathlib import Path
import pytest

from backend.database import init_db
from backend.models import Batch, Medicine
from backend.repositories.alert_repository import AlertRepository
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.services.inventory_service import InventoryService
from backend.services.notification_service import NotificationService


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture providing a clean temporary SQLite database."""
    db_file = tmp_path / "test_disposal.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_medicine_and_batch(temp_db: Path) -> tuple[Medicine, Batch]:
    """Fixture creating a medicine with an active batch."""
    med_repo = MedicineRepository(temp_db)
    batch_repo = BatchRepository(temp_db)

    med = med_repo.create(Medicine(
        name="Amoxicillin",
        strength="500 mg",
        medicine_type="Capsule",
        created_at="2026-09-01T10:00:00",
    ))

    batch = batch_repo.create(Batch(
        medicine_id=med.id,
        batch_number="LOT-DISP",
        expiry_date="2026-10-15",
        quantity=20,
        storage_location="Cabinet",
        status="active",
        created_at="2026-09-01T10:00:00",
        updated_at="2026-09-01T10:00:00",
    ))
    return med, batch


def test_batch_can_be_marked_disposed(
    temp_db: Path,
    sample_medicine_and_batch: tuple[Medicine, Batch],
) -> None:
    """7, 8, 9. Verify batch is marked disposed, disposed_date is stored, and updated_at changes."""
    _, batch = sample_medicine_and_batch
    inv_service = InventoryService(db_path=temp_db)
    batch_repo = BatchRepository(temp_db)

    orig_updated_at = batch.updated_at
    disposal_time = "2026-09-25T14:30:00"

    success = inv_service.mark_batch_as_disposed(batch.id, disposed_date=disposal_time)
    assert success is True

    # Inspect refreshed database record
    updated_batch = batch_repo.get_by_id(batch.id)
    assert updated_batch is not None
    assert updated_batch.status == "disposed"
    assert updated_batch.disposed_date == disposal_time
    assert updated_batch.updated_at != orig_updated_at


def test_disposed_batch_excluded_from_active_dashboard_counts(
    temp_db: Path,
    sample_medicine_and_batch: tuple[Medicine, Batch],
) -> None:
    """10. Verify disposed batch is excluded from active dashboard counts and urgent items."""
    _, batch = sample_medicine_and_batch
    inv_service = InventoryService(db_path=temp_db)

    # Before disposal: 1 active batch
    summary_before = inv_service.get_dashboard_summary()
    assert summary_before.total_active_batches == 1

    # Mark as disposed
    inv_service.mark_batch_as_disposed(batch.id)

    # After disposal: 0 active batches, excluded from valid/expiring/expired/urgent counts
    summary_after = inv_service.get_dashboard_summary()
    assert summary_after.total_active_batches == 0
    assert summary_after.valid_batches == 0
    assert summary_after.expiring_soon_batches == 0
    assert summary_after.expired_batches == 0
    assert len(summary_after.urgent_items) == 0


def test_disposed_batch_does_not_receive_notifications(
    temp_db: Path,
    sample_medicine_and_batch: tuple[Medicine, Batch],
) -> None:
    """11. Verify disposed batch does not trigger M4 expiry notifications even if expired."""
    _, batch = sample_medicine_and_batch
    batch_repo = BatchRepository(temp_db)
    inv_service = InventoryService(db_path=temp_db)
    notif_service = NotificationService(db_path=temp_db)

    # Set batch expiry to past date (expired)
    batch.expiry_date = "2026-09-01"
    batch_repo.update(batch)

    # Mark as disposed
    inv_service.mark_batch_as_disposed(batch.id)

    # Run notification check for 2026-09-25
    result = notif_service.check_and_notify_expiring_batches(today=date(2026, 9, 25))
    assert result.notifications_sent == 0
    assert result.checked_count == 0  # Disposed batch skipped


def test_disposed_batch_found_via_filter(
    temp_db: Path,
    sample_medicine_and_batch: tuple[Medicine, Batch],
) -> None:
    """12. Verify default inventory excludes disposed batches, but 'Disposed' filter finds them."""
    _, batch = sample_medicine_and_batch
    inv_service = InventoryService(db_path=temp_db)

    # Mark as disposed
    inv_service.mark_batch_as_disposed(batch.id)

    # Default 'All' filter must contain active records only
    default_items = inv_service.get_inventory(status_filter="All")
    assert len(default_items) == 0

    # 'Disposed' filter must return the disposed batch
    disposed_items = inv_service.get_inventory(status_filter="Disposed")
    assert len(disposed_items) == 1
    assert disposed_items[0].batch_id == batch.id
    assert disposed_items[0].status == "disposed"


def test_medicine_and_alert_history_not_deleted_by_disposal(
    temp_db: Path,
    sample_medicine_and_batch: tuple[Medicine, Batch],
) -> None:
    """13 & 14. Verify parent medicine and prior alert history remain intact after disposal."""
    med, batch = sample_medicine_and_batch
    inv_service = InventoryService(db_path=temp_db)
    med_repo = MedicineRepository(temp_db)
    alert_repo = AlertRepository(temp_db)

    # Record a prior alert history row for this batch
    alert_repo.record_alert(batch_id=batch.id, alert_type="expiry_7", sent_at="2026-09-20T10:00:00")
    assert len(alert_repo.get_alert_history(batch.id)) == 1

    # Mark as disposed
    inv_service.mark_batch_as_disposed(batch.id)

    # Parent medicine must still exist
    retrieved_med = med_repo.get_by_id(med.id)
    assert retrieved_med is not None
    assert retrieved_med.name == "Amoxicillin"

    # Alert history must remain completely intact
    history = alert_repo.get_alert_history(batch.id)
    assert len(history) == 1
    assert history[0].alert_type == "expiry_7"


def test_restore_disposed_batch_to_active(
    temp_db: Path,
    sample_medicine_and_batch: tuple[Medicine, Batch],
) -> None:
    """15. Verify a disposed batch can be restored to active status."""
    _, batch = sample_medicine_and_batch
    inv_service = InventoryService(db_path=temp_db)
    batch_repo = BatchRepository(temp_db)

    # 1. Mark as disposed
    inv_service.mark_batch_as_disposed(batch.id)
    assert batch_repo.get_by_id(batch.id).status == "disposed"

    # 2. Restore to active
    success = inv_service.restore_batch_to_active(batch.id)
    assert success is True

    # 3. Verify status, cleared disposed_date, and dashboard reappearance
    restored = batch_repo.get_by_id(batch.id)
    assert restored.status == "active"
    assert restored.disposed_date is None

    summary = inv_service.get_dashboard_summary()
    assert summary.total_active_batches == 1
