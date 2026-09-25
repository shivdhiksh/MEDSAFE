"""Backup and data export service for MEDSAFE.

Provides local, privacy-preserving CSV and JSON exports of all medicine
and batch inventory records. Uses no cloud services or external APIs.
"""

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.config import BACKUPS_DIR
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.utils.date_utils import get_now_iso
from backend.utils.logger import get_logger

logger = get_logger(__name__)

CSV_HEADERS: List[str] = [
    "Medicine Name",
    "Strength",
    "Manufacturer",
    "Medicine Type",
    "Barcode",
    "Batch Number",
    "Expiry Date",
    "Quantity",
    "Storage Location",
    "Status",
    "Opened Date",
    "Disposed Date",
    "Created At",
    "Updated At",
]


class BackupService:
    """Handles offline CSV and JSON data exports for MEDSAFE inventory."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        medicine_repo: Optional[MedicineRepository] = None,
        batch_repo: Optional[BatchRepository] = None,
        backup_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.db_path = db_path
        self.medicine_repo = medicine_repo or MedicineRepository(db_path=db_path)
        self.batch_repo = batch_repo or BatchRepository(db_path=db_path)
        self.backup_dir = Path(backup_dir) if backup_dir is not None else BACKUPS_DIR

    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Create a safe, timestamped backup filename."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"

    def export_csv(
        self,
        custom_output_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[bool, str, Optional[Path]]:
        """Export all medicine and batch inventory to a timestamped CSV file.

        Args:
            custom_output_dir: Optional override for export folder (used in testing).

        Returns:
            Tuple of (success: bool, status_message: str, output_path: Optional[Path]).
        """
        output_dir = Path(custom_output_dir) if custom_output_dir is not None else self.backup_dir

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # 1. Fetch all medicine records and batches
            medicines = self.medicine_repo.list_all()
            if not medicines:
                return False, "No medicine records available to export.", None

            rows_to_write: List[Dict[str, Any]] = []

            for med in medicines:
                batches = self.batch_repo.get_by_medicine_id(med.id)
                if not batches:
                    # Medicine with no batches
                    rows_to_write.append({
                        "Medicine Name": med.name,
                        "Strength": med.strength or "",
                        "Manufacturer": med.manufacturer or "",
                        "Medicine Type": med.medicine_type or "",
                        "Barcode": med.barcode or "",
                        "Batch Number": "",
                        "Expiry Date": "",
                        "Quantity": 0,
                        "Storage Location": "",
                        "Status": "",
                        "Opened Date": "",
                        "Disposed Date": "",
                        "Created At": med.created_at,
                        "Updated At": med.updated_at or "",
                    })
                else:
                    for b in batches:
                        rows_to_write.append({
                            "Medicine Name": med.name,
                            "Strength": med.strength or "",
                            "Manufacturer": med.manufacturer or "",
                            "Medicine Type": med.medicine_type or "",
                            "Barcode": med.barcode or "",
                            "Batch Number": b.batch_number or "",
                            "Expiry Date": b.expiry_date,
                            "Quantity": b.quantity,
                            "Storage Location": b.storage_location or "",
                            "Status": (b.status or "active").title(),
                            "Opened Date": b.opened_date or "",
                            "Disposed Date": b.disposed_date or "",
                            "Created At": b.created_at,
                            "Updated At": b.updated_at or "",
                        })

            filename = self._generate_filename("medsafe_export", "csv")
            filepath = output_dir / filename

            with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(rows_to_write)

            logger.info("Exported CSV successfully with %d rows: %s", len(rows_to_write), filepath)
            return True, "CSV export completed successfully.", filepath
        except Exception as exc:
            logger.error("Failed to export CSV: %s", exc)
            return False, "CSV export failed. Please check the backup folder and try again.", None

    def export_json(
        self,
        custom_output_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[bool, str, Optional[Path]]:
        """Export normalized medicine and batch records to a structured JSON file.

        Args:
            custom_output_dir: Optional override for export folder (used in testing).

        Returns:
            Tuple of (success: bool, status_message: str, output_path: Optional[Path]).
        """
        output_dir = Path(custom_output_dir) if custom_output_dir is not None else self.backup_dir

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            medicines = self.medicine_repo.list_all()
            if not medicines:
                return False, "No medicine records available to export.", None

            export_data: Dict[str, Any] = {
                "export_version": "1.0",
                "exported_at": get_now_iso(),
                "medicines": [],
            }

            for med in medicines:
                batches = self.batch_repo.get_by_medicine_id(med.id)
                med_entry: Dict[str, Any] = {
                    "id": med.id,
                    "name": med.name,
                    "strength": med.strength,
                    "manufacturer": med.manufacturer,
                    "medicine_type": med.medicine_type,
                    "barcode": med.barcode,
                    "notes": med.notes,
                    "created_at": med.created_at,
                    "updated_at": med.updated_at,
                    "batches": [
                        {
                            "id": b.id,
                            "batch_number": b.batch_number,
                            "expiry_date": b.expiry_date,
                            "quantity": b.quantity,
                            "storage_location": b.storage_location,
                            "status": b.status,
                            "opened_date": b.opened_date,
                            "disposed_date": b.disposed_date,
                            "created_at": b.created_at,
                            "updated_at": b.updated_at,
                        }
                        for b in batches
                    ],
                }
                export_data["medicines"].append(med_entry)

            filename = self._generate_filename("medsafe_backup", "json")
            filepath = output_dir / filename

            with open(filepath, mode="w", encoding="utf-8") as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

            logger.info("Exported JSON successfully with %d medicines: %s", len(medicines), filepath)
            return True, "JSON export completed successfully.", filepath
        except Exception as exc:
            logger.error("Failed to export JSON: %s", exc)
            return False, "JSON export failed. Please check the backup folder and try again.", None
