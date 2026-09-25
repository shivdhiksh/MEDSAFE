"""Repository for Batch entity database operations.

Provides isolated, parameterized SQL CRUD operations for the batches table.
"""

from pathlib import Path
import sqlite3
from typing import List, Optional, Union

from backend.database import get_connection
from backend.models import Batch
from backend.utils.date_utils import get_now_iso


class BatchRepository:
    """Handles database persistence for Batch entities."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def create(self, batch: Batch, conn: Optional[sqlite3.Connection] = None) -> Batch:
        """Insert a new batch record into the database.

        Args:
            batch: Batch model instance with data.
            conn: Optional existing sqlite3.Connection (used during transactions).

        Returns:
            The created Batch with its newly assigned primary key id.
        """
        sql = """
            INSERT INTO batches (
                medicine_id, batch_number, expiry_date, quantity, storage_location,
                status, opened_date, disposed_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            batch.medicine_id,
            batch.batch_number,
            batch.expiry_date,
            batch.quantity,
            batch.storage_location,
            batch.status,
            batch.opened_date,
            batch.disposed_date,
            batch.created_at,
            batch.updated_at,
        )

        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            batch.id = cursor.lastrowid
            if should_close:
                conn.commit()
            return batch
        finally:
            if should_close:
                conn.close()

    def get_by_id(self, batch_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Batch]:
        """Retrieve a batch record by its primary key ID.

        Args:
            batch_id: Integer primary key.
            conn: Optional existing connection.

        Returns:
            Batch instance if found, None otherwise.
        """
        sql = "SELECT * FROM batches WHERE id = ?"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id,))
            row = cursor.fetchone()
            if row is not None:
                return Batch.from_row(row)
            return None
        finally:
            if should_close:
                conn.close()

    def get_by_medicine_id(self, medicine_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Batch]:
        """Retrieve all batches associated with a specific medicine ID, sorted by expiry date."""
        sql = "SELECT * FROM batches WHERE medicine_id = ? ORDER BY expiry_date ASC"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (medicine_id,))
            rows = cursor.fetchall()
            return [Batch.from_row(row) for row in rows]
        finally:
            if should_close:
                conn.close()

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> List[Batch]:
        """Retrieve all batches ordered by expiry date."""
        sql = "SELECT * FROM batches ORDER BY expiry_date ASC"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Batch.from_row(row) for row in rows]
        finally:
            if should_close:
                conn.close()

    def update(self, batch: Batch, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Update an existing batch record.

        Args:
            batch: Batch instance with updated values and valid id.
            conn: Optional existing connection.

        Returns:
            True if a row was updated, False otherwise.
        """
        sql = """
            UPDATE batches
            SET batch_number = ?, expiry_date = ?, quantity = ?, storage_location = ?,
                status = ?, opened_date = ?, disposed_date = ?, updated_at = ?
            WHERE id = ?
        """
        params = (
            batch.batch_number,
            batch.expiry_date,
            batch.quantity,
            batch.storage_location,
            batch.status,
            batch.opened_date,
            batch.disposed_date,
            batch.updated_at,
            batch.id,
        )

        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()

    def delete(self, batch_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Delete a batch record by primary key ID.

        Args:
            batch_id: Integer primary key.
            conn: Optional existing connection.

        Returns:
            True if a row was deleted, False otherwise.
        """
        sql = "DELETE FROM batches WHERE id = ?"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (batch_id,))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()

    def get_distinct_locations(self, conn: Optional[sqlite3.Connection] = None) -> List[str]:
        """Fetch all unique, non-empty storage locations dynamically from batches."""
        sql = """
            SELECT DISTINCT storage_location
            FROM batches
            WHERE storage_location IS NOT NULL AND TRIM(storage_location) != ''
            ORDER BY storage_location COLLATE NOCASE ASC
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [row["storage_location"] for row in rows]
        finally:
            if should_close:
                conn.close()

    def get_all_batches_with_medicine(self, conn: Optional[sqlite3.Connection] = None) -> List[sqlite3.Row]:
        """Retrieve all batch records joined with parent medicine information.

        Returns rows containing both medicine attributes and batch attributes.
        """
        sql = """
            SELECT
                m.id AS medicine_id,
                m.name AS medicine_name,
                m.strength,
                m.medicine_type,
                m.manufacturer,
                m.barcode,
                m.notes,
                b.id AS batch_id,
                b.batch_number,
                b.expiry_date,
                b.quantity,
                b.storage_location,
                b.status,
                b.opened_date,
                b.disposed_date,
                b.created_at AS batch_created_at,
                b.updated_at AS batch_updated_at
            FROM batches b
            JOIN medicines m ON b.medicine_id = m.id
            ORDER BY b.expiry_date ASC
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            if should_close:
                conn.close()

    def mark_disposed(
        self,
        batch_id: int,
        disposed_date: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Mark a batch as disposed with a recorded disposal date and updated timestamp.

        Preserves the batch and medicine records, but updates status to 'disposed'.

        Args:
            batch_id: Integer primary key.
            disposed_date: Optional ISO date/time string (defaults to current timestamp).
            conn: Optional existing connection.

        Returns:
            True if a row was updated, False otherwise.
        """
        now = get_now_iso()
        disp_dt = disposed_date or now
        sql = """
            UPDATE batches
            SET status = 'disposed', disposed_date = ?, updated_at = ?
            WHERE id = ?
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (disp_dt, now, batch_id))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()

    def restore_active(
        self,
        batch_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Restore a disposed batch back to 'active' status, clearing disposed_date.

        Args:
            batch_id: Integer primary key.
            conn: Optional existing connection.

        Returns:
            True if a row was updated, False otherwise.
        """
        now = get_now_iso()
        sql = """
            UPDATE batches
            SET status = 'active', disposed_date = NULL, updated_at = ?
            WHERE id = ?
        """
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (now, batch_id))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()
