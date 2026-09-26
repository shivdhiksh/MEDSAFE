"""Add Medicine view for MEDSAFE.

Presents the complete medicine and initial batch entry flow using embedded
MedicineForm component. Page title and back navigation are handled by the
global floating glass top header to prevent title duplication.
"""

from typing import Callable, Optional
import customtkinter as ctk

from backend.services.medicine_service import MedicineCreationResult, MedicineService
from frontend.components.medicine_form import MedicineForm


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
        """Construct the form body directly without repeating the page title."""
        # Form Component (contains Medicine Details and Batch & Expiry Details glass cards)
        self.form = MedicineForm(
            self,
            medicine_service=self.medicine_service,
            on_success=self._on_medicine_saved,
        )
        self.form.grid(row=0, column=0, sticky="nsew", pady=(0, 16))

    def _on_medicine_saved(self, result: MedicineCreationResult) -> None:
        """Optional hook invoked after a medicine is saved."""
        if self.on_medicine_saved_callback is not None:
            self.on_medicine_saved_callback(result)
