"""Add Medicine view for MEDSAFE.

Presents the complete medicine and batch entry screen with intuitive header
and embedded MedicineForm component.
"""

from typing import Callable, Optional
import customtkinter as ctk

from backend.services.medicine_service import MedicineCreationResult, MedicineService
from frontend.components.medicine_form import MedicineForm
from frontend.config import (
    COLOR_BACKGROUND,
    FONT_BODY,
    FONT_CAPTION,
    FONT_SUBTITLE,
    FONT_TITLE,
)


class AddMedicineView(ctk.CTkScrollableFrame):
    """View container for adding a new medicine and initial batch."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        medicine_service: Optional[MedicineService] = None,
        on_back: Optional[Callable[[], None]] = None,
        on_medicine_saved: Optional[Callable[[MedicineCreationResult], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.medicine_service = medicine_service
        self.on_back_callback = on_back
        self.on_medicine_saved_callback = on_medicine_saved

        self.grid_columnconfigure(0, weight=1)
        self._build_view()

    def _build_view(self) -> None:
        """Construct the view header and form body."""
        # Navigation / Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header_frame.grid_columnconfigure(1, weight=1)

        if self.on_back_callback is not None:
            back_btn = ctk.CTkButton(
                header_frame,
                text="← Back",
                font=FONT_BODY,
                width=80,
                height=32,
                fg_color=("gray85", "gray30"),
                hover_color=("gray75", "gray40"),
                text_color=("black", "white"),
                command=self.on_back_callback,
            )
            back_btn.grid(row=0, column=0, padx=(0, 16), sticky="w")

        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.grid(row=0, column=1 if self.on_back_callback else 0, sticky="w")

        view_title = ctk.CTkLabel(
            title_container,
            text="Add Medicine",
            font=FONT_TITLE,
            anchor="w",
        )
        view_title.pack(anchor="w")

        view_desc = ctk.CTkLabel(
            title_container,
            text="Record drug details and expiry date for your local offline inventory.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        view_desc.pack(anchor="w", pady=(2, 0))

        # Form Component
        self.form = MedicineForm(
            self,
            medicine_service=self.medicine_service,
            on_success=self._on_medicine_saved,
        )
        self.form.grid(row=1, column=0, sticky="nsew", pady=(0, 16))

    def _on_medicine_saved(self, result: MedicineCreationResult) -> None:
        """Optional hook invoked after a medicine is saved."""
        if self.on_medicine_saved_callback is not None:
            self.on_medicine_saved_callback(result)
