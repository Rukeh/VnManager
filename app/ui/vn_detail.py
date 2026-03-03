import customtkinter
from app.utils.image import load_image_from_url, submit_image_task
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
    def _async_load_image(label, url, size):
        img = load_image_from_url(url, size=size)
        if img:
            def _apply():
                if label.winfo_exists():
                    label.configure(image=img)
                    label.image = img
            label.after(0, _apply)

    popup = customtkinter.CTkToplevel(parent)
    popup.title(vn["title"])
    popup.geometry("620x540")
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

    cover_frame = customtkinter.CTkFrame(
        top, width=160, height=220, fg_color=PINK_LIGHT, corner_radius=12,
    )
    cover_frame.pack(side="left", padx=(0, 16))
    cover_frame.pack_propagate(False)

    img_label = customtkinter.CTkLabel(cover_frame, text="", font=("Nunito", 32))
    img_label.place(relx=0.5, rely=0.5, anchor="center")

    img_url = (vn.get("image") or {}).get("url", "")
    if img_url:
        submit_image_task(_async_load_image, img_label, img_url, (160, 220))

    meta = customtkinter.CTkFrame(top, fg_color="transparent")
    meta.pack(side="left", fill="both", expand=True)

    customtkinter.CTkLabel(
        meta, text=vn["title"],
        font=("Nunito", 17, "bold"), text_color=TEXT,
        anchor="w", wraplength=390, justify="left",
    ).pack(fill="x")

    if vn.get("alttitle"):
        customtkinter.CTkLabel(
            meta, text=vn["alttitle"],
            font=("Quicksand", 12, "italic"), text_color=TEXT_MUTED,
            anchor="w", wraplength=390,
        ).pack(fill="x", pady=(2, 8))
    else:
        customtkinter.CTkFrame(meta, fg_color="transparent", height=8).pack()

    def _meta_row(label: str, value: str) -> None:
        row = customtkinter.CTkFrame(meta, fg_color="transparent")
        row.pack(fill="x", pady=2)
        customtkinter.CTkLabel(
            row, text=label,
            font=("Nunito", 11, "bold"), text_color=PINK_DARK,
            width=90, anchor="w",
        ).pack(side="left")
        customtkinter.CTkLabel(
            row, text=value,
            font=FONT_SMALL, text_color=TEXT,
            anchor="w", wraplength=270, justify="left",
        ).pack(side="left", fill="x", expand=True)

    _meta_row("Released", vn.get("released") or "Unknown")

    rating = vn.get("rating")
    _meta_row("Rating", f"★ {rating:.2f} / 10" if rating else "N/A")

    length_map = {1: "Very short (<2h)", 2: "Short (2-10h)", 3: "Medium (10-30h)", 4: "Long (30-50h)", 5: "Very long (>50h)"}
    _meta_row("Length", length_map.get(vn.get("length"), "Unknown"))

    langs = vn.get("languages") or []
    _meta_row("Languages", ", ".join(langs) if langs else "Unknown")

    platforms = vn.get("platforms") or []
    _meta_row("Platforms", ", ".join(platforms) if platforms else "Unknown")

    if vn.get("id"):
        _meta_row("VNDB ID", vn["id"])

    #divider frame
    customtkinter.CTkFrame(body, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x", pady=(4, 12))

    customtkinter.CTkLabel(
        body, text="Description",
        font=("Nunito", 13, "bold"), text_color=PINK_DARK, anchor="w",
    ).pack(fill="x", pady=(0, 6))

    customtkinter.CTkLabel(
        body,
        text=clean_description(vn.get("description")),
        font=FONT_BODY, text_color=TEXT_MUTED,
        anchor="w", wraplength=560, justify="left",
    ).pack(fill="x")