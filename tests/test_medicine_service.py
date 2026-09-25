"""Automated tests for MedicineService, validation, repositories, and transaction safety.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from backend.database import get_connection, init_db
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.services.medicine_service import MedicineService


@pytest.fixture
def test_service(tmp_path: Path) -> MedicineService:
    """Fixture providing a fresh MedicineService backed by an isolated temporary database."""
    test_db = tmp_path / "test_medsafe_service.db"
    init_db(test_db)
    return MedicineService(db_path=test_db)


def test_successful_medicine_and_batch_creation(test_service: MedicineService):
    """Verify that a medicine and its associated batch are successfully created and linked."""
    result = test_service.add_medicine_with_initial_batch(
        name="Paracetamol",
        expiry_date="2027-12-31",
        quantity=20,
        strength="500 mg",
        medicine_type="Tablet",
        manufacturer="GSK",
        barcode="8901234567890",
        notes="Keep in a dry place",
        batch_number="TEST-001",
        storage_location="Home Cabinet",
    )

    # 1. Verify returned objects
    assert result.medicine.id is not None
    assert result.batch.id is not None
    assert result.batch.medicine_id == result.medicine.id

    # 2. Verify medicine persistence in database
    persisted_med = test_service.get_medicine_by_id(result.medicine.id)
    assert persisted_med is not None
    assert persisted_med.name == "Paracetamol"
    assert persisted_med.strength == "500 mg"
    assert persisted_med.medicine_type == "Tablet"
    assert persisted_med.manufacturer == "GSK"
    assert persisted_med.barcode == "8901234567890"
    assert persisted_med.notes == "Keep in a dry place"

    # 3. Verify batch persistence in database
    batches = test_service.get_batches_for_medicine(result.medicine.id)
    assert len(batches) == 1
    persisted_batch = batches[0]
    assert persisted_batch.id == result.batch.id
    assert persisted_batch.medicine_id == result.medicine.id
    assert persisted_batch.batch_number == "TEST-001"
    assert persisted_batch.expiry_date == "2027-12-31"
    assert persisted_batch.quantity == 20
    assert persisted_batch.storage_location == "Home Cabinet"
    assert persisted_batch.status == "active"


def test_required_medicine_name_validation(test_service: MedicineService):
    """Verify that missing or blank medicine names are rejected."""
    with pytest.raises(ValueError, match="Medicine name is required"):
        test_service.add_medicine_with_initial_batch(name="", expiry_date="2027-12-31")

    with pytest.raises(ValueError, match="Medicine name is required"):
        test_service.add_medicine_with_initial_batch(name="   ", expiry_date="2027-12-31")

    with pytest.raises(ValueError, match="Medicine name is required"):
        test_service.add_medicine_with_initial_batch(name=None, expiry_date="2027-12-31")


def test_required_expiry_date_validation(test_service: MedicineService):
    """Verify that missing expiry date is rejected."""
    with pytest.raises(ValueError, match="Expiry date is required"):
        test_service.add_medicine_with_initial_batch(name="Aspirin", expiry_date="")

    with pytest.raises(ValueError, match="Expiry date is required"):
        test_service.add_medicine_with_initial_batch(name="Aspirin", expiry_date=None)


def test_invalid_expiry_date_rejection(test_service: MedicineService):
    """Verify that malformed or non-existent calendar dates are rejected."""
    # Invalid calendar day
    with pytest.raises(ValueError, match="Please enter the expiry date in YYYY-MM-DD format"):
        test_service.add_medicine_with_initial_batch(name="Aspirin", expiry_date="2026-02-31")

    # Wrong separator
    with pytest.raises(ValueError, match="Please enter the expiry date in YYYY-MM-DD format"):
        test_service.add_medicine_with_initial_batch(name="Aspirin", expiry_date="2026/12/31")

    # Non-ISO order
    with pytest.raises(ValueError, match="Please enter the expiry date in YYYY-MM-DD format"):
        test_service.add_medicine_with_initial_batch(name="Aspirin", expiry_date="31-12-2026")


def test_quantity_validation(test_service: MedicineService):
    """Verify non-negative integer rules for quantity."""
    # Negative value
    with pytest.raises(ValueError, match="Quantity must be a non-negative whole number"):
        test_service.add_medicine_with_initial_batch(name="Ibuprofen", expiry_date="2027-05-15", quantity=-5)

    # Decimal value
    with pytest.raises(ValueError, match="Quantity must be a non-negative whole number"):
        test_service.add_medicine_with_initial_batch(name="Ibuprofen", expiry_date="2027-05-15", quantity="12.5")

    # Text string
    with pytest.raises(ValueError, match="Quantity must be a non-negative whole number"):
        test_service.add_medicine_with_initial_batch(name="Ibuprofen", expiry_date="2027-05-15", quantity="ten")


def test_empty_quantity_defaults_to_zero(test_service: MedicineService):
    """Verify that omitting quantity or passing empty string defaults to 0."""
    res1 = test_service.add_medicine_with_initial_batch(name="Cough Syrup", expiry_date="2028-01-01", quantity="")
    assert res1.batch.quantity == 0

    res2 = test_service.add_medicine_with_initial_batch(name="Eye Drops", expiry_date="2028-01-01", quantity=None)
    assert res2.batch.quantity == 0


def test_optional_fields_stored_correctly(test_service: MedicineService):
    """Verify that optional fields are stripped of whitespace or stored as None when blank."""
    result = test_service.add_medicine_with_initial_batch(
        name="  Amoxicillin  ",
        expiry_date="2026-11-30",
        quantity=" 15 ",
        strength="  250 mg  ",
        medicine_type="Capsule",
        manufacturer="   Pfizer Inc   ",
        barcode="   ",  # Blank should become None
        notes="",        # Empty should become None
        batch_number="   LOT-99   ",
        storage_location="",
    )

    assert result.medicine.name == "Amoxicillin"
    assert result.medicine.strength == "250 mg"
    assert result.medicine.manufacturer == "Pfizer Inc"
    assert result.medicine.barcode is None
    assert result.medicine.notes is None
    assert result.batch.batch_number == "LOT-99"
    assert result.batch.quantity == 15
    assert result.batch.storage_location is None

    # Test blank manufacturer becomes None
    result2 = test_service.add_medicine_with_initial_batch(
        name="Ibuprofen",
        expiry_date="2027-01-01",
        manufacturer="   ",
    )
    assert result2.medicine.manufacturer is None


def test_atomic_transaction_rollback_on_batch_failure(tmp_path: Path):
    """Verify that if batch creation fails, the medicine creation is rolled back (atomicity)."""
    test_db = tmp_path / "test_rollback.db"
    init_db(test_db)

    # Create a batch repository with a failing create method
    failing_batch_repo = BatchRepository(db_path=test_db)
    failing_batch_repo.create = MagicMock(side_effect=RuntimeError("Simulated disk error during batch write"))

    service = MedicineService(
        db_path=test_db,
        batch_repo=failing_batch_repo,
    )

    # Attempting to add medicine should fail
    with pytest.raises(RuntimeError, match="Database error occurred while saving medicine"):
        service.add_medicine_with_initial_batch(
            name="RollbackTestMed",
            expiry_date="2027-10-10",
            quantity=5,
        )

    # Verify no orphaned medicine was committed to SQLite
    conn = get_connection(test_db)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM medicines WHERE name = 'RollbackTestMed'")
        assert cursor.fetchone()["total"] == 0, "Medicine record should have been rolled back!"

        cursor.execute("SELECT COUNT(*) AS total FROM batches")
        assert cursor.fetchone()["total"] == 0, "No batches should exist in database!"
    finally:
        conn.close()
