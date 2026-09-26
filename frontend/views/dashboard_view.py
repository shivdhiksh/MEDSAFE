"""Dashboard view for MEDSAFE.

Second Visual Upgrade: Premium Glassmorphism & Ambient Gradient Experience.
Displays ambient hero backdrop, 4 floating KPI cards with non-misleading wording,
glass distribution analytics panel, and urgent items sorted by nearest expiry date.
"""

import threading
from typing import Callable, Optional
import customtkinter as ctk

from backend.models import DashboardSummary, InventoryItem
from backend.services.inventory_service import InventoryService
from backend.services.notification_service import NotificationService
from frontend.components.ambient_background import AmbientHeroPanel, CapsuleCanvas
from frontend.components.glass_card import GlassCard, GlassCardHover, GlassKPI
from frontend.components.status_badge import StatusBadge
from frontend.config import (
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_CARD_ELEVATED,
    COLOR_CARD_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_SUBTLE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_HERO,
    FONT_SECTION,
    FONT_SUBTITLE,
    STATUS_EXPIRED,
    STATUS_EXPIRED_BG,
    STATUS_EXPIRED_TEXT,
    STATUS_EXPIRING,
    STATUS_EXPIRING_BG,
    STATUS_EXPIRING_TEXT,
    STATUS_VALID,
    STATUS_VALID_BG,
    STATUS_VALID_TEXT,
)


