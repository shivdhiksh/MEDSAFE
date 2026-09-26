"""Reusable status badge component for MEDSAFE.

Renders an accessible, high-contrast pill badge with distinct color styling,
a bullet dot indicator, and explicit status text.
"""

from typing import Tuple
import customtkinter as ctk

from backend.services.expiry_service import (
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
)
from frontend.config import (
    FONT_BADGE,
    STATUS_EXPIRED_BG,
    STATUS_EXPIRED_TEXT,
    STATUS_EXPIRING_BG,
    STATUS_EXPIRING_TEXT,
    STATUS_INACTIVE_BG,
    STATUS_INACTIVE_TEXT,
    STATUS_VALID_BG,
    STATUS_VALID_TEXT,
)


class StatusBadge(ctk.CTkLabel):
    """Pill badge showing status with distinct color and explicit text."""

    def __init__(self, master: ctk.CTkBaseClass, status: str, **kwargs) -> None:
        clean_status = str(status).strip().lower()
        text_label, fg_color, text_color = self._resolve_styling(clean_status)

        super().__init__(
            master,
            text=text_label,
            font=FONT_BADGE,
            fg_color=fg_color,
            text_color=text_color,
            corner_radius=10,
            padx=10,
            pady=3,
            **kwargs,
        )

    def _resolve_styling(self, status: str) -> Tuple[str, Tuple[str, str], Tuple[str, str]]:
        """Return (display_text, fg_color_tuple, text_color_tuple) for a status."""
        if status == STATUS_VALID:
            return (
                "● Valid",
                STATUS_VALID_BG,
                STATUS_VALID_TEXT,
            )
        elif status in (STATUS_EXPIRING_SOON, "expiring soon", "expiring_soon"):
            return (
                "● Expiring Soon",
                STATUS_EXPIRING_BG,
                STATUS_EXPIRING_TEXT,
            )
        elif status in (STATUS_EXPIRED, "expired", "status_expired"):
            return (
                "● Expired",
                STATUS_EXPIRED_BG,
                STATUS_EXPIRED_TEXT,
            )
        elif status in ("disposed", "inactive"):
            return (
                "● Disposed",
                STATUS_INACTIVE_BG,
                STATUS_INACTIVE_TEXT,
            )
        else:
            return (
                f"● {status.title()}",
                STATUS_INACTIVE_BG,
                STATUS_INACTIVE_TEXT,
            )
