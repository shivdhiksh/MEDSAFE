"""Reusable glassmorphism cards and metric presentation components for MEDSAFE.

Implements desktop glassmorphism styling using layered surfaces, subtle borders,
elevated tonal hierarchy, controlled contrast, and interactive hover states.
"""

from typing import Optional, Tuple, Union
import customtkinter as ctk

from frontend.config import (
    COLOR_BORDER,
    COLOR_BORDER_HIGHLIGHT,
    COLOR_BORDER_STRONG,
    COLOR_CARD,
    COLOR_CARD_ELEVATED,
    COLOR_CARD_HOVER,
    COLOR_DIVIDER,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_KPI_NUM,
    FONT_SECTION,
)


class GlassCard(ctk.CTkFrame):
    """Base surface for modern desktop glassmorphism.

    Provides a clean, elevated container with consistent rounded corners,
    subtle border, and theme-aware surface coloring.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        elevated: bool = False,
        corner_radius: int = 12,
        border_width: int = 1,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        **kwargs,
    ) -> None:
        chosen_fg = fg_color or (COLOR_CARD_ELEVATED if elevated else COLOR_CARD)
        chosen_border = border_color or COLOR_BORDER

        super().__init__(
            master,
            fg_color=chosen_fg,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=chosen_border,
            **kwargs,
        )


class GlassCardElevated(GlassCard):
    """Elevated translucent-like glass card surface for high-hierarchy content."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        corner_radius: int = 12,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            elevated=True,
            corner_radius=corner_radius,
            border_color=COLOR_BORDER_STRONG,
            **kwargs,
        )


class GlassCardHover(ctk.CTkFrame):
    """Interactive glass card with micro-interaction hover surface transitions."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        default_fg: Optional[Union[str, Tuple[str, str]]] = None,
        hover_fg: Optional[Union[str, Tuple[str, str]]] = None,
        corner_radius: int = 10,
        border_width: int = 1,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,
        **kwargs,
    ) -> None:
        self.default_fg = default_fg or COLOR_CARD_ELEVATED
        self.hover_fg = hover_fg or COLOR_CARD_HOVER
        chosen_border = border_color or COLOR_BORDER

        super().__init__(
            master,
            fg_color=self.default_fg,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=chosen_border,
            **kwargs,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None) -> None:
        """Slight elevation change on mouse enter."""
        self.configure(fg_color=self.hover_fg)

    def _on_leave(self, event=None) -> None:
        """Restore surface on mouse leave."""
        self.configure(fg_color=self.default_fg)


class GlassKPI(ctk.CTkFrame):
    """Floating KPI Metric card with glowing accent edge, icon badge, and large stat counter."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        value: Union[int, str],
        icon: str,
        accent_color: Union[str, Tuple[str, str]] = COLOR_PRIMARY,
        supporting_text: str = "",
        corner_radius: int = 14,
        card_bg: Optional[Union[str, Tuple[str, str]]] = None,
        card_border: Optional[Union[str, Tuple[str, str]]] = None,
        badge_bg: Optional[Union[str, Tuple[str, str]]] = None,
        **kwargs,
    ) -> None:
        chosen_fg = card_bg or COLOR_CARD
        chosen_border = card_border or COLOR_BORDER

        super().__init__(
            master,
            fg_color=chosen_fg,
            corner_radius=corner_radius,
            border_width=1,
            border_color=chosen_border,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(14, 14))
        content.grid_columnconfigure(0, weight=1)

        # Header row: Title on left and Icon Badge on right
        header_row = ctk.CTkFrame(content, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 6))

        title_lbl = ctk.CTkLabel(
            header_row,
            text=title,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        title_lbl.pack(side="left")

        chosen_badge_bg = badge_bg or COLOR_CARD_ELEVATED
        icon_badge = ctk.CTkLabel(
            header_row,
            text=icon,
            font=(FONT_BODY[0], 14),
            text_color=accent_color,
            fg_color=chosen_badge_bg,
            corner_radius=8,
            width=30,
            height=30,
        )
        icon_badge.pack(side="right")

        # Large KPI Number
        self.value_lbl = ctk.CTkLabel(
            content,
            text=str(value),
            font=FONT_KPI_NUM,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.value_lbl.pack(fill="x", pady=(0, 2))

        # Bottom row: Supporting description
        self.desc_lbl = None
        if supporting_text:
            self.desc_lbl = ctk.CTkLabel(
                content,
                text=supporting_text,
                font=FONT_CAPTION,
                text_color=COLOR_TEXT_MUTED,
                anchor="w",
            )
            self.desc_lbl.pack(fill="x", pady=(4, 0))

    def update_value(self, new_val: Union[int, str]) -> None:
        """Dynamically update the displayed count."""
        self.value_lbl.configure(text=str(new_val))


# Alias KPICard to GlassKPI for full backward compatibility with any previous imports
KPICard = GlassKPI


class GlassSection(ctk.CTkFrame):
    """Section container featuring a title header, optional action widget, divider, and body."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        subtitle: str = "",
        action_widget: Optional[ctk.CTkBaseClass] = None,
        corner_radius: int = 12,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_CARD,
            corner_radius=corner_radius,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        # Header Frame
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 12))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            title_box,
            text=title,
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        title_lbl.pack(anchor="w")

        if subtitle:
            sub_lbl = ctk.CTkLabel(
                title_box,
                text=subtitle,
                font=FONT_CAPTION,
                text_color=COLOR_TEXT_MUTED,
                anchor="w",
            )
            sub_lbl.pack(anchor="w", pady=(1, 0))

        if action_widget is not None:
            action_widget.grid(row=0, column=1, sticky="e")

        # Subtle divider
        divider = ctk.CTkFrame(self, height=1, fg_color=COLOR_DIVIDER)
        divider.pack(fill="x", padx=16, pady=(0, 14))

        # Body container where child widgets are placed
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.body.grid_columnconfigure(0, weight=1)


# Alias SectionCard to GlassSection for full backward compatibility
SectionCard = GlassSection
