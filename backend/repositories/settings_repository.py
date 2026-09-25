"""Repository for System Settings database operations.

Provides isolated, parameterized SQL operations for retrieving and updating
notification configurations and user preferences.
"""

from pathlib import Path
import sqlite3
from typing import List, Optional, Union

from backend.database import get_connection
from backend.models import Settings
from backend.utils.date_utils import get_now_iso

DEFAULT_ALERT_DAYS: List[int] = [30, 7, 1]
DEFAULT_ALERT_DAYS_STR: str = "30,7,1"


def parse_alert_days(alert_days_str: Optional[str]) -> List[int]:
    """Parse comma-separated alert thresholds string into a sorted list of positive integers.

    Gracefully handles malformed input, whitespace, non-numeric values, and negative numbers.
    Falls back to [30, 7, 1] if no valid thresholds are found.

    Examples:
        '30,7,1'    -> [30, 7, 1]
        ' 14 , 3 '  -> [14, 3]
        'invalid'   -> [30, 7, 1]
        ''          -> [30, 7, 1]
        None        -> [30, 7, 1]
    """
    if not alert_days_str or not isinstance(alert_days_str, str):
        return list(DEFAULT_ALERT_DAYS)

    valid_thresholds: List[int] = []
    for part in alert_days_str.split(","):
        cleaned = part.strip()
        if not cleaned:
            continue
        try:
            val = int(cleaned)
            if val >= 0 and val not in valid_thresholds:
                valid_thresholds.append(val)
        except ValueError:
            continue

    if not valid_thresholds:
        return list(DEFAULT_ALERT_DAYS)

    # Return descending order of days
    valid_thresholds.sort(reverse=True)
    return valid_thresholds


class SettingsRepository:
    """Handles database retrieval and persistence for Settings entities."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def get_settings(self, conn: Optional[sqlite3.Connection] = None) -> Settings:
        """Fetch active application settings.

        If no settings record exists, creates the default row and returns it.
        """
        sql = "SELECT * FROM settings ORDER BY id ASC LIMIT 1"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is not None:
                return Settings.from_row(row)

            # Insert default settings row if table is empty
            now = get_now_iso()
            cursor.execute(
                """
                INSERT INTO settings (notifications_enabled, alert_days, theme, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, DEFAULT_ALERT_DAYS_STR, "system", now, now),
            )
            settings_id = cursor.lastrowid
            if should_close:
                conn.commit()

            return Settings(
                id=settings_id,
                notifications_enabled=1,
                alert_days=DEFAULT_ALERT_DAYS_STR,
                theme="system",
                created_at=now,
                updated_at=now,
            )
        finally:
            if should_close:
                conn.close()

    def update_notifications_enabled(
        self,
        enabled: bool,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Toggle notifications on or off in the database."""
        now = get_now_iso()
        sql = """
            UPDATE settings
            SET notifications_enabled = ?, updated_at = ?
            WHERE id = (SELECT id FROM settings ORDER BY id ASC LIMIT 1)
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (1 if enabled else 0, now))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()

    def update_alert_days(
        self,
        alert_days_str: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Update the configured expiry threshold string in the database."""
        now = get_now_iso()
        sql = """
            UPDATE settings
            SET alert_days = ?, updated_at = ?
            WHERE id = (SELECT id FROM settings ORDER BY id ASC LIMIT 1)
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (alert_days_str, now))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()

    def update_theme(
        self,
        theme: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Update system theme preference ('system', 'light', 'dark')."""
        now = get_now_iso()
        sql = """
            UPDATE settings
            SET theme = ?, updated_at = ?
            WHERE id = (SELECT id FROM settings ORDER BY id ASC LIMIT 1)
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (theme.strip().lower(), now))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()
