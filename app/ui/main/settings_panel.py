import os
import sys
import subprocess
import customtkinter
import traceback
from app.ui.shared.theme import *
from app.ui.shared.theme import (
    list_themes,
    get_active_theme_name,
    MIN_FONT_SCALE,
    MAX_FONT_SCALE,
)
from app.ui.shared.components import set_low_perf_mode
from app.utils.image import set_cover_cache_max, set_cache_main_only, _COVER_CACHE_DIR
from app.utils.save import save_data, reset_data


def build_settings(parent, data: dict) -> None:
    """
    Renders the settings panel into parent.
    Args:
        parent: The CTkFrame to render into.
        data:   The full application state dict (used to persist settings).
    """
    settings = data.setdefault("settings", {})
    settings.setdefault("font_scale", 1.0)
    settings.setdefault("high_contrast_mode", False)

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

    theme_card = customtkinter.CTkFrame(scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
    theme_card.pack(fill="x", pady=(0, 8))

    theme_row = customtkinter.CTkFrame(theme_card, fg_color="transparent")
    theme_row.pack(fill="x", padx=16, pady=14)

    theme_text_col = customtkinter.CTkFrame(theme_row, fg_color="transparent")
    theme_text_col.pack(side="left", fill="x", expand=True)
    customtkinter.CTkLabel(
        theme_text_col, text="Theme",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(anchor="w")
    customtkinter.CTkLabel(
        theme_text_col,
        text="Switch app theme instantly from settings.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w", justify="left",
    ).pack(anchor="w", pady=(2, 0))

    available_themes = list(list_themes())
    current_theme = settings.get("theme_name", get_active_theme_name())
    if current_theme not in available_themes:
        current_theme = available_themes[0]
    settings["theme_name"] = current_theme

    restart_confirm_popup = [None]

    def _open_restart_confirm_popup(
        title: str,
        message: str,
        on_confirm,
        on_cancel,
    ) -> None:
        if restart_confirm_popup[0] is not None and restart_confirm_popup[0].winfo_exists():
            restart_confirm_popup[0].destroy()

        popup = customtkinter.CTkToplevel(parent.winfo_toplevel())
        restart_confirm_popup[0] = popup
        popup.title(title)
        popup.geometry("390x140")
        popup.configure(fg_color=SIDEBAR_BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(
            popup,
            text=message,
            font=FONT_TITLE,
            text_color=TEXT,
            wraplength=350,
            justify="center",
        ).pack(pady=(16, 10))

        btn_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack()

        def _cancel_inner() -> None:
            on_cancel()
            popup.destroy()

        def _confirm_inner() -> None:
            on_confirm()
            popup.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

        popup.protocol("WM_DELETE_WINDOW", _cancel_inner)
        customtkinter.CTkButton(
            btn_frame,
            text="Cancel",
            width=95,
            text_color=WHITE,
            fg_color=PINK_MID,
            hover_color=PINK_HOVER_SOFT,
            command=_cancel_inner,
        ).pack(side="left", padx=8)
        customtkinter.CTkButton(
            btn_frame,
            text="Apply",
            width=95,
            text_color=WHITE,
            fg_color=PINK,
            hover_color=PINK_DARK,
            command=_confirm_inner,
        ).pack(side="left", padx=8)

    def _switch_theme(next_theme: str) -> None:
        previous_theme = settings.get("theme_name", available_themes[0])
        if next_theme == previous_theme:
            return

        def _cancel() -> None:
            theme_var.set(previous_theme)

        def _confirm() -> None:
            settings["theme_name"] = next_theme
            save_data(data)

        _open_restart_confirm_popup(
            "Confirm theme change",
            f'Apply "{next_theme.capitalize()}" theme?\nThe app will restart to apply this change.',
            _confirm,
            _cancel,
        )

    theme_var = customtkinter.StringVar(value=settings["theme_name"])
    customtkinter.CTkOptionMenu(
        theme_row,
        variable=theme_var,
        values=available_themes,
        width=170,
        height=30,
        fg_color=PINK_LIGHT,
        button_color=PINK_MID,
        button_hover_color=PINK,
        dropdown_fg_color=CARD_BG,
        dropdown_hover_color=PINK_LIGHT,
        dropdown_text_color=TEXT,
        text_color=PINK_DARK,
        font=("Nunito", 12, "bold"),
        corner_radius=20,
        command=_switch_theme,
    ).pack(side="right")

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

    # ── Accessibility ──────────────────────────────────────────────────────────
    customtkinter.CTkLabel(
        scroll, text="ACCESSIBILITY",
        font=("Nunito", 10, "bold"), text_color=TEXT_MUTED, anchor="w",
    ).pack(anchor="w", padx=4, pady=(12, 4))

    accessibility_card = customtkinter.CTkFrame(scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
    accessibility_card.pack(fill="x", pady=(0, 8))

    accessibility_inner = customtkinter.CTkFrame(accessibility_card, fg_color="transparent")
    accessibility_inner.pack(fill="x", padx=16, pady=14)

    scale_row = customtkinter.CTkFrame(accessibility_inner, fg_color="transparent")
    scale_row.pack(fill="x", pady=(0, 10))

    scale_text_col = customtkinter.CTkFrame(scale_row, fg_color="transparent")
    scale_text_col.pack(side="left", fill="x", expand=True)
    customtkinter.CTkLabel(
        scale_text_col, text="Font scaling",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(anchor="w")
    customtkinter.CTkLabel(
        scale_text_col,
        text="Increase or decrease global font size for readability.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w", justify="left",
    ).pack(anchor="w", pady=(2, 0))

    font_scale_options = [
        round(step / 10.0, 1)
        for step in range(int(MIN_FONT_SCALE * 10), int(MAX_FONT_SCALE * 10) + 1)
    ]
    font_scale_to_label = {value: f"{int(value * 100)}%" for value in font_scale_options}
    label_to_font_scale = {label: value for value, label in font_scale_to_label.items()}

    current_font_scale = round(float(settings.get("font_scale", 1.0)), 1)
    if current_font_scale not in font_scale_options:
        current_font_scale = 1.0
    settings["font_scale"] = current_font_scale

    font_scale_var = customtkinter.StringVar(value=font_scale_to_label[current_font_scale])

    def _switch_font_scale(next_label: str) -> None:
        next_scale = label_to_font_scale[next_label]
        previous_scale = round(float(settings.get("font_scale", 1.0)), 1)
        if next_scale == previous_scale:
            return

        def _cancel() -> None:
            font_scale_var.set(font_scale_to_label[previous_scale])

        def _confirm() -> None:
            settings["font_scale"] = next_scale
            save_data(data)

        _open_restart_confirm_popup(
            "Confirm font scaling",
            f"Apply {int(next_scale * 100)}% font scaling?\nThe app will restart to apply this change.",
            _confirm,
            _cancel,
        )

    customtkinter.CTkOptionMenu(
        scale_row,
        variable=font_scale_var,
        values=[font_scale_to_label[value] for value in font_scale_options],
        width=140,
        height=30,
        fg_color=PINK_LIGHT,
        button_color=PINK_MID,
        button_hover_color=PINK,
        dropdown_fg_color=CARD_BG,
        dropdown_hover_color=PINK_LIGHT,
        dropdown_text_color=TEXT,
        text_color=PINK_DARK,
        font=("Nunito", 12, "bold"),
        corner_radius=20,
        command=_switch_font_scale,
    ).pack(side="right")

    contrast_row = customtkinter.CTkFrame(accessibility_inner, fg_color="transparent")
    contrast_row.pack(fill="x")

    contrast_text_col = customtkinter.CTkFrame(contrast_row, fg_color="transparent")
    contrast_text_col.pack(side="left", fill="x", expand=True)
    customtkinter.CTkLabel(
        contrast_text_col, text="High contrast mode",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(anchor="w")
    customtkinter.CTkLabel(
        contrast_text_col,
        text="Boost text and border contrast for improved readability.",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w", justify="left",
    ).pack(anchor="w", pady=(2, 0))

    high_contrast_var = customtkinter.IntVar(value=1 if settings.get("high_contrast_mode", False) else 0)

    def _toggle_high_contrast() -> None:
        next_enabled = high_contrast_var.get() == 1
        previous_enabled = bool(settings.get("high_contrast_mode", False))
        if next_enabled == previous_enabled:
            return

        def _cancel() -> None:
            high_contrast_var.set(1 if previous_enabled else 0)

        def _confirm() -> None:
            settings["high_contrast_mode"] = next_enabled
            save_data(data)

        _open_restart_confirm_popup(
            "Confirm high contrast",
            f'{"Enable" if next_enabled else "Disable"} high contrast mode?\nThe app will restart to apply this change.',
            _confirm,
            _cancel,
        )

    customtkinter.CTkSwitch(
        contrast_row,
        text="",
        variable=high_contrast_var,
        onvalue=1, offvalue=0,
        progress_color=PINK,
        button_color=PINK_DARK,
        button_hover_color=PINK_DARK,
        command=_toggle_high_contrast,
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
    def _format_size(num_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        size = float(max(0, num_bytes))
        for unit in units:
            if size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return "0 B"

    def _get_cache_stats() -> tuple[int, int]:
        try:
            count = 0
            total_bytes = 0
            for entry in os.scandir(_COVER_CACHE_DIR):
                if entry.is_file(follow_symlinks=False):
                    count += 1
                    try:
                        total_bytes += entry.stat().st_size
                    except OSError:
                        continue
            return count, total_bytes
        except OSError:
            return 0, 0

    count, total_size = _get_cache_stats()
    cache_info_label = customtkinter.CTkLabel(
        cache_text_col,
        text=f"Currently {count} covers cached on disk ({_format_size(total_size)}).",
        font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w",
    )
    cache_info_label.pack(anchor="w", pady=(0, 4))

    def _refresh_cache_info() -> None:
        current_count, current_total_size = _get_cache_stats()
        cache_info_label.configure(
            text=f"Currently {current_count} covers cached on disk ({_format_size(current_total_size)})."
        )

    def _show_cache_error_popup(title: str, message: str) -> None:
        error_popup = customtkinter.CTkToplevel(parent.winfo_toplevel())
        error_popup.title(title)
        error_popup.geometry("360x120")
        error_popup.configure(fg_color=SIDEBAR_BG)
        error_popup.resizable(False, False)
        error_popup.after(50, lambda: error_popup.lift())
        error_popup.after(50, lambda: error_popup.focus_force())

        customtkinter.CTkLabel(
            error_popup,
            text=message,
            font=FONT_SMALL,
            text_color=TEXT_ERROR,
            wraplength=320,
            justify="center",
        ).pack(pady=(16, 10))
        customtkinter.CTkButton(
            error_popup,
            text="OK",
            width=90,
            fg_color=PINK,
            hover_color=PINK_DARK,
            text_color=WHITE,
            command=error_popup.destroy,
        ).pack()

    def _clear_cache() -> None:
        try:
            for f in os.listdir(_COVER_CACHE_DIR):
                file_path = os.path.join(_COVER_CACHE_DIR, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except OSError as e:
            traceback.print_exc()
            _show_cache_error_popup("Cache clear failed", f"Failed to clear cache:\n{e}")
        _refresh_cache_info()

    def _open_cache_folder() -> None:
        try:
            os.makedirs(_COVER_CACHE_DIR, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(_COVER_CACHE_DIR)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", _COVER_CACHE_DIR], check=True)
            else:
                subprocess.run(["xdg-open", _COVER_CACHE_DIR], check=True)
        except (OSError, subprocess.SubprocessError) as e:
            traceback.print_exc()
            _show_cache_error_popup("Open cache folder failed", f"Failed to open cache folder:\n{e}")

    cache_actions_row = customtkinter.CTkFrame(cache_text_col, fg_color="transparent")
    cache_actions_row.pack(anchor="w", pady=(4, 0))

    customtkinter.CTkButton(
        cache_actions_row,
        text="Clear cache",
        width=120, height=28,
        fg_color=PINK_LIGHT, hover_color=PINK,
        text_color=PINK_DARK, font=("Nunito", 12, "bold"),
        corner_radius=20,
        command=_clear_cache,
    ).pack(side="left")

    customtkinter.CTkButton(
        cache_actions_row,
        text="Open cache folder",
        width=160, height=28,
        fg_color=PINK_LIGHT, hover_color=PINK,
        text_color=PINK_DARK, font=("Nunito", 12, "bold"),
        corner_radius=20,
        command=_open_cache_folder,
    ).pack(side="left", padx=(8, 0))

    # Initialise slider to saved value
    saved_max = settings.get("cover_cache_max", 500)
    cache_slider.set(saved_max)
    slider_label.configure(text=f"{int(cache_slider.get())} images")
    set_cover_cache_max(int(cache_slider.get()))
    _apply_cache_scope_ui()

    # ── Danger zone ──────── (SAVE FILE RESET IS HERE) ─────────────────────────────────────────
    customtkinter.CTkLabel(
        scroll, text="DANGER ZONE",
        font=("Nunito", 10, "bold"), text_color=TEXT_MUTED, anchor="w",
    ).pack(anchor="w", padx=4, pady=(12, 4))

    danger_card = customtkinter.CTkFrame(scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
    danger_card.pack(fill="x", pady=(0, 8))

    danger_row = customtkinter.CTkFrame(danger_card, fg_color="transparent")
    danger_row.pack(fill="x", padx=16, pady=14)

    danger_text_col = customtkinter.CTkFrame(danger_row, fg_color="transparent")
    danger_text_col.pack(side="left", fill="x", expand=True)
    customtkinter.CTkLabel(
        danger_text_col,
        text="Reset savefile",
        font=FONT_BODY, text_color=TEXT, anchor="w",
    ).pack(anchor="w")
    customtkinter.CTkLabel(
        danger_text_col,
        text="Deletes all categories, VN entries, notes, and settings.\nThis cannot be undone.",
        font=FONT_SMALL, text_color=TEXT_DANGER, anchor="w", justify="left",
    ).pack(anchor="w", pady=(2, 0))

    def _open_reset_popup() -> None:
        popup = customtkinter.CTkToplevel(parent.winfo_toplevel())
        popup.title("Reset savefile")
        popup.geometry("430x190")
        popup.configure(fg_color=SIDEBAR_BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(
            popup,
            text="WARNING: This will permanently reset your entire savefile.",
            font=FONT_TITLE,
            text_color=TEXT_DANGER,
            wraplength=390,
            justify="center",
        ).pack(pady=(16, 8))

        customtkinter.CTkLabel(
            popup,
            text="All categories, VN entries, notes, and settings will be deleted.\nThe app will restart immediately after reset.",
            font=FONT_SMALL,
            text_color=TEXT,
            wraplength=390,
            justify="center",
        ).pack(pady=(0, 12))

        btn_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack()

        def _confirm_reset() -> None:
            new_data = reset_data()
            data.clear()
            data.update(new_data)
            popup.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

        customtkinter.CTkButton(
            btn_frame,
            text="Cancel",
            width=110,
            text_color=WHITE,
            fg_color=PINK_MID,
            hover_color=PINK_HOVER_SOFT,
            command=popup.destroy,
        ).pack(side="left", padx=8)
        customtkinter.CTkButton(
            btn_frame,
            text="Yes, reset everything",
            width=170,
            text_color=WHITE,
            fg_color=PINK_DANGER,
            hover_color=PINK_DANGER_HOVER,
            command=_confirm_reset,
        ).pack(side="left", padx=8)

    customtkinter.CTkButton(
        danger_row,
        text="Reset savefile",
        width=150, height=30,
        fg_color=PINK_DANGER, hover_color=PINK_DANGER_HOVER,
        text_color=WHITE, font=("Nunito", 12, "bold"),
        corner_radius=20,
        command=_open_reset_popup,
    ).pack(side="right", padx=(16, 0))
