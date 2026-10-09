"""
ui.py
Reusable widget builders shared by every page in main.py. Every color
here is pulled from theme.py so the whole app stays visually
consistent from one palette.
"""

import customtkinter as ctk
from theme import COLORS, FONTS, RADIUS, STAT_TILE_STYLE


class UIHelpers:
    """Backward-compatible mixin for older screens and helper methods."""
    pass


def top_bar(parent, title, on_back=None, on_exit=None):
    """A fixed-height header bar. Returns the bar frame."""
    bar = ctk.CTkFrame(parent, fg_color=COLORS["bg_panel"], height=64, corner_radius=0)
    bar.pack(side="top", fill="x")
    bar.pack_propagate(False)

    left = ctk.CTkFrame(bar, fg_color="transparent")
    left.pack(side="left", padx=16)

    if on_back:
        back_btn = ctk.CTkButton(
            left, text="\u2190", width=36, height=36, corner_radius=RADIUS["button"],
            fg_color=COLORS["bg_panel_light"], hover_color=COLORS["accent_soft"],
            text_color=COLORS["text_primary"], command=on_back,
        )
        back_btn.pack(side="left", padx=(0, 12), pady=14)

    ctk.CTkLabel(
        left, text=title, font=FONTS["h3"], text_color=COLORS["text_primary"]
    ).pack(side="left", pady=14)

    if on_exit:
        exit_btn = ctk.CTkButton(
            bar, text="Exit", width=64, height=32, corner_radius=RADIUS["button"],
            fg_color=COLORS["error"], hover_color="#D9455A",
            text_color=COLORS["white"], command=on_exit,
        )
        exit_btn.pack(side="right", padx=16, pady=16)

    return bar


def page_container(parent):
    """
    Scrollable content area that always sits below a top_bar (fixes the
    old overlap bug where content started at y=0 under the fixed bar).
    """
    container = ctk.CTkScrollableFrame(parent, fg_color=COLORS["bg_main"])
    container.pack(side="top", fill="both", expand=True, padx=24, pady=(20, 20))
    return container


def styled_entry(parent, placeholder, show=None, width=320):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder, show=show, width=width, height=40,
        corner_radius=RADIUS["input"], fg_color=COLORS["bg_input"],
        border_color=COLORS["border"], border_width=1,
        text_color=COLORS["text_primary"], placeholder_text_color=COLORS["text_muted"],
    )


def primary_button(parent, text, command, width=320, height=42):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=RADIUS["button"], fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"], text_color=COLORS["white"],
        font=FONTS["body_bold"],
    )


def secondary_button(parent, text, command, width=320, height=42):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=RADIUS["button"], fg_color=COLORS["bg_panel_light"],
        hover_color=COLORS["bg_input"], text_color=COLORS["text_primary"],
        font=FONTS["body_bold"], border_width=1, border_color=COLORS["border"],
    )


def danger_button(parent, text, command, width=140, height=34):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=RADIUS["button"], fg_color=COLORS["error"],
        hover_color="#D9455A", text_color=COLORS["white"], font=FONTS["small"],
    )


def banner(parent, message, kind="error"):
    """kind: 'error' | 'success' | 'warning'"""
    bg_key = {"error": "error_soft", "success": "success_soft", "warning": "warning_soft"}[kind]
    fg_key = {"error": "error", "success": "success", "warning": "warning"}[kind]
    frame = ctk.CTkFrame(parent, fg_color=COLORS[bg_key], corner_radius=RADIUS["input"])
    ctk.CTkLabel(
        frame, text=message, text_color=COLORS[fg_key], font=FONTS["small"], wraplength=320
    ).pack(padx=12, pady=8)
    return frame


def card(parent, **kwargs):
    fg = kwargs.pop("fg_color", COLORS["bg_panel"])
    return ctk.CTkFrame(parent, fg_color=fg, corner_radius=RADIUS["card"], **kwargs)


