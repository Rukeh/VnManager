import json
import os
import tkinter
import copy
import re

import customtkinter
from PIL import Image, ImageEnhance

from app.ui.search_window import open_search_window
from app.ui.vn_detail import open_vn_detail
from app.utils.image import load_image_from_url, submit_image_task, async_load_with_hover
from app.utils.text import clean_description
from app.ui.theme import *
from app.ui.components import render_tags, enable_touchpad_scroll

########## SHOULD CONSIDER REORGANISING THE ENTIRE FILE STRUCTURE BECAUSE ITS BECOMING HARD TO FIND WHAT YOU WANT IN THIS FILE !!!!!! :((((((((

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SAVE_FILE = os.path.join(_BASE_DIR, "data", "save.json")
_LOGO_PATH = os.path.join(_BASE_DIR, "assets", "logo.png")

_DEFAULT_DATA = {"categories": ["Not finished", "Finished", "Planned"], "vns": {}, "settings": {"allow_suggestive": False, "allow_explicit": False}}


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
    sort_var = tkinter.StringVar(value="Date added")

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
    right_panel = customtkinter.CTkFrame(master=layout, corner_radius=0, fg_color=BG)
    right_panel.pack(side="right", fill="both", pady=5, padx=5, expand=True)

    panel_header = customtkinter.CTkFrame(right_panel, fg_color=BG, corner_radius=0, height=52)
    panel_header.pack(fill="x", padx=20, pady=(14, 0))
    panel_header.pack_propagate(False)
    
    right_title = customtkinter.CTkLabel(
        panel_header,
        text="Select a category",
        font=FONT_H1,
        text_color=TEXT,
        anchor="w"
    )
    right_title.pack(side="left", padx=10, pady=(12, 6))

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
        corner_radius=10,
        width=140,
        command=lambda _: refresh_right_panel(),
    ).pack(side="right", pady=(12, 6))

    vns_scroll = customtkinter.CTkScrollableFrame(right_panel, fg_color="transparent", scrollbar_button_color=PINK_MID)
    vns_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    #maths

    def _card_wraplength() -> int:
        return max(120, (right_panel.winfo_width() // 2) - 160)
    
    def _sort_vns(vns: list) -> list:
        sort = sort_var.get()
        if sort == "Title (A-Z)":
            return sorted(vns, key=lambda v: v["title"].lower())
        elif sort == "Rating":
            return sorted(vns, key=lambda v: v.get("rating") or 0, reverse=True)
        elif sort == "Release date":
            return sorted(vns, key=lambda v: v.get("released") or "", reverse=True)
        elif sort == "Length":
            return sorted(vns, key=lambda v: v.get("length") or 0, reverse=True)
        return vns  # Date added — preserve list order

    # Renders for the vn panel

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
        vns = _sort_vns(vns)

        if not vns:
            customtkinter.CTkLabel(
                vns_scroll,
                text="No VNs in this category yet\nSearch for one and add it" if not query else "No VNs match your search.",
                font=("Arial", 13),
                text_color="gray",
            ).pack(pady=40)
            return

        vns_scroll.columnconfigure(0, weight=1, uniform="col")
        vns_scroll.columnconfigure(1, weight=1, uniform="col")

        for idx, vn in enumerate(vns):
            row, col = divmod(idx, 2)
            year = (vn.get("released") or "?")[:4]
            img_url = (vn.get("image") or {}).get("url", "")
            rating = vn.get("rating")

            card = customtkinter.CTkFrame(vns_scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=16)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            top_row = customtkinter.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(12, 0)) 

            cover_frame = customtkinter.CTkFrame(top_row, width=90, height=120, fg_color=PINK_LIGHT, corner_radius=10, cursor="hand2")
            cover_frame.pack(side="left", padx=(0, 10))
            cover_frame.pack_propagate(False)

            img_label = customtkinter.CTkLabel(cover_frame, text="🌸", font=("Nunito", 24), cursor="hand2", fg_color="transparent")
            img_label.place(relx=0.5, rely=0.5, anchor="center")

            _images = {"normal": None, "dimmed": None}

            if img_url:
                submit_image_task(async_load_with_hover, img_label, img_url, (90, 120), _images)

            def on_enter(_e, lbl=img_label, imgs=_images, cf=cover_frame):
                cf.configure(fg_color="#c9a0b4")
                if imgs["dimmed"]:
                    lbl.configure(image=imgs["dimmed"])
            def on_leave(_e, lbl=img_label, imgs=_images, cf=cover_frame):
                cf.configure(fg_color=PINK_LIGHT)
                if imgs["normal"]:
                    lbl.configure(image=imgs["normal"])

            for widget in (cover_frame, img_label):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", lambda _e, v=vn: open_vn_detail(app, v))
            btn_col = customtkinter.CTkFrame(top_row, fg_color="transparent")
            btn_col.pack(side="right", anchor="n", padx=(4, 0))

            customtkinter.CTkButton(
                btn_col, text="✕", width=26, height=26,
                fg_color=PINK_LIGHT, hover_color=PINK,
                text_color=PINK_DARK, font=("Nunito", 12, "bold"),
                corner_radius=13,
                command=lambda v=vn: remove_vn(cat, v),
            ).pack(pady=(0, 4))

            customtkinter.CTkButton(
                btn_col, text="↪", width=26, height=26,
                fg_color=PINK_LIGHT, hover_color=PINK,
                text_color=PINK_DARK, font=("Nunito", 12, "bold"),
                corner_radius=13,
                command=lambda v=vn: move_vn(cat, v),
            ).pack()

            text_frame = customtkinter.CTkFrame(top_row, fg_color="transparent")
            text_frame.pack(side="left", fill="y", expand=False)

            title_lbl = customtkinter.CTkLabel(
                text_frame,
                text=f"{vn['title']}",
                font=FONT_H2,
                text_color=TEXT,
                anchor="w",
                wraplength=_card_wraplength(),
                cursor="hand2",
            )
            title_lbl.pack(fill="x")
            title_lbl.bind("<Button-1>", lambda _e, v=vn: open_vn_detail(app, v))

            def _update_wraplength(lbl=title_lbl):
                w = text_frame.winfo_width()
                if w > 10:
                    lbl.configure(wraplength=w - 8)
                else:
                    lbl.configure(wraplength=_card_wraplength())

            title_lbl.bind("<Configure>", lambda e, lbl=title_lbl: _update_wraplength(lbl))

            customtkinter.CTkLabel(text_frame, text=year, text_color=TEXT_MUTED, font=FONT_SMALL, anchor='w').pack(fill="x")

            if rating:
                rating_frame = customtkinter.CTkFrame(text_frame, fg_color=PINK_LIGHT, corner_radius=20)
                rating_frame.pack(anchor='w', pady=(4,0))
                customtkinter.CTkLabel(rating_frame, text=f"★ {rating/10:.2f}", font=('Nunito', 11, "bold"), text_color=PINK_DARK).pack(padx=8, pady=2)    
            render_tags(text_frame, vn, max_tags=5)     

            customtkinter.CTkLabel(
                card,
                text=clean_description(vn.get("description"), 500),
                font=FONT_SMALL,
                text_color=TEXT_MUTED,
                anchor="w",
                wraplength=_card_wraplength(),
                justify="left"
            ).pack(fill="x", padx=12, pady=(8, 4))

            # Notes section
            notes_bar = customtkinter.CTkFrame(card, fg_color=PINK_SOFT, corner_radius=8)
            notes_bar.pack(fill="x", padx=12, pady=(0, 10))

            note_text = vn.get("notes", "").strip()
            note_preview = (note_text[:60] + "…") if len(note_text) > 60 else note_text
            notes_label = customtkinter.CTkLabel(
                notes_bar,
                text=f"📝  {note_preview}" if note_text else "📝  Add a note...",
                font=FONT_SMALL,
                text_color=TEXT if note_text else TEXT_MUTED,
                anchor="w",
                wraplength=0,
                justify="left",
                cursor="hand2",
            )
            notes_label.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)
            notes_label.bind("<Button-1>", lambda _e, v=vn, lbl=notes_label: open_notes_popup(cat, v, lbl))

    search_var.trace_add("write", lambda *_: refresh_right_panel())

    _resize_job_main = [None]
    _last_window_size = [0, 0]

    enable_touchpad_scroll(app, categories_scroll, vns_scroll)

    def _on_main_resize(event):
        if event.widget != app:
            return
        new_size = [event.width, event.height]
        if new_size == _last_window_size:
            return
        _last_window_size[:] = new_size
        if _resize_job_main[0]:
            app.after_cancel(_resize_job_main[0])
        _resize_job_main[0] = app.after(200, refresh_right_panel)

    app.bind("<Configure>", _on_main_resize)

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

    def open_notes_popup(category: str, vn: dict, notes_label) -> None:
        """
        Opens a small popup to edit the personal note for a VN in a category.
        Saves the note back into the VN dict and updates the label in-place.
        Args:
            category:    The category the VN belongs to.
            vn:          The VN dict to attach the note to.
            notes_label: The CTkLabel on the card to update after saving.
        """
        popup = customtkinter.CTkToplevel(app)
        popup.title("Note")
        popup.geometry("1200x800")
        popup.configure(fg_color=BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(
            popup,
            text=f"📝  Note for {vn['title']}",
            font=FONT_TITLE,
            text_color=TEXT,
            wraplength=320,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        text_box = customtkinter.CTkTextbox(
            popup,
            height=600,
            font=FONT_BODY,
            fg_color=PINK_SOFT,
            border_color=BORDER,
            border_width=1,
            text_color=TEXT,
            corner_radius=8,
        )
        text_box.pack(fill="x", padx=16)
        text_box.insert("0.0", vn.get("notes", ""))
        text_box.focus_set()

        def confirm():
            note = text_box.get("0.0", "end").strip()
            vn["notes"] = note
            save_data(data)
            if notes_label.winfo_exists():
                note_preview = (note[:60] + "…") if len(note) > 60 else note
                notes_label.configure(
                    text=f"📝  {note_preview}" if note else "📝  Add a note...",
                    text_color=TEXT if note else TEXT_MUTED,
                )
            popup.destroy()

        btn_row = customtkinter.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=12)
        customtkinter.CTkButton(btn_row, text="Cancel", width=80, fg_color=PINK_LIGHT, hover_color=PINK_MID, text_color=PINK_DARK, font=FONT_TITLE, corner_radius=20, command=popup.destroy).pack(side="left", padx=6)
        customtkinter.CTkButton(btn_row, text="Save", width=80, fg_color=PINK, hover_color=PINK_DARK, text_color="#fff", font=FONT_TITLE, corner_radius=20, command=confirm).pack(side="left", padx=6)

        popup.bind("<Escape>", lambda _e: popup.destroy())

    def move_vn(category: str, vn: dict) -> None:
        other_cats = [c for c in data["categories"] if c != category]
        if not other_cats:
            popup = customtkinter.CTkToplevel(app)
            popup.title("Error")
            popup.geometry("400x125")
            popup.configure(fg_color=BG)
            popup.resizable(False,False)
            popup.after(50, lambda: popup.lift())
            popup.after(50, lambda: popup.focus_force())

            customtkinter.CTkLabel(
                popup,
                text="You can't move a vn to another category if you don't have any other categories !",
                font=("Nunito", 16, "bold"),
                text_color=TEXT,
                wraplength=350
                ).pack(pady=(20, 8))

            customtkinter.CTkButton(
                popup,
                text="OK",
                width=100,
                fg_color=PINK,
                hover_color=PINK_DARK,
                text_color="#fff",
                font=FONT_TITLE,
                corner_radius=20,
                command=popup.destroy
            ).pack(side='bottom', pady=12)

        else:
            popup = customtkinter.CTkToplevel(app)
            popup.title("Move to category")
            popup.geometry("350x170")
            popup.configure(fg_color=BG)
            popup.resizable(False, False)
            popup.after(50, lambda: popup.lift())
            popup.after(50, lambda: popup.focus_force())

            customtkinter.CTkLabel(
                popup,
                text=f'Move "{vn["title"]}" to:',
                font=FONT_TITLE,
                text_color=TEXT,
                wraplength=260
            ).pack(pady=(20, 8))

            var = tkinter.StringVar(value=other_cats[0])
            customtkinter.CTkOptionMenu(
                popup,
                values=other_cats,
                variable=var,
                fg_color=PINK_LIGHT,
                button_color=PINK,
                button_hover_color=PINK_DARK,
                text_color=PINK_DARK,
                font=("Nunito", 12, "bold"),
                dropdown_fg_color=CARD_BG,
                corner_radius=10,
            ).pack(padx=20, fill="x")

            def confirm():
                dest = var.get()
                data["vns"][category] = [v for v in data["vns"].get(category, []) if v["id"] != vn["id"]]
                vns_in_dest = data["vns"].setdefault(dest, [])
                if not any(v["id"] == vn["id"] for v in vns_in_dest):
                    vns_in_dest.append(vn)
                save_data(data)
                refresh_right_panel()
                refresh_categories()
                popup.destroy()

            customtkinter.CTkButton(
                popup,
                text="Move",
                width=100,
                fg_color=PINK,
                hover_color=PINK_DARK,
                text_color="#fff",
                font=FONT_TITLE,
                corner_radius=20,
                command=confirm,
            ).pack(pady=12)

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

    def rename_category(oldname: str, newname: str):
        newname = newname.strip()
        if not newname or newname == oldname or newname in data['categories']:
            refresh_categories()
            return
        
        index = data["categories"].index(oldname)
        data["categories"][index] = newname

        if oldname in data["vns"]:
            data['vns'][newname] = data["vns"].pop(oldname)

        if selected_category[0] == oldname:
            selected_category[0] = newname
            right_title.configure(text=newname)
        
        save_data(data)
        refresh_categories()

    def start_rename(category: str, row_frame) -> None:
        for widget in row_frame.winfo_children():
            widget.destroy()
        
        entry = customtkinter.CTkEntry(
            row_frame,
            font=("Nunito", 13, "bold"),
            fg_color=PINK_LIGHT,
            border_color=PINK,
            text_color=PINK_DARK,
        )
        entry.insert(0, category)
        entry.select_range(0, "end")
        entry.pack(fill="x", expand=True, padx=6, pady=4)
        entry.focus_set()
        
        entry.bind("<Return>", lambda e: rename_category(category, entry.get()))
        entry.bind("<FocusOut>", lambda e: rename_category(category, entry.get()))
        entry.bind("<Escape>", lambda e: refresh_categories())

    def _popup_rename(category: str) -> None:
        """
        Shows a popup dialog to rename a category.
        Args:
            category: The current category name to rename.
        """
        popup = customtkinter.CTkToplevel(app)
        popup.title("Rename category")
        popup.geometry("300x130")
        popup.configure(fg_color=SIDEBAR_BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(
            popup,
            text=f'Rename "{category}" to:',
            font=FONT_TITLE,
            text_color=TEXT,
            wraplength=260,
        ).pack(pady=(16, 8))

        entry = customtkinter.CTkEntry(
            popup,
            font=FONT_BODY,
            fg_color=PINK_SOFT,
            border_color=PINK,
            text_color=TEXT,
        )
        entry.insert(0, category)
        entry.select_range(0, "end")
        entry.pack(fill="x", padx=20)
        entry.focus_set()

        def confirm():
            rename_category(category, entry.get())
            popup.destroy()

        entry.bind("<Return>", lambda _e: confirm())
        entry.bind("<Escape>", lambda _e: popup.destroy())

        customtkinter.CTkButton(
            popup,
            text="Rename",
            width=100,
            fg_color=PINK,
            hover_color=PINK_DARK,
            text_color="#fff",
            font=FONT_TITLE,
            corner_radius=20,
            command=confirm,
        ).pack(pady=12)

    def refresh_categories() -> None:
        """
        Re-renders the category list in the left panel.
        Each category gets a select button, a rename button, and a delete button.
        """        
        for widget in categories_scroll.winfo_children():
            widget.destroy()
        
        for category in data["categories"]:
            is_active = (category == selected_category[0])
            count = len(data["vns"].get(category, []))
                        
            row_frame = customtkinter.CTkFrame(categories_scroll, fg_color=PINK_LIGHT if is_active else 'transparent', corner_radius=10)
            row_frame.pack(fill="x", pady=2)

            customtkinter.CTkButton(
                master=row_frame,
                text="✕",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color=PINK_MID,
                text_color="#cc4444",
                command=lambda c=category: delete_category(c),
            ).pack(side="right", padx=(2, 4))

            customtkinter.CTkButton(
                master=row_frame,
                text="🖍",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color=PINK_MID,
                text_color=TEXT_MUTED,
                command=lambda c=category: _popup_rename(c),
            ).pack(side="right", padx=(0, 2))

            #badge that shows the number of vns in the category
            badge = customtkinter.CTkFrame(
            row_frame,
            fg_color=PINK if is_active else PINK_LIGHT,
            corner_radius=20, width=28, height=20,
            )
            badge.pack(side="right", padx=(0, 2))
            badge.pack_propagate(False)
            customtkinter.CTkLabel(
                badge, text=str(count),
                font=("Nunito", 10, "bold"),
                text_color="#fff" if is_active else PINK_DARK,
            ).place(relx=0.5, rely=0.5, anchor="center")
            
            if is_active:
                customtkinter.CTkFrame(
                    row_frame, width=3, fg_color=PINK, corner_radius=2,
                ).pack(side="left", fill="y", padx=(4, 0), pady=4)

            button_rename = customtkinter.CTkButton(
                row_frame, text=category, anchor="w",
                font=("Nunito", 13, "bold") if is_active else ("Nunito", 13),
                fg_color="transparent", hover_color=PINK_MID,
                text_color=PINK_DARK if is_active else TEXT,
                command=lambda c=category: select_category(c),
            )
            button_rename.pack(side="left", fill="x", expand=True)
            button_rename.bind("<Double-Button-1>", lambda e, c=category, f=row_frame: start_rename(c, f))

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
        popup.configure(fg_color=SIDEBAR_BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(
            popup,
            text=f'Delete "{name}"?\nAll VNs in it will be removed.',
            font= FONT_TITLE,
            text_color=TEXT,
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

        customtkinter.CTkButton(btn_frame, text="Cancel", width=80, text_color='#fff', fg_color=PINK_MID, hover_color='#f7b2d9', command=popup.destroy).pack(side="left", padx=8)
        customtkinter.CTkButton(btn_frame, text="Delete", width=80, text_color='#fff', fg_color='#db6098', hover_color="#d41167", command=confirm).pack(side="left", padx=8)

    refresh_categories()
    app.mainloop()