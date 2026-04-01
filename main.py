from app.utils.save import load_data
from app.ui.shared.theme import (
    set_active_theme,
    set_font_scale,
    set_high_contrast_mode,
    DEFAULT_THEME_NAME,
    DEFAULT_FONT_SCALE,
)

if __name__ == "__main__":
    data = load_data()
    settings = data.get("settings", {})
    theme_name = settings.get("theme_name", DEFAULT_THEME_NAME)
    font_scale = settings.get("font_scale", DEFAULT_FONT_SCALE)
    high_contrast_mode = bool(settings.get("high_contrast_mode", False))
    try:
        set_active_theme(theme_name)
    except ValueError:
        set_active_theme(DEFAULT_THEME_NAME)
    set_font_scale(font_scale)
    set_high_contrast_mode(high_contrast_mode)
    from app.ui.main.main_window import run
    run()
#do not touch
