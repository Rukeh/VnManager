import customtkinter
from app.utils.text import get_clean_tags
from app.ui.shared.theme import *

_low_perf = [False]


def set_low_perf_mode(enabled: bool) -> None:
    _low_perf[0] = enabled


def logical_width(widget) -> int:
    """
    Returns the widget's width in logical pixels, correcting for Windows DPI scaling.
    winfo_width() returns physical pixels at high DPI, but CTkLabel wraplength
    expects logical pixels matching CTk's internal layout scale.
    """
    try:
        scale = customtkinter.ScalingTracker.get_widget_scaling(widget)
    except Exception:
        scale = 1.0
    return int(widget.winfo_width() / scale)

def render_tags(parent, vn: dict, max_tags: int = 6, include_spoilers: bool = False) -> None:
    """Renders tag chips into the given parent frame."""
    tags = get_clean_tags(vn, max_tags=max_tags, include_spoilers=include_spoilers)
    if not tags:
        return
    if _low_perf[0]:
        customtkinter.CTkLabel(
            parent,
            text=" · ".join(tags),
            font=("Quicksand", 10),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))
        return
    tag_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
    tag_frame.pack(anchor="w", fill="x", pady=(4, 0))
    for name in tags:
        chip = customtkinter.CTkFrame(tag_frame, fg_color=PINK_SOFT, corner_radius=20, border_width=1, border_color=BORDER)
        chip.pack(side="left", padx=(0, 4), pady=2)
        customtkinter.CTkLabel(chip, text=name, font=("Quicksand", 10), text_color=TEXT_MUTED).pack(padx=8, pady=2)

def enable_touchpad_scroll(root, *scrollable_frames: customtkinter.CTkScrollableFrame) -> None:
    """
    Enables Linux touchpad scrolling for one or more CTkScrollableFrames by
    binding Button-4/5 events at the root window level and routing them to
    whichever registered frame the cursor is currently over.
    Args:
        root:              The root CTk or CTkToplevel window to bind events on.
        scrollable_frames: One or more CTkScrollableFrame instances to enable scrolling for.
    """
    canvases = {sf._parent_canvas: sf._parent_canvas for sf in scrollable_frames}

    def _route(event, direction):
        x, y = root.winfo_pointerx(), root.winfo_pointery()
        for canvas in canvases:
            cx = canvas.winfo_rootx()
            cy = canvas.winfo_rooty()
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
            if cx <= x <= cx + cw and cy <= y <= cy + ch:
                canvas.yview_scroll(direction, "units")
                return

    root.bind("<Button-4>", lambda e: _route(e, -1), add="+")
    root.bind("<Button-5>", lambda e: _route(e,  1), add="+")