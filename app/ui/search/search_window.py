import tkinter
import customtkinter
from concurrent.futures import ThreadPoolExecutor
import traceback
import time

from app.api.vndb import search_vns, search_tags
from app.ui.search.vn_detail import open_vn_detail
from app.utils.image import load_image_from_url, submit_image_task, async_load_with_hover, cover_size_for_width
from app.utils.text import clean_description
from app.ui.shared.components import render_tags, enable_touchpad_scroll, logical_width
from app.utils.save import save_data

from app.ui.shared.theme import *

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
    _tag_panel_open = [False]

    # Tag groups : list of lists of {"id": "gXX", "name": "..."}
    #Each list inside is = one OR group, groups are AND together
    tag_groups: list[list[dict]] = [[]]
    _group_entries: list = []
    _tag_suggest_job = [None]
    _tag_dropdown_win = [None]
    _tag_listbox = [None]
    _active_group_idx = [0]
    _active_entry = [None]
    _suggest_results = [None]
    _dropdown_mouse_inside = [False]
    _search_token = [0]
    _current_query = [""]
    _current_tag_groups = [[]]
    _current_page = [0]
    _has_more_pages = [False]
    _is_loading_more = [False]
    _rendered_count = [0]

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

    tag_toggle_btn = customtkinter.CTkButton(
        top_bar, text="Tags", width=72, height=30,
        fg_color=PINK_LIGHT, hover_color=PINK_MID,
        text_color=PINK_DARK, font=("Nunito", 12, "bold"),
        corner_radius=20, command=lambda: _toggle_tag_panel(),
    )
    tag_toggle_btn.pack(side="right", padx=(0, 4))
    
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

    #Tag panel

    tag_section = customtkinter.CTkFrame(window, fg_color=PINK_SOFT, border_width=1, border_color=BORDER, corner_radius=0)
    #this is shown when toggled

    tag_header = customtkinter.CTkFrame(tag_section, fg_color="transparent")
    tag_header.pack(fill="x", padx=10, pady=(6, 2))

    customtkinter.CTkLabel(
        tag_header, text="HELP : Tags within a group are OR'd  WHILE  groups are AND'd",
        font=("Nunito", 14), text_color=TEXT_MUTED,
    ).pack(side="left")

    customtkinter.CTkButton(
        tag_header, text="＋ AND group", width=90, height=22,
        fg_color=PINK_LIGHT, hover_color=PINK_MID,
        text_color=PINK_DARK, font=("Nunito", 10, "bold"),
        corner_radius=20, command=lambda: _add_group(),
    ).pack(side="right")

    tag_groups_frame = customtkinter.CTkFrame(tag_section, fg_color="transparent")
    tag_groups_frame.pack(fill="x", padx=10, pady=(0, 6))

    def _active_tag_count() -> int:
        return sum(len(g) for g in tag_groups)

    def _update_tag_btn_label() -> None:
        count = _active_tag_count()
        if count:
            tag_toggle_btn.configure(
                text=f"🏷️ Tags ({count})",
                fg_color=PINK, text_color="#fff", hover_color=PINK_DARK,
            )
        else:
            tag_toggle_btn.configure(
                text="🏷️ Tags",
                fg_color=PINK_LIGHT, text_color=PINK_DARK, hover_color=PINK_MID,
            )

    def _toggle_tag_panel() -> None:
        if _tag_panel_open[0]:
            tag_section.pack_forget()
            _tag_panel_open[0] = False
            _close_dropdown()
        else:
            tag_section.pack(fill="x", after=top_bar)
            _tag_panel_open[0] = True
            _render_tag_section()

    #Autocomplete for tags

    def _close_dropdown() -> None:
        _dropdown_mouse_inside[0] = False
        if _tag_dropdown_win[0]:
            try:
                _tag_dropdown_win[0].destroy()
            except Exception:
                pass
        _tag_dropdown_win[0] = None
        _tag_listbox[0] = None
        _suggest_results[0] = None

    def _show_dropdown(results: list, anchor_entry) -> None:
        _close_dropdown()
        if not results or not anchor_entry.winfo_exists():
            return

        _suggest_results[0] = results
        x = anchor_entry.winfo_rootx()
        y = anchor_entry.winfo_rooty() + anchor_entry.winfo_height() + 2
        row_h = 26
        h = min(len(results), 8) * row_h + 4

        win = tkinter.Toplevel(window)
        win.overrideredirect(True)
        win.geometry(f"240x{h}+{x}+{y}")
        win.configure(bg=CARD_BG)
        win.lift()
        _tag_dropdown_win[0] = win

        lb = tkinter.Listbox(
            win,
            font=("Quicksand", 11),
            bg=CARD_BG, fg=TEXT,
            selectbackground=PINK_LIGHT, selectforeground=PINK_DARK,
            borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER,
            relief="flat", activestyle="dotbox",
            height=len(results),
        )
        lb.pack(fill="both", expand=True)
        _tag_listbox[0] = lb

        for r in results:
            lb.insert("end", f"  {r['name']}")

        def _pick(e=None):
            sel = lb.curselection()
            if not sel:
                return
            _add_tag_to_group(_suggest_results[0][sel[0]], _active_group_idx[0])
            _close_dropdown()
            if _active_entry[0] and _active_entry[0].winfo_exists():
                _active_entry[0].delete(0, "end")
                _active_entry[0].focus_set()

        def _on_lb_key(e):
            if e.keysym == "Return":
                _pick()
            elif e.keysym == "Escape":
                _close_dropdown()
                if _active_entry[0] and _active_entry[0].winfo_exists():
                    _active_entry[0].focus_set()

        lb.bind("<ButtonRelease-1>", _pick)
        lb.bind("<KeyPress>", _on_lb_key)
        lb.bind("<Enter>", lambda e: _set_dropdown_mouse(True))
        lb.bind("<Leave>", lambda e: _set_dropdown_mouse(False))
        win.bind("<Enter>", lambda e: _set_dropdown_mouse(True))
        win.bind("<Leave>", lambda e: _set_dropdown_mouse(False))

    def _set_dropdown_mouse(inside: bool) -> None:
        _dropdown_mouse_inside[0] = inside

    def _maybe_close_dropdown() -> None:
        if _dropdown_mouse_inside[0]:
            return
        focused = window.focus_get()
        if _active_entry[0]:
            try:
                if focused == _active_entry[0]:
                    return
            except Exception:
                pass
        if _tag_listbox[0]:
            try:
                if focused == _tag_listbox[0]:
                    return
            except Exception:
                pass
        _close_dropdown()

    def _fetch_tag_suggestions(query: str, anchor_entry, g_idx: int) -> None:
        def _fetch():
            try:
                results = search_tags(query)
            except Exception:
                return
            if _active_group_idx[0] == g_idx:
                window.after(0, lambda: _show_dropdown(results, anchor_entry))
        _search_executor.submit(_fetch)

    def _on_tag_key(event, g_idx: int, raw_entry) -> None:
        if event.keysym in ("Return", "Escape", "Down", "Up", "Tab"):
            return
        _active_group_idx[0] = g_idx
        _active_entry[0] = raw_entry
        if _tag_suggest_job[0]:
            window.after_cancel(_tag_suggest_job[0])
        text = raw_entry.get().strip()
        if len(text) < 2:
            _close_dropdown()
            return
        _tag_suggest_job[0] = window.after(300, lambda: _fetch_tag_suggestions(text, raw_entry, g_idx))

    def _on_entry_down(raw_entry) -> None:
        if _tag_listbox[0]:
            _tag_listbox[0].focus_set()
            if _tag_listbox[0].size() > 0:
                _tag_listbox[0].selection_set(0)
                _tag_listbox[0].activate(0)

    def _on_entry_return(raw_entry) -> None:
        if _tag_listbox[0] and _tag_listbox[0].size() > 0:
            _tag_listbox[0].selection_set(0)
            _tag_listbox[0].event_generate("<ButtonRelease-1>")
        else:
            _close_dropdown()

    #groups manipulation

    def _add_group() -> None:
        tag_groups.append([])
        _render_tag_section()

    def _remove_group(g_idx: int) -> None:
        if len(tag_groups) > 1:
            tag_groups.pop(g_idx)
        else:
            tag_groups[0] = []
        _close_dropdown()
        _render_tag_section()
        _update_tag_btn_label()

    def _add_tag_to_group(tag: dict, g_idx: int) -> None:
        if g_idx < len(tag_groups):
            if not any(t["id"] == tag["id"] for t in tag_groups[g_idx]):
                tag_groups[g_idx].append(tag)
        _render_tag_section(refocus=g_idx)
        _update_tag_btn_label()

    def _remove_tag_from_group(g_idx: int, tag_id: str) -> None:
        if g_idx < len(tag_groups):
            tag_groups[g_idx] = [t for t in tag_groups[g_idx] if t["id"] != tag_id]
        _render_tag_section(refocus=g_idx)
        _update_tag_btn_label()

    #Tag renders

    def _render_tag_section(refocus: int = None) -> None:
        _group_entries.clear()
        _close_dropdown()
        for w in tag_groups_frame.winfo_children():
            w.destroy()

        for g_idx, group in enumerate(tag_groups):
            if g_idx > 0:
                sep_row = customtkinter.CTkFrame(tag_groups_frame, fg_color="transparent")
                sep_row.pack(fill="x", pady=(1, 0))
                customtkinter.CTkLabel(
                    sep_row, text="AND",
                    font=("Nunito", 9, "bold"), text_color="#ffffff",
                    fg_color=PINK_DARK, corner_radius=6,
                ).pack(side="left", padx=4, ipadx=5, ipady=1)

            group_row = customtkinter.CTkFrame(tag_groups_frame, fg_color=CARD_BG, border_width=1, border_color=BORDER, corner_radius=8)
            group_row.pack(fill="x", pady=(1, 0))

            chips_area = customtkinter.CTkFrame(group_row, fg_color="transparent")
            chips_area.pack(side="left", fill="y", padx=(4, 0), pady=3)

            for c_idx, tag in enumerate(group):
                if c_idx > 0:
                    customtkinter.CTkLabel(
                        chips_area, text="OR",
                        font=("Nunito", 9, "bold"), text_color=PINK_DARK,
                        fg_color=PINK_MID, corner_radius=5,
                    ).pack(side="left", padx=2, ipadx=4, ipady=1)

                chip = customtkinter.CTkFrame(chips_area, fg_color=PINK_LIGHT, corner_radius=20)
                chip.pack(side="left", padx=(0, 2), pady=2)
                customtkinter.CTkLabel(
                    chip, text=tag["name"],
                    font=("Quicksand", 10), text_color=PINK_DARK,
                ).pack(side="left", padx=(6, 1), pady=1)
                customtkinter.CTkButton(
                    chip, text="✕", width=16, height=16,
                    fg_color="transparent", hover_color=PINK_MID,
                    text_color=PINK_DARK, font=("Nunito", 9, "bold"),
                    corner_radius=8,
                    command=lambda gi=g_idx, tid=tag["id"]: _remove_tag_from_group(gi, tid),
                ).pack(side="left", padx=(0, 3), pady=1)

            entry_g = customtkinter.CTkEntry(
                group_row,
                placeholder_text="+ OR tag...",
                border_width=1, border_color=BORDER,
                fg_color=PINK_SOFT, text_color=TEXT,
                placeholder_text_color=TEXT_MUTED,
                font=("Quicksand", 10), width=140, height=24,
                corner_radius=20,
            )
            entry_g.pack(side="left", padx=4, pady=3)

            # Bind to the inner tkinter Entry so KeyRelease fires reliably
            raw = entry_g._entry
            raw.bind("<KeyRelease>", lambda e, gi=g_idx, re=raw: _on_tag_key(e, gi, re))
            raw.bind("<Down>", lambda e, re=raw: _on_entry_down(re))
            raw.bind("<Return>", lambda e, re=raw: _on_entry_return(re))
            raw.bind("<Escape>", lambda e: _close_dropdown())
            raw.bind("<FocusOut>", lambda e: window.after(200, _maybe_close_dropdown))
            _group_entries.append(entry_g)

            customtkinter.CTkButton(
                group_row, text="✕", width=20, height=20,
                fg_color="transparent", hover_color=PINK_MID,
                text_color="#cc4444", font=("Nunito", 10, "bold"),
                corner_radius=10,
                command=lambda gi=g_idx: _remove_group(gi),
            ).pack(side="right", padx=(0, 4), pady=3)

        if refocus is not None and refocus < len(_group_entries):
            window.after(10, lambda: _group_entries[refocus].focus_set())

    #______Results_______

    results_frame = customtkinter.CTkScrollableFrame(window, fg_color='transparent', scrollbar_button_color=PINK_MID)
    results_frame.pack(fill="both", expand=True, padx=12, pady=10)

    load_more_row = customtkinter.CTkFrame(window, fg_color="transparent")
    load_more_row.pack(fill="x", padx=12, pady=(0, 10))

    load_more_btn = customtkinter.CTkButton(
        load_more_row,
        text="Load more",
        width=140,
        height=30,
        fg_color=PINK_LIGHT,
        hover_color=PINK_MID,
        text_color=PINK_DARK,
        font=("Nunito", 12, "bold"),
        corner_radius=20,
    )

    def _submit_image_hover(label, url, size, images):
        future = submit_image_task(async_load_with_hover, label, url, size, images)
        image_futures.append(future)

    def _cancel_image_tasks():
        futures = list(image_futures)
        image_futures.clear()
        for f in futures:
            f.cancel()

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
                vn["added_at"] = time.time()
                vns_in_cat.append(vn)
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
    def _filter_results(api_data: list) -> list:
        max_nsfw_filter = 0
        if settings["allow_suggestive"]:
            max_nsfw_filter = 1
        if settings["allow_explicit"]:
            max_nsfw_filter = 2
        return [v for v in api_data if (v.get("image") or {}).get('sexual', 0) <= max_nsfw_filter]

    def render_results(api_data: list) -> None:
        _render_gen[0] += 1
        _last_rendered_size[:] = [window.winfo_width(), window.winfo_height()]
        for widget in results_frame.winfo_children():
            widget.destroy()
        filtered_data = _filter_results(api_data)
        _rendered_count[0] = 0

        if not filtered_data:
            customtkinter.CTkLabel(
                results_frame,
                text="No results found.",
                text_color="gray",
            ).pack(pady=20)
            _update_load_more_button()
            return

        if view_mode.get() == "list":
            _render_list(filtered_data, _render_gen[0], start_index=0)
        else:
            _render_grid(filtered_data, _render_gen[0], start_index=0)
        _rendered_count[0] = len(filtered_data)
        _update_load_more_button()

    def _render_list(api_data: list, gen: int, start_index: int = 0) -> None:
        cover_size = cover_size_for_width(window.winfo_width(), "list")
        BATCH = 5

        def _render_batch(index: int) -> None:
            if _render_gen[0] != gen:
                return
            for vn in api_data[index : index + BATCH]:
                year = (vn.get("released") or "?")[:4]
                img_url = (vn.get("image") or {}).get("url", "")
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
                title_lbl.bind("<Configure>", lambda e, lbl=title_lbl, tf=text_frame: lbl.configure(wraplength=max(100, logical_width(tf) - 8)))

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
                desc_lbl.bind("<Configure>", lambda e, lbl=desc_lbl, tf=text_frame: lbl.configure(wraplength=max(100, logical_width(tf) - 8)))

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

    def _render_grid(api_data: list, gen: int, start_index: int = 0) -> None:
        cover_size = cover_size_for_width(window.winfo_width(), "grid")
        card_width = cover_size[0] + 30
        columns = max(1, logical_width(window) // card_width)
        for i in range(20):
            results_frame.columnconfigure(i, weight=0)
        results_frame.columnconfigure(list(range(columns)), weight=1)
        BATCH = 5

        def _render_batch(index: int) -> None:
            if _render_gen[0] != gen:
                return
            for i, vn in enumerate(api_data[index : index + BATCH]):
                idx = start_index + index + i
                year = (vn.get("released") or "?")[:4]
                img_url = (vn.get("image") or {}).get("url", "")
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
                title_lbl.bind("<Configure>", lambda e, lbl=title_lbl, c=card: lbl.configure(wraplength=max(100, logical_width(c) - 8)))

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

    def _append_render_results(api_data: list) -> None:
        filtered_data = _filter_results(api_data)
        if not filtered_data:
            _update_load_more_button()
            return
        _render_gen[0] += 1
        gen = _render_gen[0]
        start_index = _rendered_count[0]
        if view_mode.get() == "list":
            _render_list(filtered_data, gen, start_index=start_index)
        else:
            _render_grid(filtered_data, gen, start_index=start_index)
        _rendered_count[0] += len(filtered_data)
        _update_load_more_button()

    def _set_load_more_loading(loading: bool) -> None:
        _is_loading_more[0] = loading
        _update_load_more_button()

    def _update_load_more_button() -> None:
        should_show = bool(last_results) and (_has_more_pages[0] or _is_loading_more[0])
        if not should_show:
            load_more_btn.pack_forget()
            return
        load_more_btn.configure(
            text="Loading..." if _is_loading_more[0] else "Load more",
            state="disabled" if _is_loading_more[0] else "normal",
        )
        if not load_more_btn.winfo_manager():
            load_more_btn.pack(pady=(2, 8))

    def _merge_results(existing: list, incoming: list) -> tuple[list, list]:
        merged = list(existing)
        seen_ids = {v.get("id") for v in merged}
        added = []
        for vn in incoming:
            vn_id = vn.get("id")
            if vn_id is None or vn_id not in seen_ids:
                merged.append(vn)
                added.append(vn)
                if vn_id is not None:
                    seen_ids.add(vn_id)
        return merged, added

    def _load_more() -> None:
        if _is_loading_more[0] or not _has_more_pages[0]:
            return
        _set_load_more_loading(True)
        token_snapshot = _search_token[0]
        page_snapshot = _current_page[0] + 1
        query_snapshot = _current_query[0]
        tg_snapshot = [list(g) for g in _current_tag_groups[0]]

        def _search_next_page():
            try:
                api_data, has_more = search_vns(
                    title=query_snapshot,
                    tag_groups=tg_snapshot,
                    page=page_snapshot,
                )
            except Exception as e:
                traceback.print_exc()
                window.after(0, lambda e=e: _show_error(e, clear_results=False))
                return
            window.after(0, lambda: _show_more_results(token_snapshot, page_snapshot, api_data, has_more))

        _search_executor.submit(_search_next_page)

    def _show_error(error, clear_results: bool = True):
        _set_load_more_loading(False)
        if clear_results:
            for widget in results_frame.winfo_children():
                widget.destroy()
            _rendered_count[0] = 0
            customtkinter.CTkLabel(
                results_frame,
                text=f'Search failed. Please check your internet connection and try again. Error: {error}',
                font=FONT_BODY,
                text_color="#f87171",
                wraplength=400
            ).pack(pady=30)
        _has_more_pages[0] = False
        _update_load_more_button()

    def _show_more_results(token: int, page: int, api_data: list, has_more: bool) -> None:
        if token != _search_token[0]:
            return
        _set_load_more_loading(False)
        _current_page[0] = page
        _has_more_pages[0] = has_more
        merged_results, added_results = _merge_results(last_results, api_data)
        last_results[:] = merged_results
        _append_render_results(added_results)

    def do_search() -> None:
        query = entry.get().strip()
        tg = [[t["id"] for t in group] for group in tag_groups if group]

        if not query and not tg:
            return

        _cancel_image_tasks()
        _close_dropdown()
        _set_load_more_loading(False)
        _rendered_count[0] = 0

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

        tg_snapshot = [list(g) for g in tg]
        query_snapshot = query
        _search_token[0] += 1
        token_snapshot = _search_token[0]
        _current_query[0] = query_snapshot
        _current_tag_groups[0] = tg_snapshot
        _current_page[0] = 1
        _has_more_pages[0] = False

        def _search():
            try:
                api_data, has_more = search_vns(title=query_snapshot, tag_groups=tg_snapshot, page=1)
            except Exception as e:
                traceback.print_exc()
                window.after(0, lambda e=e: _show_error(e))
                return
            window.after(0, lambda: _show_results(token_snapshot, api_data, has_more))

        def _show_results(token: int, api_data: list, has_more: bool):
            if token != _search_token[0]:
                return
            last_results.clear()
            last_results.extend(api_data)
            _has_more_pages[0] = has_more
            render_results(last_results)

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
    load_more_btn.configure(command=_load_more)
    enable_touchpad_scroll(window, results_frame)
