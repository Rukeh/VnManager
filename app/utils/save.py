import json
import os
import sys
import copy

import customtkinter

_DEFAULT_DATA = {"categories": ["Not finished", "Finished", "Planned"], "vns": {}, "settings": {"allow_suggestive": False, "allow_explicit": False}}


def _get_save_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "VnManager")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
        return os.path.join(base, "vnmanager")


_SAVE_FILE = os.path.join(_get_save_dir(), "save.json")


def load_data() -> dict:
    """
    Loads save data from the platform save path, returning defaults if the file is missing.
    """
    try:
        with open(_SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return copy.deepcopy(_DEFAULT_DATA)


def _show_save_error(message: str) -> None:
    """
    Displays a popup window with an error message when saving fails.
    """
    popup = customtkinter.CTkToplevel()
    popup.title("Save error")
    popup.geometry("340x110")
    popup.after(50, lambda: popup.lift())
    customtkinter.CTkLabel(
        popup,
        text=f"Failed to save data:\n{message}",
        text_color="red",
        wraplength=300,
    ).pack(pady=16)
    customtkinter.CTkButton(popup, text="OK", width=80, command=popup.destroy).pack()


def save_data(data: dict) -> None:
    """
    Saves data to the save file. Creates the directory if it doesn't exist.
    Shows an error popup if the write fails.
    """
    try:
        os.makedirs(os.path.dirname(_SAVE_FILE), exist_ok=True)
        with open(_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        _show_save_error(str(e))
