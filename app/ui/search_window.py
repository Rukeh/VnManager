import tkinter
import customtkinter

from app.api.vndb import search_vns
from app.utils.image import load_image_from_url
from app.utils.text import clean_description
from app.utils.image import load_image_from_url, _executor

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

    top_bar = customtkinter.CTkFrame(window)
    top_bar.pack(fill="x", padx=10, pady=10)

    entry = customtkinter.CTkEntry(top_bar, placeholder_text="Search a VN...  (Tip : You can press ENTER to search)")
    entry.pack(side="left", fill="x", expand=True, padx=(10, 8), pady=10)

    last_results: list = []
    view_mode = tkinter.StringVar(value="list")

    results_frame = customtkinter.CTkScrollableFrame(window)
    results_frame.pack(fill="both", expand=True)

    def _async_load_image(label, url, size):
        img = load_image_from_url(url, size=size)
        if img and label.winfo_exists():
            label.after(0, lambda: (label.configure(image=img), setattr(label, 'image', img)))

    def _add_to_category(vn: dict) -> None:
        """Shows a small popup to pick a category, then saves the VN."""
        categories = data.get("categories", [])
        if not categories:
            popup = customtkinter.CTkToplevel(window)
            popup.title("No categories")
            popup.geometry("280x80")
            popup.after(50, lambda: popup.lift())
            customtkinter.CTkLabel(popup, text="No categories yet.\nAdd one in the main window first.").pack(pady=12)
            customtkinter.CTkButton(popup, text="OK", width=80, command=popup.destroy).pack()
            return

        popup = customtkinter.CTkToplevel(window)
        popup.title("Add to category")
        popup.geometry("280x70")
        popup.resizable(False, False)
        popup.after(50, lambda: popup.lift())
        popup.after(50, lambda: popup.focus_force())

        customtkinter.CTkLabel(popup, text="Category:").pack(side="left", padx=(12, 6), pady=18)

        var = tkinter.StringVar(value=categories[0])
        customtkinter.CTkOptionMenu(popup, values=categories, variable=var).pack(side="left", padx=(0, 6))

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

        customtkinter.CTkButton(popup, text="Add", width=60, command=confirm).pack(side="left")


    def render_results(api_data: list) -> None:
        for widget in results_frame.winfo_children():
            widget.destroy()

        if view_mode.get() == "list":
            _render_list(api_data)
        else:
            _render_grid(api_data)

    def _render_list(api_data: list) -> None:
        for vn in api_data:
            year = (vn.get("released") or "?")[:4]
            img_url = (vn["image"] or {}).get("url", "")

            card = customtkinter.CTkFrame(results_frame)
            card.pack(fill="x", pady=4, padx=4)

            img_label = customtkinter.CTkLabel(card, text="", width=150, height=200)
            img_label.pack(side="left", padx=(8, 0), pady=8)
            if img_url:
                _executor.submit(_async_load_image, img_label, img_url, (150, 200))

            text_frame = customtkinter.CTkFrame(card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            customtkinter.CTkLabel(
                text_frame,
                text=f"{vn['title']} ({year})",
                font=("Arial", 20, "bold"),
                anchor="w",
                wraplength=350,
            ).pack(fill="x", pady=(4, 4))

            customtkinter.CTkLabel(
                text_frame,
                text=clean_description(vn.get("description")),
                font=("Arial", 13),
                anchor="w",
                wraplength=350,
                justify="left",
            ).pack(fill="x")

            customtkinter.CTkButton(
                text_frame,
                text='+',
                width = 160,
                command = lambda v=vn: _add_to_category
            ).pack(anchor='w', pady=(8,0))

    def _render_grid(api_data: list) -> None:
        
        card_width = 270
        window_width = window.winfo_width()
        columns = max(1, window_width // card_width)
        
        for index, vn in enumerate(api_data):
            year = (vn.get("released") or "?")[:4]
            img_url = (vn["image"] or {}).get("url", "")
            row, col = divmod(index, columns)

            card = customtkinter.CTkFrame(results_frame)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="n")

            img_label = customtkinter.CTkLabel(card, text="", width=150, height=200)
            img_label.pack(pady=(8, 4), padx=8)
            if img_url:
                _executor.submit(_async_load_image, img_label, img_url, (150, 200))

            customtkinter.CTkLabel(card,
                text=vn["title"],
                font=("Arial", 12, "bold"),
                wraplength=130,
                justify="center",
            ).pack(padx=6)

            customtkinter.CTkLabel(
                card,
                text=year,
                font=("Arial", 11),
                text_color="gray",
            ).pack(pady=(0, 8))

    def do_search() -> None:
        query = entry.get().strip()
        if not query:
            return
        api_data = search_vns(query)
        last_results.clear()
        last_results.extend(api_data)
        render_results(api_data)

    def toggle_view() -> None:
        if view_mode.get() == "list":
            view_mode.set("grid")
            toggle_btn.configure(text="☰ List")
        else:
            view_mode.set("list")
            toggle_btn.configure(text="⊞ Grid")
        if last_results:
            render_results(last_results)

    toggle_btn = customtkinter.CTkButton(top_bar, text="⊞ Grid", width=80, command=toggle_view)
    toggle_btn.pack(side="right", padx=(0, 8))

    search_btn = customtkinter.CTkButton(top_bar, text="Search", command=do_search)
    search_btn.pack(side="right")

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