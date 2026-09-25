"""Automated tests for InventoryService: dashboard analytics, filtering, sorting, and CRUD.
"""

from datetime import date, timedelta
from pathlib import Path
import pytest

from backend.database import get_connection, init_db
from backend.services.inventory_service import InventoryService
from backend.services.medicine_service import MedicineService


@pytest.fixture
def inv_setup(tmp_path: Path):
    """Fixture providing an initialized test DB and services."""
    test_db = tmp_path / "test_inventory.db"
    init_db(test_db)
    med_service = MedicineService(db_path=test_db)
    inv_service = InventoryService(db_path=test_db)
    return test_db, med_service, inv_service


def test_dashboard_counts_and_urgent_items(inv_setup):
    """Verify dashboard KPI calculations and urgent item sorting."""
    test_db, med_service, inv_service = inv_setup
    today = date(2026, 6, 1)

    # 1. Expired medicine (10 days ago)
    med_service.add_medicine_with_initial_batch(
        name="Expired Syrup",
        expiry_date=(today - timedelta(days=10)).isoformat(),
        quantity=5,
        storage_location="Fridge",
    )

    # 2. Expiring soon (5 days from now)
    med_service.add_medicine_with_initial_batch(
        name="Urgent Tablets",
        expiry_date=(today + timedelta(days=5)).isoformat(),
        quantity=10,
        storage_location="Cabinet",
    )

    # 3. Valid (60 days from now)
    med_service.add_medicine_with_initial_batch(
        name="Valid Capsules",
        expiry_date=(today + timedelta(days=60)).isoformat(),
        quantity=20,
        storage_location="Travel Kit",
    )

    summary = inv_service.get_dashboard_summary(today=today, expiring_soon_days=30)
    assert summary.total_active_batches == 3
    assert summary.valid_batches == 1
    assert summary.expiring_soon_batches == 1
    assert summary.expired_batches == 1
    assert len(summary.urgent_items) == 3

    # Urgent items must be sorted by closest expiry first
    assert summary.urgent_items[0].medicine_name == "Expired Syrup"
    assert summary.urgent_items[1].medicine_name == "Urgent Tablets"
    assert summary.urgent_items[2].medicine_name == "Valid Capsules"


def test_search_by_medicine_name_case_insensitive(inv_setup):
    """Verify case-insensitive search by medicine name."""
    test_db, med_service, inv_service = inv_setup

    med_service.add_medicine_with_initial_batch(name="Paracetamol", expiry_date="2027-12-31")
    med_service.add_medicine_with_initial_batch(name="Amoxicillin", expiry_date="2027-12-31")
    med_service.add_medicine_with_initial_batch(name="ParaCough", expiry_date="2027-12-31")

    # Search lowercase "para"
    results = inv_service.get_inventory(search_query="para")
    names = [r.medicine_name for r in results]
    assert "Paracetamol" in names
    assert "ParaCough" in names
    assert "Amoxicillin" not in names

    # Search uppercase "AMOX"
    results = inv_service.get_inventory(search_query="AMOX")
    assert len(results) == 1
    assert results[0].medicine_name == "Amoxicillin"


def test_status_and_location_filtering(inv_setup):
    """Verify filtering inventory by status and location."""
    test_db, med_service, inv_service = inv_setup
    today = date(2026, 6, 1)

    med_service.add_medicine_with_initial_batch(
        name="Med A",
        expiry_date=(today + timedelta(days=10)).isoformat(),  # expiring soon
        storage_location="Cabinet A",
    )
    med_service.add_medicine_with_initial_batch(
        name="Med B",
        expiry_date=(today + timedelta(days=50)).isoformat(),  # valid
        storage_location="Cabinet B",
    )
    med_service.add_medicine_with_initial_batch(
        name="Med C",
        expiry_date=(today - timedelta(days=5)).isoformat(),   # expired
        storage_location="Cabinet A",
    )

    # Filter Valid
    valid_items = inv_service.get_inventory(status_filter="Valid", today=today)
    assert len(valid_items) == 1
    assert valid_items[0].medicine_name == "Med B"

    # Filter Expiring Soon
    expiring_items = inv_service.get_inventory(status_filter="Expiring Soon", today=today)
    assert len(expiring_items) == 1
    assert expiring_items[0].medicine_name == "Med A"

    # Filter Expired
    expired_items = inv_service.get_inventory(status_filter="Expired", today=today)
    assert len(expired_items) == 1
    assert expired_items[0].medicine_name == "Med C"

    # Filter Location "Cabinet A"
    loc_items = inv_service.get_inventory(location_filter="Cabinet A", today=today)
    assert len(loc_items) == 2
    assert {it.medicine_name for it in loc_items} == {"Med A", "Med C"}


