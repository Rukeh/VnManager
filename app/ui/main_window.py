import json
import os

import customtkinter
from PIL import Image

from app.ui.search_window import open_search_window

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SAVE_FILE = os.path.join(_BASE_DIR, "data", "save.json")
_LOGO_PATH = os.path.join(_BASE_DIR, "assets", "logo.png")

_DEFAULT_DATA = {"categories": ["Not finished", "Finished", "Planned"]}


# ── Persistence ───────────────────────────────────────────────────────────────

def load_data() -> dict:
    """Loads save data from disk, returning defaults if the file is missing."""
    try:
        with open(_SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return _DEFAULT_DATA.copy()


def save_data(data: dict) -> None:
    """Persists data to the save file."""
    os.makedirs(os.path.dirname(_SAVE_FILE), exist_ok=True)
    with open(_SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── App ───────────────────────────────────────────────────────────────────────

def run() -> None:
    """Builds and starts the main application window."""
    app = customtkinter.CTk()
    app.geometry("1280x720")
    app.title("VnManager")

    data = load_data()

    # ── Frames ────────────────────────────────────────────────────────────────
    search_bar_frame = customtkinter.CTkFrame(
        master=app, width=800, height=30,
        border_width=2, corner_radius=15, fg_color="#303030",
    )
    left_panel = customtkinter.CTkFrame(master=app, width=230, border_width=2, corner_radius=8)
    right_panel = customtkinter.CTkFrame(master=app, border_width=2, corner_radius=8, fg_color="#1c1d1f")

    # ── Logo ──────────────────────────────────────────────────────────────────
    if os.path.exists(_LOGO_PATH):
        logo_image = customtkinter.CTkImage(light_image=Image.open(_LOGO_PATH), size=(30, 30))
        customtkinter.CTkLabel(master=app, image=logo_image, text="").place(x=90, y=5)

    # ── Left panel: categories ────────────────────────────────────────────────
    category_entry = customtkinter.CTkEntry(left_panel, placeholder_text="New category...")
    category_entry.pack(padx=8, pady=(10, 4), fill="x")

    categories_scroll = customtkinter.CTkScrollableFrame(left_panel)
    categories_scroll.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh_categories() -> None:
        for widget in categories_scroll.winfo_children():
            widget.destroy()
        for category in data["categories"]:
            customtkinter.CTkButton(
                master=categories_scroll,
                text=category,
                anchor="w",
                fg_color="transparent",
                hover_color="#3a3a3a",
            ).pack(fill="x", padx=8, pady=2)

    def add_category() -> None:
        name = category_entry.get().strip()
        if not name:
            return
        data["categories"].append(name)
        save_data(data)
        category_entry.delete(0, "end")
        refresh_categories()

    customtkinter.CTkButton(
        left_panel, text="+ Add", width=60, command=add_category,
    ).pack(padx=8, pady=(0, 8), fill="x")

    # ── Right panel: actions ──────────────────────────────────────────────────
    customtkinter.CTkButton(
        right_panel,
        text="Search VN",
        command=lambda: open_search_window(app),
    ).pack(pady=5, fill="x", padx=5)

    # ── Layout ────────────────────────────────────────────────────────────────
    search_bar_frame.pack(pady=3, fill="x", padx=(245, 5))
    left_panel.pack(side="left", fill="y", padx=5, pady=5)
    right_panel.pack(side="right", fill="both", pady=5, padx=5, expand=True)

    refresh_categories()
    app.mainloop()