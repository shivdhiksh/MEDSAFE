"""UI configuration, theme settings, color palettes, and fonts for MEDSAFE.

Second Visual Upgrade: Premium Glassmorphism & Ambient Gradient Experience.
Centralized design system tokens for desktop glassmorphism styling, ambient glow,
translucent layered surfaces, dark/light mode contrast, typography, and status indicators.
"""

from typing import Tuple

# ---------------------------------------------------------------------------
# Window Configuration
# ---------------------------------------------------------------------------
WINDOW_TITLE: str = "MedSafe"
WINDOW_DEFAULT_SIZE: str = "1040x680"
WINDOW_MIN_WIDTH: int = 840
WINDOW_MIN_HEIGHT: int = 540

# ---------------------------------------------------------------------------
# Typography (Windows Segoe UI Hierarchy)
# ---------------------------------------------------------------------------
FONT_FAMILY: str = "Segoe UI"
FONT_HERO: Tuple[str, int, str] = (FONT_FAMILY, 24, "bold")
FONT_TITLE: Tuple[str, int, str] = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE: Tuple[str, int, str] = (FONT_FAMILY, 15, "bold")
FONT_SECTION: Tuple[str, int, str] = (FONT_FAMILY, 14, "bold")
FONT_BODY: Tuple[str, int] = (FONT_FAMILY, 13)
FONT_BODY_BOLD: Tuple[str, int, str] = (FONT_FAMILY, 13, "bold")
FONT_CAPTION: Tuple[str, int] = (FONT_FAMILY, 11)
FONT_CAPTION_BOLD: Tuple[str, int, str] = (FONT_FAMILY, 11, "bold")
FONT_DISCLAIMER: Tuple[str, int, str] = (FONT_FAMILY, 11, "italic")
FONT_KPI_NUM: Tuple[str, int, str] = (FONT_FAMILY, 28, "bold")
FONT_BADGE: Tuple[str, int, str] = (FONT_FAMILY, 10, "bold")

# ---------------------------------------------------------------------------
# Color Palette: Tuples of (Light Mode, Dark Mode)
# Dark Mode: Deep navy / near-black (#070B14 / #0A0F1D) with ambient blue/purple glow
# Light Mode: Clean off-white / light slate (#F5F7FB / #FFFFFF) with soft lavender/blue depth
# ---------------------------------------------------------------------------

# Primary Brand & Accent Gradients
COLOR_PRIMARY: Tuple[str, str] = ("#0284C7", "#0EA5E9")              # Medical Blue / Sky Blue
COLOR_PRIMARY_HOVER: Tuple[str, str] = ("#0369A1", "#38BDF8")        # Deep Sky / Bright Luminous Sky
COLOR_PRIMARY_SUBTLE: Tuple[str, str] = ("#E0F2FE", "#082F49")       # Tinted blue container
COLOR_PRIMARY_BORDER: Tuple[str, str] = ("#BAE6FD", "#0284C7")       # Subtle primary outline

# Ambient Accent Colors (Inspired by reference glowing blobs)
COLOR_ACCENT_PURPLE: Tuple[str, str] = ("#7C3AED", "#A855F7")       # Royal / Luminous Purple
COLOR_ACCENT_PURPLE_HOVER: Tuple[str, str] = ("#6D28D9", "#C084FC")
COLOR_ACCENT_PURPLE_SUBTLE: Tuple[str, str] = ("#EDE9FE", "#2E1065")
COLOR_ACCENT_PINK: Tuple[str, str] = ("#DB2777", "#F472B6")         # Soft Magenta / Pink
COLOR_ACCENT_PINK_SUBTLE: Tuple[str, str] = ("#FCE7F3", "#500724")
COLOR_ACCENT_CYAN: Tuple[str, str] = ("#0891B2", "#22D3EE")         # Bright Cyan
COLOR_ACCENT_CYAN_SUBTLE: Tuple[str, str] = ("#CFFAFE", "#083344")

# Ambient Canvas Glow Blobs (Colors for stepped concentric circles)
# Dark mode luminous ambient tones; light mode soft pastel washes
GLOW_BLUE_STEPS_DARK = ["#041A33", "#072B54", "#0A3D75", "#0C5099", "#0284C7", "#38BDF8"]
GLOW_BLUE_STEPS_LIGHT = ["#F8FAFC", "#F0F9FF", "#E0F2FE", "#BAE6FD", "#7DD3FC"]
GLOW_PURPLE_STEPS_DARK = ["#130926", "#210D3F", "#32125E", "#4A188A", "#6D28D9", "#A855F7"]
GLOW_PURPLE_STEPS_LIGHT = ["#F8FAFC", "#FAF5FF", "#F3E8FF", "#E9D5FF", "#C084FC"]
GLOW_PINK_STEPS_DARK = ["#260718", "#3E0A26", "#5C0E38", "#83134F", "#BE185D", "#F472B6"]
GLOW_PINK_STEPS_LIGHT = ["#F8FAFC", "#FFF1F2", "#FFE4E6", "#FECDD3", "#F472B6"]
GLOW_AMBER_STEPS_DARK = ["#240D04", "#3D1707", "#5E250A", "#8A370E", "#C2410C", "#F59E0B"]
GLOW_AMBER_STEPS_LIGHT = ["#F8FAFC", "#FFFBEB", "#FEF3C7", "#FDE68A", "#FBBF24"]

# Flowing Ribbon Wave Colors
WAVE_COLORS_DARK = ["#38BDF8", "#60A5FA", "#818CF8", "#A78BFA", "#C084FC", "#E879F9", "#F472B6"]
WAVE_COLORS_LIGHT = ["#93C5FD", "#A5B4FC", "#C4B5FD", "#DDD6FE", "#E9D5FF", "#F5D0FE", "#FBCFE8"]

