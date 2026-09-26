"""Floating glass navigation sidebar component for MEDSAFE.

Provides modern desktop navigation across Dashboard, Inventory, Add Medicine,
Settings, and About views. Designed as a floating rounded glass container with
high-contrast active state indicators and local offline status badges.
"""

from typing import Callable, Dict, Optional
import customtkinter as ctk

from backend.config import APP_NAME, APP_VERSION
from frontend.config import (
    COLOR_BORDER,
    COLOR_CARD_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_SUBTLE,
    COLOR_SIDEBAR,
    COLOR_SIDEBAR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_TITLE,
)


class Sidebar(ctk.CTkFrame):
    """Floating rounded glass navigation sidebar with elevated pill buttons."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_navigate: Callable[[str], None],
        on_theme_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            width=230,
            corner_radius=18,
            fg_color=COLOR_SIDEBAR,
            border_width=1,
            border_color=COLOR_SIDEBAR_BORDER,
            **kwargs,
        )

        self.on_navigate_callback = on_navigate
        self.on_theme_change_callback = on_theme_change
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.active_view = "dashboard"

        self.grid_rowconfigure(7, weight=1)
        self._build_sidebar()

    def _build_sidebar(self) -> None:
        """Construct the floating sidebar branding, nav items, and offline indicator."""
        # 1. Branding Header
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(22, 16), sticky="ew")

        header_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        header_row.pack(fill="x", anchor="w")

        shield_icon = ctk.CTkLabel(
            header_row,
            text="🛡️",
            font=(FONT_TITLE[0], 20),
        )
        shield_icon.pack(side="left", padx=(0, 8))

        logo_label = ctk.CTkLabel(
            header_row,
            text=APP_NAME.upper(),
            font=FONT_TITLE,
            text_color=COLOR_PRIMARY,
            anchor="w",
        )
        logo_label.pack(side="left")

        tagline = ctk.CTkLabel(
            brand_frame,
            text="Offline Expiry Tracker",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        tagline.pack(anchor="w", pady=(3, 0))

        # Divider below branding
        divider = ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER)
        divider.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")

        # 2. Navigation Items (Floating glass pill buttons)
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("inventory", "📋  Inventory"),
            ("add_medicine", "➕  Add Medicine"),
            ("settings", "⚙️  Settings"),
            ("about", "ℹ️  About"),
        ]

        for idx, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self,
                text=label,
                font=FONT_BODY_BOLD if key == "dashboard" else FONT_BODY,
                height=42,
                corner_radius=10,
                anchor="w",
                fg_color="transparent",
                hover_color=COLOR_CARD_HOVER,
                text_color=COLOR_TEXT_SECONDARY,
                command=lambda k=key: self._on_btn_clicked(k),
            )
            btn.grid(row=idx, column=0, padx=14, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        self.set_active("dashboard")

        # 3. Bottom Footer (Offline Badge and App Info — NO appearance selector here!)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=8, column=0, padx=14, pady=18, sticky="ew")

        footer_divider = ctk.CTkFrame(bottom_frame, height=1, fg_color=COLOR_BORDER)
        footer_divider.pack(fill="x", pady=(0, 12))

        # Offline & Private Badge
        offline_pill = ctk.CTkLabel(
            bottom_frame,
            text="🔒 100% Offline & Private",
            font=FONT_CAPTION_BOLD,
            fg_color=COLOR_PRIMARY_SUBTLE,
            text_color=COLOR_PRIMARY,
            corner_radius=8,
            height=28,
        )
        offline_pill.pack(fill="x", pady=(0, 8))

        # Version & Local storage note
        version_lbl = ctk.CTkLabel(
            bottom_frame,
            text=f"v{APP_VERSION} • Local Storage",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="center",
        )
        version_lbl.pack(fill="x")

    def _handle_theme(self, mode: str) -> None:
        """Forward theme change event (maintained for backward compatibility)."""
        if self.on_theme_change_callback is not None:
            self.on_theme_change_callback(mode)

    def _on_btn_clicked(self, view_key: str) -> None:
        """Handle button click and notify parent."""
        self.set_active(view_key)
        self.on_navigate_callback(view_key)

    def set_active(self, view_key: str) -> None:
        """Update active button styling with luminous glass pill highlight."""
        self.active_view = view_key
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    text_color="white",
                    font=FONT_BODY_BOLD,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=COLOR_CARD_HOVER,
                    text_color=COLOR_TEXT_SECONDARY,
                    font=FONT_BODY,
                )
