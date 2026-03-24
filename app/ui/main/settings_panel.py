import os
import customtkinter
from app.ui.shared.theme import *
from app.ui.shared.components import set_low_perf_mode
from app.utils.image import set_cover_cache_max, set_cache_main_only, _COVER_CACHE_DIR
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

    # ── Performance ───────────────────────────────────────────────────────────
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
        text_col, text="I need faster render !!!",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(anchor="w")
    customtkinter.CTkLabel(
        text_col,
        text="Replaces tag chips with plain text. Reduces widget count\nper card (should help with faster loading, i mean maybe, maybe not i don't know)",
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

    # ── Cover cache ───────────────────────────────────────────────────────────
    customtkinter.CTkLabel(
        scroll, text="COVER CACHE",
        font=("Nunito", 10, "bold"), text_color=TEXT_MUTED, anchor="w",
    ).pack(anchor="w", padx=4, pady=(12, 4))

    cache_card = customtkinter.CTkFrame(scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
    cache_card.pack(fill="x", pady=(0, 8))

    cache_inner = customtkinter.CTkFrame(cache_card, fg_color="transparent")
    cache_inner.pack(fill="x", padx=16, pady=14)

    cache_text_col = customtkinter.CTkFrame(cache_inner, fg_color="transparent")
    cache_text_col.pack(fill="x")

    cache_title_row = customtkinter.CTkFrame(cache_text_col, fg_color="transparent")
    cache_title_row.pack(fill="x")

    customtkinter.CTkLabel(
        cache_title_row, text="Max cached covers",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(side="left")

    current_max = settings.get("cover_cache_max", 500)
    slider_label = customtkinter.CTkLabel(
        cache_title_row,
        text=f"{current_max} images",
        font=("Nunito", 12, "bold"), text_color=PINK_DARK, anchor="e",
    )
    slider_label.pack(side="right")

    customtkinter.CTkLabel(
        cache_text_col,
        text="Oldest covers are deleted automatically when the limit is reached.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w", justify="left",
    ).pack(anchor="w", pady=(2, 8))

    scope_row = customtkinter.CTkFrame(cache_text_col, fg_color="transparent")
    scope_row.pack(fill="x", pady=(0, 8))

    customtkinter.CTkLabel(
        scope_row,
        text="Cache scope",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(side="left")

    scope_button = customtkinter.CTkButton(
        scope_row,
        text="",
        width=170,
        height=28,
        fg_color=PINK_LIGHT,
        hover_color=PINK_MID,
        text_color=PINK_DARK,
        font=("Nunito", 12, "bold"),
        corner_radius=20,
    )
    scope_button.pack(side="right")

    customtkinter.CTkLabel(
        cache_text_col,
        text="Choose whether search results also populate cache.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w", justify="left",
    ).pack(anchor="w", pady=(0, 8))

    def _apply_cache_scope_ui() -> None:
        main_only = bool(settings.get("cache_main_only", False))
        set_cache_main_only(main_only)
        scope_button.configure(
            text="Main window only" if main_only else "All windows",
            fg_color=PINK if main_only else PINK_LIGHT,
            hover_color=PINK_DARK if main_only else PINK_MID,
            text_color=WHITE if main_only else PINK_DARK,
        )

    def _toggle_cache_scope() -> None:
        settings["cache_main_only"] = not bool(settings.get("cache_main_only", False))
        _apply_cache_scope_ui()
        save_data(data)

    scope_button.configure(command=_toggle_cache_scope)

    def _on_slider(val: float) -> None:
        limit = int(val)
        slider_label.configure(text=f"{limit} images")
        settings["cover_cache_max"] = limit
        set_cover_cache_max(limit)
        save_data(data)

    cache_slider = customtkinter.CTkSlider(
        cache_text_col,
        from_=50, to=2000,
        number_of_steps=39,
        command=_on_slider,
        progress_color=PINK,
        button_color=PINK_DARK,
        button_hover_color=PINK_DARK,
    )
    cache_slider.pack(fill="x", pady=(0, 4))

    # Current cache size on disk
    def _get_cache_count() -> int:
        try:
            return len(os.listdir(_COVER_CACHE_DIR))
        except OSError:
            return 0

    count = _get_cache_count()
    cache_info_label = customtkinter.CTkLabel(
        cache_text_col,
        text=f"Currently {count} covers cached on disk.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w",
    )
    cache_info_label.pack(anchor="w", pady=(0, 4))

    def _clear_cache() -> None:
        try:
            for f in os.listdir(_COVER_CACHE_DIR):
                os.remove(os.path.join(_COVER_CACHE_DIR, f))
        except OSError:
            pass
        cache_info_label.configure(text="Currently 0 covers cached on disk.")

    customtkinter.CTkButton(
        cache_text_col,
        text="Clear cache",
        width=120, height=28,
        fg_color=PINK_LIGHT, hover_color=PINK,
        text_color=PINK_DARK, font=("Nunito", 12, "bold"),
        corner_radius=20,
        command=_clear_cache,
    ).pack(anchor="w", pady=(4, 0))

    # Initialise slider to saved value
    saved_max = settings.get("cover_cache_max", 500)
    cache_slider.set(saved_max)
    slider_label.configure(text=f"{int(cache_slider.get())} images")
    set_cover_cache_max(int(cache_slider.get()))
    _apply_cache_scope_ui()
