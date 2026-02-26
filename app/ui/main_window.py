import json
import os
import tkinter
import copy

import customtkinter
from PIL import Image

from app.ui.search_window import open_search_window
from app.utils.image import load_image_from_url, submit_image_task
from app.utils.text import clean_description

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SAVE_FILE = os.path.join(_BASE_DIR, "data", "save.json")
_LOGO_PATH = os.path.join(_BASE_DIR, "assets", "logo.png")

_DEFAULT_DATA = {"categories": ["Not finished", "Finished", "Planned"], "vns": {}}
#Color palette for cute theme 
BG           = "#fff8f9"
SIDEBAR_BG   = "#fff0f3"
CARD_BG      = "#ffffff"
PINK         = "#f472b6"
PINK_LIGHT   = "#fce7f3"
PINK_MID     = "#fbcfe8"
PINK_DARK    = "#db2777"
PINK_SOFT    = "#fdf2f8"
TEXT         = "#3d2535"
TEXT_MUTED   = "#b07090"
BORDER       = "#fad4e8"
TOPBAR_BG    = "#ffffff"

FONT_TITLE  = ("Nunito", 13, "bold")
FONT_BODY   = ("Quicksand", 12)
FONT_SMALL  = ("Quicksand", 11)
FONT_H1     = ("Nunito", 20, "bold")
FONT_H2     = ("Nunito", 15, "bold")
FONT_LOGO   = ("Nunito", 18, "bold")


