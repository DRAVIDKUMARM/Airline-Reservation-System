"""
theme.py
Single source of truth for color and font choices across every screen.
Palette direction: deep navy chrome (admin dashboard reference) + a
sky-blue-to-lavender gradient feel for hero/booking screens + a vivid
purple accent for primary actions, with a small set of status colors
used consistently for badges, stat tiles, and success/error banners.
"""

COLORS = {
    # Core chrome
    "bg_main": "#071426",
    "bg_panel": "#102333",
    "bg_panel_light": "#17345A",
    "bg_input": "#132B47",

    # Text
    "text_primary": "#F8FAFC",
    "text_secondary": "#B7C9DC",
    "text_muted": "#8EA7C0",

    # Accent (primary actions / links)
    "accent": "#1677FF",
    "accent_hover": "#0B5ED7",
    "accent_soft": "#00D4FF",

    # Multi-tone gradient pair used on hero / booking headers
    "gradient_start": "#1677FF",
    "gradient_end": "#00D4FF",

    # Status colors
    "success": "#2ECC91",
    "success_soft": "#173B32",
    "error": "#FF5C6C",
    "error_soft": "#3B1E24",
    "warning": "#F5B942",
    "warning_soft": "#3B321A",

    # Stat tile icon-badge colors (Flights / Bookings / Revenue / Users)
    "stat_flights": "#5B8DEF",
    "stat_bookings": "#2ECC91",
    "stat_revenue": "#F5B942",
    "stat_users": "#FF6FA5",

    "white": "#FFFFFF",
    "border": "#31365C",
}

FONTS = {
    "family": "Segoe UI",
    "h1": ("Segoe UI", 28, "bold"),
    "h2": ("Segoe UI", 20, "bold"),
    "h3": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 13),
    "body_bold": ("Segoe UI", 13, "bold"),
    "small": ("Segoe UI", 11),
    "stat_number": ("Segoe UI", 26, "bold"),
}

RADIUS = {
    "card": 14,
    "input": 8,
    "button": 8,
    "badge": 999,  # fully round
}

# Icon glyph + color used for each admin stat tile. main.py/ui.py pick
# these by label so new tiles just need an entry here.
STAT_TILE_STYLE = {
    "Flights": {"icon": "\u2708", "color": COLORS["stat_flights"]},   # ✈
    "Bookings": {"icon": "\U0001F4D1", "color": COLORS["stat_bookings"]},  # 🔑-ish bookmark
    "Revenue": {"icon": "\U0001F4B0", "color": COLORS["stat_revenue"]},    # 💰
    "Users": {"icon": "\U0001F464", "color": COLORS["stat_users"]},        # 👤
}
