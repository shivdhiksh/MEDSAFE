"""About view for MEDSAFE.

Presents application information, offline-first data principles, and
the mandatory medical safety disclaimer.
"""

import customtkinter as ctk

from backend.config import APP_DISCLAIMER, APP_FULL_TITLE, APP_VERSION
from frontend.components.ambient_background import CapsuleCanvas
from frontend.components.glass_card import GlassCard
from frontend.config import (
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD_ELEVATED,
    COLOR_PRIMARY,
    COLOR_PRIMARY_SUBTLE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_DISCLAIMER,
    FONT_SECTION,
    FONT_TITLE,
)


class AboutView(ctk.CTkScrollableFrame):
    """View container for application information and mandatory safety notices."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the about card and safety notice."""
        # Main Info Card
        card = GlassCard(self)
        card.pack(fill="x", pady=(0, 20), padx=4)

        # Top branding row with capsule icon & version badge
        top_brand_row = ctk.CTkFrame(card, fg_color="transparent")
        top_brand_row.pack(fill="x", padx=24, pady=(20, 4))

        capsule = CapsuleCanvas(top_brand_row, size=40)
        capsule.pack(side="left", padx=(0, 12))

        badge = ctk.CTkLabel(
            top_brand_row,
            text=f"v{APP_VERSION} • Windows Desktop",
            font=FONT_CAPTION_BOLD,
            fg_color=COLOR_PRIMARY_SUBTLE,
            text_color=COLOR_PRIMARY,
            corner_radius=8,
            padx=10,
            pady=3,
        )
        badge.pack(side="left")


        subtitle = ctk.CTkLabel(
            card,
            text=APP_FULL_TITLE,
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        subtitle.pack(fill="x", padx=24, pady=(4, 14))

        desc = ctk.CTkLabel(
            card,
            text=(
                "MedSafe is a completely free, private, offline-first Windows desktop application.\n"
                "It helps families and individuals organize their home medicine inventory and track expiry dates locally."
            ),
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            wraplength=640,
        )
        desc.pack(fill="x", padx=24, pady=(0, 20))

        # Local storage details
        storage_box = ctk.CTkFrame(
            card,
            fg_color=COLOR_CARD_ELEVATED,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        storage_box.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkLabel(
            storage_box,
            text="Local Data Storage & Privacy",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 4))

        from backend.config import DATA_DIR, get_db_path, is_frozen
        from backend.utils.file_utils import open_folder_in_explorer

        db_label = "data/medsafe.db" if not is_frozen() else str(get_db_path())
        ctk.CTkLabel(
            storage_box,
            text=(
                f"Database File: {db_label}\n"
                "• All medicine data is stored entirely on your computer.\n"
                "• No internet connection, cloud accounts, or telemetry are ever required."
            ),
            font=FONT_CAPTION,
            justify="left",
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(fill="x", padx=18, pady=(0, 12))

        open_data_btn = ctk.CTkButton(
            storage_box,
            text="📂 Open Data Folder",
            font=FONT_BODY,
            height=34,
            width=160,
            corner_radius=8,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            command=lambda: open_folder_in_explorer(DATA_DIR),
        )
        open_data_btn.pack(anchor="w", padx=18, pady=(0, 16))

        # Mandatory Safety Disclaimer Box
        disclaimer_box = ctk.CTkFrame(
            card,
            fg_color=COLOR_CARD_ELEVATED,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        disclaimer_box.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(
            disclaimer_box,
            text="Important Safety & Medical Notice",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 4))

        ctk.CTkLabel(
            disclaimer_box,
            text=APP_DISCLAIMER,
            font=FONT_DISCLAIMER,
            justify="left",
            wraplength=620,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(fill="x", padx=18, pady=(0, 16))