def load_data() -> dict:
    """
    Loads save data from ../data/save.json , returning defaults values if the file is missing. (eg : first-time users with no save file yet)
    """
    try:
        with open(_SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return copy.deepcopy(_DEFAULT_DATA)


def _show_save_error(message: str) -> None:
    """
    Displays a popup window with an error message when saving fails.
    Args:
        message: The OSError message string to display to the user.
    """
    popup = customtkinter.CTkToplevel()
    popup.title("Save error")
    popup.geometry("340x110")
    popup.after(50, lambda: popup.lift())
    customtkinter.CTkLabel(
        popup,
        text=f"Failed to save data:\n{message}",
        text_color="red",
        wraplength=300,
    ).pack(pady=16)
    customtkinter.CTkButton(popup, text="OK", width=80, command=popup.destroy).pack()

def save_data(data: dict) -> None:
    """
    Saves data to the save file. Creates the data directory if it doesn't exist.
    Shows an error popup if the write fails (e.g. permissions, disk full).
    Args:
        data: The full application state dict containing categories and vns.
    """
    try:
        os.makedirs(os.path.dirname(_SAVE_FILE), exist_ok=True)
        with open(_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        _show_save_error(str(e))

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

    #topbar 
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

    search_bar_frame = customtkinter.CTkFrame(
        topbar, height=34, fg_color=PINK_SOFT,
        border_width=1, border_color=BORDER, corner_radius=20,
    )
    search_bar_frame.pack(side="left", fill="x", expand=True, padx=20, pady=10)
    search_bar_frame.pack_propagate(False)

    customtkinter.CTkLabel(search_bar_frame, text="🔍", font=("Quicksand", 13), text_color=PINK,).pack(side="left", padx=(12, 4))

    search_entry = customtkinter.CTkEntry(
        search_bar_frame,
        placeholder_text="Filter VNs in current category...",
        textvariable=search_var,
        border_width=0,
        fg_color="transparent",
        font=FONT_BODY,
        text_color=TEXT,
        placeholder_text_color=TEXT_MUTED,
    )
    search_entry.pack(fill="x", expand=True, padx=(0, 12), pady=4)
    
    customtkinter.CTkButton(
        topbar,
        text="✦  Search VN",
        font=FONT_TITLE,
        fg_color=PINK,
        hover_color=PINK_DARK,
        text_color="#ffffff",
        corner_radius=20,
        height=34,
        width=130,
        command=lambda: open_search_window(app, data, on_vn_added=refresh_right_panel),
    ).pack(side="right", padx=(0, 16), pady=10)

    #layout of the app

    layout = customtkinter.CTkFrame(app, fg_color=BG, corner_radius=0)
    layout.pack(fill="both", expand=True)

    # Categories sidebar

    sidebar = customtkinter.CTkFrame(
        layout, width=220, fg_color=SIDEBAR_BG,
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

    # New category input at the bottom
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

    category_entry.bind("<Return>", lambda _e: add_category())

    customtkinter.CTkButton(
        new_cat_frame, text="Add", width=46, height=28,
        fg_color=PINK_LIGHT, hover_color=PINK_MID,
        text_color=PINK_DARK, font=("Nunito", 12, "bold"),
        corner_radius=8, command=add_category,
    ).pack(side="right", padx=(0, 6), pady=6)    

    #right panel
    right_panel = customtkinter.CTkFrame(master=layout, border_width=2, corner_radius=8, fg_color="#1c1d1f")
    right_panel.pack(side="right", fill="both", pady=5, padx=5, expand=True)

    right_title = customtkinter.CTkLabel(
        right_panel,
        text="Select a category",
        font=("Arial", 18, "bold"),
        anchor="center",
    )
    right_title.pack(fill="x", padx=10, pady=(12, 6))

    vns_scroll = customtkinter.CTkScrollableFrame(right_panel, fg_color="transparent")
    vns_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    # Renders for the vn panel

    def _async_load_image(label, url, size) :
        """
        Fetches an image from a URL and applies it to a label once loaded.
        Intended to be run in a background thread via submit_image_task.
        Args:
            label: The CTkLabel to update with the loaded image.
            url:   Direct URL to the image.
            size:  (width, height) tuple for the image.
        """
        img = load_image_from_url(url, size=size)
        if img:
            def _apply():
                if label.winfo_exists():
                    label.configure(image=img)
                    label.image = img
            label.after(0, _apply)


    def refresh_right_panel() -> None:
        """
        Re-renders the VN list for the currently selected category.
        Filters results by the current search bar query if one is set.
        Does nothing if no category is selected.
        """
        for widget in vns_scroll.winfo_children():
            widget.destroy()

        cat = selected_category[0]
        if cat is None:
            return

        right_title.configure(text=cat)
        query = search_var.get().strip().lower()
        vns = [
            v for v in data["vns"].get(cat, [])
            if query in v["title"].lower() or query in (v.get("alttitle") or "").lower()
        ]

        if not vns:
            customtkinter.CTkLabel(
                vns_scroll,
                text="No VNs in this category yet\nSearch for one and add it" if not query else "No VNs match your search.",
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
                submit_image_task(_async_load_image, img_label, img_url, (150, 200))

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

    search_var.trace_add("write", lambda *_: refresh_right_panel())

    def remove_vn(category: str, vn: dict) -> None:
        """
        Removes a VN from a category, saves the updated data, and refreshes the panel.
        Args:
            category: The category name to remove the VN from.
            vn:       The VN dict to remove, identified by its id field.
        """        
        data["vns"][category] = [v for v in data["vns"].get(category, []) if v["id"] != vn["id"]]
        save_data(data)
        refresh_right_panel()

    def select_category(name: str) -> None:
        """
        Sets the active category and refreshes the right panel to show its VNs.
        Also clears the search bar when switching categories.
        Args:
            name: The category name to select.
        """        
        selected_category[0] = name
        search_var.set("")
        refresh_right_panel()
        refresh_categories() 

    # Left panel

    def refresh_categories() -> None:
        """
        Re-renders the category list in the left panel.
        Each category gets a select button and a delete button.
        """        
        for widget in categories_scroll.winfo_children():
            widget.destroy()
        
        for category in data["categories"]:
            is_active = (category == selected_category[0])
            
            row_frame = customtkinter.CTkFrame(categories_scroll, fg_color=PINK_LIGHT if is_active else 'transparent', corner_radius=10)
            row_frame.pack(fill="x", pady=2)

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

            if is_active:
                customtkinter.CTkFrame(
                    row_frame, width=3, fg_color=PINK, corner_radius=2,
                ).pack(side="left", fill="y", padx=(4, 0), pady=4)

            customtkinter.CTkButton(
                row_frame, text=category, anchor="w",
                font=("Nunito", 13, "bold") if is_active else ("Nunito", 13),
                fg_color="transparent", hover_color=PINK_MID,
                text_color=PINK_DARK if is_active else TEXT,
                command=lambda c=category: select_category(c),
            ).pack(side="left", fill="x", expand=True)

    def delete_category(name) -> None:
        """
        Asks for confirmation before deleting a category and all its VNs.
        Shows a popup with Cancel and Delete buttons. If confirmed, removes
        the category from data, clears the right panel if it was selected,
        and refreshes the category list.
        Args:
            name: The category name to delete.
        """
        popup = customtkinter.CTkToplevel(app)
        popup.title("Delete category")
        popup.geometry("300x110")
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(
            popup,
            text=f'Delete "{name}"?\nAll VNs in it will be removed.',
            wraplength=260,
        ).pack(pady=14)

        btn_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack()

        def confirm():
            popup.destroy()
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

        customtkinter.CTkButton(btn_frame, text="Cancel", width=80, command=popup.destroy).pack(side="left", padx=8)
        customtkinter.CTkButton(btn_frame, text="Delete", width=80, fg_color="#7a2020", hover_color="#5a1515", command=confirm).pack(side="left", padx=8)

    refresh_categories()
    app.mainloop()