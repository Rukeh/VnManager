import customtkinter
from app.utils.image import load_image_from_url, submit_image_task, cover_size_for_width
from app.utils.text import clean_description
from app.ui.theme import *
from app.ui.components import render_tags

def open_vn_detail(parent, vn: dict) -> None:
    """
    Opens a detail popup for a VN.
    Can be called from any window.
    Args:
        parent: The parent window (CTk or CTkToplevel).
        vn:     The VN dict.
    """
    _cover_ctk_img = [None]

    def _async_load_image(label, url, size):
        img = load_image_from_url(url, size=size)
        if img:
            _cover_ctk_img[0] = img
            def _apply():
                if label.winfo_exists():
                    label.configure(image=img)
                    label.image = img
            label.after(0, _apply)

    popup = customtkinter.CTkToplevel(parent)
    popup.title(vn["title"])
    popup.geometry("1200x700")
    popup.configure(fg_color=BG)
    popup.resizable(True, True)
    popup.after(100, lambda: popup.lift())
    popup.after(100, lambda: popup.focus_force())
    popup.attributes("-topmost", True)
    popup.after(200, lambda: popup.attributes("-topmost", False))

    header = customtkinter.CTkFrame(
        popup, fg_color=CARD_BG,
        border_width=1, border_color=BORDER, corner_radius=0, height=56,
    )
    header.pack(fill="x")
    header.pack_propagate(False)

    customtkinter.CTkLabel(
        header, text="📖  Details",
        font=("Nunito", 15, "bold"), text_color=PINK_DARK,
    ).pack(side="left", padx=16)

    customtkinter.CTkButton(
        header, text="✕ Close", width=80, height=30,
        fg_color=PINK_LIGHT, hover_color=PINK_MID,
        text_color=PINK_DARK, font=FONT_TITLE, corner_radius=20,
        command=popup.destroy,
    ).pack(side="right", padx=12)

    body = customtkinter.CTkScrollableFrame(
        popup, fg_color="transparent", scrollbar_button_color=PINK_MID,
    )
    body.pack(fill="both", expand=True, padx=16, pady=12)

    # Top section cover and data
    top = customtkinter.CTkFrame(body, fg_color="transparent")
    top.pack(fill="x", pady=(0, 12))

    initial_size = cover_size_for_width(1200, "detail")

    cover_frame = customtkinter.CTkFrame(
        top, width=initial_size[0], height=initial_size[1],
        fg_color=PINK_LIGHT, corner_radius=12,
    )
    cover_frame.pack(side="left", padx=(0, 16))
    cover_frame.pack_propagate(False)

    img_label = customtkinter.CTkLabel(cover_frame, text="", font=("Nunito", 32))
    img_label.place(relx=0.5, rely=0.5, anchor="center")

    img_url = (vn.get("image") or {}).get("url", "")
    if img_url:
        submit_image_task(_async_load_image, img_label, img_url, initial_size)

    meta = customtkinter.CTkFrame(top, fg_color="transparent")
    meta.pack(side="left", fill="both", expand=True)

    title_lbl = customtkinter.CTkLabel(
        meta, text=vn["title"],
        font=("Nunito", 17, "bold"), text_color=TEXT,
        anchor="w", wraplength=390, justify="left",
    )
    title_lbl.pack(fill="x")

    alt_lbl = None
    if vn.get("alttitle"):
        alt_lbl = customtkinter.CTkLabel(
            meta, text=vn["alttitle"],
            font=("Quicksand", 12, "italic"), text_color=TEXT_MUTED,
            anchor="w", wraplength=390,
        )
        alt_lbl.pack(fill="x", pady=(2, 8))
    else:
        customtkinter.CTkFrame(meta, fg_color="transparent", height=8).pack()

    value_labels = []

    def _meta_row(label: str, value: str) -> None:
        row = customtkinter.CTkFrame(meta, fg_color="transparent")
        row.pack(fill="x", pady=2)
        customtkinter.CTkLabel(
            row, text=label,
            font=("Nunito", 11, "bold"), text_color=PINK_DARK,
            width=90, anchor="w",
        ).pack(side="left")
        val_lbl = customtkinter.CTkLabel(
            row, text=value,
            font=FONT_SMALL, text_color=TEXT,
            anchor="w", wraplength=270, justify="left",
        )
        val_lbl.pack(side="left", fill="x", expand=True)
        value_labels.append(val_lbl)

    _meta_row("Released", vn.get("released") or "Unknown")

    rating = vn.get("rating")
    _meta_row("Rating", f"★ {rating / 10:.2f} / 10" if rating else "N/A")

    length_map = {1: "Very short (<2h)", 2: "Short (2-10h)", 3: "Medium (10-30h)", 4: "Long (30-50h)", 5: "Very long (>50h)"}
    length_minutes = vn.get("length_minutes")
    if length_minutes:
        h, m = divmod(length_minutes, 60)
        length_str = f"{h}h {m:02d}m" if h else f"{m}m"
        category = length_map.get(vn.get("length"))
        if category:
            length_str += f"  ({category})"
    else:
        length_str = length_map.get(vn.get("length"), "Unknown")
    _meta_row("Length", length_str)

    langs = vn.get("languages") or []
    _meta_row("Languages", ", ".join(langs) if langs else "Unknown")

    platforms = vn.get("platforms") or []
    _meta_row("Platforms", ", ".join(platforms) if platforms else "Unknown")

    if vn.get("id"):
        _meta_row("VNDB ID", vn["id"])

    render_tags(meta, vn, max_tags=8)

    #divider frame
    customtkinter.CTkFrame(body, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x", pady=(4, 12))

    customtkinter.CTkLabel(
        body, text="Description",
        font=("Nunito", 13, "bold"), text_color=PINK_DARK, anchor="w",
    ).pack(fill="x", pady=(0, 6))

    desc_lbl = customtkinter.CTkLabel(
        body,
        text=clean_description(vn.get("description")),
        font=("Quicksand", 15), text_color=TEXT_MUTED,
        anchor="w", wraplength=560, justify="left",
    )
    desc_lbl.pack(fill="x")

    _resize_job = [None]

    def _do_resize():
        _update_wraplengths()
        new_size = cover_size_for_width(popup.winfo_width(), "detail")
        if cover_frame.winfo_exists():
            cover_frame.configure(width=new_size[0], height=new_size[1])
        if _cover_ctk_img[0] is not None:
            _cover_ctk_img[0].configure(size=new_size)

    def _update_wraplengths():
        w_meta = max(100, meta.winfo_width() - 8)
        w_row  = max(80,  meta.winfo_width() - 98)
        w_body = max(100, body.winfo_width() - 32)

        if title_lbl.winfo_exists():
            title_lbl.configure(wraplength=w_meta)
        if alt_lbl and alt_lbl.winfo_exists():
            alt_lbl.configure(wraplength=w_meta)
        if desc_lbl.winfo_exists():
            desc_lbl.configure(wraplength=w_body)
        for lbl in value_labels:
            if lbl.winfo_exists():
                lbl.configure(wraplength=w_row)

    def _on_resize(event):
        if event.widget != popup:
            return
        if _resize_job[0]:
            popup.after_cancel(_resize_job[0])
        _resize_job[0] = popup.after(50, _do_resize)

    popup.bind("<Configure>", _on_resize)