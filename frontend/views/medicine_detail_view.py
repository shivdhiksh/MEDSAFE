"""Medicine and batches detail view for MEDSAFE.

Allows viewing and editing drug profiles, managing multiple batches,
adding new batches to an existing medicine, and safe permanent deletion.
"""

from typing import Callable, Optional
import customtkinter as ctk

from backend.models import Batch, MedicineDetail
from backend.services.expiry_service import (
    days_until_expiry,
    format_expiry_human_label,
    get_expiry_status,
)
from backend.services.inventory_service import InventoryService
from frontend.components.confirmation_dialog import ConfirmationDialog
from frontend.components.medicine_form import MEDICINE_TYPES
from frontend.components.status_badge import StatusBadge
from frontend.config import (
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
)


class MedicineDetailView(ctk.CTkScrollableFrame):
    """View container for inspecting, editing, and managing batches for a medicine."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        medicine_id: int,
        inventory_service: Optional[InventoryService] = None,
        on_back: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.medicine_id = medicine_id
        self.inventory_service = inventory_service or InventoryService()
        self.on_back_callback = on_back

        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self) -> None:
        """Reload medicine detail and re-render."""
        for child in self.winfo_children():
            child.destroy()

        detail: Optional[MedicineDetail] = self.inventory_service.get_medicine_detail(self.medicine_id)
        if detail is None:
            self._render_not_found()
            return

        self._build_header(detail)
        self._build_medicine_card(detail)
        self._build_batches_section(detail)

    def _render_not_found(self) -> None:
        """Display not found notice if record was removed."""
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10)
        card.pack(fill="x", padx=16, pady=32)

        ctk.CTkLabel(card, text="Medicine not found.", font=FONT_SECTION).pack(pady=(24, 8))
        if self.on_back_callback is not None:
            ctk.CTkButton(
                card,
                text="← Back to Inventory",
                font=FONT_BODY,
                command=self.on_back_callback,
            ).pack(pady=(0, 24))

    def _build_header(self, detail: MedicineDetail) -> None:
        """Construct top action header."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(1, weight=1)

        if self.on_back_callback is not None:
            back_btn = ctk.CTkButton(
                header,
                text="← Back to Inventory",
                font=FONT_BODY,
                width=140,
                height=34,
                fg_color=("gray85", "gray30"),
                hover_color=("gray75", "gray40"),
                text_color=("black", "white"),
                command=self.on_back_callback,
            )
            back_btn.grid(row=0, column=0, padx=(0, 16), sticky="w")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w")

        title = ctk.CTkLabel(
            title_box,
            text=detail.medicine.name,
            font=FONT_TITLE,
            anchor="w",
        )
        title.pack(anchor="w")

        delete_btn = ctk.CTkButton(
            header,
            text="Delete Medicine",
            font=FONT_BODY_BOLD,
            fg_color=("#FEE2E2", "#7F1D1D"),
            hover_color=("#EF4444", "#991B1B"),
            text_color=("#991B1B", "#FEE2E2"),
            height=34,
            command=lambda: self._prompt_delete_medicine(detail.medicine.name),
        )
        delete_btn.grid(row=0, column=2, sticky="e")

    def _prompt_delete_medicine(self, med_name: str) -> None:
        """Show confirmation dialog before permanently deleting the medicine."""
        ConfirmationDialog(
            self,
            title="Delete Medicine Permanently?",
            message=(
                f"Are you sure you want to permanently delete '{med_name}'?\n\n"
                "This action cannot be undone. All associated batches and history "
                "will also be permanently deleted."
            ),
            confirm_text="Delete Permanently",
            is_destructive=True,
            on_confirm=self._delete_medicine,
        )

    def _delete_medicine(self) -> None:
        """Execute permanent deletion and navigate back."""
        self.inventory_service.delete_medicine(self.medicine_id)
        if self.on_back_callback is not None:
            self.on_back_callback()

    def _build_medicine_card(self, detail: MedicineDetail) -> None:
        """Card for displaying and editing medicine details."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        card.grid_columnconfigure((0, 1), weight=1)

        # Header with Save Changes action
        sec_header = ctk.CTkFrame(card, fg_color="transparent")
        sec_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))
        sec_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sec_header, text="Medicine Profile", font=FONT_SECTION, anchor="w").grid(
            row=0, column=0, sticky="w"
        )

        self.med_feedback = ctk.CTkLabel(
            sec_header,
            text="",
            font=FONT_BODY_BOLD,
            corner_radius=6,
            height=28,
        )

        # Fields Grid
        # 1. Medicine Name
        name_box = ctk.CTkFrame(card, fg_color="transparent")
        name_box.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(name_box, text="Medicine Name *", font=FONT_BODY_BOLD, anchor="w").pack(fill="x")
        self.name_entry = ctk.CTkEntry(name_box, font=FONT_BODY, height=34)
        self.name_entry.insert(0, detail.medicine.name)
        self.name_entry.pack(fill="x", pady=(2, 0))

        # 2. Strength
        strength_box = ctk.CTkFrame(card, fg_color="transparent")
        strength_box.grid(row=1, column=1, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(strength_box, text="Strength", font=FONT_BODY, anchor="w").pack(fill="x")
        self.strength_entry = ctk.CTkEntry(strength_box, font=FONT_BODY, height=34)
        if detail.medicine.strength:
            self.strength_entry.insert(0, detail.medicine.strength)
        self.strength_entry.pack(fill="x", pady=(2, 0))

        # 3. Manufacturer
        mfr_box = ctk.CTkFrame(card, fg_color="transparent")
        mfr_box.grid(row=2, column=0, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(mfr_box, text="Manufacturer", font=FONT_BODY, anchor="w").pack(fill="x")
        self.mfr_entry = ctk.CTkEntry(mfr_box, font=FONT_BODY, height=34)
        if detail.medicine.manufacturer:
            self.mfr_entry.insert(0, detail.medicine.manufacturer)
        self.mfr_entry.pack(fill="x", pady=(2, 0))

        # 4. Medicine Type
        type_box = ctk.CTkFrame(card, fg_color="transparent")
        type_box.grid(row=2, column=1, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(type_box, text="Medicine Form / Type", font=FONT_BODY, anchor="w").pack(fill="x")
        self.type_menu = ctk.CTkOptionMenu(type_box, values=MEDICINE_TYPES, font=FONT_BODY, height=34)
        curr_type = detail.medicine.medicine_type or MEDICINE_TYPES[0]
        self.type_menu.set(curr_type if curr_type in MEDICINE_TYPES else MEDICINE_TYPES[0])
        self.type_menu.pack(fill="x", pady=(2, 0))

        # 5. Barcode
        barcode_box = ctk.CTkFrame(card, fg_color="transparent")
        barcode_box.grid(row=3, column=0, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(barcode_box, text="Barcode", font=FONT_BODY, anchor="w").pack(fill="x")
        self.barcode_entry = ctk.CTkEntry(barcode_box, font=FONT_BODY, height=34)
        if detail.medicine.barcode:
            self.barcode_entry.insert(0, detail.medicine.barcode)
        self.barcode_entry.pack(fill="x", pady=(2, 0))

        # 6. Notes
        notes_box = ctk.CTkFrame(card, fg_color="transparent")
        notes_box.grid(row=3, column=1, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(notes_box, text="Notes", font=FONT_BODY, anchor="w").pack(fill="x")
        self.notes_entry = ctk.CTkEntry(notes_box, font=FONT_BODY, height=34)
        if detail.medicine.notes:
            self.notes_entry.insert(0, detail.medicine.notes)
        self.notes_entry.pack(fill="x", pady=(2, 0))

        # Save Button
        save_btn = ctk.CTkButton(
            card,
            text="Save Profile Changes",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=36,
            command=self._save_medicine_changes,
        )
        save_btn.grid(row=4, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="e")

    def _save_medicine_changes(self) -> None:
        """Submit medicine profile changes to service."""
        try:
            sel_type = self.type_menu.get()
            m_type = sel_type if sel_type != MEDICINE_TYPES[0] else ""

            self.inventory_service.update_medicine(
                medicine_id=self.medicine_id,
                name=self.name_entry.get(),
                strength=self.strength_entry.get(),
                medicine_type=m_type,
                manufacturer=self.mfr_entry.get(),
                barcode=self.barcode_entry.get(),
                notes=self.notes_entry.get(),
            )
            self._show_feedback("Medicine profile updated successfully.", is_error=False)
        except ValueError as exc:
            self._show_feedback(str(exc), is_error=True)
        except Exception:
            self._show_feedback("Failed to update medicine.", is_error=True)

    def _show_feedback(self, msg: str, is_error: bool) -> None:
        """Show inline status message for medicine profile edits."""
        if is_error:
            self.med_feedback.configure(
                text=msg,
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#991B1B", "#FCA5A5"),
            )
        else:
            self.med_feedback.configure(
                text=msg,
                fg_color=("#DCFCE7", "#14532D"),
                text_color=("#166534", "#86EFAC"),
            )
        self.med_feedback.grid(row=0, column=1, sticky="e", padx=(8, 0))

    def _build_batches_section(self, detail: MedicineDetail) -> None:
        """Section listing all batches for this medicine with Add Batch form."""
        batches_box = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        batches_box.grid(row=2, column=0, sticky="ew", pady=(0, 24))
        batches_box.grid_columnconfigure(0, weight=1)

        # Header row
        sec_header = ctk.CTkFrame(batches_box, fg_color="transparent")
        sec_header.pack(fill="x", padx=16, pady=(16, 12))
        sec_header.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            sec_header,
            text=f"Associated Batches ({len(detail.batches)})",
            font=FONT_SECTION,
            anchor="w",
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        # Toggleable Add Batch panel
        self.add_batch_frame = ctk.CTkFrame(
            batches_box,
            fg_color=("gray95", "#18202F"),
            corner_radius=8,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        # Built once, packed when "+ Add New Batch" is toggled
        self._build_add_batch_panel()

        add_batch_btn = ctk.CTkButton(
            sec_header,
            text="+ Add New Batch",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=32,
            command=self._toggle_add_batch_panel,
        )
        add_batch_btn.grid(row=0, column=1, sticky="e")

        # Divider
        self.batch_divider = ctk.CTkFrame(batches_box, height=1, fg_color=("gray90", "gray25"))
        self.batch_divider.pack(fill="x", padx=16, pady=(0, 12))

        # Render list of batches
        for batch in detail.batches:
            self._render_batch_row(batches_box, batch)

    def _build_add_batch_panel(self) -> None:
        """Construct the collapsible inline form to add another batch."""
        self.add_batch_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            self.add_batch_frame,
            text="Add Another Batch for this Medicine",
            font=FONT_BODY_BOLD,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, padx=14, pady=(12, 6), sticky="w")

        # Expiry date *
        ctk.CTkLabel(self.add_batch_frame, text="Expiry Date * (YYYY-MM-DD)", font=FONT_CAPTION, anchor="w").grid(
            row=1, column=0, padx=14, pady=(2, 0), sticky="w"
        )
        self.new_exp_entry = ctk.CTkEntry(self.add_batch_frame, placeholder_text="e.g. 2028-05-15", height=32)
        self.new_exp_entry.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="ew")

        # Quantity
        ctk.CTkLabel(self.add_batch_frame, text="Quantity", font=FONT_CAPTION, anchor="w").grid(
            row=1, column=1, padx=14, pady=(2, 0), sticky="w"
        )
        self.new_qty_entry = ctk.CTkEntry(self.add_batch_frame, placeholder_text="e.g. 10", height=32)
        self.new_qty_entry.grid(row=2, column=1, padx=14, pady=(0, 10), sticky="ew")

        # Batch Number
        ctk.CTkLabel(self.add_batch_frame, text="Batch Number", font=FONT_CAPTION, anchor="w").grid(
            row=1, column=2, padx=14, pady=(2, 0), sticky="w"
        )
        self.new_lot_entry = ctk.CTkEntry(self.add_batch_frame, placeholder_text="e.g. B-002", height=32)
        self.new_lot_entry.grid(row=2, column=2, padx=14, pady=(0, 10), sticky="ew")

        # Location
        ctk.CTkLabel(self.add_batch_frame, text="Storage Location", font=FONT_CAPTION, anchor="w").grid(
            row=1, column=3, padx=14, pady=(2, 0), sticky="w"
        )
        self.new_loc_entry = ctk.CTkEntry(self.add_batch_frame, placeholder_text="e.g. Home Cabinet", height=32)
        self.new_loc_entry.grid(row=2, column=3, padx=14, pady=(0, 10), sticky="ew")

        # Buttons
        btn_box = ctk.CTkFrame(self.add_batch_frame, fg_color="transparent")
        btn_box.grid(row=3, column=0, columnspan=4, padx=14, pady=(0, 12), sticky="e")

        save_batch_btn = ctk.CTkButton(
            btn_box,
            text="Save Batch",
            font=FONT_BODY_BOLD,
            height=30,
            command=self._submit_new_batch,
        )
        save_batch_btn.pack(side="right", padx=(8, 0))

        cancel_batch_btn = ctk.CTkButton(
            btn_box,
            text="Cancel",
            font=FONT_BODY,
            height=30,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=self._toggle_add_batch_panel,
        )
        cancel_batch_btn.pack(side="right")

        self.batch_err_lbl = ctk.CTkLabel(
            btn_box,
            text="",
            font=FONT_CAPTION,
            text_color=("red", "#FCA5A5"),
        )
        self.batch_err_lbl.pack(side="right", padx=(0, 12))

    def _toggle_add_batch_panel(self) -> None:
        """Toggle display of the inline Add Batch panel."""
        if self.add_batch_frame.winfo_ismapped():
            self.add_batch_frame.pack_forget()
        else:
            self.add_batch_frame.pack(fill="x", padx=16, pady=(0, 14), before=self.batch_divider)

    def _submit_new_batch(self) -> None:
        """Save a new batch for this medicine."""
        try:
            self.batch_err_lbl.configure(text="")
            self.inventory_service.add_batch_to_medicine(
                medicine_id=self.medicine_id,
                expiry_date=self.new_exp_entry.get(),
                quantity=self.new_qty_entry.get(),
                batch_number=self.new_lot_entry.get(),
                storage_location=self.new_loc_entry.get(),
            )
            self.refresh()
        except ValueError as exc:
            self.batch_err_lbl.configure(text=str(exc))
        except Exception:
            self.batch_err_lbl.configure(text="Failed to save batch.")

    def _render_batch_row(self, parent: ctk.CTkFrame, batch: Batch) -> None:
        """Render a single batch row with edit/delete actions."""
        days = days_until_expiry(batch.expiry_date)
        status_val = get_expiry_status(batch.expiry_date)
        human_label = format_expiry_human_label(days)

        row = ctk.CTkFrame(
            parent,
            fg_color=("gray95", "#18202F"),
            corner_radius=8,
        )
        row.pack(fill="x", padx=16, pady=4)
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)

        # Left Info
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=14, pady=8)

        lot_str = f"Batch: {batch.batch_number or 'Standard'}"
        ctk.CTkLabel(left, text=lot_str, font=FONT_BODY_BOLD, anchor="w").pack(anchor="w")

        info_parts = [f"Qty: {batch.quantity}"]
        if batch.storage_location:
            info_parts.append(f"Location: {batch.storage_location}")
        info_parts.append(f"Status: {batch.status.title()}")
        if batch.disposed_date:
            info_parts.append(f"Disposed: {batch.disposed_date[:10]}")

        ctk.CTkLabel(left, text=" • ".join(info_parts), font=FONT_CAPTION, text_color="gray", anchor="w").pack(
            anchor="w"
        )

        # Center Expiry Info
        center = ctk.CTkFrame(row, fg_color="transparent")
        center.grid(row=0, column=1, sticky="w", padx=10, pady=8)

        ctk.CTkLabel(center, text=f"Expires: {batch.expiry_date}", font=FONT_BODY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(center, text=human_label, font=FONT_CAPTION, text_color=("gray30", "gray75"), anchor="w").pack(
            anchor="w"
        )

        # Right Controls: Badge, Dispose/Restore, Edit, Delete
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=14, pady=8)

        badge = StatusBadge(right, status=status_val if batch.status == "active" else batch.status)
        badge.pack(side="left", padx=(0, 8))

        if batch.status == "active":
            dispose_btn = ctk.CTkButton(
                right,
                text="Dispose",
                font=FONT_BODY,
                width=64,
                height=28,
                fg_color=("gray85", "gray30"),
                hover_color=("gray75", "gray40"),
                text_color=("black", "white"),
                command=lambda b_id=batch.id: self._prompt_dispose_batch(b_id),
            )
            dispose_btn.pack(side="left", padx=(0, 6))
        else:
            restore_btn = ctk.CTkButton(
                right,
                text="Restore",
                font=FONT_BODY,
                width=64,
                height=28,
                fg_color=("#DCFCE7", "#14532D"),
                hover_color=("#BBF7D0", "#166534"),
                text_color=("#15803D", "#86EFAC"),
                command=lambda b_id=batch.id: self._restore_batch(b_id),
            )
            restore_btn.pack(side="left", padx=(0, 6))

        edit_btn = ctk.CTkButton(
            right,
            text="Edit",
            font=FONT_BODY,
            width=50,
            height=28,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=lambda b=batch: self._open_edit_batch_dialog(b),
        )
        edit_btn.pack(side="left", padx=(0, 6))

        del_btn = ctk.CTkButton(
            right,
            text="Delete",
            font=FONT_BODY,
            width=54,
            height=28,
            fg_color=("#FEE2E2", "#7F1D1D"),
            hover_color=("#EF4444", "#991B1B"),
            text_color=("#991B1B", "#FEE2E2"),
            command=lambda b_id=batch.id: self._prompt_delete_batch(b_id),
        )
        del_btn.pack(side="left")

    def _prompt_dispose_batch(self, batch_id: int) -> None:
        """Confirm before marking an individual batch as disposed."""
        ConfirmationDialog(
            self,
            title="Mark this batch as disposed?",
            message=(
                "Disposed batches remain in your records but are excluded "
                "from active inventory and expiry reminders."
            ),
            confirm_text="Mark as Disposed",
            is_destructive=False,
            on_confirm=lambda: self._dispose_batch(batch_id),
        )

    def _dispose_batch(self, batch_id: int) -> None:
        """Mark batch as disposed and refresh view."""
        self.inventory_service.mark_batch_as_disposed(batch_id)
        self.refresh()

    def _restore_batch(self, batch_id: int) -> None:
        """Restore disposed batch back to active status and refresh view."""
        self.inventory_service.restore_batch_to_active(batch_id)
        self.refresh()

    def _prompt_delete_batch(self, batch_id: int) -> None:
        """Confirm before deleting an individual batch."""
        ConfirmationDialog(
            self,
            title="Delete Batch Permanently?",
            message="Are you sure you want to permanently delete this batch record?",
            confirm_text="Delete Batch",
            is_destructive=True,
            on_confirm=lambda: self._delete_batch(batch_id),
        )

    def _delete_batch(self, batch_id: int) -> None:
        """Delete single batch and refresh view."""
        self.inventory_service.delete_batch(batch_id)
        self.refresh()

    def _open_edit_batch_dialog(self, batch: Batch) -> None:
        """Open a simple modal dialog to edit batch fields."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Batch")
        dlg.geometry("420x360")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        card = ctk.CTkFrame(dlg, fg_color=COLOR_CARD, corner_radius=10)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(card, text="Edit Batch Details", font=FONT_SECTION).pack(anchor="w", padx=16, pady=(14, 10))

        # Expiry
        ctk.CTkLabel(card, text="Expiry Date * (YYYY-MM-DD)", font=FONT_CAPTION).pack(anchor="w", padx=16)
        exp_entry = ctk.CTkEntry(card, font=FONT_BODY, height=32)
        exp_entry.insert(0, batch.expiry_date)
        exp_entry.pack(fill="x", padx=16, pady=(2, 8))

        # Quantity
        ctk.CTkLabel(card, text="Quantity", font=FONT_CAPTION).pack(anchor="w", padx=16)
        qty_entry = ctk.CTkEntry(card, font=FONT_BODY, height=32)
        qty_entry.insert(0, str(batch.quantity))
        qty_entry.pack(fill="x", padx=16, pady=(2, 8))

        # Batch Number
        ctk.CTkLabel(card, text="Batch / Lot Number", font=FONT_CAPTION).pack(anchor="w", padx=16)
        lot_entry = ctk.CTkEntry(card, font=FONT_BODY, height=32)
        if batch.batch_number:
            lot_entry.insert(0, batch.batch_number)
        lot_entry.pack(fill="x", padx=16, pady=(2, 8))

        # Location
        ctk.CTkLabel(card, text="Storage Location", font=FONT_CAPTION).pack(anchor="w", padx=16)
        loc_entry = ctk.CTkEntry(card, font=FONT_BODY, height=32)
        if batch.storage_location:
            loc_entry.insert(0, batch.storage_location)
        loc_entry.pack(fill="x", padx=16, pady=(2, 14))

        err_lbl = ctk.CTkLabel(card, text="", font=FONT_CAPTION, text_color=("red", "#FCA5A5"))
        err_lbl.pack(fill="x", padx=16, pady=(0, 6))

        # Actions
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=FONT_BODY,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=dlg.destroy,
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        def save_changes():
            try:
                self.inventory_service.update_batch(
                    batch_id=batch.id,
                    expiry_date=exp_entry.get(),
                    quantity=qty_entry.get(),
                    batch_number=lot_entry.get(),
                    storage_location=loc_entry.get(),
                )
                dlg.destroy()
                self.refresh()
            except ValueError as err:
                err_lbl.configure(text=str(err))
            except Exception:
                err_lbl.configure(text="Failed to update batch.")

        save_btn = ctk.CTkButton(
            btn_row,
            text="Save Batch",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=save_changes,
        )
        save_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")
