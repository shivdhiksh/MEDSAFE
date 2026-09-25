"""Validation utilities for MEDSAFE.

Provides pure business-rule validators for user inputs:
- Required medicine name validation
- Strict ISO expiry date validation
- Integer quantity validation (defaults to 0 if blank, rejects negatives and decimals)
- Optional string trimming and sanitization
"""

from typing import Any, Dict, Optional
from backend.utils.date_utils import format_iso_date, parse_iso_date


def clean_optional_string(val: Optional[Any]) -> Optional[str]:
    """Trim surrounding whitespace from a string, returning None if empty or blank."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def validate_medicine_name(name: Optional[str]) -> str:
    """Validate that the medicine name is non-empty after trimming.

    Raises:
        ValueError: If name is missing or consists solely of whitespace.
    """
    if name is None or not str(name).strip():
        raise ValueError("Medicine name is required.")
    return str(name).strip()


def validate_expiry_date(expiry_date_str: Optional[str]) -> str:
    """Validate that the expiry date is provided and strictly conforms to YYYY-MM-DD.

    Reuses backend.utils.date_utils.parse_iso_date.

    Raises:
        ValueError: If expiry date is missing, malformed, or an invalid calendar date.
    """
    if expiry_date_str is None or not str(expiry_date_str).strip():
        raise ValueError("Expiry date is required. Expected format: YYYY-MM-DD.")

    cleaned_str = str(expiry_date_str).strip()
    try:
        parsed = parse_iso_date(cleaned_str)
        return format_iso_date(parsed)
    except ValueError as exc:
        raise ValueError(
            "Please enter the expiry date in YYYY-MM-DD format (e.g., 2027-12-31)."
        ) from exc


def validate_quantity(qty_val: Any) -> int:
    """Validate quantity input.

    Rules:
    - If empty, None, or blank string: defaults to 0.
    - Must be a non-negative integer (>= 0).
    - Rejects negative numbers, decimal values, and non-numeric strings.

    Raises:
        ValueError: If input is negative, decimal, or non-numeric.
    """
    if qty_val is None:
        return 0

    if isinstance(qty_val, bool):
        raise ValueError("Quantity must be a non-negative whole number.")

    if isinstance(qty_val, int):
        if qty_val < 0:
            raise ValueError("Quantity must be a non-negative whole number.")
        return qty_val

    if isinstance(qty_val, float):
        raise ValueError("Quantity must be a non-negative whole number.")

    str_val = str(qty_val).strip()
    if not str_val:
        return 0

    if not str_val.isdigit():
        raise ValueError("Quantity must be a non-negative whole number.")

    parsed_int = int(str_val)
    if parsed_int < 0:
        raise ValueError("Quantity must be a non-negative whole number.")

    return parsed_int


def validate_medicine_and_batch_input(
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
) -> Dict[str, Any]:
    """Validate and clean all inputs required to create a medicine and its initial batch.

    Returns:
        Dictionary containing cleaned, validated fields separated into 'medicine' and 'batch'.
    """
    cleaned_name = validate_medicine_name(name)
    cleaned_expiry = validate_expiry_date(expiry_date)
    cleaned_qty = validate_quantity(quantity)

    return {
        "medicine": {
            "name": cleaned_name,
            "strength": clean_optional_string(strength),
            "medicine_type": clean_optional_string(medicine_type),
            "manufacturer": clean_optional_string(manufacturer),
            "barcode": clean_optional_string(barcode),
            "notes": clean_optional_string(notes),
        },
        "batch": {
            "expiry_date": cleaned_expiry,
            "quantity": cleaned_qty,
            "batch_number": clean_optional_string(batch_number),
            "storage_location": clean_optional_string(storage_location),
            "status": "active",
        },
    }


def validate_medicine_update(
    name: Optional[str],
    strength: Optional[str] = None,
    medicine_type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    barcode: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and sanitize fields for updating an existing medicine."""
    cleaned_name = validate_medicine_name(name)
    return {
        "name": cleaned_name,
        "strength": clean_optional_string(strength),
        "medicine_type": clean_optional_string(medicine_type),
        "manufacturer": clean_optional_string(manufacturer),
        "barcode": clean_optional_string(barcode),
        "notes": clean_optional_string(notes),
    }


def validate_batch_input(
    expiry_date: Optional[str],
    quantity: Any = 0,
    batch_number: Optional[str] = None,
    storage_location: Optional[str] = None,
    status: str = "active",
) -> Dict[str, Any]:
    """Validate and sanitize fields for creating or updating a batch."""
    cleaned_expiry = validate_expiry_date(expiry_date)
    cleaned_qty = validate_quantity(quantity)
    cleaned_status = str(status).strip().lower() if status else "active"

    return {
        "expiry_date": cleaned_expiry,
        "quantity": cleaned_qty,
        "batch_number": clean_optional_string(batch_number),
        "storage_location": clean_optional_string(storage_location),
        "status": cleaned_status,
    }
