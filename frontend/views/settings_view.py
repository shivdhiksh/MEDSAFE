"""Settings view for MEDSAFE.

Provides user interface controls for:
- Toggling local Windows notifications on/off
- Configuring custom expiry alert thresholds
- Selecting application appearance theme (System, Light, Dark)
- Exporting complete inventory data to offline CSV and JSON files
- Inspecting local SQLite database storage and opening data/backup folders
"""

from typing import Callable, Optional
import customtkinter as ctk

from backend.models import Settings
from backend.services.backup_service import BackupService
from backend.services.settings_service import SettingsService
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


class SettingsView(ctk.CTkScrollableFrame):
    """Complete Settings view container for user preferences, alerts, and data exports."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings_service: Optional[SettingsService] = None,
        backup_service: Optional[BackupService] = None,
        on_theme_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.settings_service = settings_service or SettingsService()
        self.backup_service = backup_service or BackupService()
        self.on_theme_change_callback = on_theme_change

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct all settings sections."""
        settings: Settings = self.settings_service.get_settings()

        self._build_header()
        self._build_notifications_card(settings)
        self._build_appearance_card(settings)
        self._build_save_bar()
        self._build_export_card()
        self._build_storage_card()

    def _build_header(self) -> None:
        """Construct top title and description."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20), padx=4)

        title = ctk.CTkLabel(header, text="Settings", font=FONT_TITLE, anchor="w")
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Configure notifications, appearance themes, data backups, and storage.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

    def _build_notifications_card(self, settings: Settings) -> None:
        """Notification enable toggle and threshold configuration."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(card, text="Expiry Notifications", font=FONT_SECTION, anchor="w").pack(
            fill="x", padx=20, pady=(16, 4)
        )
        ctk.CTkLabel(
            card,
            text="Control whether and when local Windows toast alerts are sent for expiring batches.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

        # Toggle Switch
        self.notif_var = ctk.BooleanVar(value=bool(settings.notifications_enabled))
        self.notif_switch = ctk.CTkSwitch(
            card,
            text="Enable local Windows expiry notifications",
            variable=self.notif_var,
            font=FONT_BODY_BOLD,
            progress_color=COLOR_PRIMARY,
        )
        self.notif_switch.pack(anchor="w", padx=20, pady=(0, 14))

        divider = ctk.CTkFrame(card, height=1, fg_color=("gray90", "gray25"))
        divider.pack(fill="x", padx=20, pady=(0, 14))

        # Thresholds input
        thresh_box = ctk.CTkFrame(card, fg_color="transparent")
        thresh_box.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(thresh_box, text="Alert Warning Thresholds (days remaining)", font=FONT_BODY_BOLD, anchor="w").pack(
            anchor="w", pady=(0, 2)
        )
        ctk.CTkLabel(
            thresh_box,
            text="These thresholds control when MEDSAFE sends expiry reminders (e.g. at 30, 7, and 1 days before expiry).",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        row_input = ctk.CTkFrame(thresh_box, fg_color="transparent")
        row_input.pack(fill="x")

        self.thresholds_entry = ctk.CTkEntry(
            row_input,
            placeholder_text="e.g. 30,7,1",
            font=FONT_BODY,
            width=240,
            height=36,
        )
        self.thresholds_entry.insert(0, settings.alert_days)
        self.thresholds_entry.pack(side="left", padx=(0, 12))

        reset_btn = ctk.CTkButton(
            row_input,
            text="Reset to Default (30, 7, 1)",
            font=FONT_BODY,
            height=36,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=self._reset_thresholds,
        )
        reset_btn.pack(side="left")

    def _reset_thresholds(self) -> None:
        """Reset threshold input back to standard default values."""
        self.thresholds_entry.delete(0, "end")
        self.thresholds_entry.insert(0, "30,7,1")

    def _build_appearance_card(self, settings: Settings) -> None:
        """Theme selection card."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(card, text="Appearance Theme", font=FONT_SECTION, anchor="w").pack(
            fill="x", padx=20, pady=(16, 4)
        )
        ctk.CTkLabel(
            card,
            text="Choose between System, Light, or Dark interface appearance.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

        theme_box = ctk.CTkFrame(card, fg_color="transparent")
        theme_box.pack(fill="x", padx=20, pady=(0, 16))

        current_theme = (settings.theme or "system").capitalize()
        self.theme_menu = ctk.CTkOptionMenu(
            theme_box,
            values=["System", "Light", "Dark"],
            font=FONT_BODY,
            width=180,
            height=36,
            command=self._on_theme_select,
        )
        self.theme_menu.set(current_theme)
        self.theme_menu.pack(side="left")

    def _on_theme_select(self, theme_val: str) -> None:
        """Apply theme preview immediately if callback is available."""
        if self.on_theme_change_callback is not None:
            self.on_theme_change_callback(theme_val.lower())

    def _build_save_bar(self) -> None:
        """Construct Save Changes action bar with inline status feedback."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 24), padx=4)

        self.save_btn = ctk.CTkButton(
            bar,
            text="Save Settings",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=38,
            width=160,
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
                text_color=("#15803D", "#86EFAC"),
            )
            # Re-normalize entry display
            _, normalized, _ = self.settings_service.validate_and_normalize_thresholds(thresholds_str)
            self.thresholds_entry.delete(0, "end")
            self.thresholds_entry.insert(0, normalized)
        else:
            self.save_status_lbl.configure(
                text="⚠️ " + msg,
                text_color=("#B91C1C", "#FCA5A5"),
            )

    def _build_export_card(self) -> None:
        """Offline data backup and export actions card."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=(0, 16), padx=4)

        ctk.CTkLabel(card, text="Data Export & Backups", font=FONT_SECTION, anchor="w").pack(
            fill="x", padx=20, pady=(16, 4)
        )
        ctk.CTkLabel(
            card,
            text="Export all your medicine inventory records to offline CSV or JSON files. No cloud sync is used.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 10))

        csv_btn = ctk.CTkButton(
            btn_row,
            text="📥 Export CSV",
            font=FONT_BODY_BOLD,
            height=36,
            width=140,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=self._handle_export_csv,
        )
        csv_btn.pack(side="left", padx=(0, 10))

        json_btn = ctk.CTkButton(
            btn_row,
            text="📥 Export JSON",
            font=FONT_BODY_BOLD,
            height=36,
            width=140,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=self._handle_export_json,
        )
        json_btn.pack(side="left")

        self.export_status_lbl = ctk.CTkLabel(
            card,
            text="",
            font=FONT_BODY,
            anchor="w",
        )
        self.export_status_lbl.pack(fill="x", padx=20, pady=(0, 14))

    def _handle_export_csv(self) -> None:
        """Trigger CSV export and display result."""
        success, msg, path = self.backup_service.export_csv()
        if success and path is not None:
            self.export_status_lbl.configure(
                text=f"✓ CSV export completed successfully: {path.name}",
                text_color=("#15803D", "#86EFAC"),
            )
        else:
            self.export_status_lbl.configure(
                text=f"⚠️ {msg}",
                text_color=("#B91C1C", "#FCA5A5"),
            )

    def _handle_export_json(self) -> None:
        """Trigger JSON export and display result."""
        success, msg, path = self.backup_service.export_json()
        if success and path is not None:
            self.export_status_lbl.configure(
                text=f"✓ JSON export completed successfully: {path.name}",
                text_color=("#15803D", "#86EFAC"),
            )
        else:
            self.export_status_lbl.configure(
                text=f"⚠️ {msg}",
                text_color=("#B91C1C", "#FCA5A5"),
            )

    def _build_storage_card(self) -> None:
        """Local database location card with explorer access buttons."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=(0, 20), padx=4)

        ctk.CTkLabel(card, text="Local Data Storage", font=FONT_SECTION, anchor="w").pack(
            fill="x", padx=20, pady=(16, 4)
        )

        data_info = self.settings_service.get_data_info()
        rel_path = data_info["relative_db_path"]

        path_lbl = ctk.CTkLabel(
            card,
            text=f"Database file: {rel_path}",
            font=FONT_BODY_BOLD,
            anchor="w",
        )
        path_lbl.pack(fill="x", padx=20, pady=(0, 2))

        ctk.CTkLabel(
            card,
            text="All data is stored strictly locally in your user workspace. No cloud connections are created.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

        folder_btns = ctk.CTkFrame(card, fg_color="transparent")
        folder_btns.pack(fill="x", padx=20, pady=(0, 16))

        open_data_btn = ctk.CTkButton(
            folder_btns,
            text="📂 Open Data Folder",
            font=FONT_BODY,
            height=34,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=self.settings_service.open_data_folder,
        )
        open_data_btn.pack(side="left", padx=(0, 10))

        open_backups_btn = ctk.CTkButton(
            folder_btns,
            text="📂 Open Backups Folder",
            font=FONT_BODY,
            height=34,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=self.settings_service.open_backups_folder,
        )
        open_backups_btn.pack(side="left")
