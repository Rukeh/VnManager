import customtkinter
from app.ui.shared.theme import *
from app.ui.shared.components import set_low_perf_mode
from app.utils.save import save_data


def build_settings(parent, data: dict) -> None:
    """
    Renders the settings panel into parent.
    Args:
        parent: The CTkFrame to render into.
        data:   The full application state dict (used to persist settings).
    """
    settings = data.setdefault("settings", {})

    header = customtkinter.CTkFrame(parent, fg_color=BG, corner_radius=0, height=52)
    header.pack(fill="x", padx=20, pady=(14, 0))
    header.pack_propagate(False)
    customtkinter.CTkLabel(
        header, text="Settings",
        font=FONT_H1, text_color=TEXT, anchor="w",
    ).pack(side="left", padx=10, pady=(12, 6))

    scroll = customtkinter.CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=PINK_MID)
    scroll.pack(fill="both", expand=True, padx=16, pady=(8, 16))

    #for performance (may work may not idk help me optimize this shit)
    customtkinter.CTkLabel(
        scroll, text="PERFORMANCE",
        font=("Nunito", 10, "bold"), text_color=TEXT_MUTED, anchor="w",
    ).pack(anchor="w", padx=4, pady=(8, 4))

    perf_card = customtkinter.CTkFrame(scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
    perf_card.pack(fill="x", pady=(0, 8))

    row = customtkinter.CTkFrame(perf_card, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=14)

    text_col = customtkinter.CTkFrame(row, fg_color="transparent")
    text_col.pack(side="left", fill="x", expand=True)
    customtkinter.CTkLabel(
        text_col, text="Low Performance Mode",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(anchor="w")
    customtkinter.CTkLabel(
        text_col,
        text="Replaces tag chips with plain text. Reduces widget count\nper card — helps on low-end hardware.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w", justify="left",
    ).pack(anchor="w", pady=(2, 0))

    def _toggle(val):
        enabled = switch_var.get() == 1
        settings["low_perf_mode"] = enabled
        set_low_perf_mode(enabled)
        save_data(data)

    switch_var = customtkinter.IntVar(value=1 if settings.get("low_perf_mode", False) else 0)
    customtkinter.CTkSwitch(
        row,
        text="",
        variable=switch_var,
        onvalue=1, offvalue=0,
        progress_color=PINK,
        button_color=PINK_DARK,
        button_hover_color=PINK_DARK,
        command=lambda: _toggle(switch_var.get()),
    ).pack(side="right", padx=(16, 0))