def small_stat_card(parent, label, value, icon_key=None):
    """
    Icon-badge stat tile: colored circle + icon, big number, label
    underneath — matches the admin-dashboard reference image.
    `icon_key` looks up STAT_TILE_STYLE by label if not given.
    """
    style = STAT_TILE_STYLE.get(icon_key or label, {"icon": "\u2022", "color": COLORS["accent"]})

    tile = card(parent, width=180, height=110)
    tile.pack_propagate(False)

    top_row = ctk.CTkFrame(tile, fg_color="transparent")
    top_row.pack(fill="x", padx=14, pady=(14, 0))

    badge = ctk.CTkFrame(
        top_row, width=34, height=34, corner_radius=17, fg_color=style["color"]
    )
    badge.pack(side="left")
    badge.pack_propagate(False)
    ctk.CTkLabel(badge, text=style["icon"], font=FONTS["body"], text_color=COLORS["white"]).pack(
        expand=True
    )

    ctk.CTkLabel(
        tile, text=str(value), font=FONTS["stat_number"], text_color=COLORS["text_primary"]
    ).pack(anchor="w", padx=14, pady=(6, 0))
    ctk.CTkLabel(
        tile, text=label, font=FONTS["small"], text_color=COLORS["text_secondary"]
    ).pack(anchor="w", padx=14, pady=(0, 12))

    return tile


def flight_result_row(parent, flight, on_select):
    """One row in the search-results list: airline, times, price, select button."""
    row = card(parent)
    row.pack(fill="x", pady=6)

    left = ctk.CTkFrame(row, fg_color="transparent")
    left.pack(side="left", fill="x", expand=True, padx=16, pady=12)

    ctk.CTkLabel(
        left, text=flight["airline"], font=FONTS["body_bold"], text_color=COLORS["text_primary"]
    ).pack(anchor="w")
    ctk.CTkLabel(
        left,
        text=f"{flight['origin']} \u2192 {flight['destination']}   "
             f"{flight['depart_time']} - {flight['arrival_time']}",
        font=FONTS["small"], text_color=COLORS["text_secondary"],
    ).pack(anchor="w", pady=(2, 0))
    seats_left = flight["seats_available"]
    seat_color = COLORS["error"] if seats_left <= 5 else COLORS["text_muted"]
    ctk.CTkLabel(
        left, text=f"{seats_left} seats left", font=FONTS["small"], text_color=seat_color
    ).pack(anchor="w", pady=(2, 0))

    right = ctk.CTkFrame(row, fg_color="transparent")
    right.pack(side="right", padx=16, pady=12)
    ctk.CTkLabel(
        right, text=f"${flight['price']:,.0f}", font=FONTS["h3"], text_color=COLORS["accent"]
    ).pack()
    ctk.CTkButton(
        right, text="Select", width=90, height=32, corner_radius=RADIUS["button"],
        fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
        text_color=COLORS["white"], font=FONTS["small"],
        command=lambda: on_select(flight),
        state="normal" if seats_left > 0 else "disabled",
    ).pack(pady=(6, 0))

    return row


def seat_button(parent, seat_label, taken, selected, on_click):
    if taken:
        fg, hover, state = COLORS["bg_panel_light"], COLORS["bg_panel_light"], "disabled"
        text_color = COLORS["text_muted"]
    elif selected:
        fg, hover, state = COLORS["accent"], COLORS["accent"], "normal"
        text_color = COLORS["white"]
    else:
        fg, hover, state = COLORS["bg_input"], COLORS["accent_soft"], "normal"
        text_color = COLORS["text_primary"]

    return ctk.CTkButton(
        parent, text=seat_label, width=44, height=40, corner_radius=RADIUS["input"],
        fg_color=fg, hover_color=hover, text_color=text_color, state=state,
        font=FONTS["small"], command=lambda: on_click(seat_label),
    )
