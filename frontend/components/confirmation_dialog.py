"""Modal confirmation dialog component for MEDSAFE.

Ensures that irreversible actions (such as permanent deletion) require explicit user confirmation.
Implements desktop glassmorphism styling with distinct destructive indicators.
"""

from typing import Callable, Optional
import customtkinter as ctk

from frontend.config import (
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
)


class ConfirmationDialog(ctk.CTkToplevel):
    """Modal confirmation dialog for destructive and high-impact actions."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        on_confirm: Optional[Callable[[], None]] = None,
        is_destructive: bool = False,
    ) -> None:
        super().__init__(master)

        self.on_confirm_callback = on_confirm
        self.title(title)
        self.geometry("480x230")
        self.resizable(False, False)

        # Modal behavior
        self.transient(master)
        self.grab_set()

        # Center on parent window
        self._center(master)

        self._build_ui(title, message, confirm_text, cancel_text, is_destructive)

    def _center(self, master: ctk.CTkBaseClass) -> None:
        """Position modal in center of parent window."""
        self.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() - 480) // 2
            y = master.winfo_rooty() + (master.winfo_height() - 230) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(
        self,
        title: str,
        message: str,
        confirm_text: str,
        cancel_text: str,
        is_destructive: bool,
    ) -> None:
        """Construct dialog layout with modern glassmorphism aesthetic."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Title row with icon
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=18, pady=(16, 6))

        icon_str = "⚠️ " if is_destructive else "ℹ️ "
        title_label = ctk.CTkLabel(
            header_row,
            text=icon_str + title,
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        title_label.pack(side="left")

        # Message body
        msg_label = ctk.CTkLabel(
            card,
            text=message,
            font=FONT_BODY,
            justify="left",
            wraplength=410,
            text_color=COLOR_TEXT_SECONDARY,
        )
        msg_label.pack(fill="x", padx=18, pady=(0, 20))

        # Button row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(0, 16))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        cancel_btn = ctk.CTkButton(
            btn_row,
            text=cancel_text,
            font=FONT_BODY,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            height=36,
            corner_radius=8,
            command=self.destroy,
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        confirm_fg = COLOR_DANGER if is_destructive else COLOR_PRIMARY
        confirm_hover = COLOR_DANGER_HOVER if is_destructive else COLOR_PRIMARY_HOVER

        confirm_btn = ctk.CTkButton(
            btn_row,
            text=confirm_text,
            font=FONT_BODY_BOLD,
            fg_color=confirm_fg,
            hover_color=confirm_hover,
            text_color="white",
            height=36,
            corner_radius=8,
            command=self._confirm,
        )
        confirm_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _confirm(self) -> None:
        """Execute confirmation callback and close dialog."""
        self.destroy()
        if self.on_confirm_callback is not None:
            self.on_confirm_callback()