# Secondary & Neutral Accents
COLOR_SECONDARY: Tuple[str, str] = ("#475569", "#64748B")
COLOR_SECONDARY_HOVER: Tuple[str, str] = ("#334155", "#94A3B8")
COLOR_BTN_SECONDARY: Tuple[str, str] = ("#EDF2F7", "#131E35")
COLOR_BTN_SECONDARY_HOVER: Tuple[str, str] = ("#E2E8F0", "#1E2C4A")
COLOR_BTN_SECONDARY_TEXT: Tuple[str, str] = ("#1E293B", "#F1F5F9")

# Danger / Destructive
COLOR_DANGER: Tuple[str, str] = ("#DC2626", "#EF4444")
COLOR_DANGER_HOVER: Tuple[str, str] = ("#B91C1C", "#DC2626")
COLOR_DANGER_SUBTLE: Tuple[str, str] = ("#FEE2E2", "#3B0D0D")
COLOR_DANGER_BG: Tuple[str, str] = ("#FEE2E2", "#3B0D0D")
COLOR_DANGER_TEXT: Tuple[str, str] = ("#991B1B", "#FCA5A5")
COLOR_DANGER_BORDER: Tuple[str, str] = ("#FCA5A5", "#7F1D1D")

# Surfaces & Glassmorphic Desktop Layers
COLOR_BACKGROUND: Tuple[str, str] = ("#F0F4FA", "#060913")           # Deep near-black obsidian dark / Cool light canvas
COLOR_HEADER_BG: Tuple[str, str] = ("#FFFFFF", "#0C1527")            # Floating glass top header
COLOR_SIDEBAR: Tuple[str, str] = ("#FFFFFF", "#0C1527")              # Floating glass sidebar surface
COLOR_SIDEBAR_BORDER: Tuple[str, str] = ("#E2E8F0", "#1E2F4C")
COLOR_CARD: Tuple[str, str] = ("#FFFFFF", "#0F182B")                 # Translucent-like base glass card
COLOR_CARD_ELEVATED: Tuple[str, str] = ("#F8FAFC", "#14223A")        # Elevated glass panel
COLOR_CARD_HOVER: Tuple[str, str] = ("#F1F5F9", "#1B2D4C")           # Interactive glass hover
COLOR_BORDER: Tuple[str, str] = ("#E2E8F0", "#1E304E")               # Subtle crisp glass border
COLOR_BORDER_STRONG: Tuple[str, str] = ("#CBD5E1", "#2A4168")
COLOR_BORDER_HIGHLIGHT: Tuple[str, str] = ("#BAE6FD", "#38BDF8")     # Glass inner highlight rim
COLOR_DIVIDER: Tuple[str, str] = ("#EDF2F7", "#17233D")
COLOR_INPUT_BG: Tuple[str, str] = ("#F8FAFC", "#0C1424")             # Frosted glass input surface
COLOR_INPUT_BORDER: Tuple[str, str] = ("#CBD5E1", "#223554")

# Text Hierarchy
COLOR_TEXT_PRIMARY: Tuple[str, str] = ("#0F172A", "#F8FAFC")         # Highest contrast
COLOR_TEXT_SECONDARY: Tuple[str, str] = ("#475569", "#94A3B8")       # Medium contrast
COLOR_TEXT_MUTED: Tuple[str, str] = ("#94A3B8", "#64748B")           # Captions / hints
COLOR_TEXT_WHITE: str = "#FFFFFF"

# ---------------------------------------------------------------------------
# Status Colors (Calm, Professional, Non-Misleading)
# ---------------------------------------------------------------------------

# Valid: Calm Green
STATUS_VALID: Tuple[str, str] = ("#16A34A", "#22C55E")
STATUS_VALID_BG: Tuple[str, str] = ("#DCFCE7", "#052E16")
STATUS_VALID_TEXT: Tuple[str, str] = ("#15803D", "#4ADE80")
STATUS_VALID_BORDER: Tuple[str, str] = ("#86EFAC", "#166534")

# Expiring Soon: Warm Amber / Yellow
STATUS_EXPIRING: Tuple[str, str] = ("#D97706", "#F59E0B")
STATUS_EXPIRING_BG: Tuple[str, str] = ("#FEF3C7", "#451A03")
STATUS_EXPIRING_TEXT: Tuple[str, str] = ("#B45309", "#FBBF24")
STATUS_EXPIRING_BORDER: Tuple[str, str] = ("#FCD34D", "#78350F")

# Expired: Coral / Crimson Red
STATUS_EXPIRED: Tuple[str, str] = ("#DC2626", "#EF4444")
STATUS_EXPIRED_BG: Tuple[str, str] = ("#FEE2E2", "#450A0A")
STATUS_EXPIRED_TEXT: Tuple[str, str] = ("#B91C1C", "#F87171")
STATUS_EXPIRED_BORDER: Tuple[str, str] = ("#FCA5A5", "#7F1D1D")

# Disposed / Inactive: Muted Slate Gray
STATUS_INACTIVE: Tuple[str, str] = ("#64748B", "#94A3B8")
STATUS_INACTIVE_BG: Tuple[str, str] = ("#F1F5F9", "#1E293B")
STATUS_INACTIVE_TEXT: Tuple[str, str] = ("#475569", "#94A3B8")
STATUS_INACTIVE_BORDER: Tuple[str, str] = ("#CBD5E1", "#334155")
