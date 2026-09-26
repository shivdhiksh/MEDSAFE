"""Ambient gradient backdrop and decorative canvas components for MEDSAFE.

Implements lightweight, offline desktop ambient studio lighting and visual glassmorphism
elements inspired directly by the reference designs:
- Subtle, soft, blurred, low-contrast ambient studio lighting
- No visible geometric circles, no wallpaper, no posters, no giant banners
- Sleek 3D-styled medicine capsule icon
- Floating glass hero panel with offline pill badge and glass action buttons
"""

import math
from typing import Callable, List, Optional, Tuple, Union
import customtkinter as ctk

from frontend.config import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_PRIMARY_SUBTLE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_HERO,
)


class CapsuleCanvas(ctk.CTkCanvas):
    """Clean, high-precision medicine capsule canvas drawing.
    Renders an angled (45-degree) medicine capsule with magenta/pink upper half,
    cyan/blue lower half, divider ring, and glossy specular highlight.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        size: int = 44,
        bg_color: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.size = size
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        canvas_bg = bg_color or (COLOR_CARD[1] if is_dark else COLOR_CARD[0])

        super().__init__(
            master,
            width=size,
            height=size,
            bg=canvas_bg,
            highlightthickness=0,
            borderwidth=0,
            **kwargs,
        )
        self.redraw()

    def redraw(self) -> None:
        """Draw the styled 3D-effect medicine capsule."""
        self.delete("all")
        s = self.size
        cx, cy = s // 2, s // 2
        r = max(4, int(s * 0.16))
        d = max(5, int(s * 0.20))
        w = r * 2

        # Outer subtle bloom
        self.create_line(cx - 1, cy - 1, cx + d + 1, cy + d + 1, width=w + 3, capstyle="round", fill="#07203A")
        self.create_line(cx + 1, cy + 1, cx - d - 1, cy - d - 1, width=w + 3, capstyle="round", fill="#3A0B1A")

        # Bottom-right half: Cyan / Sky Blue
        self.create_line(cx - 1, cy - 1, cx + d, cy + d, width=w, capstyle="round", fill="#0284C7")
        self.create_line(cx, cy, cx + d - 2, cy + d - 2, width=max(2, w - 4), capstyle="round", fill="#38BDF8")

        # Top-left half: Magenta / Pink
        self.create_line(cx + 1, cy + 1, cx - d, cy - d, width=w, capstyle="round", fill="#DB2777")
        self.create_line(cx, cy, cx - d + 2, cy - d + 2, width=max(2, w - 4), capstyle="round", fill="#F472B6")

        # Seam ring
        ring_r = int(w * 0.38)
        self.create_line(cx - ring_r, cy + ring_r, cx + ring_r, cy - ring_r, width=2, fill="#0F172A")

        # Specular gloss highlight on upper curve
        self.create_line(
            cx - d + 2,
            cy - d + int(r * 0.7),
            cx + d - int(r * 0.7),
            cy + d - 2,
            width=max(1, int(w * 0.14)),
            capstyle="round",
            fill="#FFFFFF",
        )


class AmbientRenderer:
    """Pre-renders smooth, diffuse, low-contrast atmospheric lighting buffers using PPM format.
    Produces studio-quality soft out-of-focus lighting behind frosted glass:
    - Delta RGB is restrained to only 15-25 units over dark obsidian base
    - Zero sharp geometric edges, zero concentric rings, zero wallpaper effect
    """

    def __init__(self, width: int = 160, height: int = 100):
        self.w = width
        self.h = height
        self._cache = {}

    def generate_ppm(self, is_dark: bool) -> bytes:
        mode_key = "dark" if is_dark else "light"
        if mode_key in self._cache:
            return self._cache[mode_key]

        w, h = self.w, self.h
        if is_dark:
            base_r, base_g, base_b = 6, 9, 18  # #060912 obsidian navy
            lights = [
                # x, y, radius, r, g, b, intensity (restrained to 0.08 - 0.14)
                (0.20, 0.12, 0.45, 14, 165, 233, 0.14),  # soft cyan/sky blue
                (0.06, 0.72, 0.50, 168, 85, 247, 0.11),  # soft violet/purple
                (0.80, 0.25, 0.45, 99, 102, 241, 0.09),  # soft indigo
                (0.75, 0.85, 0.40, 16, 185, 129, 0.06),  # subtle emerald
            ]
        else:
            base_r, base_g, base_b = 240, 243, 249  # #F0F3F9 soft pearl
            lights = [
                (0.20, 0.12, 0.45, 215, 235, 255, 0.35),
                (0.06, 0.72, 0.50, 235, 225, 255, 0.30),
                (0.80, 0.25, 0.45, 225, 230, 255, 0.25),
                (0.75, 0.85, 0.40, 225, 250, 240, 0.20),
            ]

        buf = bytearray(w * h * 3)
        pre_lights = []
        for lx, ly, lrad, lr, lg, lb, lint in lights:
            inv_r2 = 1.0 / (lrad * lrad)
            x_d2 = [((x / w - lx) ** 2) * inv_r2 for x in range(w)]
            y_d2 = [((y / h - ly) ** 2) * inv_r2 for y in range(h)]
            del_r = (lr - base_r) * lint
            del_g = (lg - base_g) * lint
            del_b = (lb - base_b) * lint
            pre_lights.append((x_d2, y_d2, del_r, del_g, del_b))

        for y in range(h):
            row_off = y * w * 3
            y_vals = [(pl[1][y], pl[2], pl[3], pl[4], pl[0]) for pl in pre_lights]
            for x in range(w):
                r = base_r
                g = base_g
                b = base_b
                for y_d2, del_r, del_g, del_b, x_d2_list in y_vals:
                    d2 = x_d2_list[x] + y_d2
                    if d2 < 1.0:
                        dist = math.isqrt(int(d2 * 10000)) / 100.0
                        fade = 1.0 - (3.0 * d2 - 2.0 * d2 * dist)
                        r += del_r * fade
                        g += del_g * fade
                        b += del_b * fade
                idx = row_off + x * 3
                buf[idx] = min(255, max(0, int(r)))
                buf[idx + 1] = min(255, max(0, int(g)))
                buf[idx + 2] = min(255, max(0, int(b)))

        header = f"P6\n{w} {h}\n255\n".encode("ascii")
        ppm_data = header + bytes(buf)
        self._cache[mode_key] = ppm_data
        return ppm_data


# Global ambient renderer instance
_AMBIENT_RENDERER = AmbientRenderer(width=160, height=100)


class AmbientBackground(ctk.CTkCanvas):
    """Full-window ambient backdrop rendering soft, out-of-focus atmospheric studio lighting.
    Uses fast, memory-cached low-contrast PPM PhotoImage zooming to produce
    genuine blurred ambient studio light behind floating glass panels.
    NO sharp concentric rings, NO wave ribbons, NO poster wallpaper.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        draw_blobs: bool = True,
        draw_waves: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            highlightthickness=0,
            borderwidth=0,
            **kwargs,
        )
        self.draw_blobs = draw_blobs
        self.draw_waves = draw_waves
        self._last_w = 0
        self._last_h = 0
        self._resize_timer = None
        self._photo_ref = None

        self.bind("<Configure>", self._on_resize)

    def _is_dark_mode(self) -> bool:
        return ctk.get_appearance_mode().lower() == "dark"

    def _on_resize(self, event) -> None:
        if abs(event.width - self._last_w) > 40 or abs(event.height - self._last_h) > 40:
            self._last_w = event.width
            self._last_h = event.height
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(80, self.redraw)

    def redraw(self) -> None:
        """Update and repaint the ambient studio lighting backdrop."""
        w = max(self.winfo_width(), 840)
        h = max(self.winfo_height(), 540)
        is_dark = self._is_dark_mode()

        base_color = COLOR_BACKGROUND[1] if is_dark else COLOR_BACKGROUND[0]
        self.configure(bg=base_color)
        self.delete("all")

        try:
            ppm_data = _AMBIENT_RENDERER.generate_ppm(is_dark)
            base_photo = ctk.CTkImage._photo_image = None  # prevent Tkinter image leak
            import tkinter as tk
            base_img = tk.PhotoImage(data=ppm_data)
            scale_x = max(1, math.ceil(w / 160))
            scale_y = max(1, math.ceil(h / 100))
            scale = max(scale_x, scale_y)
            zoomed = base_img.zoom(scale, scale)
            self._photo_ref = zoomed  # keep Python reference
            self.create_image(w // 2, h // 2, image=zoomed)
        except Exception:
            # Fallback if image buffer cannot be created
            pass


class AmbientCanvas(AmbientBackground):
    """Compatibility wrapper for AmbientBackground supporting historical constructor arguments."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        draw_blobs: bool = True,
        draw_waves: bool = True,
        height: int = 140,
        **kwargs,
    ) -> None:
        super().__init__(master, draw_blobs=draw_blobs, draw_waves=draw_waves, height=height, **kwargs)


class AmbientHeroPanel(ctk.CTkFrame):
    """Floating glass hero panel matching the reference image layout.
    Structure:
    - Translucent glass surface with subtle border
    - Left: 3D-styled medicine capsule icon + MEDSAFE title + [ 🔒 Offline & Private ] pill badge + subtitle
    - Right: [ 📋 View Inventory ] and [ 🔔 Test Notification ] glass action buttons
    - NO decorative wallpaper, NO wave banner, NO duplicate Add Medicine button
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_view_inventory: Optional[Callable[[], None]] = None,
        on_test_notif: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )

        self.on_view_inventory_callback = on_view_inventory
        self.on_test_notif_callback = on_test_notif

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the reference-matching hero layout."""
        content_box = ctk.CTkFrame(self, fg_color="transparent")
        content_box.pack(fill="x", padx=20, pady=18)
        content_box.grid_columnconfigure(0, weight=1)

        # Left Column: Capsule Icon + Typography & Pill Badge
        left_box = ctk.CTkFrame(content_box, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="w")

        # 3D-styled Medicine Capsule Icon
        self.capsule_icon = CapsuleCanvas(left_box, size=46)
        self.capsule_icon.pack(side="left", padx=(0, 14))

        text_col = ctk.CTkFrame(left_box, fg_color="transparent")
        text_col.pack(side="left", fill="y", expand=True)

        title_row = ctk.CTkFrame(text_col, fg_color="transparent")
        title_row.pack(anchor="w")

        hero_title = ctk.CTkLabel(
            title_row,
            text="MEDSAFE",
            font=FONT_HERO,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        hero_title.pack(side="left")

        privacy_badge = ctk.CTkLabel(
            title_row,
            text="🔒 Offline & Private",
            font=FONT_CAPTION_BOLD,
            fg_color=COLOR_PRIMARY_SUBTLE,
            text_color=COLOR_PRIMARY,
            corner_radius=10,
            padx=10,
            pady=3,
        )
        privacy_badge.pack(side="left", padx=(12, 0))

        subtitle = ctk.CTkLabel(
            text_col,
            text="Your medicine inventory overview and local expiry tracking.",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        subtitle.pack(anchor="w", pady=(3, 0))

        # Right Column: Quick Action Glass Buttons (View Inventory & Test Notification)
        actions_box = ctk.CTkFrame(content_box, fg_color="transparent")
        actions_box.grid(row=0, column=1, sticky="e")

        if self.on_view_inventory_callback is not None:
            self.view_inv_btn = ctk.CTkButton(
                actions_box,
                text="📋 View Inventory",
                font=FONT_BODY,
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_BTN_SECONDARY_HOVER,
                text_color=COLOR_BTN_SECONDARY_TEXT,
                height=36,
                corner_radius=8,
                border_width=1,
                border_color=COLOR_BORDER,
                command=self.on_view_inventory_callback,
            )
            self.view_inv_btn.pack(side="left", padx=(0, 10))

        if self.on_test_notif_callback is not None:
            self.test_notif_btn = ctk.CTkButton(
                actions_box,
                text="🔔 Test Notification",
                font=FONT_BODY,
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_BTN_SECONDARY_HOVER,
                text_color=COLOR_BTN_SECONDARY_TEXT,
                height=36,
                corner_radius=8,
                border_width=1,
                border_color=COLOR_BORDER,
                command=self.on_test_notif_callback,
            )
            self.test_notif_btn.pack(side="left")


# Aliases for explicit component architecture
AmbientWaveCanvas = AmbientCanvas
