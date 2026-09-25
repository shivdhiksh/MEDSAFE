"""SQLite database management layer for MEDSAFE.

Handles database connection lifecycles, foreign key enforcement,
schema migrations, safe first-run data migration, and initial configuration provisioning.
"""

import os
from pathlib import Path
import shutil
import sqlite3
from typing import Optional, Tuple, Union

from backend.config import get_app_root, get_db_path
from backend.utils.date_utils import get_now_iso
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# SQL DDL for complete MedSafe schema
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    strength TEXT,
    medicine_type TEXT,
    manufacturer TEXT,
    barcode TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    batch_number TEXT,
    expiry_date TEXT NOT NULL,
    quantity INTEGER DEFAULT 0,
    storage_location TEXT,
    status TEXT DEFAULT 'active',
    opened_date TEXT,
    disposed_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notifications_enabled INTEGER DEFAULT 1,
    alert_days TEXT DEFAULT '30,7,1',
    theme TEXT DEFAULT 'system',
    created_at TEXT NOT NULL,
    updated_at TEXT
);
"""

SQLITE_HEADER = b"SQLite format 3\x00"


def get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Open and return a configured SQLite connection.

    - Resolves the target database path (defaults to active DB path via get_db_path()).
    - Automatically creates parent directories if they do not exist.
    - Enables foreign key enforcement (PRAGMA foreign_keys = ON).
    - Sets sqlite3.Row as the row factory for dictionary-like column access.

    Args:
        db_path: Optional custom path to SQLite database (used for testing).

    Returns:
        Configured sqlite3.Connection instance.
    """
    target_path = Path(db_path) if db_path is not None else get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def migrate_database(
    source_path: Union[str, Path],
    target_path: Optional[Union[str, Path]] = None,
    overwrite: bool = False,
) -> Tuple[bool, str]:
    """Safely migrate an existing SQLite database into the production database location.

    Safety Rules:
    - Never overwrites an existing database unless overwrite=True is explicitly passed.
    - Never deletes or modifies the source database.
    - Never automatically merges databases.
    - Validates that the source file exists and is a valid SQLite database.
    - Verifies database integrity after copying.

    Args:
        source_path: Path to source SQLite database file.
        target_path: Destination path (defaults to active DB path via get_db_path()).
        overwrite: Safety flag. If False, rejects if destination already exists.

    Returns:
        Tuple of (success: bool, status_message: str).
    """
    src = Path(source_path).resolve()
    if not src.exists() or not src.is_file():
        msg = f"Source database file does not exist: {src}"
        logger.warning(msg)
        return False, msg

    # Validate SQLite header magic bytes
    try:
        with open(src, "rb") as f:
            header = f.read(16)
            if header != SQLITE_HEADER:
                msg = f"Source file is not a valid SQLite database: {src}"
                logger.warning(msg)
                return False, msg
    except Exception as exc:
        msg = f"Could not read source database header: {exc}"
        logger.error(msg)
        return False, msg

    dest = Path(target_path).resolve() if target_path is not None else get_db_path().resolve()

    if dest.exists() and not overwrite:
        msg = f"Target database already exists at '{dest}'. Migration aborted to protect existing data."
        logger.warning(msg)
        return False, msg

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))

        # Integrity check on copied destination
        test_conn = sqlite3.connect(str(dest))
        try:
            cursor = test_conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if not row or row[0] != "ok":
                test_conn.close()
                if dest.exists():
                    dest.unlink()
                msg = f"Migrated database failed SQLite integrity check: {row}"
                logger.error(msg)
                return False, msg
        finally:
            test_conn.close()

        msg = f"Database successfully migrated from '{src}' to '{dest}'."
        logger.info(msg)
        return True, msg
    except Exception as exc:
        msg = f"Migration failed with error: {exc}"
        logger.error(msg)
        return False, msg


def maybe_migrate_dev_database(target_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """Check if explicit development-to-production migration is requested via environment variable.

    Triggered only when MEDSAFE_MIGRATE_DEV_DATA=1 is explicitly set.
    Never overwrites an existing database.
    Never silently copies test data without the explicit environment flag.
    """
    if os.environ.get("MEDSAFE_MIGRATE_DEV_DATA") != "1":
        return False, "Migration skipped (MEDSAFE_MIGRATE_DEV_DATA not enabled)."

    dest = Path(target_path) if target_path is not None else get_db_path()
    if dest.exists():
        return False, f"Target database '{dest}' already exists. Skipping auto-migration."

    dev_db = get_app_root() / "data" / "medsafe.db"
    if not dev_db.exists():
        return False, f"Development database not found at '{dev_db}'."

    logger.info("Executing requested dev-to-production database migration from %s to %s", dev_db, dest)
    return migrate_database(dev_db, dest, overwrite=False)


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize SQLite database tables and default configuration.

    - If explicit migration is enabled (MEDSAFE_MIGRATE_DEV_DATA=1), migrates existing data first.
    - Creates all four core tables if they do not exist.
    - Provisions exactly one default settings row if no settings row exists.
    - Does NOT insert any fake or demo medicine records.

    Args:
        db_path: Optional custom path to SQLite database.
    """
    if db_path is None:
        maybe_migrate_dev_database()

    conn = get_connection(db_path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)

            # Ensure exactly one default settings record exists
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM settings")
            row = cursor.fetchone()
            if row and row["total"] == 0:
                current_time = get_now_iso()
                cursor.execute(
                    """
                    INSERT INTO settings (notifications_enabled, alert_days, theme, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (1, "30,7,1", "system", current_time, current_time),
                )
    finally:
        conn.close()
