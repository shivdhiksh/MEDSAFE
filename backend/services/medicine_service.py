"""Medicine and batch coordination service for MEDSAFE.

Coordinates business validation, atomic transaction handling, and repository
interactions to persist medicines and their initial batch securely.
"""

from dataclasses import dataclass
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional, Tuple, Union

from backend.database import get_connection
from backend.models import Batch, Medicine
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.utils.date_utils import get_now_iso
from backend.utils.validators import validate_medicine_and_batch_input

logger = logging.getLogger(__name__)


@dataclass
class MedicineCreationResult:
    """Encapsulates the result of a successful atomic medicine and batch creation."""

    medicine: Medicine
    batch: Batch


class MedicineService:
    """Business service governing medicine and batch lifecycle operations."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        medicine_repo: Optional[MedicineRepository] = None,
        batch_repo: Optional[BatchRepository] = None,
    ) -> None:
        self.db_path = db_path
        self.medicine_repo = medicine_repo or MedicineRepository(db_path=db_path)
        self.batch_repo = batch_repo or BatchRepository(db_path=db_path)

    def add_medicine_with_initial_batch(
        self,
        name: Optional[str],
        expiry_date: Optional[str],
        quantity: Any = 0,
        strength: Optional[str] = None,
        medicine_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        barcode: Optional[str] = None,
        notes: Optional[str] = None,
        batch_number: Optional[str] = None,
        storage_location: Optional[str] = None,
    ) -> MedicineCreationResult:
        """Validate, construct, and atomically persist a medicine with its first batch.

        Transaction Safety:
            Executes within a single SQLite transaction block ('with conn:').
            If batch insertion or any validation fails, the entire transaction is rolled back,
            ensuring no orphaned medicine record is ever left in the database.

        Args:
            name: Medicine name (Required).
            expiry_date: ISO expiry date 'YYYY-MM-DD' (Required).
            quantity: Medicine count (Optional, non-negative integer, default 0).
            strength: Drug strength specification, e.g. '500 mg' (Optional).
            medicine_type: Controlled form classification, e.g. 'Tablet' (Optional).
            manufacturer: Manufacturing pharmaceutical company (Optional).
            barcode: Barcode value string (Optional).
            notes: Additional usage or caution notes (Optional).
            batch_number: Specific batch/lot identifier (Optional).
            storage_location: Physical storage location (Optional).

        Returns:
            MedicineCreationResult with persisted Medicine and Batch models.

        Raises:
            ValueError: On user validation errors (missing name, invalid date, negative quantity).
            RuntimeError: On unexpected database errors during execution.
        """
        # 1. Validate business inputs
        validated = validate_medicine_and_batch_input(
            name=name,
            expiry_date=expiry_date,
            quantity=quantity,
            strength=strength,
            medicine_type=medicine_type,
            manufacturer=manufacturer,
            barcode=barcode,
            notes=notes,
            batch_number=batch_number,
            storage_location=storage_location,
        )

        med_data = validated["medicine"]
        batch_data = validated["batch"]
        now_str = get_now_iso()

        # 2. Build model entities
        medicine = Medicine(
            name=med_data["name"],
            strength=med_data["strength"],
            medicine_type=med_data["medicine_type"],
            manufacturer=med_data["manufacturer"],
            barcode=med_data["barcode"],
            notes=med_data["notes"],
            created_at=now_str,
            updated_at=now_str,
        )

        batch = Batch(
            expiry_date=batch_data["expiry_date"],
            quantity=batch_data["quantity"],
            batch_number=batch_data["batch_number"],
            storage_location=batch_data["storage_location"],
            status="active",
            created_at=now_str,
            updated_at=now_str,
        )

        # 3. Execute atomic transaction
        conn = get_connection(self.db_path)
        try:
            with conn:
                # Insert parent medicine
                persisted_medicine = self.medicine_repo.create(medicine, conn=conn)
                if persisted_medicine.id is None:
                    raise RuntimeError("Failed to obtain primary key ID for created medicine.")

                # Link batch to newly generated medicine ID
                batch.medicine_id = persisted_medicine.id

                # Insert child batch
                persisted_batch = self.batch_repo.create(batch, conn=conn)

            logger.info(
                "Atomically created medicine ID %d with initial batch ID %d.",
                persisted_medicine.id,
                persisted_batch.id,
            )
            return MedicineCreationResult(medicine=persisted_medicine, batch=persisted_batch)

        except (sqlite3.Error, Exception) as exc:
            logger.error("Failed to atomically save medicine and batch: %s", exc)
            if isinstance(exc, ValueError):
                raise
            raise RuntimeError("Database error occurred while saving medicine.") from exc
        finally:
            conn.close()

    def get_medicine_by_id(self, medicine_id: int) -> Optional[Medicine]:
        """Fetch a medicine by its identifier."""
        return self.medicine_repo.get_by_id(medicine_id)

    def get_batches_for_medicine(self, medicine_id: int) -> list[Batch]:
        """Fetch all batches associated with a medicine identifier."""
        return self.batch_repo.get_by_medicine_id(medicine_id)
