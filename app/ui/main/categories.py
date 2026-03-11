import customtkinter
from app.ui.shared.theme import *
from app.utils.save import save_data


def build_categories(categories_scroll, category_entry, app_state, app):
    """
    Wires all category sidebar logic into the given widgets.
    Returns (refresh_categories, add_category).
    Args:
        categories_scroll: CTkScrollableFrame that holds the category list.
        category_entry:    CTkEntry for typing a new category name.
        app_state:         Shared AppState instance.
        app:               Root CTk window (used as parent for popups).
    """
    data = app_state.data
    selected_category = app_state.selected_category

    def add_category() -> None:
        name = category_entry.get().strip()
        if not name or name in data["categories"]:
            return
        data["categories"].append(name)
        save_data(data)
        category_entry.delete(0, "end")
        refresh_categories()

    category_entry.bind("<Return>", lambda _e: add_category())

    def select_category(name: str) -> None:
        selected_category[0] = name
        app_state.search_var.set("")
        if app_state.refresh_library:
            app_state.refresh_library()
        refresh_categories()

    def rename_category(oldname: str, newname: str) -> None:
        newname = newname.strip()
        if not newname or newname == oldname or newname in data["categories"]:
            refresh_categories()
            return

        index = data["categories"].index(oldname)
        data["categories"][index] = newname

        if oldname in data["vns"]:
            data["vns"][newname] = data["vns"].pop(oldname)

        if selected_category[0] == oldname:
            selected_category[0] = newname
            if app_state.right_title:
                app_state.right_title.configure(text=newname)

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

    def delete_category(name: str) -> None:
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
            font=FONT_TITLE,
            text_color=TEXT,
            wraplength=260,
        ).pack(pady=14)

        btn_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack()

        def confirm():
            popup.destroy()
            if name in data["categories"]:
                data["categories"].remove(name)
                data["vns"].pop(name, None)
                save_data(data)
                if selected_category[0] == name:
                    selected_category[0] = None
                    if app_state.right_title:
                        app_state.right_title.configure(text="Select a category")
                    if app_state.refresh_library:
                        app_state.refresh_library()
                refresh_categories()

        customtkinter.CTkButton(btn_frame, text="Cancel", width=80, text_color="#fff", fg_color=PINK_MID, hover_color="#f7b2d9", command=popup.destroy).pack(side="left", padx=8)
        customtkinter.CTkButton(btn_frame, text="Delete", width=80, text_color="#fff", fg_color="#db6098", hover_color="#d41167", command=confirm).pack(side="left", padx=8)

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

            row_frame = customtkinter.CTkFrame(categories_scroll, fg_color=PINK_LIGHT if is_active else "transparent", corner_radius=10)
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

    app_state.refresh_categories = refresh_categories
    return refresh_categories, add_category
