from app.utils.save import load_data
from app.ui.shared.theme import set_active_theme, DEFAULT_THEME_NAME

if __name__ == "__main__":
    data = load_data()
    theme_name = data.get("settings", {}).get("theme_name", DEFAULT_THEME_NAME)
    try:
        set_active_theme(theme_name)
    except ValueError:
        set_active_theme(DEFAULT_THEME_NAME)
    from app.ui.main.main_window import run
    run()
#do not touch
