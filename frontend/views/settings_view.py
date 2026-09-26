"""Settings view for MEDSAFE.

Organized settings center featuring:
- Section 1: Notifications (Enable toggle, thresholds, test notification)
- Section 2: Appearance (System, Light, Dark mode selection)
- Section 3: Data Management (Storage path, open folders, CSV & JSON exports)
- Section 4: About & Version (App information and offline privacy notice)
- Section 5: Safety & Medical Notice (Mandatory safety disclaimer)
"""

import threading
from typing import Callable, Optional
import customtkinter as ctk

from backend.config import APP_DISCLAIMER, APP_FULL_TITLE, APP_VERSION
from backend.models import Settings
from backend.services.backup_service import BackupService
from backend.services.notification_service import NotificationService
from backend.services.settings_service import SettingsService
from frontend.components.glass_card import GlassCard
from frontend.config import (
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_CARD_ELEVATED,
    COLOR_CARD_HOVER,
    COLOR_DIVIDER,
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
    FONT_CAPTION_BOLD,
    FONT_DISCLAIMER,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
    STATUS_EXPIRED_BG,
    STATUS_EXPIRED_TEXT,
    STATUS_VALID_BG,
    STATUS_VALID_TEXT,
)


class SettingsView(ctk.CTkScrollableFrame):
    """Organized settings center for user preferences, alerts, data exports, and safety."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings_service: Optional[SettingsService] = None,
        backup_service: Optional[BackupService] = None,
        notification_service: Optional[NotificationService] = None,
        on_theme_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.settings_service = settings_service or SettingsService()
        self.backup_service = backup_service or BackupService()
        self.notification_service = notification_service or NotificationService()
        self.on_theme_change_callback = on_theme_change

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct all settings sections in logical visual hierarchy (title in global header)."""
        settings: Settings = self.settings_service.get_settings()

        self._build_notifications_card(settings)
        self._build_appearance_card(settings)
        self._build_save_bar()
        self._build_data_management_card()
        self._build_about_card()
        self._build_safety_card()

    # =========================================================================
    # SECTION 1: NOTIFICATIONS
    # =========================================================================
    def _build_notifications_card(self, settings: Settings) -> None:
        """Section 1: Notification enable toggle, alert thresholds, and test button."""
        card = GlassCard(self)
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(
            card,
            text="1. Expiry Notifications",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            card,
            text="Control whether and when local Windows toast alerts are sent for expiring batches.",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

        # Toggle Switch
        self.notif_var = ctk.BooleanVar(value=bool(settings.notifications_enabled))
        self.notif_switch = ctk.CTkSwitch(
            card,
            text="Enable local Windows expiry notifications",
            variable=self.notif_var,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            progress_color=COLOR_PRIMARY,
        )
        self.notif_switch.pack(anchor="w", padx=20, pady=(0, 14))

        divider = ctk.CTkFrame(card, height=1, fg_color=COLOR_DIVIDER)
        divider.pack(fill="x", padx=20, pady=(0, 14))

        # Thresholds input & Explanation
        thresh_box = ctk.CTkFrame(card, fg_color="transparent")
        thresh_box.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            thresh_box,
            text="Alert Warning Thresholds (days before expiry)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            thresh_box,
            text=(
                "Specify comma-separated day intervals when notifications should fire.\n"
                "Standard default is 30, 7, 1 (alerts at 30 days, 7 days, and 1 day remaining, plus upon expiry)."
            ),
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        row_input = ctk.CTkFrame(thresh_box, fg_color="transparent")
        row_input.pack(fill="x")

        self.thresholds_entry = ctk.CTkEntry(
            row_input,
            placeholder_text="e.g. 30,7,1",
            font=FONT_BODY,
            width=220,
            height=36,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            corner_radius=8,
        )
        self.thresholds_entry.insert(0, settings.alert_days)
        self.thresholds_entry.pack(side="left", padx=(0, 10))

        reset_btn = ctk.CTkButton(
            row_input,
            text="Reset to Default (30, 7, 1)",
            font=FONT_BODY,
            height=36,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=self._reset_thresholds,
        )
        reset_btn.pack(side="left", padx=(0, 10))

        # Section 1 Test Notification Button
        self.test_notif_btn = ctk.CTkButton(
            row_input,
            text="🔔 Test Notification",
            font=FONT_BODY,
            height=36,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=self._handle_test_notification,
        )
        self.test_notif_btn.pack(side="left")

        # Test Notification Feedback Label
        self.test_status_lbl = ctk.CTkLabel(
            card,
            text="",
            font=FONT_CAPTION_BOLD,
            anchor="w",
        )
        self.test_status_lbl.pack(fill="x", padx=20, pady=(0, 14))

    def _reset_thresholds(self) -> None:
        """Reset threshold input back to standard default values."""
        self.thresholds_entry.delete(0, "end")
        self.thresholds_entry.insert(0, "30,7,1")

    def _handle_test_notification(self) -> None:
        """Trigger local Windows test toast asynchronously with user feedback."""
        self.test_notif_btn.configure(text="Sending...", state="disabled")
        self.test_status_lbl.configure(text="")

        def worker() -> None:
            success, msg = self.notification_service.send_test_notification()
            self.after(0, lambda: self._on_test_notif_complete(success, msg))

        threading.Thread(target=worker, daemon=True, name="SettingsTestNotifWorker").start()

    def _on_test_notif_complete(self, success: bool, message: str) -> None:
        """Update Section 1 UI with test notification outcome."""
        try:
            if not self.winfo_exists():
                return
            if success:
                self.test_notif_btn.configure(
                    text="✓ Sent!",
                    fg_color=STATUS_VALID_BG,
                    text_color=STATUS_VALID_TEXT,
                )
                self.test_status_lbl.configure(
                    text="✓ Windows notification delivered successfully.",
                    text_color=STATUS_VALID_TEXT,
                )
                self.after(3000, self._reset_test_notif_button)
            else:
                self.test_notif_btn.configure(
                    text="⚠️ Failed",
                    state="normal",
                    fg_color=STATUS_EXPIRED_BG,
                    text_color=STATUS_EXPIRED_TEXT,
                )
                self.test_status_lbl.configure(
                    text=f"⚠️ {message}",
                    text_color=STATUS_EXPIRED_TEXT,
                )
                self.after(4000, self._reset_test_notif_button)
        except Exception:
            pass

    def _reset_test_notif_button(self) -> None:
        """Restore test notification button to default appearance."""
        try:
            if self.winfo_exists() and hasattr(self, "test_notif_btn") and self.test_notif_btn.winfo_exists():
                self.test_notif_btn.configure(
                    text="🔔 Test Notification",
                    state="normal",
                    fg_color=COLOR_BTN_SECONDARY,
                    text_color=COLOR_BTN_SECONDARY_TEXT,
                )
                self.test_status_lbl.configure(text="")
        except Exception:
            pass

    # =========================================================================
    # SECTION 2: APPEARANCE
    # =========================================================================
    def _build_appearance_card(self, settings: Settings) -> None:
        """Section 2: Polished appearance mode selector."""
        card = GlassCard(self)
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(
            card,
            text="2. Appearance Theme",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            card,
            text="Choose between System, Light, or Dark interface appearance. Theme changes persist automatically.",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

        theme_box = ctk.CTkFrame(card, fg_color="transparent")
        theme_box.pack(fill="x", padx=20, pady=(0, 18))

        current_theme = (settings.theme or "system").capitalize()
        self.theme_menu = ctk.CTkSegmentedButton(
            theme_box,
            values=["System", "Light", "Dark"],
            font=FONT_BODY_BOLD,
            width=320,
            height=38,
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
            unselected_color=COLOR_CARD_ELEVATED,
            unselected_hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10,
            command=self._on_theme_select,
        )
        self.theme_menu.set(current_theme)
        self.theme_menu.pack(side="left")

    def _on_theme_select(self, theme_val: str) -> None:
        """Apply theme preview immediately if callback is available."""
        if self.on_theme_change_callback is not None:
            self.on_theme_change_callback(theme_val.lower())

    # =========================================================================
    # SAVE SETTINGS ACTION BAR
    # =========================================================================
    def _build_save_bar(self) -> None:
        """Construct Save Changes action bar with inline status feedback."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 20), padx=4)

        self.save_btn = ctk.CTkButton(
            bar,
            text="✓ Save Settings",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            height=38,
            width=160,
            corner_radius=8,
            command=self._handle_save_settings,
        )
        self.save_btn.pack(side="left")

        self.save_status_lbl = ctk.CTkLabel(
            bar,
            text="",
            font=FONT_BODY_BOLD,
            anchor="w",
        )
        self.save_status_lbl.pack(side="left", padx=16)

    def _handle_save_settings(self) -> None:
        """Validate and persist all configured settings."""
        self.save_status_lbl.configure(text="")
        enabled = self.notif_var.get()
        thresholds_str = self.thresholds_entry.get()
        theme_str = self.theme_menu.get().lower()

        success, msg = self.settings_service.save_settings(
            notifications_enabled=enabled,
            thresholds_str=thresholds_str,
            theme=theme_str,
        )

        if success:
            self.save_status_lbl.configure(
                text="✓ " + msg,
                text_color=STATUS_VALID_TEXT,
            )
            # Re-normalize entry display
            _, normalized, _ = self.settings_service.validate_and_normalize_thresholds(thresholds_str)
            self.thresholds_entry.delete(0, "end")
            self.thresholds_entry.insert(0, normalized)
        else:
            self.save_status_lbl.configure(
                text="⚠️ " + msg,
                text_color=STATUS_EXPIRED_TEXT,
            )

    # =========================================================================
    # SECTION 3: DATA MANAGEMENT
    # =========================================================================
    def _build_data_management_card(self) -> None:
        """Section 3: Database location, folder shortcuts, and offline data exports."""
        card = GlassCard(self)
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(
            card,
            text="3. Data Management & Storage",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 4))

        data_info = self.settings_service.get_data_info()
        rel_path = data_info["relative_db_path"]

        ctk.CTkLabel(
            card,
            text=f"Database file: {rel_path}",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 2))

        ctk.CTkLabel(
            card,
            text=(
                "All medicine records are stored strictly in a local SQLite file in your user workspace.\n"
                "You can export your complete inventory to offline CSV or JSON anytime."
            ),
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=20, pady=(0, 14))

        # Folder and Export Buttons
        btn_grid = ctk.CTkFrame(card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=20, pady=(0, 10))

        open_data_btn = ctk.CTkButton(
            btn_grid,
            text="📂 Open Data Folder",
            font=FONT_BODY,
            height=36,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=self.settings_service.open_data_folder,
        )
        open_data_btn.pack(side="left", padx=(0, 10))

        open_backups_btn = ctk.CTkButton(
            btn_grid,
            text="📂 Open Backups Folder",
            font=FONT_BODY,
            height=36,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=self.settings_service.open_backups_folder,
        )
        open_backups_btn.pack(side="left", padx=(0, 10))

        csv_btn = ctk.CTkButton(
            btn_grid,
            text="📥 Export CSV",
            font=FONT_BODY_BOLD,
            height=36,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=self._handle_export_csv,
        )
        csv_btn.pack(side="left", padx=(0, 10))

        json_btn = ctk.CTkButton(
            btn_grid,
            text="📥 Export JSON",
            font=FONT_BODY_BOLD,
            height=36,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=self._handle_export_json,
        )
        json_btn.pack(side="left")

        self.export_status_lbl = ctk.CTkLabel(
            card,
            text="",
            font=FONT_CAPTION_BOLD,
            anchor="w",
        )
        self.export_status_lbl.pack(fill="x", padx=20, pady=(0, 16))

    def _handle_export_csv(self) -> None:
        """Trigger CSV export and display result."""
        success, msg, path = self.backup_service.export_csv()
        if success and path is not None:
            self.export_status_lbl.configure(
                text=f"✓ CSV export completed successfully: {path.name}",
                text_color=STATUS_VALID_TEXT,
            )
        else:
            self.export_status_lbl.configure(
                text=f"⚠️ {msg}",
                text_color=STATUS_EXPIRED_TEXT,
            )

    def _handle_export_json(self) -> None:
        """Trigger JSON export and display result."""
        success, msg, path = self.backup_service.export_json()
        if success and path is not None:
            self.export_status_lbl.configure(
                text=f"✓ JSON export completed successfully: {path.name}",
                text_color=STATUS_VALID_TEXT,
            )
        else:
            self.export_status_lbl.configure(
                text=f"⚠️ {msg}",
                text_color=STATUS_EXPIRED_TEXT,
            )

    # =========================================================================
    # SECTION 4: ABOUT / VERSION
    # =========================================================================
    def _build_about_card(self) -> None:
        """Section 4: Application details, version, and privacy commitments."""
        card = GlassCard(self)
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(
            card,
            text="4. About & Version",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            card,
            text=f"{APP_FULL_TITLE} • Version {APP_VERSION}",
            font=FONT_BODY_BOLD,
            text_color=COLOR_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 4))

        desc_text = (
            "MEDSAFE is a completely offline-first, private medicine inventory and expiry tracker.\n"
            "• All records and expiry calculations are processed strictly on your computer.\n"
            "• No cloud synchronization, external tracking, or network connections are ever used."
        )
        ctk.CTkLabel(
            card,
            text=desc_text,
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 18))

    # =========================================================================
    # SECTION 5: SAFETY
    # =========================================================================
    def _build_safety_card(self) -> None:
        """Section 5: Mandatory safety disclaimer retained exactly."""
        card = GlassCard(self)
        card.pack(fill="x", pady=(0, 24), padx=4)

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(18, 6))

        ctk.CTkLabel(
            header_row,
            text="5. Important Safety & Medical Notice",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        # Disclaimer Box
        disc_box = ctk.CTkFrame(
            card,
            fg_color=COLOR_CARD_ELEVATED,
            corner_radius=8,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        disc_box.pack(fill="x", padx=20, pady=(0, 18))

        ctk.CTkLabel(
            disc_box,
            text=APP_DISCLAIMER,
            font=FONT_DISCLAIMER,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            wraplength=640,
        ).pack(fill="x", padx=16, pady=14)
