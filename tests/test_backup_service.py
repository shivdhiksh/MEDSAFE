"""Tests for MEDSAFE BackupService (CSV and JSON offline exports).

Validates:
- File creation in the designated backup directory.
- CSV header compliance and data completeness.
- Structured JSON format, versioning, and relationship preservation.
- Graceful handling of empty databases.
"""

import csv
import json
from pathlib import Path
import pytest

from backend.database import init_db
from backend.models import Batch, Medicine
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.services.backup_service import CSV_HEADERS, BackupService


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture providing a clean temporary SQLite database."""
    db_file = tmp_path / "test_backup.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def backup_dir(tmp_path: Path) -> Path:
    """Fixture providing an isolated backups directory."""
    b_dir = tmp_path / "backups"
    b_dir.mkdir(parents=True, exist_ok=True)
    return b_dir


@pytest.fixture
def populated_db(temp_db: Path) -> Path:
    """Fixture populating database with multiple medicines and batches."""
    med_repo = MedicineRepository(temp_db)
    batch_repo = BatchRepository(temp_db)

    # Medicine 1: Ibuprofen with two batches
    m1 = med_repo.create(Medicine(
        name="Ibuprofen",
        strength="400 mg",
        medicine_type="Tablet",
        manufacturer="HealthCorp",
        barcode="1234567890",
        notes="Anti-inflammatory",
        created_at="2026-09-01T10:00:00",
    ))
    batch_repo.create(Batch(
        medicine_id=m1.id,
        batch_number="LOT-IBU-1",
        expiry_date="2027-05-15",
        quantity=30,
        storage_location="Kitchen Shelf",
        status="active",
        created_at="2026-09-01T10:00:00",
    ))
    batch_repo.create(Batch(
        medicine_id=m1.id,
        batch_number="LOT-IBU-2",
        expiry_date="2026-11-20",
        quantity=15,
        storage_location="First Aid Kit",
        status="disposed",
        disposed_date="2026-09-20T12:00:00",
        created_at="2026-09-01T10:00:00",
    ))

    # Medicine 2: Cetirizine with one batch
    m2 = med_repo.create(Medicine(
        name="Cetirizine",
        strength="10 mg",
        medicine_type="Syrup",
        manufacturer="PharmaLabs",
        created_at="2026-09-05T12:00:00",
    ))
    batch_repo.create(Batch(
        medicine_id=m2.id,
        batch_number="LOT-CET-1",
        expiry_date="2026-12-01",
        quantity=1,
        storage_location="Refrigerator",
        status="active",
        created_at="2026-09-05T12:00:00",
    ))

    return temp_db


def test_csv_export_creates_file_with_expected_headers_and_data(
    populated_db: Path,
    backup_dir: Path,
) -> None:
    """16, 17, 18. Verify CSV file is created with expected headers and rows."""
    service = BackupService(db_path=populated_db, backup_dir=backup_dir)

    success, msg, file_path = service.export_csv()
    assert success is True
    assert "successfully" in msg
    assert file_path is not None
    assert file_path.exists()
    assert file_path.suffix == ".csv"

    # Open and inspect CSV content
    with open(file_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_HEADERS

        rows = list(reader)
        # Total 3 batches across the 2 medicines
        assert len(rows) == 3

        # Verify fields of first row
        names = [r["Medicine Name"] for r in rows]
        assert "Ibuprofen" in names
        assert "Cetirizine" in names

        # Verify lot numbers and status
        lots = [r["Batch Number"] for r in rows]
        assert "LOT-IBU-1" in lots
        assert "LOT-IBU-2" in lots
        assert "LOT-CET-1" in lots


def test_csv_export_handles_empty_database(
    temp_db: Path,
    backup_dir: Path,
) -> None:
    """19. Verify CSV export returns user-friendly feedback when no records exist."""
    service = BackupService(db_path=temp_db, backup_dir=backup_dir)

    success, msg, file_path = service.export_csv()
    assert success is False
    assert "No medicine records available to export" in msg
    assert file_path is None


def test_json_export_creates_file_and_preserves_structure(
    populated_db: Path,
    backup_dir: Path,
) -> None:
    """20, 21, 22, 23. Verify JSON file creation, version, medicines, and batch relationships."""
    service = BackupService(db_path=populated_db, backup_dir=backup_dir)

    success, msg, file_path = service.export_json()
    assert success is True
    assert "successfully" in msg
    assert file_path is not None
    assert file_path.exists()
    assert file_path.suffix == ".json"

    # Read and parse JSON content
    with open(file_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["export_version"] == "1.0"
    assert "exported_at" in data
    assert isinstance(data["medicines"], list)
    assert len(data["medicines"]) == 2

    # Verify first medicine (Ibuprofen) has 2 nested batches
    ibu = next(m for m in data["medicines"] if m["name"] == "Ibuprofen")
    assert ibu["strength"] == "400 mg"
    assert ibu["manufacturer"] == "HealthCorp"
    assert len(ibu["batches"]) == 2

    batch_numbers = [b["batch_number"] for b in ibu["batches"]]
    assert "LOT-IBU-1" in batch_numbers
    assert "LOT-IBU-2" in batch_numbers

    # Verify second medicine (Cetirizine) has 1 nested batch
    cet = next(m for m in data["medicines"] if m["name"] == "Cetirizine")
    assert len(cet["batches"]) == 1
    assert cet["batches"][0]["batch_number"] == "LOT-CET-1"


def test_json_export_handles_empty_database(
    temp_db: Path,
    backup_dir: Path,
) -> None:
    """Verify JSON export handles empty database gracefully."""
    service = BackupService(db_path=temp_db, backup_dir=backup_dir)

    success, msg, file_path = service.export_json()
    assert success is False
    assert "No medicine records available to export" in msg
    assert file_path is None
