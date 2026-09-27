"""Reusable search bar component for MEDSAFE.

Provides an integrated search input with search icon, placeholder text,
live keystroke triggers, dynamic clear button, and luminous focus highlight.
"""

from typing import Callable, Optional
import customtkinter as ctk

from frontend.config import (
    COLOR_BORDER_HIGHLIGHT,
    COLOR_CARD,
    COLOR_CARD_ELEVATED,
    COLOR_INPUT_BG,
    COLOR_INPUT_BORDER,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_CAPTION,
)


class SearchBar(ctk.CTkFrame):
    """Modern search input bar with search icon and interactive clear button."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        placeholder: str = "Search medicine by name...",
        on_search: Optional[Callable[[str], None]] = None,
        height: int = 38,
        width: int = 280,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_INPUT_BG,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_INPUT_BORDER,
            height=height,
            width=width,
            **kwargs,
        )

        self.on_search_callback = on_search
        self.grid_columnconfigure(1, weight=1)

        # Search Icon
        self.icon_label = ctk.CTkLabel(
            self,
            text="🔍",
            font=(FONT_BODY[0], 12),
            text_color=COLOR_TEXT_MUTED,
            width=28,
        )
        self.icon_label.grid(row=0, column=0, padx=(10, 2), pady=2, sticky="w")

        # Text Entry
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=FONT_BODY,
            fg_color="transparent",
            border_width=0,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text_color=COLOR_TEXT_MUTED,
            height=height - 6,
        )
        self.entry.grid(row=0, column=1, padx=(0, 6), pady=2, sticky="ew")
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        # Clear Button (✕) - shown when text is present
        self.clear_btn = ctk.CTkButton(
            self,
            text="✕",
            font=(FONT_CAPTION[0], 10, "bold"),
            width=22,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color=COLOR_CARD_ELEVATED,
            text_color=COLOR_TEXT_MUTED,
            command=self.clear,
        )
        # Initially unmapped until text is entered

    def _on_focus_in(self, event=None) -> None:
        """Luminous focus ring border."""
        self.configure(border_color=COLOR_BORDER_HIGHLIGHT)

    def _on_focus_out(self, event=None) -> None:
        """Reset default border."""
        self.configure(border_color=COLOR_INPUT_BORDER)

    def _on_key_release(self, event=None) -> None:
        """Handle entry change, update clear button visibility, and fire callback."""
        query = self.get()
        if query:
            if not self.clear_btn.winfo_ismapped():
                self.clear_btn.grid(row=0, column=2, padx=(0, 6), pady=2, sticky="e")
        else:
            if self.clear_btn.winfo_ismapped():
                self.clear_btn.grid_forget()

        if self.on_search_callback is not None:
            self.on_search_callback(query)

    def get(self) -> str:
        """Return current search query string."""
        return self.entry.get()

    def set_text(self, text: str, trigger_callback: bool = True) -> None:
        """Programmatically set text with optional callback trigger."""
        self.entry.delete(0, "end")
        self.entry.insert(0, text)
        if text:
            if not self.clear_btn.winfo_ismapped():
                self.clear_btn.grid(row=0, column=2, padx=(0, 6), pady=2, sticky="e")
        else:
            if self.clear_btn.winfo_ismapped():
                self.clear_btn.grid_forget()

        if trigger_callback and self.on_search_callback is not None:
            self.on_search_callback(text)

    def clear(self) -> None:
        """Clear search query and fire callback with empty string."""
        self.entry.delete(0, "end")
        if self.clear_btn.winfo_ismapped():
            self.clear_btn.grid_forget()
        if self.on_search_callback is not None:
            self.on_search_callback("")
        self.entry.focus_set()
