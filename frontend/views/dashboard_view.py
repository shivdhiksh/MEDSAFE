"""Dashboard view for MEDSAFE.

Displays key inventory metrics (total active, valid, expiring soon, expired)
and urgent items sorted by nearest expiry date.
"""

import threading
from typing import Callable, Optional
import customtkinter as ctk

from backend.models import DashboardSummary, InventoryItem
from backend.services.inventory_service import InventoryService
from backend.services.notification_service import NotificationService
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


class DashboardView(ctk.CTkScrollableFrame):
    """Main dashboard view container."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        inventory_service: Optional[InventoryService] = None,
        notification_service: Optional[NotificationService] = None,
        on_add_medicine: Optional[Callable[[], None]] = None,
        on_view_medicine: Optional[Callable[[int], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.inventory_service = inventory_service or InventoryService()
        self.notification_service = notification_service or NotificationService()
        self.on_add_medicine_callback = on_add_medicine
        self.on_view_medicine_callback = on_view_medicine

        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self) -> None:
        """Fetch updated summary metrics and rebuild the dashboard widgets."""
        for child in self.winfo_children():
            child.destroy()

        summary: DashboardSummary = self.inventory_service.get_dashboard_summary()

        self._build_header()
        self._build_metric_cards(summary)
        self._build_urgent_section(summary)

    def _build_header(self) -> None:
        """Construct top title and action buttons (Test Notification, Add Medicine)."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(title_box, text="Dashboard", font=FONT_TITLE, anchor="w")
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Real-time status of your household medicine stock and expiry dates.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.grid(row=0, column=1, sticky="e")

        self.test_notif_btn = ctk.CTkButton(
            actions_box,
            text="🔔 Test Notification",
            font=FONT_BODY,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            text_color=("black", "white"),
            height=38,
            command=self._handle_test_notification,
        )
        self.test_notif_btn.pack(side="left", padx=(0, 10))

        if self.on_add_medicine_callback is not None:
            add_btn = ctk.CTkButton(
                actions_box,
                text="+ Add Medicine",
                font=FONT_BODY_BOLD,
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                height=38,
                command=self.on_add_medicine_callback,
            )
            add_btn.pack(side="left")

    def _handle_test_notification(self) -> None:
        """Trigger local Windows test toast asynchronously with user feedback."""
        self.test_notif_btn.configure(text="Sending...", state="disabled")

        def worker() -> None:
            success, msg = self.notification_service.send_test_notification()
            self.after(0, lambda: self._on_test_notif_complete(success, msg))

        threading.Thread(target=worker, daemon=True, name="TestNotificationWorker").start()

    def _on_test_notif_complete(self, success: bool, message: str) -> None:
        """Update UI with test notification outcome."""
        try:
            if not self.winfo_exists():
                return
            if success:
                self.test_notif_btn.configure(
                    text="✓ Sent!",
                    fg_color=("#DCFCE7", "#14532D"),
                    text_color=("#15803D", "#86EFAC"),
                )
                self.after(2500, self._reset_test_notif_button)
            else:
                self.test_notif_btn.configure(
                    text="⚠️ Delivery Failed",
                    state="normal",
                    fg_color=("#FEE2E2", "#7F1D1D"),
                    text_color=("#B91C1C", "#FCA5A5"),
                )
                self.after(3500, self._reset_test_notif_button)
        except Exception:
            pass

    def _reset_test_notif_button(self) -> None:
        """Restore test notification button to default appearance."""
        try:
            if self.winfo_exists() and hasattr(self, "test_notif_btn") and self.test_notif_btn.winfo_exists():
                self.test_notif_btn.configure(
                    text="🔔 Test Notification",
                    state="normal",
                    fg_color=("gray85", "gray25"),
                    text_color=("black", "white"),
                )
        except Exception:
            pass

    def _build_metric_cards(self, summary: DashboardSummary) -> None:
        """Display the 4 summary KPI cards in a 4-column layout."""
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 24))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        metrics = [
            ("Total Active", summary.total_active_batches, ("#F1F5F9", "#1E293B"), ("#0F172A", "#F8FAFC")),
            ("Valid", summary.valid_batches, ("#DCFCE7", "#14532D"), ("#15803D", "#86EFAC")),
            ("Expiring Soon", summary.expiring_soon_batches, ("#FEF3C7", "#78350F"), ("#B45309", "#FCD34D")),
            ("Expired", summary.expired_batches, ("#FEE2E2", "#7F1D1D"), ("#B91C1C", "#FCA5A5")),
        ]

        for idx, (label, count, bg_color, text_color) in enumerate(metrics):
            card = ctk.CTkFrame(
                cards_frame,
                fg_color=COLOR_CARD,
                corner_radius=10,
                border_width=1,
                border_color=("gray85", "gray30"),
            )
            card.grid(row=0, column=idx, padx=6 if 0 < idx < 3 else (0 if idx == 0 else 6), sticky="nsew")

            count_label = ctk.CTkLabel(
                card,
                text=str(count),
                font=(FONT_TITLE[0], 28, "bold"),
                text_color=text_color,
            )
            count_label.pack(pady=(16, 2))

            title_label = ctk.CTkLabel(
                card,
                text=label,
                font=FONT_BODY,
                text_color=("gray30", "gray70"),
            )
            title_label.pack(pady=(0, 16))

    def _build_urgent_section(self, summary: DashboardSummary) -> None:
        """Construct the prioritized urgent medicines list."""
        section_box = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        section_box.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        section_box.grid_columnconfigure(0, weight=1)

        # Section Header
        sec_header = ctk.CTkFrame(section_box, fg_color="transparent")
        sec_header.pack(fill="x", padx=20, pady=(18, 12))

        sec_title = ctk.CTkLabel(
            sec_header,
            text="Urgent & Upcoming Expiries",
            font=FONT_SECTION,
            anchor="w",
        )
        sec_title.pack(side="left")

        sec_desc = ctk.CTkLabel(
            sec_header,
            text="(Sorted by closest expiry date)",
            font=FONT_CAPTION,
            text_color="gray",
        )
        sec_desc.pack(side="left", padx=(8, 0))

        # Divider
        divider = ctk.CTkFrame(section_box, height=1, fg_color=("gray90", "gray25"))
        divider.pack(fill="x", padx=16, pady=(0, 12))

        # Check for empty state
        if summary.total_active_batches == 0:
            empty_frame = ctk.CTkFrame(section_box, fg_color="transparent")
            empty_frame.pack(fill="x", padx=20, pady=36)

            empty_msg = ctk.CTkLabel(
                empty_frame,
                text="No active medicines yet.",
                font=FONT_SUBTITLE,
                text_color=("gray40", "gray70"),
            )
            empty_msg.pack(pady=(0, 8))

            if self.on_add_medicine_callback is not None:
                add_cta = ctk.CTkButton(
                    empty_frame,
                    text="+ Add Medicine",
                    font=FONT_BODY_BOLD,
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    height=36,
                    command=self.on_add_medicine_callback,
                )
                add_cta.pack()
            return

        if not summary.urgent_items:
            empty_frame = ctk.CTkFrame(section_box, fg_color="transparent")
            empty_frame.pack(fill="x", padx=20, pady=36)

            empty_msg = ctk.CTkLabel(
                empty_frame,
                text="✓ All medicines are currently within valid dates.",
                font=FONT_SUBTITLE,
                text_color=("gray40", "gray70"),
            )
            empty_msg.pack()
            return

        # Render list of urgent items
        for item in summary.urgent_items[:10]:  # Highlight top 10 urgent items
            self._render_urgent_row(section_box, item)

    def _render_urgent_row(self, parent: ctk.CTkFrame, item: InventoryItem) -> None:
        """Render an individual row inside the urgent section."""
        row_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray95", "#18202F"),
            corner_radius=8,
            height=54,
        )
        row_frame.pack(fill="x", padx=16, pady=4)
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=1)

        # Left Column: Medicine Name, Strength, Batch & Location
        left_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="w", padx=14, pady=8)

        med_title_str = f"{item.medicine_name}"
        if item.strength:
            med_title_str += f" ({item.strength})"

        name_label = ctk.CTkLabel(left_box, text=med_title_str, font=FONT_BODY_BOLD, anchor="w")
        name_label.pack(anchor="w")

        sub_details = []
        if item.batch_number:
            sub_details.append(f"Batch: {item.batch_number}")
        if item.storage_location:
            sub_details.append(f"Location: {item.storage_location}")
        sub_details.append(f"Qty: {item.quantity}")

        meta_label = ctk.CTkLabel(
            left_box,
            text=" • ".join(sub_details),
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        meta_label.pack(anchor="w")

        # Center Column: Expiry Date and Human-readable label
        center_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        center_box.grid(row=0, column=1, sticky="w", padx=10, pady=8)

        expiry_date_label = ctk.CTkLabel(center_box, text=f"Expires: {item.expiry_date}", font=FONT_BODY, anchor="w")
        expiry_date_label.pack(anchor="w")

        remaining_label = ctk.CTkLabel(
            center_box,
            text=item.expiry_label,
            font=FONT_CAPTION,
            text_color=("gray30", "gray75"),
            anchor="w",
        )
        remaining_label.pack(anchor="w")

        # Right Column: Badge & View button
        right_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        right_box.grid(row=0, column=2, sticky="e", padx=14, pady=8)

        badge = StatusBadge(right_box, status=item.expiry_status)
        badge.pack(side="left", padx=(0, 12))

        if self.on_view_medicine_callback is not None:
            view_btn = ctk.CTkButton(
                right_box,
                text="View",
                font=FONT_BODY,
                width=64,
                height=30,
                fg_color=("gray85", "gray30"),
                hover_color=("gray75", "gray40"),
                text_color=("black", "white"),
                command=lambda m_id=item.medicine_id: self.on_view_medicine_callback(m_id),
            )
            view_btn.pack(side="left")
