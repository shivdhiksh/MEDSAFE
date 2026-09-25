"""Navigation sidebar component for MEDSAFE.

Provides permanent desktop navigation across Dashboard, Inventory, Add Medicine,
Settings, and About views.
"""

from typing import Callable, Dict, Optional
import customtkinter as ctk

from frontend.config import (
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_SUBTITLE,
    FONT_TITLE,
)


class Sidebar(ctk.CTkFrame):
    """Sidebar navigation panel."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_navigate: Callable[[str], None],
        on_theme_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            width=220,
            corner_radius=0,
            fg_color=COLOR_CARD,
            border_width=1,
            border_color=("gray85", "gray25"),
            **kwargs,
        )

        self.on_navigate_callback = on_navigate
        self.on_theme_change_callback = on_theme_change
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.active_view = "dashboard"

        self.grid_rowconfigure(6, weight=1)
        self._build_sidebar()

    def _build_sidebar(self) -> None:
        """Construct the sidebar header, nav buttons, and bottom controls."""
        # Branding Header
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="ew")

        logo_label = ctk.CTkLabel(
            brand_frame,
            text="MedSafe",
            font=FONT_TITLE,
            text_color=COLOR_PRIMARY,
            anchor="w",
        )
        logo_label.pack(anchor="w")

        tagline = ctk.CTkLabel(
            brand_frame,
            text="Offline Expiry Tracker",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        tagline.pack(anchor="w", pady=(2, 0))

        # Divider
        divider = ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30"))
        divider.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")

        # Navigation Items
        nav_items = [
            ("dashboard", "Dashboard"),
            ("inventory", "Inventory"),
            ("add_medicine", "+ Add Medicine"),
            ("settings", "Settings"),
            ("about", "About"),
        ]

        for idx, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self,
                text=label,
                font=FONT_BODY_BOLD if key == "dashboard" else FONT_BODY,
                height=40,
                corner_radius=8,
                anchor="w",
                fg_color="transparent",
                hover_color=("gray90", "gray25"),
                text_color=("gray20", "gray85"),
                command=lambda k=key: self._on_btn_clicked(k),
            )
            btn.grid(row=idx, column=0, padx=14, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        self.set_active("dashboard")

        # Bottom Theme Switcher Frame
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=7, column=0, padx=14, pady=20, sticky="ew")

        theme_label = ctk.CTkLabel(
            bottom_frame,
            text="Appearance",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        theme_label.pack(fill="x", pady=(0, 4))

        self.theme_menu = ctk.CTkOptionMenu(
            bottom_frame,
            values=["System", "Light", "Dark"],
            font=FONT_BODY,
            height=32,
            command=self._handle_theme,
        )
        self.theme_menu.set("System")
        self.theme_menu.pack(fill="x")

    def _handle_theme(self, mode: str) -> None:
        """Forward theme change event."""
        if self.on_theme_change_callback is not None:
            self.on_theme_change_callback(mode)

    def _on_btn_clicked(self, view_key: str) -> None:
        """Handle button click and notify parent."""
        self.set_active(view_key)
        self.on_navigate_callback(view_key)

    def set_active(self, view_key: str) -> None:
        """Update active button styling."""
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
                    hover_color=("gray90", "gray25"),
                    text_color=("gray20", "gray85"),
                    font=FONT_BODY,
                )
