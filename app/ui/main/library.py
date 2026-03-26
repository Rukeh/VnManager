import tkinter
import customtkinter
from app.ui.shared.theme import *
from app.ui.shared.components import render_tags, logical_width
from app.ui.search.vn_detail import open_vn_detail
from app.utils.image import submit_image_task, async_load_with_hover, cover_size_for_width
from app.utils.text import clean_description
from app.utils.save import save_data


def build_library(vns_scroll, right_panel, app_state, app):
    """
    Wires all library right-panel logic.
    Returns refresh_right_panel.
    Args:
        vns_scroll:  CTkScrollableFrame that holds VN cards.
        right_panel: Parent CTkFrame of the right panel (used for sizing).
        app_state:   Shared AppState instance.
        app:         Root CTk window (used as parent for popups).
    """
    data = app_state.data
    selected_category = app_state.selected_category
    search_var = app_state.search_var
    sort_var = app_state.sort_var

    def _card_wraplength() -> int:
        return max(120, (logical_width(right_panel) // 2) - 160)

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
        return sorted(vns, key=lambda v: v.get("added_at") or 0, reverse=True)

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

        if app_state.right_title:
            app_state.right_title.configure(text=cat)

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

        cover_size = cover_size_for_width(right_panel.winfo_width(), "card")

        for idx, vn in enumerate(vns):
            row, col = divmod(idx, 2)
            year = (vn.get("released") or "?")[:4]
            img_url = (vn.get("image") or {}).get("url", "")
            rating = vn.get("rating")

            card = customtkinter.CTkFrame(vns_scroll, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=16)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            top_row = customtkinter.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(12, 0))

            cover_frame = customtkinter.CTkFrame(top_row, width=cover_size[0], height=cover_size[1], fg_color=PINK_LIGHT, corner_radius=10, cursor="hand2")
            cover_frame.pack(side="left", padx=(0, 10))
            cover_frame.pack_propagate(False)

            img_label = customtkinter.CTkLabel(cover_frame, text="🌸", font=("Nunito", 24), cursor="hand2", fg_color="transparent")
            img_label.place(relx=0.5, rely=0.5, anchor="center")

            _images = {"normal": None, "dimmed": None}

            if img_url:
                submit_image_task(async_load_with_hover, img_label, img_url, cover_size, _images)

            def on_enter(_e, lbl=img_label, imgs=_images, cf=cover_frame):
                cf.configure(fg_color=COVER_HOVER_BG)
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
                command=lambda v=vn, c=cat: remove_vn(c, v),
            ).pack(pady=(0, 4))

            customtkinter.CTkButton(
                btn_col, text="↪", width=26, height=26,
                fg_color=PINK_LIGHT, hover_color=PINK,
                text_color=PINK_DARK, font=("Nunito", 12, "bold"),
                corner_radius=13,
                command=lambda v=vn, c=cat: move_vn(c, v),
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
                w = logical_width(text_frame)
                if w > 10:
                    lbl.configure(wraplength=w - 8)
                else:
                    lbl.configure(wraplength=_card_wraplength())

            title_lbl.bind("<Configure>", lambda e, lbl=title_lbl: _update_wraplength(lbl))

            customtkinter.CTkLabel(text_frame, text=year, text_color=TEXT_MUTED, font=FONT_SMALL, anchor='w').pack(fill="x")

            if rating:
                rating_frame = customtkinter.CTkFrame(text_frame, fg_color=PINK_LIGHT, corner_radius=20)
                rating_frame.pack(anchor='w', pady=(4, 0))
                customtkinter.CTkLabel(rating_frame, text=f"★ {rating/10:.2f}", font=('Nunito', 11, "bold"), text_color=PINK_DARK).pack(padx=8, pady=2)

            render_tags(text_frame, vn, max_tags=5)

            desc_lbl = customtkinter.CTkLabel(
                card,
                text=clean_description(vn.get("description"), 500),
                font=FONT_SMALL,
                text_color=TEXT_MUTED,
                anchor="w",
                wraplength=_card_wraplength(),
                justify="left",
            )
            desc_lbl.pack(fill="x", padx=12, pady=(8, 4))
            desc_lbl.bind("<Configure>", lambda e, lbl=desc_lbl, c=card: lbl.configure(wraplength=max(100, logical_width(c) - 32)))

            # Notes section
            notes_bar = customtkinter.CTkFrame(card, fg_color=PINK_SOFT, corner_radius=8, height=32)
            notes_bar.pack(side="bottom", fill="x", padx=12, pady=(0, 10))
            notes_bar.pack_propagate(False)

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
            notes_label.bind("<Button-1>", lambda _e, v=vn, lbl=notes_label, c=cat: open_notes_popup(c, v, lbl))

    search_var.trace_add("write", lambda *_: refresh_right_panel())

    def remove_vn(category: str, vn: dict) -> None:
        """
        Removes a VN from a category, saves the updated data, and refreshes the panel.
        """
        data["vns"][category] = [v for v in data["vns"].get(category, []) if v["id"] != vn["id"]]
        save_data(data)
        refresh_right_panel()

    def open_notes_popup(category: str, vn: dict, notes_label) -> None:
        """
        Opens a small popup to edit the personal note for a VN in a category.
        Saves the note back into the VN dict and updates the label in-place.
        """
        popup = customtkinter.CTkToplevel(app)
        popup.title("Note")
        popup.geometry("1200x800")
        popup.configure(fg_color=BG)
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
        text_box.pack(fill="both", expand=True, padx=16)
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
        customtkinter.CTkButton(btn_row, text="Save", width=80, fg_color=PINK, hover_color=PINK_DARK, text_color=WHITE, font=FONT_TITLE, corner_radius=20, command=confirm).pack(side="left", padx=6)

        popup.bind("<Escape>", lambda _e: popup.destroy())

    def move_vn(category: str, vn: dict) -> None:
        other_cats = [c for c in data["categories"] if c != category]
        if not other_cats:
            popup = customtkinter.CTkToplevel(app)
            popup.title("Error")
            popup.geometry("400x125")
            popup.configure(fg_color=BG)
            popup.resizable(False, False)
            popup.after(50, lambda: popup.lift())
            popup.after(50, lambda: popup.focus_force())

            customtkinter.CTkLabel(
                popup,
                text="You can't move a vn to another category if you don't have any other categories !",
                font=("Nunito", 16, "bold"),
                text_color=TEXT,
                wraplength=350,
            ).pack(pady=(20, 8))

            customtkinter.CTkButton(
                popup,
                text="OK",
                width=100,
                fg_color=PINK,
                hover_color=PINK_DARK,
                text_color=WHITE,
                font=FONT_TITLE,
                corner_radius=20,
                command=popup.destroy,
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
                wraplength=260,
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
                dropdown_text_color=TEXT,
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
                if app_state.refresh_categories:
                    app_state.refresh_categories()
                popup.destroy()

            customtkinter.CTkButton(
                popup,
                text="Move",
                width=100,
                fg_color=PINK,
                hover_color=PINK_DARK,
                text_color=WHITE,
                font=FONT_TITLE,
                corner_radius=20,
                command=confirm,
            ).pack(pady=12)

    app_state.refresh_library = refresh_right_panel
    return refresh_right_panel
