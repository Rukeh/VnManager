import os

import customtkinter
from PIL import Image
from app.ui.shared.theme import *


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _resolve_icon_path(icon: str) -> str | None:
    candidates = (
        icon,
        os.path.join(os.path.dirname(__file__), icon),
        os.path.join(_PROJECT_ROOT, icon),
    )
    for files in candidates:
        absolute = os.path.abspath(files)
        if os.path.isfile(absolute):
            return absolute
    return None


def _looks_like_image_path(value: str) -> bool:
    lower = value.lower()
    return (
        "/" in value
        or "\\" in value
        or lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".ico"))
    )


def build_menu(parent, on_library, on_settings) -> None:
    """
    Renders the welcome menu screen into parent.
    Args:
        parent:      The CTkFrame to render into (menu_frame from main_window).
        on_library:  Callback to navigate to the library view.
        on_settings: Callback to navigate to the settings view.
    """
    center = customtkinter.CTkFrame(parent, fg_color="transparent")
    center.place(relx=0.5, rely=0.5, anchor="center")

    customtkinter.CTkLabel(
        center, text="🌸  VnManager",
        font=FONT_LOGO, text_color=PINK_DARK,
    ).pack(pady=(0, 6))

    customtkinter.CTkLabel(
        center, text="what would you like to do?",
        font=FONT_BODY, text_color=TEXT_MUTED,
    ).pack(pady=(0, 36))

    cards_row = customtkinter.CTkFrame(center, fg_color="transparent")
    cards_row.pack()

    def _make_card(parent_frame, icon, title, subtitle, callback):
        card = customtkinter.CTkFrame(
            parent_frame, fg_color=CARD_BG,
            border_width=1, border_color=BORDER,
            corner_radius=20, cursor="hand2",
            width=230, height=210,
        )
        card.pack(side="left", padx=16)
        card.pack_propagate(False)

        icon_label = None
        if isinstance(icon, str):
            icon_path = _resolve_icon_path(icon)
            if icon_path is not None:
                try:
                    with Image.open(icon_path) as icon_source:
                        icon_pil = icon_source.copy()
                    card._icon_image = customtkinter.CTkImage(icon_pil, size=(85, 85))
                    icon_label = customtkinter.CTkLabel(card, text="", image=card._icon_image)
                except (FileNotFoundError, OSError):
                    icon_label = None

        if icon_label is None:
            fallback_icon = "X" if isinstance(icon, str) and _looks_like_image_path(icon) else icon
            icon_label = customtkinter.CTkLabel(card, text=str(fallback_icon), font=("Nunito", 48))

        icon_label.pack(pady=(40, 6))
        customtkinter.CTkLabel(card, text=title, font=FONT_H2, text_color=TEXT).pack()
        customtkinter.CTkLabel(card, text=subtitle, font=FONT_SMALL, text_color=TEXT_MUTED, wraplength=180).pack(pady=(4, 0))

        def _on_enter(_e):
            card.configure(border_color=PINK, fg_color=PINK_SOFT)
        def _on_leave(_e):
            card.configure(border_color=BORDER, fg_color=CARD_BG)

        for widget in (card, *card.winfo_children()):
            widget.bind("<Button-1>", lambda _e: callback())
            widget.bind("<Enter>", _on_enter)
            widget.bind("<Leave>", _on_leave)

    _make_card(cards_row, "assets/menu_icons/Library.png", "My Library", "Browse & manage your VNs", on_library)
    _make_card(cards_row, "assets/menu_icons/Settings.png", "Settings", "Performance & preferences", on_settings)
