"""About view for MEDSAFE.

Presents application information, offline-first data principles, and
the mandatory medical safety disclaimer.
"""

import customtkinter as ctk

from backend.config import APP_DISCLAIMER, APP_FULL_TITLE, APP_VERSION, DB_PATH
from frontend.config import (
    COLOR_CARD,
    COLOR_PRIMARY,
    FONT_BODY,
    FONT_CAPTION,
    FONT_DISCLAIMER,
    FONT_SECTION,
    FONT_SUBTITLE,
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
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=(0, 20), padx=4)

        title = ctk.CTkLabel(card, text="About MedSafe", font=FONT_TITLE, anchor="w")
        title.pack(fill="x", padx=24, pady=(24, 4))

        subtitle = ctk.CTkLabel(
            card,
            text=f"{APP_FULL_TITLE} • Version {APP_VERSION}",
            font=FONT_BODY,
            text_color="gray",
            anchor="w",
        )
        subtitle.pack(fill="x", padx=24, pady=(0, 16))

        desc = ctk.CTkLabel(
            card,
            text=(
                "MedSafe is a completely free, private, offline-first Windows desktop application.\n"
                "It helps families and individuals organize their home medicine inventory and prevents "
                "the accidental use of expired medications by tracking expiry dates locally."
            ),
            font=FONT_BODY,
            justify="left",
            wraplength=640,
        )
        desc.pack(fill="x", padx=24, pady=(0, 20))

        # Local storage details
        storage_box = ctk.CTkFrame(card, fg_color=("gray95", "#18202F"), corner_radius=8)
        storage_box.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkLabel(storage_box, text="Local Data Storage", font=FONT_SECTION, anchor="w").pack(
            fill="x", padx=16, pady=(12, 4)
        )
        from backend.config import get_db_path, is_frozen
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
            text_color=("gray30", "gray70"),
        ).pack(fill="x", padx=16, pady=(0, 10))

        from backend.utils.file_utils import open_folder_in_explorer
        from backend.config import DATA_DIR
        open_data_btn = ctk.CTkButton(
            storage_box,
            text="📂 Open Data Folder",
            font=FONT_BODY,
            height=32,
            width=160,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            command=lambda: open_folder_in_explorer(DATA_DIR),
        )
        open_data_btn.pack(anchor="w", padx=16, pady=(0, 14))

        # Mandatory Safety Disclaimer Box
        disclaimer_box = ctk.CTkFrame(
            card,
            fg_color=("gray95", "#18202F"),
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        disclaimer_box.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(
            disclaimer_box,
            text="Important Safety & Medical Notice",
            font=FONT_SECTION,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            disclaimer_box,
            text=APP_DISCLAIMER,
            font=FONT_DISCLAIMER,
            justify="left",
            wraplength=620,
            text_color=("gray30", "gray75"),
        ).pack(fill="x", padx=16, pady=(0, 14))
