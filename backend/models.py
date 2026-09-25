"""Data models for MEDSAFE.

Defines lightweight dataclass entities representing medicines, batches,
alert history, and system settings.
"""

from dataclasses import dataclass
import sqlite3
from typing import Any, Dict, Optional


@dataclass
class Medicine:
    """Represents a medicine or drug profile."""

    id: Optional[int] = None
    name: str = ""
    strength: Optional[str] = None
    medicine_type: Optional[str] = None
    manufacturer: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Medicine":
        """Instantiate a Medicine object from a database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            strength=row["strength"],
            medicine_type=row["medicine_type"],
            manufacturer=row["manufacturer"],
            barcode=row["barcode"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class Batch:
    """Represents a physical batch/package of a medicine with its specific expiry date."""

    id: Optional[int] = None
    medicine_id: int = 0
    batch_number: Optional[str] = None
    expiry_date: str = ""
    quantity: int = 0
    storage_location: Optional[str] = None
    status: str = "active"
    opened_date: Optional[str] = None
    disposed_date: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Batch":
        """Instantiate a Batch object from a database row."""
        return cls(
            id=row["id"],
            medicine_id=row["medicine_id"],
            batch_number=row["batch_number"],
            expiry_date=row["expiry_date"],
            quantity=row["quantity"],
            storage_location=row["storage_location"],
            status=row["status"],
            opened_date=row["opened_date"],
            disposed_date=row["disposed_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class AlertHistory:
    """Tracks local notifications sent for a batch to prevent duplicate alerts."""

    id: Optional[int] = None
    batch_id: int = 0
    alert_type: str = ""
    sent_at: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AlertHistory":
        """Instantiate an AlertHistory object from a database row."""
        return cls(
            id=row["id"],
            batch_id=row["batch_id"],
            alert_type=row["alert_type"],
            sent_at=row["sent_at"],
        )


@dataclass
class Settings:
    """User preferences, notification controls, and UI theme options."""

    id: Optional[int] = None
    notifications_enabled: int = 1
    alert_days: str = "30,7,1"
    theme: str = "system"
    created_at: str = ""
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Settings":
        """Instantiate a Settings object from a database row."""
        return cls(
            id=row["id"],
            notifications_enabled=row["notifications_enabled"],
            alert_days=row["alert_days"],
            theme=row["theme"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class InventoryItem:
    """View model representing a batch combined with parent drug details for display."""

    medicine_id: int
    medicine_name: str
    strength: Optional[str]
    medicine_type: Optional[str]
    manufacturer: Optional[str]
    barcode: Optional[str]
    notes: Optional[str]
    batch_id: int
    batch_number: Optional[str]
    expiry_date: str
    quantity: int
    storage_location: Optional[str]
    status: str
    days_until_expiry: int
    expiry_status: str  # 'valid', 'expiring_soon', 'expired'
    expiry_label: str   # Plain English label, e.g. 'Expires in 7 days'


@dataclass
class DashboardSummary:
    """Aggregated metrics and prioritized items for the dashboard."""

    total_active_batches: int
    valid_batches: int
    expiring_soon_batches: int
    expired_batches: int
    urgent_items: list[InventoryItem]


@dataclass
class MedicineDetail:
    """Container for a medicine and all of its associated batches."""

    medicine: Medicine
    batches: list[Batch]
