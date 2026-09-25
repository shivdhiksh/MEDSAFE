"""Modal confirmation dialog component for MEDSAFE.

Ensures that irreversible actions (such as permanent deletion) require explicit user confirmation.
"""

from typing import Callable, Optional
import customtkinter as ctk

from frontend.config import (
    COLOR_CARD,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_TITLE,
)


class ConfirmationDialog(ctk.CTkToplevel):
    """Modal confirmation dialog for destructive actions."""

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
        self.geometry("460x220")
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
            x = master.winfo_rootx() + (master.winfo_width() - 460) // 2
            y = master.winfo_rooty() + (master.winfo_height() - 220) // 2
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
        """Construct dialog layout."""
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        title_label = ctk.CTkLabel(card, text=title, font=FONT_SECTION, anchor="w")
        title_label.pack(fill="x", padx=16, pady=(16, 8))

        msg_label = ctk.CTkLabel(
            card,
            text=message,
            font=FONT_BODY,
            justify="left",
            wraplength=390,
            text_color=("gray30", "gray75"),
        )
        msg_label.pack(fill="x", padx=16, pady=(0, 20))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        cancel_btn = ctk.CTkButton(
            btn_row,
            text=cancel_text,
            font=FONT_BODY,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            height=36,
            command=self.destroy,
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        confirm_color = ("#DC2626", "#B91C1C") if is_destructive else ("#0284C7", "#0369A1")
        confirm_hover = ("#B91C1C", "#991B1B") if is_destructive else ("#0369A1", "#0284C7")

        confirm_btn = ctk.CTkButton(
            btn_row,
            text=confirm_text,
            font=FONT_BODY_BOLD,
            fg_color=confirm_color,
            hover_color=confirm_hover,
            height=36,
            command=self._confirm,
        )
        confirm_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _confirm(self) -> None:
        """Execute confirmation callback and close dialog."""
        self.destroy()
        if self.on_confirm_callback is not None:
            self.on_confirm_callback()
