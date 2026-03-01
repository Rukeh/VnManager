import tkinter
import customtkinter
from concurrent.futures import ThreadPoolExecutor

from app.api.vndb import search_vns
from app.utils.image import load_image_from_url
from app.utils.text import clean_description

_search_executor = ThreadPoolExecutor(max_workers=2)
_image_executor = ThreadPoolExecutor(max_workers=6)

#this cache grows unbounded during a session should consider adding a cache cap or a way to clear it if it becomes a issue on memory
_image_cache = {}

#Color palette for cute theme 
BG          = "#fff8f9"
CARD_BG     = "#ffffff"
PINK        = "#f472b6"
PINK_LIGHT  = "#fce7f3"
PINK_MID    = "#fbcfe8"
PINK_DARK   = "#db2777"
PINK_SOFT   = "#fdf2f8"
TEXT        = "#3d2535"
TEXT_MUTED  = "#b07090"
BORDER      = "#fad4e8"

FONT_TITLE  = ("Nunito", 13, "bold")
FONT_BODY   = ("Quicksand", 12)
FONT_SMALL  = ("Quicksand", 11)
FONT_H2     = ("Nunito", 14, "bold")

def open_search_window(parent: customtkinter.CTk, data, on_vn_added = None) -> None:
    """
    Opens a Toplevel window that lets the user search VnDB and browse results
    in either list or grid view.
    """
    window = customtkinter.CTkToplevel(parent)
    window.title("Search a Visual Novel from VnDB database...")
    window.geometry("600x450")
    window.after(100, lambda: window.lift())
    window.after(100, lambda: window.focus_force())
    window.configure(fg_color=BG)

    last_results: list = []
    view_mode = tkinter.StringVar(value="list")
    image_futures: list = []    
    
    #___________Header__________
    
    top_bar = customtkinter.CTkFrame(window, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=0, height=64)
    top_bar.pack(fill="x")
    top_bar.pack_propagate(False)

    toggle_btn = customtkinter.CTkButton(top_bar, text="⊞ Grid", width=76,fg_color=PINK_LIGHT, hover_color=PINK_MID, text_color=PINK_DARK,font=("Nunito", 12, "bold"),corner_radius=20, command=lambda :toggle_view())
    toggle_btn.pack(side="right", padx=(0, 12))

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
   
   #____image_related____
    def _async_load_image(label, url, size):
        key = (url, size)
        if key in _image_cache:
            img = _image_cache[key]
        else:
            img = load_image_from_url(url, size=size)
            if img:
                _image_cache[key] = img
        if img:
            def _apply():
                if label.winfo_exists():
                    label.configure(image=img, text="")
                    label.image = img
            label.after(0, _apply)

    def _submit_image(label, url, size):
        future = _image_executor.submit(_async_load_image, label, url, size)
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
        popup.geometry("350x170")
        popup.configure(fg_color=BG)
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkButton(
            popup, text="✕ Close", width=80, height=30,
            fg_color=PINK_LIGHT, hover_color=PINK_MID,
            text_color=PINK_DARK, font=FONT_TITLE, corner_radius=20,
            command=popup.destroy,
        ).place(x=260, y= 10)

        customtkinter.CTkLabel(popup, 
            text=f'Add "{vn["title"]}" to :', 
            font= FONT_TITLE,
            text_color=TEXT,
            wraplength=260,
        ).pack(pady=(35,8))

        var = tkinter.StringVar(value=categories[0])
        customtkinter.CTkOptionMenu(popup, 
        values=categories, 
        variable=var,
        fg_color=PINK_LIGHT,
        button_color=PINK,
        button_hover_color=PINK_DARK,
        text_color=PINK_DARK,
        font=("Nunito", 12, "bold"),
        dropdown_fg_color=CARD_BG,
        corner_radius=10
        ).pack(padx=20, fill="x")

        def confirm():
            cat = var.get()
            vns_in_cat = data["vns"].setdefault(cat, [])
            if not any(v["id"] == vn["id"] for v in vns_in_cat):
                vns_in_cat.append(vn)
                from app.ui.main_window import save_data
                save_data(data)
                if on_vn_added:
                    on_vn_added()
            popup.destroy()

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
        for widget in results_frame.winfo_children():
            widget.destroy()

        if not api_data:
            customtkinter.CTkLabel(
                results_frame,
                text="No results found.",
                text_color="gray",
            ).pack(pady=20)
            return

        if view_mode.get() == "list":
            _render_list(api_data)
        else:
            _render_grid(api_data)

    def _render_list(api_data: list) -> None:
        for vn in api_data:
            year = (vn.get("released") or "?")[:4]
            img_url = (vn["image"] or {}).get("url", "")
            rating  = vn.get("rating")

            card = customtkinter.CTkFrame(results_frame, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
            card.pack(fill="x", pady=4, padx=4)

            inner = customtkinter.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", padx=12, pady=12)

            cover_frame = customtkinter.CTkFrame(inner, width=165, height=200, fg_color='transparent', corner_radius=10)
            cover_frame.pack(side="left", pady=(10, 6), padx=10)
            cover_frame.pack_propagate(False)


            img_label = customtkinter.CTkLabel(cover_frame, text="🌸", font=("Nunito", 18), bg_color="transparent")
            img_label.pack(fill="both", expand=True)
            if img_url:
                _submit_image(img_label, img_url, (165, 200))

            text_frame = customtkinter.CTkFrame(inner, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True)

            customtkinter.CTkLabel(
                text_frame,
                text=vn["title"],
                font=FONT_H2,
                text_color=TEXT,
                anchor="w",
                wraplength=380,
            ).pack(fill="x")
            year_rat = year
            if rating:
                year_rat += f"   ★ {rating:.2f}"
            customtkinter.CTkLabel(text_frame, text=year_rat,font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w",).pack(fill="x", pady=(1, 4))            

            customtkinter.CTkLabel(
                text_frame,
                text=clean_description(vn.get("description")),
                font=FONT_SMALL,
                text_color=TEXT_MUTED,
                anchor="w",
                wraplength=max(300, window.winfo_width()),
                justify="left",
            ).pack(fill="x")

            customtkinter.CTkButton(
                text_frame,
                text='+ Add',
                width = 72,
                height=28,
                fg_color=PINK_LIGHT,
                hover_color=PINK,
                text_color=PINK_DARK,
                font=('Nunito', 12, "bold"),
                corner_radius=20,
                command = lambda v=vn: _add_to_category(v)
            ).pack(anchor='center',side = 'right', pady=(8,0))

    def _render_grid(api_data: list) -> None:
        
        card_width = 195
        window_width = window.winfo_width()
        columns = max(1, window_width // card_width)

        results_frame.columnconfigure(list(range(columns)), weight=1)
        
        for index, vn in enumerate(api_data):
            year = (vn.get("released") or "?")[:4]
            img_url = (vn["image"] or {}).get("url", "")
            row, col = divmod(index, columns)

            card = customtkinter.CTkFrame(results_frame, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=14)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="n")

            cover_frame = customtkinter.CTkFrame(card, width=165, height=200, fg_color='transparent', corner_radius=10)
            cover_frame.pack(pady=(10, 6), padx=10)
            cover_frame.pack_propagate(False)            
            
            
            img_label = customtkinter.CTkLabel(cover_frame, text="🌸", font=("Nunito", 28), bg_color="transparent")
            img_label.pack(fill="both", expand=True)
            if img_url:
                _submit_image(img_label, img_url, (165, 200))

            customtkinter.CTkLabel(card,
            text=vn["title"],
                font=("Nunito", 12, "bold"), 
                text_color=TEXT,
                wraplength=130,
                justify="center",
            ).pack(padx=6)

            customtkinter.CTkLabel(
                card, text=year,
                font=FONT_SMALL, 
                text_color=TEXT_MUTED,
            ).pack(pady=(0, 8))

            customtkinter.CTkButton(
                card, text="＋ Add", 
                width=100, height=28,
                fg_color=PINK_LIGHT, 
                hover_color=PINK,
                text_color=PINK_DARK, 
                font=("Nunito", 12, "bold"),
                corner_radius=20,
                command=lambda v=vn: _add_to_category(v),
            ).pack(pady=(0, 10))         

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
            except Exception:
                window.after(0, lambda: _show_error())
                return
            window.after(0, lambda: _show_results(api_data))

        def _show_error():
            for widget in results_frame.winfo_children():
                widget.destroy()
            customtkinter.CTkLabel(
                results_frame,
                text="Search failed. Please check your internet connection and try again.",
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

    def _on_resize(event):
        nonlocal _resize_job
        if event.widget != window:
            return
        if view_mode.get() != "grid" or not last_results:
            return
        new_size = [window.winfo_width(), window.winfo_height()]
        if new_size == _last_size:
            return
        _last_size[:] = new_size
        if _resize_job:
            window.after_cancel(_resize_job)
        _resize_job = window.after(150, lambda: render_results(last_results))

    window.bind("<Configure>", _on_resize)

    entry.bind("<Return>", lambda _e: do_search())