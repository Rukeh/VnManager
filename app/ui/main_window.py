import json
import os

import customtkinter
from PIL import Image

from app.ui.search_window import open_search_window
from app.utils.image import load_image_from_url, _executor
from app.utils.text import clean_description

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SAVE_FILE = os.path.join(_BASE_DIR, "data", "save.json")
_LOGO_PATH = os.path.join(_BASE_DIR, "assets", "logo.png")

_DEFAULT_DATA = {"categories": ["Not finished", "Finished", "Planned"], "vns": {}}

def load_data() -> dict:
    """
    Loads save data from ../data/save.json , returning defaults values if the file is missing. (eg : first-time users with no save file yet)
    """
    try:
        with open(_SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return _DEFAULT_DATA.copy()


def save_data(data: dict) -> None:
    """
    Saves data to the save file
    """
    os.makedirs(os.path.dirname(_SAVE_FILE), exist_ok=True)
    with open(_SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run() -> None:
    """
    Builds and starts the main application window
    """
    app = customtkinter.CTk()
    app.geometry("1280x720")
    app.title("VnManager")

    data = load_data()

    selected_category = [None]

    search_bar_frame = customtkinter.CTkFrame(
        master=app, width=800, height=30,
        border_width=2, corner_radius=15, fg_color="#303030",
    )
    left_panel = customtkinter.CTkFrame(master=app, width=230, border_width=2, corner_radius=8)
    right_panel = customtkinter.CTkFrame(master=app, border_width=2, corner_radius=8, fg_color="#1c1d1f")

    if os.path.exists(_LOGO_PATH):
        logo_image = customtkinter.CTkImage(light_image=Image.open(_LOGO_PATH), size=(30, 30))
        customtkinter.CTkLabel(master=app, image=logo_image, text="").place(x=108, y=5)

    # Left panel (Categories)

    category_entry = customtkinter.CTkEntry(left_panel, placeholder_text="New category...")
    category_entry.pack(padx=8, pady=(10, 4), fill="x")

    categories_scroll = customtkinter.CTkScrollableFrame(left_panel)
    categories_scroll.pack(fill="both", expand=True, padx=4, pady=4)

    right_title = customtkinter.CTkLabel(
        right_panel,
        text="Select a category",
        font=("Arial", 18, "bold"),
        anchor="center",
    )
    right_title.pack(fill="x", padx=10, pady=(12, 6))

    customtkinter.CTkButton(
        right_panel,
        text="Search VN",
        command=lambda: open_search_window(app, data, on_vn_added=refresh_right_panel),
    ).pack(pady=(0, 8), fill="x", padx=8)

    vns_scroll = customtkinter.CTkScrollableFrame(right_panel, fg_color="transparent")
    vns_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    # Renders for the vn panel

    def _async_load_image(label, url, size):
        img = load_image_from_url(url, size=size)
        if img:
            def _apply():
                if label.winfo_exists():
                    label.configure(image=img)
                    label.image = img
            label.after(0, _apply)


    def refresh_right_panel() -> None:
        """
        Re-renders the VN list for the currently selected category
        """
        for widget in vns_scroll.winfo_children():
            widget.destroy()

        cat = selected_category[0]
        if cat is None:
            return

        right_title.configure(text=cat)
        vns = data["vns"].get(cat, [])

        if not vns:
            customtkinter.CTkLabel(
                vns_scroll,
                text="No VNs in this category yet\nSearch for one and add it",
                font=("Arial", 13),
                text_color="gray",
            ).pack(pady=40)
            return

        for vn in vns:
            year = (vn.get("released") or "?")[:4]
            img_url = (vn.get("image") or {}).get("url", "")

            card = customtkinter.CTkFrame(vns_scroll)
            card.pack(fill="x", pady=4, padx=4)

            img_label = customtkinter.CTkLabel(card, text="", width=90, height=120)
            img_label.pack(side="left", padx=(8, 0), pady=8)
            if img_url:
                _executor.submit(_async_load_image, img_label, img_url, (150, 200))

            text_frame = customtkinter.CTkFrame(card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            customtkinter.CTkLabel(
                text_frame,
                text=f"{vn['title']} ({year})",
                font=("Arial", 15, "bold"),
                anchor="w",
                wraplength=500,
            ).pack(fill="x")

            customtkinter.CTkLabel(
                text_frame,
                text=clean_description(vn.get("description")),
                font=("Arial", 12),
                anchor="w",
                wraplength=500,
                justify="left",
                text_color="gray",
            ).pack(fill="x", pady=(4, 0))

            customtkinter.CTkButton(
                card,
                text="✕",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color="#5a2020",
                text_color="#cc4444",
                command=lambda v=vn: remove_vn(cat, v),
            ).pack(side="right", anchor="n", padx=(0, 6), pady=6)

    def remove_vn(category: str, vn: dict) -> None:
        data["vns"][category] = [v for v in data["vns"].get(category, []) if v["id"] != vn["id"]]
        save_data(data)
        refresh_right_panel()

    def select_category(name: str) -> None:
        selected_category[0] = name
        refresh_right_panel()

    # Left panel

    def refresh_categories() -> None:
        for widget in categories_scroll.winfo_children():
            widget.destroy()
        for category in data["categories"]:
            row_frame = customtkinter.CTkFrame(categories_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            customtkinter.CTkButton(
                master=row_frame,
                text=category,
                anchor="w",
                fg_color="transparent",
                hover_color="#3a3a3a",
                command=lambda c=category: select_category(c)
            ).pack(side="left", fill="x", expand=True, padx=(8, 0))

            customtkinter.CTkButton(
                master=row_frame,
                text="✕",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color="#5a2020",
                text_color="#cc4444",
                command=lambda c=category: delete_category(c),
            ).pack(side="right", padx=(2, 4))

    def add_category() -> None:
        """
        Adds a category,
        fetches the name from the entry attached to it
        -> attach to a button
        Stores it inside save data and refreshes categories to display the changes
        """
        name = category_entry.get().strip()
        if not name or name in data["categories"]:
            return
        data["categories"].append(name)
        save_data(data)
        category_entry.delete(0, "end")
        refresh_categories()

    customtkinter.CTkButton(
        left_panel, text="+ Add", width=60, command=add_category,
    ).pack(padx=8, pady=(0, 8), fill="x")

    def delete_category(name) -> None:
        """
        Delete a category
        This function is called by a button
        The button role is to store the name of the category then send it to this function
        """
        if name in data['categories']:
            data['categories'].remove(name)
            data['vns'].pop(name, None)
            save_data(data)
            if selected_category[0] == name:
                selected_category[0] = None
                right_title.configure(text="Select a category")
                for widget in vns_scroll.winfo_children():
                    widget.destroy()
            refresh_categories()

    search_bar_frame.pack(pady=3, fill="x", padx=(245, 5))
    left_panel.pack(side="left", fill="y", padx=5, pady=5)
    right_panel.pack(side="right", fill="both", pady=5, padx=5, expand=True)

    refresh_categories()
    app.mainloop()