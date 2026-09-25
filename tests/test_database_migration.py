"""Tests for safe database initialization and migration in MEDSAFE.

Verifies:
- Fresh production database initialization creates clean tables with 0 records.
- Database persistence across multiple connections.
- Deterministic and safe database migration mechanism.
- Strict protection against overwriting existing production data.
- Strict preservation of source database (never deleted).
- Rejection of invalid or corrupt source files.
- Controlled migration via MEDSAFE_MIGRATE_DEV_DATA.
"""

from pathlib import Path
import sqlite3
import pytest

from backend.database import get_connection, init_db, maybe_migrate_dev_database, migrate_database
from backend.models import Batch, Medicine
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.repositories.settings_repository import SettingsRepository


def test_fresh_production_database_initialization(tmp_path: Path) -> None:
    """Verify that initializing a fresh database produces 0 medicines, 0 batches, and 1 default settings row."""
    fresh_db = tmp_path / "fresh_medsafe.db"
    init_db(fresh_db)

    conn = get_connection(fresh_db)
    try:
        med_count = conn.execute("SELECT COUNT(*) AS total FROM medicines").fetchone()["total"]
        batch_count = conn.execute("SELECT COUNT(*) AS total FROM batches").fetchone()["total"]
        alert_count = conn.execute("SELECT COUNT(*) AS total FROM alert_history").fetchone()["total"]
        settings_row = conn.execute("SELECT * FROM settings").fetchone()

        assert med_count == 0
        assert batch_count == 0
        assert alert_count == 0
        assert settings_row is not None
        assert settings_row["notifications_enabled"] == 1
        assert settings_row["alert_days"] == "30,7,1"
        assert settings_row["theme"] == "system"
    finally:
        conn.close()


def test_database_persistence_across_connections(tmp_path: Path) -> None:
    """Verify that records saved to the database persist across distinct connections and initializations."""
    db_file = tmp_path / "persist_test.db"
    init_db(db_file)

    med_repo = MedicineRepository(db_file)
    created_med = med_repo.create(Medicine(name="Amoxicillin", strength="250 mg", created_at="2026-09-01T10:00:00"))

    batch_repo = BatchRepository(db_file)
    batch_repo.create(Batch(medicine_id=created_med.id, batch_number="AMX01", expiry_date="2027-01-01", created_at="2026-09-01T10:00:00"))

    # Re-open database with a new connection and re-run init_db (idempotent)
    init_db(db_file)
    new_med_repo = MedicineRepository(db_file)
    new_batch_repo = BatchRepository(db_file)

    all_meds = new_med_repo.list_all()
    assert len(all_meds) == 1
    assert all_meds[0].name == "Amoxicillin"

    batches = new_batch_repo.get_by_medicine_id(created_med.id)
    assert len(batches) == 1
    assert batches[0].batch_number == "AMX01"


def test_migrate_database_success(tmp_path: Path) -> None:
    """Verify valid SQLite database is copied safely to destination with data and schema intact."""
    src_db = tmp_path / "source.db"
    dest_db = tmp_path / "dest" / "production.db"

    init_db(src_db)
    med_repo = MedicineRepository(src_db)
    med_repo.create(Medicine(name="Cetirizine", strength="10 mg", created_at="2026-09-01T10:00:00"))

    success, msg = migrate_database(src_db, dest_db)

    assert success is True
    assert "Database successfully migrated" in msg
    assert dest_db.exists()

    # Verify content in destination
    dest_repo = MedicineRepository(dest_db)
    meds = dest_repo.list_all()
    assert len(meds) == 1
    assert meds[0].name == "Cetirizine"

    # Verify source database was NOT deleted or altered
    assert src_db.exists()
    src_meds = med_repo.list_all()
    assert len(src_meds) == 1


def test_migrate_database_refuses_to_overwrite_existing(tmp_path: Path) -> None:
    """Verify migrate_database aborts and protects existing destination database when overwrite=False."""
    src_db = tmp_path / "src.db"
    dest_db = tmp_path / "dest.db"

    init_db(src_db)
    init_db(dest_db)

    dest_repo = MedicineRepository(dest_db)
    dest_repo.create(Medicine(name="Existing Production Medicine", created_at="2026-09-01T10:00:00"))

    success, msg = migrate_database(src_db, dest_db, overwrite=False)

    assert success is False
    assert "Target database already exists" in msg

    # Verify existing production record was preserved
    meds = dest_repo.list_all()
    assert len(meds) == 1
    assert meds[0].name == "Existing Production Medicine"


def test_migrate_database_rejects_invalid_source_file(tmp_path: Path) -> None:
    """Verify migration fails safely when source file is not a valid SQLite database."""
    fake_file = tmp_path / "fake.db"
    fake_file.write_text("This is not a sqlite database file!", encoding="utf-8")

    dest_db = tmp_path / "target.db"
    success, msg = migrate_database(fake_file, dest_db)

    assert success is False
    assert "not a valid SQLite database" in msg
    assert not dest_db.exists()


def test_maybe_migrate_dev_database_requires_explicit_env_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify maybe_migrate_dev_database does not silently copy data unless MEDSAFE_MIGRATE_DEV_DATA=1."""
    monkeypatch.delenv("MEDSAFE_MIGRATE_DEV_DATA", raising=False)
    target_db = tmp_path / "target.db"

    success, msg = maybe_migrate_dev_database(target_path=target_db)
    assert success is False
    assert "not enabled" in msg
    assert not target_db.exists()
