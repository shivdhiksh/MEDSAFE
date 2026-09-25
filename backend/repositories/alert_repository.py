"""Repository for AlertHistory database operations.

Provides isolated, parameterized SQL operations for checking prior notifications,
preventing duplicate alerts on the same calendar day, and recording delivery history.
"""

from datetime import date, datetime
from pathlib import Path
import sqlite3
from typing import List, Optional, Union

from backend.database import get_connection
from backend.models import AlertHistory
from backend.utils.date_utils import get_now_iso


class AlertRepository:
    """Handles database persistence and duplicate-detection for AlertHistory entities."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def has_alert_for_day(
        self,
        batch_id: int,
        alert_type: str,
        local_date: Union[str, date],
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Determine whether an alert of a specific type has already been sent for a batch on a given local date.

        Args:
            batch_id: Primary key of the batch.
            alert_type: Internal alert type identifier (e.g. 'expiry_30', 'expiry_7', 'expiry_1', 'expired').
            local_date: Target local calendar date (as string 'YYYY-MM-DD' or date object).
            conn: Optional existing connection.

        Returns:
            True if at least one matching notification was recorded on that date, False otherwise.
        """
        date_str = str(local_date)[:10]

        sql = """
            SELECT COUNT(*) AS total
            FROM alert_history
            WHERE batch_id = ?
              AND alert_type = ?
              AND DATE(sent_at) = DATE(?)
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id, alert_type, date_str))
            row = cursor.fetchone()
            return bool(row and row["total"] > 0)
        finally:
            if should_close:
                conn.close()

    def has_alert_ever(
        self,
        batch_id: int,
        alert_type: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Determine whether an alert of a specific type has ever been recorded for a batch.

        Args:
            batch_id: Primary key of the batch.
            alert_type: Internal alert type identifier.
            conn: Optional existing connection.

        Returns:
            True if recorded previously, False otherwise.
        """
        sql = """
            SELECT COUNT(*) AS total
            FROM alert_history
            WHERE batch_id = ?
              AND alert_type = ?
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id, alert_type))
            row = cursor.fetchone()
            return bool(row and row["total"] > 0)
        finally:
            if should_close:
                conn.close()

    def record_alert(
        self,
        batch_id: int,
        alert_type: str,
        sent_at: Optional[Union[str, datetime]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> AlertHistory:
        """Record a successfully delivered notification in the alert_history table.

        Args:
            batch_id: Primary key of the batch.
            alert_type: Internal alert identifier.
            sent_at: Optional ISO timestamp (defaults to current system time).
            conn: Optional existing connection.

        Returns:
            The newly created AlertHistory record.
        """
        timestamp = str(sent_at) if sent_at is not None else get_now_iso()

        sql = """
            INSERT INTO alert_history (batch_id, alert_type, sent_at)
            VALUES (?, ?, ?)
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id, alert_type, timestamp))
            alert_id = cursor.lastrowid
            if should_close:
                conn.commit()

            return AlertHistory(
                id=alert_id,
                batch_id=batch_id,
                alert_type=alert_type,
                sent_at=timestamp,
            )
        finally:
            if should_close:
                conn.close()

    def get_alert_history(
        self,
        batch_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[AlertHistory]:
        """Retrieve all alert records for a specific batch, ordered by sent_at descending."""
        sql = """
            SELECT * FROM alert_history
            WHERE batch_id = ?
            ORDER BY sent_at DESC, id DESC
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id,))
            rows = cursor.fetchall()
            return [AlertHistory.from_row(row) for row in rows]
        finally:
            if should_close:
                conn.close()

    def list_all(
        self,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[AlertHistory]:
        """Retrieve all recorded alerts across all batches, ordered by sent_at descending."""
        sql = "SELECT * FROM alert_history ORDER BY sent_at DESC, id DESC"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [AlertHistory.from_row(row) for row in rows]
        finally:
            if should_close:
                conn.close()

    def delete_for_batch(
        self,
        batch_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """Delete alert history records for a batch (useful for test resets)."""
        sql = "DELETE FROM alert_history WHERE batch_id = ?"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id,))
            if should_close:
                conn.commit()
            return cursor.rowcount
        finally:
            if should_close:
                conn.close()
