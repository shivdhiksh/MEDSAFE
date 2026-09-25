"""Automated tests for MEDSAFE database initialization, schema integrity, and constraints.
"""

from pathlib import Path
import sqlite3
import pytest

from backend.database import get_connection, init_db
from backend.models import Batch, Medicine, Settings


def test_init_db_creates_all_required_tables(tmp_path: Path):
    """Verify that init_db creates all 4 required tables: medicines, batches, alert_history, settings."""
    test_db_path = tmp_path / "test_medsafe.db"
    init_db(test_db_path)

    conn = get_connection(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}

        required_tables = {"medicines", "batches", "alert_history", "settings"}
        assert required_tables.issubset(tables), f"Missing tables. Found: {tables}"
    finally:
        conn.close()


def test_default_settings_provisioned_and_idempotent(tmp_path: Path):
    """Verify that exactly one default settings record is created with specified defaults."""
    test_db_path = tmp_path / "test_medsafe.db"
    init_db(test_db_path)

    conn = get_connection(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings")
        rows = cursor.fetchall()
        assert len(rows) == 1, "Exactly one settings row should exist upon initialization."

        settings = Settings.from_row(rows[0])
        assert settings.notifications_enabled == 1
        assert settings.alert_days == "30,7,1"
        assert settings.theme == "system"
        assert settings.created_at != ""

        # Re-running init_db must be idempotent and not create duplicate settings
        init_db(test_db_path)
        cursor.execute("SELECT COUNT(*) AS total FROM settings")
        assert cursor.fetchone()["total"] == 1
    finally:
        conn.close()


def test_no_fake_medicines_or_batches(tmp_path: Path):
    """Verify that an initialized database is clean and contains no demo or dummy data."""
    test_db_path = tmp_path / "test_medsafe.db"
    init_db(test_db_path)

    conn = get_connection(test_db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM medicines")
        assert cursor.fetchone()["total"] == 0

        cursor.execute("SELECT COUNT(*) AS total FROM batches")
        assert cursor.fetchone()["total"] == 0

        cursor.execute("SELECT COUNT(*) AS total FROM alert_history")
        assert cursor.fetchone()["total"] == 0
    finally:
        conn.close()


def test_foreign_key_enforcement(tmp_path: Path):
    """Verify that foreign key constraints are strictly enforced."""
    test_db_path = tmp_path / "test_medsafe.db"
    init_db(test_db_path)

    conn = get_connection(test_db_path)
    try:
        cursor = conn.cursor()
        # Attempt to insert a batch pointing to non-existent medicine_id 9999
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO batches (medicine_id, batch_number, expiry_date, quantity, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (9999, "B123", "2026-12-31", 10, "active", "2026-01-01 00:00:00"),
            )
            conn.commit()
    finally:
        conn.close()


def test_foreign_key_cascade_deletion(tmp_path: Path):
    """Verify that deleting a medicine cascades and cleans up its associated batches."""
    test_db_path = tmp_path / "test_medsafe.db"
    init_db(test_db_path)

    conn = get_connection(test_db_path)
    try:
        cursor = conn.cursor()

        # 1. Insert a parent medicine
        cursor.execute(
            """
            INSERT INTO medicines (name, strength, created_at)
            VALUES (?, ?, ?)
            """,
            ("Paracetamol", "500 mg", "2026-01-01 00:00:00"),
        )
        medicine_id = cursor.lastrowid

        # 2. Insert a child batch
        cursor.execute(
            """
            INSERT INTO batches (medicine_id, batch_number, expiry_date, quantity, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (medicine_id, "BATCH-001", "2026-10-20", 8, "active", "2026-01-01 00:00:00"),
        )
        conn.commit()

        # Verify batch exists
        cursor.execute("SELECT COUNT(*) AS total FROM batches WHERE medicine_id = ?", (medicine_id,))
        assert cursor.fetchone()["total"] == 1

        # 3. Delete parent medicine
        cursor.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
        conn.commit()

        # Verify batch was cascaded
        cursor.execute("SELECT COUNT(*) AS total FROM batches WHERE medicine_id = ?", (medicine_id,))
        assert cursor.fetchone()["total"] == 0
    finally:
        conn.close()
