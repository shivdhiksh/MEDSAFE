"""Reusable medicine and initial batch input form component for MEDSAFE.

Follows strict frontend/backend separation:
- Gathers user input from UI widgets.
- Forwards payload directly to MedicineService.
- Never performs SQL queries or direct database access.
"""

from typing import Callable, Optional
import customtkinter as ctk

from backend.services.medicine_service import MedicineCreationResult, MedicineService
from frontend.components.glass_card import GlassCard
from frontend.config import (
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_DANGER_BG,
    COLOR_DANGER_TEXT,
    COLOR_INPUT_BG,
    COLOR_INPUT_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_SECTION,
    STATUS_EXPIRED_BG,
    STATUS_EXPIRED_TEXT,
    STATUS_VALID_BG,
    STATUS_VALID_TEXT,
)

MEDICINE_TYPES = [
    "-- Select Type (Optional) --",
    "Tablet",
    "Capsule",
    "Syrup",
    "Ointment",
    "Drops",
    "Injection",
    "Inhaler",
    "Powder",
    "Other",
]


class MedicineForm(ctk.CTkFrame):
    """Component managing input fields and validation feedback for adding a medicine and batch."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        medicine_service: Optional[MedicineService] = None,
        on_success: Optional[Callable[[MedicineCreationResult], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.medicine_service = medicine_service or MedicineService()
        self.on_success_callback = on_success

        self.grid_columnconfigure(0, weight=1)
        self._build_form()

    def _build_form(self) -> None:
        """Construct the form UI layout with modern glassmorphism cards."""
        # Top Feedback Banner (dynamically mapped on save/validation error)
        self.feedback_banner = ctk.CTkLabel(
            self,
            text="",
            font=FONT_BODY_BOLD,
            corner_radius=8,
            height=38,
        )

        # Two-column container
        sections_frame = ctk.CTkFrame(self, fg_color="transparent")
        sections_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 16))
        sections_frame.grid_columnconfigure((0, 1), weight=1)

        # ----------------------------------------------------
        # Section 1: Medicine Information Card
        # ----------------------------------------------------
        med_card = GlassCard(sections_frame, corner_radius=12)
        med_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        med_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            med_card,
            text="1. Medicine Details",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 4))

        ctk.CTkLabel(
            med_card,
            text="General identification of the medication",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 14))

        # Medicine Name (Required)
        name_lbl_row = ctk.CTkFrame(med_card, fg_color="transparent")
        name_lbl_row.pack(fill="x", padx=18, pady=(4, 2))
        ctk.CTkLabel(name_lbl_row, text="Medicine Name", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(name_lbl_row, text=" *", font=FONT_BODY_BOLD, text_color=STATUS_EXPIRED_TEXT).pack(side="left")

        self.name_entry = ctk.CTkEntry(
            med_card,
            placeholder_text="e.g. Paracetamol, Amoxicillin",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.name_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Strength (Optional)
        ctk.CTkLabel(med_card, text="Strength (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.strength_entry = ctk.CTkEntry(
            med_card,
            placeholder_text="e.g. 500 mg, 10 ml, 2%",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.strength_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Manufacturer (Optional)
        ctk.CTkLabel(med_card, text="Manufacturer (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.manufacturer_entry = ctk.CTkEntry(
            med_card,
            placeholder_text="e.g. Pfizer, GSK, Cipla",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.manufacturer_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Medicine Type (Optional)
        ctk.CTkLabel(med_card, text="Form / Type (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.type_menu = ctk.CTkOptionMenu(
            med_card,
            values=MEDICINE_TYPES,
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_INPUT_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
        )
        self.type_menu.set(MEDICINE_TYPES[0])
        self.type_menu.pack(fill="x", padx=18, pady=(0, 12))

        # Barcode (Optional)
        ctk.CTkLabel(med_card, text="Barcode (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.barcode_entry = ctk.CTkEntry(
            med_card,
            placeholder_text="e.g. 8901234567890",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.barcode_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Notes (Optional)
        ctk.CTkLabel(med_card, text="Notes (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.notes_entry = ctk.CTkEntry(
            med_card,
            placeholder_text="e.g. Take after food, prescription only",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.notes_entry.pack(fill="x", padx=18, pady=(0, 20))

        # ----------------------------------------------------
        # Section 2: Batch Information Card
        # ----------------------------------------------------
        batch_card = GlassCard(sections_frame, corner_radius=12)
        batch_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        batch_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            batch_card,
            text="2. Batch & Expiry Details",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 4))

        ctk.CTkLabel(
            batch_card,
            text="Specific pack details and expiry date",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 14))

        # Expiry Date (Required)
        exp_lbl_row = ctk.CTkFrame(batch_card, fg_color="transparent")
        exp_lbl_row.pack(fill="x", padx=18, pady=(4, 2))
        ctk.CTkLabel(exp_lbl_row, text="Expiry Date (YYYY-MM-DD)", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(exp_lbl_row, text=" *", font=FONT_BODY_BOLD, text_color=STATUS_EXPIRED_TEXT).pack(side="left")

        self.expiry_entry = ctk.CTkEntry(
            batch_card,
            placeholder_text="e.g. 2027-12-31",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.expiry_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Batch Number (Optional)
        ctk.CTkLabel(batch_card, text="Batch / Lot Number (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.batch_entry = ctk.CTkEntry(
            batch_card,
            placeholder_text="e.g. B-90214",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.batch_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Quantity (Optional)
        ctk.CTkLabel(batch_card, text="Quantity / Count (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.quantity_entry = ctk.CTkEntry(
            batch_card,
            placeholder_text="e.g. 20 (defaults to 0)",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.quantity_entry.pack(fill="x", padx=18, pady=(0, 12))

        # Storage Location (Optional)
        ctk.CTkLabel(batch_card, text="Storage Location (Optional)", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            fill="x", padx=18, pady=(4, 2)
        )
        self.location_entry = ctk.CTkEntry(
            batch_card,
            placeholder_text="e.g. Home Cabinet, Refrigerator, Travel Kit",
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.location_entry.pack(fill="x", padx=18, pady=(0, 20))

        # ----------------------------------------------------
        # Form Action Buttons
        # ----------------------------------------------------
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self.save_btn = ctk.CTkButton(
            buttons_frame,
            text="✓ Save Medicine",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            height=42,
            corner_radius=8,
            command=self._handle_save,
        )
        self.save_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Clear Form",
            font=FONT_BODY,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            height=42,
            corner_radius=8,
            command=self.clear_form,
        )
        self.clear_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _show_feedback(self, message: str, is_error: bool = False) -> None:
        """Display an inline user feedback banner."""
        if is_error:
            self.feedback_banner.configure(
                text="⚠️ " + message,
                fg_color=STATUS_EXPIRED_BG,
                text_color=STATUS_EXPIRED_TEXT,
            )
        else:
            self.feedback_banner.configure(
                text="✓ " + message,
                fg_color=STATUS_VALID_BG,
                text_color=STATUS_VALID_TEXT,
            )
        self.feedback_banner.grid(row=0, column=0, sticky="ew", pady=(0, 14))

    def _hide_feedback(self) -> None:
        """Remove the feedback banner from view."""
        self.feedback_banner.grid_forget()

    def _handle_save(self) -> None:
        """Collect form values, submit to service, and render feedback."""
        self._hide_feedback()

        name = self.name_entry.get()
        strength = self.strength_entry.get()
        manufacturer = self.manufacturer_entry.get()
        selected_type = self.type_menu.get()
        medicine_type = selected_type if selected_type != MEDICINE_TYPES[0] else ""
        barcode = self.barcode_entry.get()
        notes = self.notes_entry.get()

        expiry_date = self.expiry_entry.get()
        batch_number = self.batch_entry.get()
        quantity = self.quantity_entry.get()
        storage_location = self.location_entry.get()

        try:
            result = self.medicine_service.add_medicine_with_initial_batch(
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

            # Display clear success message
            self._show_feedback(
                f"'{result.medicine.name}' (Batch: {result.batch.batch_number or 'Standard'}) saved successfully.",
                is_error=False,
            )
            self.clear_form(preserve_feedback=True)

            if self.on_success_callback is not None:
                self.on_success_callback(result)

        except ValueError as val_err:
            # User-friendly validation error
            self._show_feedback(str(val_err), is_error=True)
        except Exception:
            # Unexpected technical error
            self._show_feedback(
                "An unexpected database error occurred. Please check your inputs and try again.",
                is_error=True,
            )

    def clear_form(self, preserve_feedback: bool = False) -> None:
        """Reset all form entry fields to empty defaults."""
        if not preserve_feedback:
            self._hide_feedback()

        self.name_entry.delete(0, "end")
        self.strength_entry.delete(0, "end")
        self.manufacturer_entry.delete(0, "end")
        self.type_menu.set(MEDICINE_TYPES[0])
        self.barcode_entry.delete(0, "end")
        self.notes_entry.delete(0, "end")

        self.expiry_entry.delete(0, "end")
        self.batch_entry.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self.location_entry.delete(0, "end")
