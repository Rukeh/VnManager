import customtkinter

from app.ui.shared.theme import *
from app.api.vndb import search_news


def build_news(parent) -> None:
    """
    Renders a placeholder news screen into parent.
    """
    container = customtkinter.CTkFrame(parent, fg_color="transparent")
    container.place(relx=0.5, rely=0.5, anchor="center")

    customtkinter.CTkLabel(
        container,
        text="News",
        font=FONT_H1,
        text_color=TEXT,
    ).pack(pady=(0, 8))

    customtkinter.CTkLabel(
        container,
        text="This section is ready for updates.\nNext step: connect a news source and render entries.",
        font=FONT_BODY,
        text_color=TEXT_MUTED,
        justify="center",
    ).pack()
