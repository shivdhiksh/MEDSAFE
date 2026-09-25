"""Repository for Medicine entity database operations.

Provides isolated, parameterized SQL CRUD operations for the medicines table.
"""

from pathlib import Path
import sqlite3
from typing import List, Optional, Union

from backend.database import get_connection
from backend.models import Medicine


class MedicineRepository:
    """Handles database persistence for Medicine entities."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def create(self, medicine: Medicine, conn: Optional[sqlite3.Connection] = None) -> Medicine:
        """Insert a new medicine record into the database.

        Args:
            medicine: Medicine model instance with data.
            conn: Optional existing sqlite3.Connection (used during transactions).

        Returns:
            The created Medicine with its newly assigned primary key id.
        """
        sql = """
            INSERT INTO medicines (
                name, strength, medicine_type, manufacturer, barcode, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            medicine.name,
            medicine.strength,
            medicine.medicine_type,
            medicine.manufacturer,
            medicine.barcode,
            medicine.notes,
            medicine.created_at,
            medicine.updated_at,
        )

        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            medicine.id = cursor.lastrowid
            if should_close:
                conn.commit()
            return medicine
        finally:
            if should_close:
                conn.close()

    def get_by_id(self, medicine_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Medicine]:
        """Retrieve a medicine record by its primary key ID.

        Args:
            medicine_id: Integer primary key.
            conn: Optional existing connection.

        Returns:
            Medicine instance if found, None otherwise.
        """
        sql = "SELECT * FROM medicines WHERE id = ?"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (medicine_id,))
            row = cursor.fetchone()
            if row is not None:
                return Medicine.from_row(row)
            return None
        finally:
            if should_close:
                conn.close()

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> List[Medicine]:
        """Retrieve all medicines ordered alphabetically by name."""
        sql = "SELECT * FROM medicines ORDER BY name COLLATE NOCASE ASC"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Medicine.from_row(row) for row in rows]
        finally:
            if should_close:
                conn.close()

    def update(self, medicine: Medicine, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Update an existing medicine record.

        Args:
            medicine: Medicine instance with updated fields and valid id.
            conn: Optional existing connection.

        Returns:
            True if a record was updated, False otherwise.
        """
        sql = """
            UPDATE medicines
            SET name = ?, strength = ?, medicine_type = ?, manufacturer = ?,
                barcode = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """
        params = (
            medicine.name,
            medicine.strength,
            medicine.medicine_type,
            medicine.manufacturer,
            medicine.barcode,
            medicine.notes,
            medicine.updated_at,
            medicine.id,
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

    def delete(self, medicine_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Delete a medicine record by ID.

        Foreign keys cascade will automatically delete associated batches.

        Args:
            medicine_id: Integer primary key.
            conn: Optional existing connection.

        Returns:
            True if a record was deleted, False otherwise.
        """
        sql = "DELETE FROM medicines WHERE id = ?"
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True

        try:
            cursor = conn.cursor()
            cursor.execute(sql, (medicine_id,))
            if should_close:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if should_close:
                conn.close()
