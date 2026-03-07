import tkinter
import customtkinter
from concurrent.futures import ThreadPoolExecutor
import traceback

from app.api.vndb import search_vns
from app.ui.vn_detail import open_vn_detail
from app.utils.image import load_image_from_url, submit_image_task, async_load_with_hover, cover_size_for_width
from app.utils.text import clean_description
from app.ui.components import render_tags, enable_touchpad_scroll

from app.ui.theme import *

_search_executor = ThreadPoolExecutor(max_workers=2)

def open_search_window(parent: customtkinter.CTk, data, on_vn_added = None) -> None:
    """
    Opens a Toplevel window that lets the user search VnDB and browse results
    in either list or grid view.
    """
    window = customtkinter.CTkToplevel(parent)
    window.title("Search a Visual Novel from VnDB database...")
    window.geometry("1000x750")
    window.after(100, lambda: window.lift())
    window.after(100, lambda: window.focus_force())
    window.configure(fg_color=BG)

    last_results: list = []
    view_mode = tkinter.StringVar(value="list")
    image_futures: list = []
    _render_gen = [0] 

    def _get_vn_categories(vn_id: str) -> list[str]:
        return [cat for cat, vns in data.get("vns", {}).items() if any(v["id"] == vn_id for v in vns)]

    #___________Header__________
    
    top_bar = customtkinter.CTkFrame(window, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=0, height=64)
    top_bar.pack(fill="x")
    top_bar.pack_propagate(False)

    toggle_btn = customtkinter.CTkButton(top_bar, text="⊞ Grid", width=76,fg_color=PINK_LIGHT, hover_color=PINK_MID, text_color=PINK_DARK,font=("Nunito", 12, "bold"),corner_radius=20, command=lambda :toggle_view())
    toggle_btn.pack(side="right", padx=(0, 12))

    settings = data.setdefault("settings", {"allow_suggestive": False, "allow_explicit": False})

    def _toggle_suggestive():
        settings["allow_suggestive"] = not settings["allow_suggestive"]
        btn_suggestive.configure(
            fg_color=PINK if settings["allow_suggestive"] else PINK_LIGHT,
            text_color="#fff" if settings["allow_suggestive"] else PINK_DARK,
            hover_color="#d90764" if settings["allow_suggestive"] else PINK_MID
            ),
        from app.ui.main_window import save_data
        save_data(data)
        if last_results:
            render_results(last_results)

    def _toggle_explicit():
        settings["allow_explicit"] = not settings["allow_explicit"]
        btn_explicit.configure(
            fg_color=PINK if settings["allow_explicit"] else PINK_LIGHT,
            text_color="#fff" if settings["allow_explicit"] else PINK_DARK,
            hover_color="#d90764" if settings["allow_explicit"] else PINK_MID
            )
        from app.ui.main_window import save_data
        save_data(data)
        if last_results:
            render_results(last_results)

    btn_suggestive = customtkinter.CTkButton(
        top_bar, text="🌸 Suggestive", width=100,
        fg_color=PINK if settings["allow_suggestive"] else PINK_LIGHT,
        hover_color="#d90764" if settings["allow_suggestive"] else PINK_MID, 
        text_color="#fff" if settings["allow_suggestive"] else PINK_DARK,
        font=("Nunito", 12, "bold"), corner_radius=20,
        command=_toggle_suggestive,
    )
    btn_suggestive.pack(side="right", padx=(0, 6))

    btn_explicit = customtkinter.CTkButton(
        top_bar, text="🚫 Explicit", width=90,
        fg_color=PINK if settings["allow_explicit"] else PINK_LIGHT,
        hover_color="#d90764" if settings["allow_explicit"] else PINK_MID,
        text_color="#fff" if settings["allow_explicit"] else PINK_DARK,
        font=("Nunito", 12, "bold"), corner_radius=20,
        command=_toggle_explicit,
    )
    btn_explicit.pack(side="right", padx=(0, 4))

    search_btn = customtkinter.CTkButton(top_bar, text="Search", width=80,fg_color=PINK, hover_color=PINK_DARK,text_color="#fff", font = ("Nunito", 13, "bold"), corner_radius=20, command=lambda :do_search())
    search_btn.pack(side="right", padx=(0,6))    
    
    customtkinter.CTkLabel(
        top_bar, text="🔎  Search VnDB",
        font=("Nunito", 16, "bold"), text_color=PINK_DARK,
    ).pack(side="left", padx=(16, 0))

    search_frame = customtkinter.CTkFrame(
        top_bar, fg_color=PINK_SOFT,
        border_width=1, border_color=BORDER, corner_radius=20,
    )
    search_frame.pack(side="right", fill="x", expand=True, padx=(12, 8), pady=12)

    customtkinter.CTkLabel(
        search_frame, text="🔍", font=("Quicksand", 12), text_color=PINK,
    ).pack(side="left", padx=(10, 4))

    entry = customtkinter.CTkEntry(search_frame, placeholder_text="Search a VN...  (Press Enter)", border_width=0, fg_color='transparent', font = FONT_BODY, text_color=TEXT, placeholder_text_color=TEXT_MUTED)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=6)

    #______Results_______

    results_frame = customtkinter.CTkScrollableFrame(window, fg_color='transparent', scrollbar_button_color=PINK_MID)
    results_frame.pack(fill="both", expand=True, padx=12, pady=10)

    def _submit_image_hover(label, url, size, images):
        future = submit_image_task(async_load_with_hover, label, url, size, images)
        image_futures.append(future)

    def _cancel_image_tasks():
        for f in image_futures:
            f.cancel()
        image_futures.clear()

    #_________________________
    def _add_to_category(vn: dict) -> None:
        """Shows a small popup to pick a category, then saves the VN."""
        categories = data.get("categories", [])
        if not categories:
            popup = customtkinter.CTkToplevel(window)
            popup.title("No categories")
            popup.geometry("300x100")
            popup.configure(fg_color=BG)
            popup.after(50, lambda: popup.lift())
            customtkinter.CTkLabel(popup, 
            text="No categories yet.\nAdd one in the main window first.",
            font=FONT_BODY, 
            text_color=TEXT
            ).pack(pady=12)
            customtkinter.CTkButton(popup, 
            text="OK", 
            width=80,
            fg_color=PINK,
            hover_color=PINK_DARK,
            text_color="#fff",
            corner_radius=20, 
            command=popup.destroy).pack()
            return

        popup = customtkinter.CTkToplevel(window)
        popup.title("Add to category")
        popup.geometry("350x210")
        popup.configure(fg_color=BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        def _fit_popup():
            popup.update_idletasks()
            popup.geometry(f"350x{popup.winfo_reqheight() + 20}")

        popup.after(100, _fit_popup)

        top_row = customtkinter.CTkFrame(popup, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(12, 8))

        customtkinter.CTkLabel(
            top_row,
            text=f'Add "{vn["title"]}" to :',
            font=FONT_TITLE,
            text_color=TEXT,
            wraplength=220,
            anchor="w",
            justify="left",
        ).pack(side="left", fill="x", expand=True)

        customtkinter.CTkButton(
            top_row, text="Close ✕", width=28, height=28,
            fg_color=PINK_LIGHT, hover_color=PINK_MID,
            text_color=PINK_DARK, font=FONT_TITLE, corner_radius=20,
            command=popup.destroy,
        ).pack(side="right", anchor="n")

        var = tkinter.StringVar(value=categories[0])
        customtkinter.CTkOptionMenu(popup, 
        values=categories, 
        variable=var,
        fg_color=PINK_LIGHT,
        button_color=PINK,
        button_hover_color=PINK_DARK,
        text_color=PINK_DARK,
        dropdown_text_color=TEXT, 
        font=("Nunito", 12, "bold"),
        dropdown_fg_color=CARD_BG,
        corner_radius=10
        ).pack(padx=20, fill="x")

        def confirm():
            cat = var.get()
            vns_in_cat = data["vns"].setdefault(cat, [])
            added = not any(v["id"] == vn["id"] for v in vns_in_cat)
            if added:
                vns_in_cat.append(vn)
                from app.ui.main_window import save_data
                save_data(data)
            popup.destroy()
            if added and on_vn_added:
                window.after(300, on_vn_added)

        customtkinter.CTkButton(popup, 
        text="+ Add", 
        width=100, 
        fg_color=PINK,
        hover_color=PINK_DARK,
        text_color="#fff",
        font=FONT_TITLE,
        corner_radius=20,
        command=confirm
        ).pack(pady=12)

    #_____renders______
    def render_results(api_data: list) -> None:
        _render_gen[0] += 1
        _last_rendered_size[:] = [window.winfo_width(), window.winfo_height()]
        for widget in results_frame.winfo_children():
            widget.destroy()
        max_nsfw_filter = 0
        if settings["allow_suggestive"]:
            max_nsfw_filter = 1
        if settings["allow_explicit"]:
            max_nsfw_filter = 2
        
        api_data = [v for v in api_data if (v.get("image") or {}).get('sexual', 0) <= max_nsfw_filter]

        if not api_data:
            customtkinter.CTkLabel(
                results_frame,
                text="No results found.",
                text_color="gray",
            ).pack(pady=20)
            return

        if view_mode.get() == "list":
            _render_list(api_data, _render_gen[0])
        else:
            _render_grid(api_data, _render_gen[0])

    def _render_list(api_data: list, gen: int) -> None:
        cover_size = cover_size_for_width(window.winfo_width(), "list")
        BATCH = 5

        def _render_batch(index: int) -> None:
            if _render_gen[0] != gen:
                return
            for vn in api_data[index : index + BATCH]:
                year = (vn.get("released") or "?")[:4]
                img_url = (vn["image"] or {}).get("url", "")
                rating  = vn.get("rating")

                card = customtkinter.CTkFrame(results_frame, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
                card.pack(fill="x", pady=4, padx=4)

                inner = customtkinter.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="both", padx=12, pady=12)

                cover_frame = customtkinter.CTkFrame(inner, width=cover_size[0], height=cover_size[1], fg_color=PINK_LIGHT, corner_radius=10, cursor="hand2")
                cover_frame.pack(side="left", pady=(10, 6), padx=10)
                cover_frame.pack_propagate(False)

                img_label = customtkinter.CTkLabel(cover_frame, text="🌸", font=("Nunito", 18), bg_color="transparent", cursor="hand2", fg_color="transparent")
                img_label.pack(fill="both", expand=True)

                _images = {"normal": None, "dimmed": None}
                if img_url:
                    _submit_image_hover(img_label, img_url, cover_size, _images)

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
                    widget.bind("<Button-1>", lambda _e, v=vn: open_vn_detail(window, v))

                text_frame = customtkinter.CTkFrame(inner, fg_color="transparent")
                text_frame.pack(side="left", fill="both", expand=True)

                title_lbl = customtkinter.CTkLabel(
                    text_frame,
                    text=vn["title"],
                    font=FONT_H2,
                    text_color=TEXT,
                    anchor="w",
                    wraplength=380,
                    cursor="hand2",
                )
                title_lbl.pack(fill="x")
                title_lbl.bind("<Button-1>", lambda _e, v=vn: open_vn_detail(window, v))

                cats = _get_vn_categories(vn["id"])
                if cats:
                    customtkinter.CTkLabel(
                        text_frame,
                        text="✓  " + ", ".join(cats),
                        font=("Nunito", 11, "bold"),
                        text_color="#9b6dbd",
                        fg_color="#e8d5f5",
                        corner_radius=20,
                        anchor="w",
                    ).pack(anchor="w", pady=(2, 4))

                year_rat = year
                if rating:
                    year_rat += f"   ★ {rating / 10:.2f}"
                customtkinter.CTkLabel(text_frame, text=year_rat, font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").pack(fill="x", pady=(1, 4))

                render_tags(text_frame, vn)

                desc_lbl = customtkinter.CTkLabel(
                    text_frame,
                    text=clean_description(vn.get("description")),
                    font=FONT_SMALL,
                    text_color=TEXT_MUTED,
                    anchor="w",
                    wraplength=300,
                    justify="left",
                )
                desc_lbl.pack(fill="x")
                desc_lbl.bind("<Configure>", lambda e, lbl=desc_lbl: lbl.configure(wraplength=max(100, text_frame.winfo_width() - 8)))

                customtkinter.CTkButton(
                    text_frame,
                    text='+ Add',
                    width=72,
                    height=28,
                    fg_color=PINK_LIGHT,
                    hover_color=PINK,
                    text_color=PINK_DARK,
                    font=('Nunito', 12, "bold"),
                    corner_radius=20,
                    command=lambda v=vn: _add_to_category(v),
                ).pack(anchor='center', side='right', pady=(8, 0))

            if index + BATCH < len(api_data):
                window.after(16, lambda: _render_batch(index + BATCH))

        _render_batch(0)

    def _render_grid(api_data: list, gen: int) -> None:
        cover_size = cover_size_for_width(window.winfo_width(), "grid")
        card_width = cover_size[0] + 30
        window_width = window.winfo_width()
        columns = max(1, window_width // card_width)
        for i in range(20):
            results_frame.columnconfigure(i, weight=0)
        results_frame.columnconfigure(list(range(columns)), weight=1)
        BATCH = 5

        def _render_batch(index: int) -> None:
            if _render_gen[0] != gen:
                return
            for i, vn in enumerate(api_data[index : index + BATCH]):
                idx = index + i
                year = (vn.get("released") or "?")[:4]
                img_url = (vn["image"] or {}).get("url", "")
                row, col = divmod(idx, columns)

                card = customtkinter.CTkFrame(results_frame, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
                card.grid(row=row, column=col, padx=6, pady=6, sticky="n")

                cover_frame = customtkinter.CTkFrame(card, width=cover_size[0], height=cover_size[1], fg_color=PINK_LIGHT, corner_radius=10, cursor="hand2")
                cover_frame.pack(pady=(10, 6), padx=10)
                cover_frame.pack_propagate(False)

                img_label = customtkinter.CTkLabel(cover_frame, text="🌸", font=("Nunito", 28), bg_color="transparent", cursor="hand2", fg_color="transparent")
                img_label.pack(fill="both", expand=True)

                _images = {"normal": None, "dimmed": None}
                if img_url:
                    _submit_image_hover(img_label, img_url, cover_size, _images)

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
                    widget.bind("<Button-1>", lambda _e, v=vn: open_vn_detail(window, v))

                title_lbl = customtkinter.CTkLabel(
                    card,
                    text=vn["title"],
                    font=("Nunito", 12, "bold"),
                    text_color=TEXT,
                    wraplength=130,
                    justify="center",
                    cursor="hand2",
                )
                title_lbl.pack(padx=6)
                title_lbl.bind("<Button-1>", lambda _e, v=vn: open_vn_detail(window, v))
                title_lbl.bind("<Configure>", lambda e, lbl=title_lbl: lbl.configure(wraplength=max(100, card.winfo_width() - 8)))

                cats = _get_vn_categories(vn["id"])
                if cats:
                    customtkinter.CTkLabel(
                        card,
                        text="✓  " + ", ".join(cats),
                        font=("Nunito", 10, "bold"),
                        text_color="#9b6dbd",
                        fg_color="#e8d5f5",
                        corner_radius=20,
                    ).pack(pady=(2, 4), padx=6)

                customtkinter.CTkLabel(
                    card, text=year,
                    font=FONT_SMALL,
                    text_color=TEXT_MUTED,
                ).pack(pady=(0, 8))

                customtkinter.CTkButton(
                    card, text="＋ Add",
                    width=100, height=28,
                    fg_color=PINK_LIGHT, hover_color=PINK,
                    text_color=PINK_DARK, font=("Nunito", 12, "bold"),
                    corner_radius=20,
                    command=lambda v=vn: _add_to_category(v),
                ).pack(pady=(0, 10))

            if index + BATCH < len(api_data):
                window.after(16, lambda: _render_batch(index + BATCH))

        _render_batch(0)

    def do_search() -> None:
        query = entry.get().strip()
        if not query:
            return

        _cancel_image_tasks()

        for widget in results_frame.winfo_children():
            widget.destroy()
        loading = customtkinter.CTkFrame(results_frame, fg_color="transparent")
        loading.pack(pady=40)
        customtkinter.CTkLabel(
            loading, text="🔍", font=("Nunito", 32), text_color=PINK_MID,
        ).pack()
        customtkinter.CTkLabel(
            loading, text="Searching VnDB...",
            font=("Nunito", 14, "bold"), text_color=TEXT_MUTED,
        ).pack(pady=(6, 0))

        def _search():
            try:
                api_data = search_vns(query)
            except Exception as e:
                traceback.print_exc()
                window.after(0, lambda e=e: _show_error(e))
                return
            window.after(0, lambda: _show_results(api_data))

        def _show_error(error):
            for widget in results_frame.winfo_children():
                widget.destroy()
            customtkinter.CTkLabel(
                results_frame,
                text=f'Search failed. Please check your internet connection and try again. Error: {error}',
                font=FONT_BODY,
                text_color="#f87171", 
                wraplength=400
            ).pack(pady=30)

        def _show_results(api_data):
            last_results.clear()
            last_results.extend(api_data)
            render_results(api_data)

        _search_executor.submit(_search)

    def toggle_view() -> None:
        if view_mode.get() == "list":
            view_mode.set("grid")
            toggle_btn.configure(text="☰ List")
        else:
            view_mode.set("list")
            toggle_btn.configure(text="⊞ Grid")
        if last_results:
            render_results(last_results)

    _resize_job = None
    _last_size = [0, 0]
    _last_rendered_size = [0, 0]

    def _on_resize(event):
        nonlocal _resize_job
        if event.widget != window:
            return
        if not last_results:
            return
        new_size = [event.width, event.height]
        if new_size == _last_size:
            return
        _last_size[:] = new_size
        if _resize_job:
            window.after_cancel(_resize_job)
        def _maybe_render():
            actual = [window.winfo_width(), window.winfo_height()]
            if actual == _last_rendered_size:
                return
            _last_rendered_size[:] = actual
            render_results(last_results)
        _resize_job = window.after(200, _maybe_render)

    window.bind("<Configure>", _on_resize)

    entry.bind("<Return>", lambda _e: do_search())
    enable_touchpad_scroll(window, results_frame)