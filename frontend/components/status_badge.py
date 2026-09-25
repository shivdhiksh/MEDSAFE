"""Reusable status badge component for MEDSAFE.

Renders an accessible pill badge with both high-contrast color and explicit status text.
"""

from typing import Tuple
import customtkinter as ctk

from backend.services.expiry_service import (
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
)
from frontend.config import FONT_CAPTION


class StatusBadge(ctk.CTkLabel):
    """Pill badge showing status with distinct color and explicit text."""

    def __init__(self, master: ctk.CTkBaseClass, status: str, **kwargs) -> None:
        clean_status = str(status).strip().lower()
        text_label, fg_color, text_color = self._resolve_styling(clean_status)

        super().__init__(
            master,
            text=text_label,
            font=(FONT_CAPTION[0], FONT_CAPTION[1], "bold"),
            fg_color=fg_color,
            text_color=text_color,
            corner_radius=6,
            padx=10,
            pady=3,
            **kwargs,
        )

    def _resolve_styling(self, status: str) -> Tuple[str, Tuple[str, str], Tuple[str, str]]:
        """Return (display_text, fg_color_tuple, text_color_tuple) for a status."""
        if status == STATUS_VALID:
            return (
                "Valid",
                ("#DCFCE7", "#14532D"),
                ("#15803D", "#86EFAC"),
            )
        elif status in (STATUS_EXPIRING_SOON, "expiring soon"):
            return (
                "Expiring Soon",
                ("#FEF3C7", "#78350F"),
                ("#B45309", "#FCD34D"),
            )
        elif status == STATUS_EXPIRED:
            return (
                "Expired",
                ("#FEE2E2", "#7F1D1D"),
                ("#B91C1C", "#FCA5A5"),
            )
        elif status in ("disposed", "inactive"):
            return (
                "Disposed",
                ("#F1F5F9", "#1E293B"),
                ("#64748B", "#94A3B8"),
            )
        else:
            return (
                status.title(),
                ("#F1F5F9", "#1E293B"),
                ("#475569", "#94A3B8"),
            )