def test_sorting_options(inv_setup):
    """Verify sorting by nearest expiry, oldest expiry, and A-Z / Z-A."""
    test_db, med_service, inv_service = inv_setup
    today = date(2026, 6, 1)

    med_service.add_medicine_with_initial_batch(name="Zinc", expiry_date="2027-01-01")
    med_service.add_medicine_with_initial_batch(name="Aspirin", expiry_date="2026-07-01")
    med_service.add_medicine_with_initial_batch(name="Calcium", expiry_date="2028-01-01")

    # Name A-Z
    az = inv_service.get_inventory(sort_by="name_asc", today=today)
    assert [x.medicine_name for x in az] == ["Aspirin", "Calcium", "Zinc"]

    # Name Z-A
    za = inv_service.get_inventory(sort_by="name_desc", today=today)
    assert [x.medicine_name for x in za] == ["Zinc", "Calcium", "Aspirin"]

    # Nearest expiry
    nearest = inv_service.get_inventory(sort_by="nearest_expiry", today=today)
    assert [x.medicine_name for x in nearest] == ["Aspirin", "Zinc", "Calcium"]

    # Oldest expiry (farthest)
    oldest = inv_service.get_inventory(sort_by="oldest_expiry", today=today)
    assert [x.medicine_name for x in oldest] == ["Calcium", "Zinc", "Aspirin"]


def test_multiple_batches_for_single_medicine(inv_setup):
    """Verify adding multiple batches to one medicine without duplicating medicine record."""
    test_db, med_service, inv_service = inv_setup

    res = med_service.add_medicine_with_initial_batch(
        name="Paracetamol",
        strength="500 mg",
        expiry_date="2026-10-20",
        quantity=8,
        batch_number="A001",
    )
    med_id = res.medicine.id

    # Add second batch to the same medicine
    batch2 = inv_service.add_batch_to_medicine(
        medicine_id=med_id,
        expiry_date="2028-03-15",
        quantity=20,
        batch_number="B001",
        storage_location="Cabinet 2",
    )

    # Verify detail returns 1 medicine with 2 batches
    detail = inv_service.get_medicine_detail(med_id)
    assert detail is not None
    assert detail.medicine.name == "Paracetamol"
    assert len(detail.batches) == 2
    batch_numbers = [b.batch_number for b in detail.batches]
    assert "A001" in batch_numbers
    assert "B001" in batch_numbers

    # Verify total medicines count in database is still 1
    conn = get_connection(test_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM batches").fetchone()[0] == 2
    finally:
        conn.close()


def test_update_medicine_and_batch_with_validation(inv_setup):
    """Verify updates to medicine and batch data, including validation enforcement."""
    test_db, med_service, inv_service = inv_setup

    res = med_service.add_medicine_with_initial_batch(
        name="Original Name",
        strength="100 mg",
        expiry_date="2027-01-01",
        quantity=10,
    )
    med_id = res.medicine.id
    batch_id = res.batch.id

    # 1. Update medicine successfully
    updated_med = inv_service.update_medicine(
        medicine_id=med_id,
        name="Updated Name",
        strength="200 mg",
        manufacturer="New Pharma",
        notes="Updated notes",
    )
    assert updated_med.name == "Updated Name"
    assert updated_med.strength == "200 mg"
    assert updated_med.manufacturer == "New Pharma"

    # Validation: blank name rejected
    with pytest.raises(ValueError, match="Medicine name is required"):
        inv_service.update_medicine(medicine_id=med_id, name="   ")

    # 2. Update batch successfully
    updated_batch = inv_service.update_batch(
        batch_id=batch_id,
        expiry_date="2027-06-30",
        quantity=25,
        batch_number="NEW-LOT",
        storage_location="Shelf 3",
    )
    assert updated_batch.expiry_date == "2027-06-30"
    assert updated_batch.quantity == 25
    assert updated_batch.batch_number == "NEW-LOT"

    # Validation: negative quantity rejected
    with pytest.raises(ValueError, match="Quantity must be a non-negative whole number"):
        inv_service.update_batch(batch_id=batch_id, expiry_date="2027-06-30", quantity=-1)

    # Validation: invalid date format rejected
    with pytest.raises(ValueError, match="Please enter the expiry date in YYYY-MM-DD format"):
        inv_service.update_batch(batch_id=batch_id, expiry_date="2027/06/30", quantity=10)


def test_permanent_delete_cascades_batches(inv_setup):
    """Verify deleting a medicine cascades and deletes all associated batches."""
    test_db, med_service, inv_service = inv_setup

    res = med_service.add_medicine_with_initial_batch(
        name="To Delete",
        expiry_date="2027-01-01",
    )
    med_id = res.medicine.id
    inv_service.add_batch_to_medicine(medicine_id=med_id, expiry_date="2028-01-01")

    # Confirm exists
    assert inv_service.get_medicine_detail(med_id) is not None

    # Delete medicine
    deleted = inv_service.delete_medicine(med_id)
    assert deleted is True

    # Confirm detail is None and batches are gone
    assert inv_service.get_medicine_detail(med_id) is None
    conn = get_connection(test_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM medicines WHERE id = ?", (med_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM batches WHERE medicine_id = ?", (med_id,)).fetchone()[0] == 0
    finally:
        conn.close()
