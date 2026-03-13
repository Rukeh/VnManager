import tkinter
import customtkinter

from app.utils.save import load_data
from app.ui.shared.theme import *
from app.ui.shared.components import enable_touchpad_scroll, set_low_perf_mode
from app.ui.main.menu import build_menu
from app.ui.main.categories import build_categories
from app.ui.main.library import build_library
from app.ui.main.settings_panel import build_settings
from app.ui.search.search_window import open_search_window


class AppState:
    def __init__(self, data, selected_category, search_var, sort_var):
        self.data = data
        self.selected_category = selected_category
        self.search_var = search_var
        self.sort_var = sort_var
        self.right_title = None
        self.refresh_categories = None
        self.refresh_library = None


def run() -> None:
    """
    Builds and starts the main application window.
    Initializes all UI panels, loads save data, and enters the Tkinter main loop.
    """
    app = customtkinter.CTk()
    app.geometry("1280x720")
    app.title("VnManager")
    app.configure(fg_color=BG)

    data = load_data()
    selected_category = [None]
    search_var = tkinter.StringVar()
    sort_var = tkinter.StringVar(value="Date added")
    app_state = AppState(data, selected_category, search_var, sort_var)

    set_low_perf_mode(data.get("settings", {}).get("low_perf_mode", False))

    # ── Topbar ────────────────────────────────────────────────────────────────
    topbar = customtkinter.CTkFrame(
        app, height=56, fg_color=TOPBAR_BG,
        border_width=1, border_color=BORDER, corner_radius=0,
    )
    topbar.pack(fill="x", side="top")
    topbar.pack_propagate(False)

    customtkinter.CTkLabel(
        topbar, text="🌸  VnManager",
        font=FONT_LOGO, text_color=PINK_DARK,
    ).pack(side="left", padx=(16, 0))

    back_btn = customtkinter.CTkButton(
        topbar,
        text="← Menu",
        font=FONT_BODY,
        fg_color=PINK_LIGHT,
        hover_color=PINK_MID,
        text_color=PINK_DARK,
        corner_radius=20,
        height=34,
        width=90,
        command=lambda: show_menu(),
    )

    search_vn_btn = customtkinter.CTkButton(
        topbar,
        text="✦  Search VN",
        font=FONT_TITLE,
        fg_color=PINK,
        hover_color=PINK_DARK,
        text_color="#ffffff",
        corner_radius=20,
        height=34,
        width=130,
        command=lambda: open_search_window(
            app, data,
            on_vn_added=lambda: (
                app_state.refresh_library() if app_state.refresh_library else None,
                app_state.refresh_categories() if app_state.refresh_categories else None,
            ),
        ),
    )

    # ── Content frame ─────────────────────────────────────────────────────────
    content = customtkinter.CTkFrame(app, fg_color=BG, corner_radius=0)
    content.pack(fill="both", expand=True)

    # ── Menu frame ────────────────────────────────────────────────────────────
    menu_frame = customtkinter.CTkFrame(content, fg_color=BG, corner_radius=0)
    build_menu(
        menu_frame,
        on_library=lambda: show_library(),
        on_settings=lambda: show_settings(),
    )

    # ── Library frame ─────────────────────────────────────────────────────────
    library_frame = customtkinter.CTkFrame(content, fg_color=BG, corner_radius=0)

    sidebar = customtkinter.CTkFrame(
        library_frame, width=220, fg_color=SIDEBAR_BG,
        border_width=1, border_color=BORDER, corner_radius=0,
    )
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    customtkinter.CTkLabel(
        sidebar, text="MY LIBRARY",
        font=("Nunito", 10, "bold"), text_color=TEXT_MUTED,
    ).pack(anchor="w", padx=16, pady=(14, 4))

    categories_scroll = customtkinter.CTkScrollableFrame(
        sidebar, fg_color="transparent", scrollbar_button_color=PINK_MID,
    )
    categories_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    new_cat_frame = customtkinter.CTkFrame(
        sidebar, fg_color=CARD_BG,
        border_width=1, border_color=PINK_MID, corner_radius=10,
    )
    new_cat_frame.pack(fill="x", padx=8, pady=(0, 10))

    category_entry = customtkinter.CTkEntry(
        new_cat_frame,
        placeholder_text="＋  New category...",
        border_width=0, fg_color="transparent",
        font=FONT_BODY, text_color=PINK_DARK,
        placeholder_text_color=PINK,
    )
    category_entry.pack(side="left", fill="x", expand=True, padx=(10, 4), pady=6)

    refresh_categories, add_category = build_categories(categories_scroll, category_entry, app_state, app)

    customtkinter.CTkButton(
        new_cat_frame, text="Add", width=46, height=28,
        fg_color=PINK_LIGHT, hover_color=PINK_MID,
        text_color=PINK_DARK, font=("Nunito", 12, "bold"),
        corner_radius=8, command=add_category,
    ).pack(side="right", padx=(0, 6), pady=6)

    right_panel = customtkinter.CTkFrame(library_frame, corner_radius=0, fg_color=BG)
    right_panel.pack(side="right", fill="both", pady=5, padx=5, expand=True)

    panel_header = customtkinter.CTkFrame(right_panel, fg_color=BG, corner_radius=0, height=52)
    panel_header.pack(fill="x", padx=20, pady=(14, 0))
    panel_header.pack_propagate(False)

    right_title = customtkinter.CTkLabel(
        panel_header,
        text="Select a category",
        font=FONT_H1,
        text_color=TEXT,
        anchor="w",
    )
    right_title.pack(side="left", padx=10, pady=(12, 6))
    app_state.right_title = right_title

    customtkinter.CTkOptionMenu(
        panel_header,
        values=["Date added", "Title (A-Z)", "Rating", "Release date", "Length"],
        variable=sort_var,
        fg_color=PINK_LIGHT,
        button_color=PINK,
        button_hover_color=PINK_DARK,
        text_color=PINK_DARK,
        font=("Nunito", 12, "bold"),
        dropdown_fg_color=CARD_BG,
        dropdown_text_color=TEXT,
        corner_radius=10,
        width=140,
        command=lambda _: app_state.refresh_library() if app_state.refresh_library else None,
    ).pack(side="right", pady=(12, 6))

    search_bar_frame = customtkinter.CTkFrame(
        right_panel, height=34, fg_color=PINK_SOFT,
        border_width=1, border_color=BORDER, corner_radius=20,
    )
    search_bar_frame.pack(fill="x", padx=20, pady=(6, 4))
    search_bar_frame.pack_propagate(False)

    customtkinter.CTkLabel(search_bar_frame, text="🔍", font=("Quicksand", 13), text_color=PINK).pack(side="left", padx=(12, 4))

    customtkinter.CTkEntry(
        search_bar_frame,
        placeholder_text="Filter VNs in current category...",
        textvariable=search_var,
        border_width=0,
        fg_color="transparent",
        font=FONT_BODY,
        text_color=TEXT,
        placeholder_text_color=TEXT_MUTED,
    ).pack(fill="x", expand=True, padx=(0, 12), pady=4)

    vns_scroll = customtkinter.CTkScrollableFrame(right_panel, fg_color="transparent", scrollbar_button_color=PINK_MID)
    vns_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    build_library(vns_scroll, right_panel, app_state, app)

    # ── Settings frame ────────────────────────────────────────────────────────
    settings_frame = customtkinter.CTkFrame(content, fg_color=BG, corner_radius=0)
    build_settings(settings_frame, data)

    # ── Navigation ────────────────────────────────────────────────────────────
    def show_menu() -> None:
        library_frame.pack_forget()
        settings_frame.pack_forget()
        menu_frame.pack(fill="both", expand=True)
        back_btn.pack_forget()
        search_vn_btn.pack_forget()

    def show_library() -> None:
        menu_frame.pack_forget()
        settings_frame.pack_forget()
        library_frame.pack(fill="both", expand=True)
        back_btn.pack(side="left", padx=(8, 0), pady=10)
        search_vn_btn.pack(side="right", padx=(0, 16), pady=10)

    def show_settings() -> None:
        menu_frame.pack_forget()
        library_frame.pack_forget()
        settings_frame.pack(fill="both", expand=True)
        back_btn.pack(side="left", padx=(8, 0), pady=10)
        search_vn_btn.pack_forget()

    # ── Resize handler ────────────────────────────────────────────────────────
    _resize_job_main = [None]
    _last_window_size = [0, 0]

    def _on_main_resize(event):
        if event.widget != app:
            return
        new_size = [event.width, event.height]
        if new_size == _last_window_size:
            return
        _last_window_size[:] = new_size
        if _resize_job_main[0]:
            app.after_cancel(_resize_job_main[0])
        _resize_job_main[0] = app.after(200, lambda: (
            app_state.refresh_library() if (app_state.refresh_library and library_frame.winfo_ismapped()) else None
        ))

    app.bind("<Configure>", _on_main_resize)

    enable_touchpad_scroll(app, categories_scroll, vns_scroll)

    refresh_categories()
    show_menu()
    app.mainloop()