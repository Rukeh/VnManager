import customtkinter
from app.utils.text import get_clean_tags
from app.ui.theme import *

def render_tags(parent, vn: dict, max_tags: int = 6, include_spoilers: bool = False) -> None:
    """Renders tag chips into the given parent frame."""
    tags = get_clean_tags(vn, max_tags=max_tags, include_spoilers=include_spoilers)
    if not tags:
        return
    tag_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
    tag_frame.pack(anchor="w", fill="x", pady=(4, 0))
    for name in tags:
        chip = customtkinter.CTkFrame(tag_frame, fg_color=PINK_SOFT, corner_radius=20, border_width=1, border_color=BORDER)
        chip.pack(side="left", padx=(0, 4), pady=2)
        customtkinter.CTkLabel(chip, text=name, font=("Quicksand", 10), text_color=TEXT_MUTED).pack(padx=8, pady=2)