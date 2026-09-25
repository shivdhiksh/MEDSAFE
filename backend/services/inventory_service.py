"""Inventory and dashboard business service for MEDSAFE.

Coordinates dashboard analytics, inventory filtering, search, sorting,
and CRUD operations for medicines and their batches.
"""

from datetime import date
import logging
from pathlib import Path
from typing import Any, List, Optional, Union

from backend.models import (
    Batch,
    DashboardSummary,
    InventoryItem,
    Medicine,
    MedicineDetail,
)
from backend.repositories.batch_repository import BatchRepository
from backend.repositories.medicine_repository import MedicineRepository
from backend.services.expiry_service import (
    DEFAULT_EXPIRING_SOON_DAYS,
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
    days_until_expiry,
    format_expiry_human_label,
    get_expiry_status,
)
from backend.utils.date_utils import get_now_iso
from backend.utils.validators import (
    validate_batch_input,
    validate_medicine_update,
)

logger = logging.getLogger(__name__)


class InventoryService:
    """Provides high-level inventory querying, dashboard metric aggregation, and record updates."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        medicine_repo: Optional[MedicineRepository] = None,
        batch_repo: Optional[BatchRepository] = None,
    ) -> None:
        self.db_path = db_path
        self.medicine_repo = medicine_repo or MedicineRepository(db_path=db_path)
        self.batch_repo = batch_repo or BatchRepository(db_path=db_path)

    def get_dashboard_summary(
        self,
        today: Optional[date] = None,
        expiring_soon_days: int = DEFAULT_EXPIRING_SOON_DAYS,
    ) -> DashboardSummary:
        """Calculate high-level dashboard metrics and retrieve urgent items."""
        rows = self.batch_repo.get_all_batches_with_medicine()

        total_active = 0
        valid_count = 0
        expiring_soon_count = 0
        expired_count = 0
        active_items: List[InventoryItem] = []

        for row in rows:
            batch_status = (row["status"] or "active").lower()
            if batch_status != "active":
                continue

            days = days_until_expiry(row["expiry_date"], today=today)
            exp_status = get_expiry_status(row["expiry_date"], today=today, expiring_soon_days=expiring_soon_days)
            label = format_expiry_human_label(days)

            total_active += 1
            if exp_status == STATUS_VALID:
                valid_count += 1
            elif exp_status == STATUS_EXPIRING_SOON:
                expiring_soon_count += 1
            elif exp_status == STATUS_EXPIRED:
                expired_count += 1

            item = InventoryItem(
                medicine_id=row["medicine_id"],
                medicine_name=row["medicine_name"],
                strength=row["strength"],
                medicine_type=row["medicine_type"],
                manufacturer=row["manufacturer"],
                barcode=row["barcode"],
                notes=row["notes"],
                batch_id=row["batch_id"],
                batch_number=row["batch_number"],
                expiry_date=row["expiry_date"],
                quantity=row["quantity"],
                storage_location=row["storage_location"],
                status=row["status"],
                days_until_expiry=days,
                expiry_status=exp_status,
                expiry_label=label,
            )
            active_items.append(item)

        # Urgent items are sorted by closest expiry date first (ascending days_until_expiry)
        active_items.sort(key=lambda x: x.days_until_expiry)

        return DashboardSummary(
            total_active_batches=total_active,
            valid_batches=valid_count,
            expiring_soon_batches=expiring_soon_count,
            expired_batches=expired_count,
            urgent_items=active_items,
        )

    def get_inventory(
        self,
        search_query: str = "",
        status_filter: str = "All",
        location_filter: str = "All",
        sort_by: str = "nearest_expiry",
        today: Optional[date] = None,
        expiring_soon_days: int = DEFAULT_EXPIRING_SOON_DAYS,
    ) -> List[InventoryItem]:
        """Retrieve, filter, and sort inventory items."""
        rows = self.batch_repo.get_all_batches_with_medicine()
        items: List[InventoryItem] = []

        for row in rows:
            days = days_until_expiry(row["expiry_date"], today=today)
            exp_status = get_expiry_status(row["expiry_date"], today=today, expiring_soon_days=expiring_soon_days)
            label = format_expiry_human_label(days)

            item = InventoryItem(
                medicine_id=row["medicine_id"],
                medicine_name=row["medicine_name"],
                strength=row["strength"],
                medicine_type=row["medicine_type"],
                manufacturer=row["manufacturer"],
                barcode=row["barcode"],
                notes=row["notes"],
                batch_id=row["batch_id"],
                batch_number=row["batch_number"],
                expiry_date=row["expiry_date"],
                quantity=row["quantity"],
                storage_location=row["storage_location"],
                status=row["status"] or "active",
                days_until_expiry=days,
                expiry_status=exp_status,
                expiry_label=label,
            )
            items.append(item)

        # 1. Search filter (case-insensitive medicine name)
        clean_search = search_query.strip().lower()
        if clean_search:
            items = [it for it in items if clean_search in it.medicine_name.lower()]

        # 2. Status filter
        clean_status = status_filter.strip().lower()
        if clean_status in ("valid", "status_valid"):
            items = [it for it in items if it.expiry_status == STATUS_VALID and it.status.lower() != "disposed"]
        elif clean_status in ("expiring soon", "expiring_soon"):
            items = [it for it in items if it.expiry_status == STATUS_EXPIRING_SOON and it.status.lower() != "disposed"]
        elif clean_status in ("expired", "status_expired"):
            items = [it for it in items if it.expiry_status == STATUS_EXPIRED and it.status.lower() != "disposed"]
        elif clean_status in ("disposed", "inactive"):
            items = [it for it in items if it.status.lower() in ("disposed", "inactive")]
        else:
            # Default "All": active records only
            items = [it for it in items if it.status.lower() != "disposed"]

        # 3. Location filter
        if location_filter not in ("All", "All Locations", ""):
            items = [it for it in items if (it.storage_location or "").strip() == location_filter.strip()]

        # 4. Sorting
        clean_sort = sort_by.strip().lower()
        if clean_sort in ("oldest_expiry", "furthest expiry", "farthest first"):
            items.sort(key=lambda x: x.days_until_expiry, reverse=True)
        elif clean_sort in ("name_asc", "medicine name a-z", "a-z", "name a-z"):
            items.sort(key=lambda x: (x.medicine_name.lower(), x.days_until_expiry))
        elif clean_sort in ("name_desc", "medicine name z-a", "z-a", "name z-a"):
            items.sort(key=lambda x: (x.medicine_name.lower()), reverse=True)
        else:
            # Default: Nearest expiry first
            items.sort(key=lambda x: x.days_until_expiry)

        return items

    def get_storage_locations(self) -> List[str]:
        """Fetch all unique storage locations currently in use."""
        return self.batch_repo.get_distinct_locations()

    def get_medicine_detail(self, medicine_id: int) -> Optional[MedicineDetail]:
        """Retrieve medicine profile and all of its associated batches."""
        medicine = self.medicine_repo.get_by_id(medicine_id)
        if medicine is None:
            return None

        batches = self.batch_repo.get_by_medicine_id(medicine_id)
        return MedicineDetail(medicine=medicine, batches=batches)

    def add_batch_to_medicine(
        self,
        medicine_id: int,
        expiry_date: str,
        quantity: Any = 0,
        batch_number: Optional[str] = None,
        storage_location: Optional[str] = None,
        status: str = "active",
    ) -> Batch:
        """Add an additional batch to an existing medicine."""
        medicine = self.medicine_repo.get_by_id(medicine_id)
        if medicine is None:
            raise ValueError(f"Medicine with ID {medicine_id} does not exist.")

        validated = validate_batch_input(
            expiry_date=expiry_date,
            quantity=quantity,
            batch_number=batch_number,
            storage_location=storage_location,
            status=status,
        )

        now_str = get_now_iso()
        batch = Batch(
            medicine_id=medicine_id,
            expiry_date=validated["expiry_date"],
            quantity=validated["quantity"],
            batch_number=validated["batch_number"],
            storage_location=validated["storage_location"],
            status=validated["status"],
            created_at=now_str,
            updated_at=now_str,
        )

        persisted_batch = self.batch_repo.create(batch)
        logger.info("Added batch ID %d to existing medicine ID %d.", persisted_batch.id, medicine_id)
        return persisted_batch

    def update_medicine(
        self,
        medicine_id: int,
        name: str,
        strength: Optional[str] = None,
        medicine_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        barcode: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Medicine:
        """Validate and update an existing medicine record."""
        existing = self.medicine_repo.get_by_id(medicine_id)
        if existing is None:
            raise ValueError(f"Medicine with ID {medicine_id} not found.")

        validated = validate_medicine_update(
            name=name,
            strength=strength,
            medicine_type=medicine_type,
            manufacturer=manufacturer,
            barcode=barcode,
            notes=notes,
        )

        existing.name = validated["name"]
        existing.strength = validated["strength"]
        existing.medicine_type = validated["medicine_type"]
        existing.manufacturer = validated["manufacturer"]
        existing.barcode = validated["barcode"]
        existing.notes = validated["notes"]
        existing.updated_at = get_now_iso()

        updated = self.medicine_repo.update(existing)
        if not updated:
            raise RuntimeError(f"Failed to update medicine ID {medicine_id}.")

        logger.info("Updated medicine ID %d.", medicine_id)
        return existing

    def update_batch(
        self,
        batch_id: int,
        expiry_date: str,
        quantity: Any = 0,
        batch_number: Optional[str] = None,
        storage_location: Optional[str] = None,
        status: str = "active",
    ) -> Batch:
        """Validate and update an existing batch record."""
        existing = self.batch_repo.get_by_id(batch_id)
        if existing is None:
            raise ValueError(f"Batch with ID {batch_id} not found.")

        validated = validate_batch_input(
            expiry_date=expiry_date,
            quantity=quantity,
            batch_number=batch_number,
            storage_location=storage_location,
            status=status,
        )

        existing.expiry_date = validated["expiry_date"]
        existing.quantity = validated["quantity"]
        existing.batch_number = validated["batch_number"]
        existing.storage_location = validated["storage_location"]
        existing.status = validated["status"]
        existing.updated_at = get_now_iso()

        updated = self.batch_repo.update(existing)
        if not updated:
            raise RuntimeError(f"Failed to update batch ID {batch_id}.")

        logger.info("Updated batch ID %d.", batch_id)
        return existing

    def delete_medicine(self, medicine_id: int) -> bool:
        """Permanently delete a medicine and its associated batches via SQLite cascade."""
        success = self.medicine_repo.delete(medicine_id)
        if success:
            logger.info("Permanently deleted medicine ID %d and cascaded batches.", medicine_id)
        return success

    def delete_batch(self, batch_id: int) -> bool:
        """Permanently delete an individual batch record."""
        success = self.batch_repo.delete(batch_id)
        if success:
            logger.info("Permanently deleted batch ID %d.", batch_id)
        return success

    def mark_batch_as_disposed(
        self,
        batch_id: int,
        disposed_date: Optional[str] = None,
    ) -> bool:
        """Mark an inventory batch as disposed without permanently deleting it.

        Preserves medicine, batch, and alert history records, but updates status
        to 'disposed' so it is excluded from active inventory and dashboard counts.
        """
        success = self.batch_repo.mark_disposed(batch_id=batch_id, disposed_date=disposed_date)
        if success:
            logger.info("Marked batch ID %d as disposed.", batch_id)
        return success

    def restore_batch_to_active(self, batch_id: int) -> bool:
        """Restore a disposed inventory batch back to active status."""
        success = self.batch_repo.restore_active(batch_id=batch_id)
        if success:
            logger.info("Restored batch ID %d to active.", batch_id)
        return success