class DashboardView(ctk.CTkScrollableFrame):
    """Main dashboard view container featuring ambient gradient hero and glassmorphic cards."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        inventory_service: Optional[InventoryService] = None,
        notification_service: Optional[NotificationService] = None,
        on_add_medicine: Optional[Callable[[], None]] = None,
        on_view_medicine: Optional[Callable[[int], None]] = None,
        on_view_inventory: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.inventory_service = inventory_service or InventoryService()
        self.notification_service = notification_service or NotificationService()
        self.on_add_medicine_callback = on_add_medicine
        self.on_view_medicine_callback = on_view_medicine
        self.on_view_inventory_callback = on_view_inventory

        self.grid_columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self) -> None:
        """Fetch updated summary metrics and rebuild the dashboard widgets."""
        for child in self.winfo_children():
            child.destroy()

        summary: DashboardSummary = self.inventory_service.get_dashboard_summary()

        self._build_hero_panel()
        self._build_metric_cards(summary)
        self._build_distribution_section(summary)
        self._build_urgent_section(summary)

    def _build_hero_panel(self) -> None:
        """Construct the ambient gradient hero panel (NO duplicate Add Medicine button)."""
        self.hero_panel = AmbientHeroPanel(
            self,
            on_view_inventory=self.on_view_inventory_callback,
            on_test_notif=self._handle_test_notification,
        )
        self.hero_panel.grid(row=0, column=0, sticky="ew", pady=(0, 20))

    def _handle_test_notification(self) -> None:
        """Trigger local Windows test toast asynchronously with user feedback."""
        if hasattr(self.hero_panel, "test_notif_btn"):
            self.hero_panel.test_notif_btn.configure(text="Sending...", state="disabled")

        def worker() -> None:
            success, msg = self.notification_service.send_test_notification()
            self.after(0, lambda: self._on_test_notif_complete(success, msg))

        threading.Thread(target=worker, daemon=True, name="TestNotificationWorker").start()

    def _on_test_notif_complete(self, success: bool, message: str) -> None:
        """Update hero UI with test notification outcome."""
        try:
            if not self.winfo_exists() or not hasattr(self, "hero_panel"):
                return
            btn = getattr(self.hero_panel, "test_notif_btn", None)
            if not btn or not btn.winfo_exists():
                return

            if success:
                btn.configure(
                    text="✓ Sent!",
                    fg_color=STATUS_VALID_BG,
                    text_color=STATUS_VALID_TEXT,
                )
                self.after(2500, self._reset_test_notif_button)
            else:
                btn.configure(
                    text="⚠️ Delivery Failed",
                    state="normal",
                    fg_color=STATUS_EXPIRED_BG,
                    text_color=STATUS_EXPIRED_TEXT,
                )
                self.after(3500, self._reset_test_notif_button)
        except Exception:
            pass

    def _reset_test_notif_button(self) -> None:
        """Restore test notification button to default appearance."""
        try:
            if not self.winfo_exists() or not hasattr(self, "hero_panel"):
                return
            btn = getattr(self.hero_panel, "test_notif_btn", None)
            if btn and btn.winfo_exists():
                btn.configure(
                    text="🔔 Test Notification",
                    state="normal",
                    fg_color=COLOR_BTN_SECONDARY,
                    text_color=COLOR_BTN_SECONDARY_TEXT,
                )
        except Exception:
            pass

    def _build_metric_cards(self, summary: DashboardSummary) -> None:
        """Display the 4 summary KPI cards in a responsive grid.

        Safety Language Notice:
        Valid card supporting text strictly uses 'Expiry date not reached'
        rather than 'Within safe date range' to avoid implying medical safety.
        """
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        metrics = [
            ("Total Active", summary.total_active_batches, "📦", COLOR_PRIMARY, "Active in household",
             ("#FFFFFF", "#0A1428"), ("#BAE6FD", "#183658"), ("#E0F2FE", "#0C2548")),
            ("Valid", summary.valid_batches, "✓", STATUS_VALID, "Expiry date not reached",
             ("#FFFFFF", "#08171E"), ("#BBF7D0", "#124432"), ("#DCFCE7", "#0A2E23")),
            ("Expiring Soon", summary.expiring_soon_batches, "⏳", STATUS_EXPIRING, "Approaching expiry",
             ("#FFFFFF", "#17150F"), ("#FEF08A", "#48320B"), ("#FEF3C7", "#33250A")),
            ("Expired", summary.expired_batches, "⚠️", STATUS_EXPIRED, "Review for disposal",
             ("#FFFFFF", "#190F14"), ("#FECACA", "#4C141B"), ("#FEE2E2", "#381116")),
        ]

        self.kpi_cards = []
        for idx, (title, val, icon, accent, desc, c_bg, c_border, b_bg) in enumerate(metrics):
            card = GlassKPI(
                cards_frame,
                title=title,
                value=val,
                icon=icon,
                accent_color=accent,
                supporting_text=desc,
                card_bg=c_bg,
                card_border=c_border,
                badge_bg=b_bg,
            )
            padx_tuple = (0 if idx == 0 else 6, 0 if idx == 3 else 6)
            card.grid(row=0, column=idx, padx=padx_tuple, sticky="nsew")
            self.kpi_cards.append(card)

        if len(self.kpi_cards) == 4:
            self.card_total = self.kpi_cards[0]
            self.card_valid = self.kpi_cards[1]
            self.card_expiring = self.kpi_cards[2]
            self.card_expired = self.kpi_cards[3]

    def _build_distribution_section(self, summary: DashboardSummary) -> None:
        """Construct the visual expiry distribution bar and breakdown."""
        dist_card = GlassCard(self)
        dist_card.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        dist_card.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(dist_card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header_row,
            text="Inventory Expiry Distribution",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        total = summary.total_active_batches
        valid = summary.valid_batches
        expiring = summary.expiring_soon_batches
        expired = summary.expired_batches

        # Multi-segment progress bar container
        bar_container = ctk.CTkFrame(dist_card, height=12, corner_radius=6, fg_color=COLOR_CARD_ELEVATED)
        bar_container.pack(fill="x", padx=20, pady=(0, 12))

        if total > 0:
            bar_container.grid_columnconfigure(0, weight=max(1, valid))
            bar_container.grid_columnconfigure(1, weight=max(1, expiring))
            bar_container.grid_columnconfigure(2, weight=max(1, expired))

            if valid > 0:
                seg_valid = ctk.CTkFrame(bar_container, height=12, corner_radius=4, fg_color=STATUS_VALID)
                seg_valid.grid(row=0, column=0, sticky="nsew", padx=1)
            if expiring > 0:
                seg_exp = ctk.CTkFrame(bar_container, height=12, corner_radius=4, fg_color=STATUS_EXPIRING)
                seg_exp.grid(row=0, column=1, sticky="nsew", padx=1)
            if expired > 0:
                seg_dead = ctk.CTkFrame(bar_container, height=12, corner_radius=4, fg_color=STATUS_EXPIRED)
                seg_dead.grid(row=0, column=2, sticky="nsew", padx=1)
        else:
            empty_bar = ctk.CTkFrame(bar_container, height=12, corner_radius=6, fg_color=COLOR_CARD_ELEVATED)
            empty_bar.pack(fill="both", expand=True)

        # Bottom Breakdown Pills
        pills_row = ctk.CTkFrame(dist_card, fg_color="transparent")
        pills_row.pack(fill="x", padx=20, pady=(0, 16))

        valid_pct = round((valid / total * 100)) if total > 0 else 0
        expiring_pct = round((expiring / total * 100)) if total > 0 else 0
        expired_pct = round((expired / total * 100)) if total > 0 else 0

        pills = [
            (f"● Valid: {valid} ({valid_pct}%)", STATUS_VALID_TEXT, STATUS_VALID_BG),
            (f"● Expiring Soon: {expiring} ({expiring_pct}%)", STATUS_EXPIRING_TEXT, STATUS_EXPIRING_BG),
            (f"● Expired: {expired} ({expired_pct}%)", STATUS_EXPIRED_TEXT, STATUS_EXPIRED_BG),
        ]

        for text, txt_color, bg_color in pills:
            pill = ctk.CTkLabel(
                pills_row,
                text=text,
                font=FONT_CAPTION_BOLD,
                text_color=txt_color,
                fg_color=bg_color,
                corner_radius=8,
                padx=10,
                pady=4,
            )
            pill.pack(side="left", padx=(0, 10))

    def _build_urgent_section(self, summary: DashboardSummary) -> None:
        """Construct the prioritized urgent medicines list."""
        section_box = GlassCard(self)
        section_box.grid(row=3, column=0, sticky="nsew", pady=(0, 20))
        section_box.grid_columnconfigure(0, weight=1)

        # Section Header
        sec_header = ctk.CTkFrame(section_box, fg_color="transparent")
        sec_header.pack(fill="x", padx=20, pady=(18, 12))
        sec_header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(sec_header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        sec_title = ctk.CTkLabel(
            title_box,
            text="📅 Urgent & Upcoming Expiries",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        sec_title.pack(side="left")

        sec_desc = ctk.CTkLabel(
            title_box,
            text="(Sorted by closest expiry date)",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
        )
        sec_desc.pack(side="left", padx=(8, 0))

        if self.on_view_inventory_callback is not None:
            view_all_btn = ctk.CTkButton(
                sec_header,
                text="View All in Inventory →",
                font=FONT_CAPTION_BOLD,
                fg_color="transparent",
                hover_color=COLOR_CARD_ELEVATED,
                text_color=COLOR_PRIMARY,
                height=28,
                command=self.on_view_inventory_callback,
            )
            view_all_btn.grid(row=0, column=1, sticky="e")

        # Divider
        divider = ctk.CTkFrame(section_box, height=1, fg_color=COLOR_BORDER)
        divider.pack(fill="x", padx=16, pady=(0, 12))

        # Check for empty state: No active medicines
        if summary.total_active_batches == 0:
            empty_frame = ctk.CTkFrame(section_box, fg_color="transparent")
            empty_frame.pack(fill="x", padx=20, pady=36)

            ctk.CTkLabel(
                empty_frame,
                text="📦",
                font=(FONT_HERO[0], 36),
            ).pack(pady=(0, 8))

            empty_msg = ctk.CTkLabel(
                empty_frame,
                text="No active medicines recorded yet.",
                font=FONT_SUBTITLE,
                text_color=COLOR_TEXT_PRIMARY,
            )
            empty_msg.pack(pady=(0, 4))

            empty_sub = ctk.CTkLabel(
                empty_frame,
                text="Add your first medicine and batch to start tracking expiry dates locally.",
                font=FONT_CAPTION,
                text_color=COLOR_TEXT_MUTED,
            )
            empty_sub.pack(pady=(0, 16))

            if self.on_add_medicine_callback is not None:
                add_cta = ctk.CTkButton(
                    empty_frame,
                    text="➕ Add First Medicine",
                    font=FONT_BODY_BOLD,
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    text_color="white",
                    height=36,
                    corner_radius=8,
                    command=self.on_add_medicine_callback,
                )
                add_cta.pack()
            return

        # Check for empty state: No urgent items (all valid)
        if not summary.urgent_items:
            empty_frame = ctk.CTkFrame(section_box, fg_color="transparent")
            empty_frame.pack(fill="x", padx=20, pady=36)

            ctk.CTkLabel(
                empty_frame,
                text="✓",
                font=(FONT_HERO[0], 36),
                text_color=STATUS_VALID,
            ).pack(pady=(0, 8))

            empty_msg = ctk.CTkLabel(
                empty_frame,
                text="All medicines are currently within valid dates.",
                font=FONT_SUBTITLE,
                text_color=COLOR_TEXT_PRIMARY,
            )
            empty_msg.pack(pady=(0, 4))

            empty_sub = ctk.CTkLabel(
                empty_frame,
                text="There are no urgent or expiring batches requiring immediate attention.",
                font=FONT_CAPTION,
                text_color=COLOR_TEXT_MUTED,
            )
            empty_sub.pack()
            return

        # Render list of urgent items (top 10 closest expiries) using floating glass rows
        for item in summary.urgent_items[:10]:
            self._render_urgent_row(section_box, item)

    def _render_urgent_row(self, parent: ctk.CTkFrame, item: InventoryItem) -> None:
        """Render an individual row inside the urgent section using GlassCardHover."""
        row_frame = GlassCardHover(
            parent,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
            height=56,
        )
        row_frame.pack(fill="x", padx=16, pady=4)
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=1)

        # Left Column: Capsule Icon + Medicine Name, Strength, Batch & Location
        left_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        capsule = CapsuleCanvas(left_box, size=28)
        capsule.pack(side="left", padx=(0, 10))

        text_sub_box = ctk.CTkFrame(left_box, fg_color="transparent")
        text_sub_box.pack(side="left", fill="y", expand=True)

        med_title_str = f"{item.medicine_name}"
        if item.strength:
            med_title_str += f" ({item.strength})"
        if item.medicine_type:
            med_title_str += f" • {item.medicine_type}"

        name_label = ctk.CTkLabel(
            text_sub_box,
            text=med_title_str,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        name_label.pack(anchor="w")

        sub_details = []
        if item.batch_number:
            sub_details.append(f"Batch: {item.batch_number}")
        if item.storage_location:
            sub_details.append(f"📍 {item.storage_location}")
        sub_details.append(f"Qty: {item.quantity}")

        meta_label = ctk.CTkLabel(
            text_sub_box,
            text=" • ".join(sub_details),
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        meta_label.pack(anchor="w", pady=(2, 0))

        # Center Column: Expiry Date and Human-readable countdown
        center_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        center_box.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        expiry_date_label = ctk.CTkLabel(
            center_box,
            text=f"Expires: {item.expiry_date}",
            font=FONT_BODY,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        expiry_date_label.pack(anchor="w")

        remaining_label = ctk.CTkLabel(
            center_box,
            text=item.expiry_label,
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        remaining_label.pack(anchor="w", pady=(2, 0))

        # Right Column: Badge & View button
        right_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        right_box.grid(row=0, column=2, sticky="e", padx=14, pady=10)

        badge = StatusBadge(right_box, status=item.expiry_status)
        badge.pack(side="left", padx=(0, 10))

        if self.on_view_medicine_callback is not None:
            view_btn = ctk.CTkButton(
                right_box,
                text="View",
                font=FONT_BODY,
                width=64,
                height=30,
                corner_radius=8,
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_BTN_SECONDARY_HOVER,
                text_color=COLOR_BTN_SECONDARY_TEXT,
                command=lambda m_id=item.medicine_id: self.on_view_medicine_callback(m_id),
            )
            view_btn.pack(side="left")
