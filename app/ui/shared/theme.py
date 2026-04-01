import os
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ThemeColors:
    BG: str
    SIDEBAR_BG: str
    CARD_BG: str
    WHITE: str
    PINK: str
    PINK_LIGHT: str
    PINK_MID: str
    PINK_DARK: str
    PINK_SOFT: str
    PINK_HOVER_SOFT: str
    PINK_ACCENT_HOVER: str
    PINK_DANGER: str
    PINK_DANGER_HOVER: str
    TEXT: str
    TEXT_MUTED: str
    TEXT_DANGER: str
    TEXT_ERROR: str
    BORDER: str
    TOPBAR_BG: str
    COVER_HOVER_BG: str
    STATUS_BADGE_TEXT: str
    STATUS_BADGE_BG: str


@dataclass(frozen=True)
class ThemeFonts:
    FONT_TITLE: tuple
    FONT_BODY: tuple
    FONT_SMALL: tuple
    FONT_H1: tuple
    FONT_H2: tuple
    FONT_LOGO: tuple


@dataclass(frozen=True)
class Theme:
    name: str
    colors: ThemeColors
    fonts: ThemeFonts


THEMES: dict[str, Theme] = {
    "pink": Theme(
        name="pink",
        colors=ThemeColors(
            BG="#fff8f9",
            SIDEBAR_BG="#fff0f3",
            CARD_BG="#ffffff",
            WHITE="#ffffff",
            PINK="#f472b6",
            PINK_LIGHT="#fce7f3",
            PINK_MID="#fbcfe8",
            PINK_DARK="#db2777",
            PINK_SOFT="#fdf2f8",
            PINK_HOVER_SOFT="#f7b2d9",
            PINK_ACCENT_HOVER="#d90764",
            PINK_DANGER="#db6098",
            PINK_DANGER_HOVER="#d41167",
            TEXT="#3d2535",
            TEXT_MUTED="#b07090",
            TEXT_DANGER="#cc4444",
            TEXT_ERROR="#f87171",
            BORDER="#fad4e8",
            TOPBAR_BG="#ffffff",
            COVER_HOVER_BG="#c9a0b4",
            STATUS_BADGE_TEXT="#9b6dbd",
            STATUS_BADGE_BG="#e8d5f5",
        ),
        fonts=ThemeFonts(
            FONT_TITLE=("Nunito", 13, "bold"),
            FONT_BODY=("Quicksand", 12),
            FONT_SMALL=("Quicksand", 11),
            FONT_H1=("Nunito", 20, "bold"),
            FONT_H2=("Nunito", 15, "bold"),
            FONT_LOGO=("Nunito", 18, "bold"),
        ),
    ),
    "dark": Theme(
        name="dark",
        colors=ThemeColors(
            BG="#1b1420",
            SIDEBAR_BG="#23182a",
            CARD_BG="#2b1f33",
            WHITE="#ffffff",
            PINK="#f472b6",
            PINK_LIGHT="#5c2f47",
            PINK_MID="#7a3a5d",
            PINK_DARK="#ff89c5",
            PINK_SOFT="#362237",
            PINK_HOVER_SOFT="#8a4869",
            PINK_ACCENT_HOVER="#ec4899",
            PINK_DANGER="#ef5d8f",
            PINK_DANGER_HOVER="#e11d6d",
            TEXT="#f8ddeb",
            TEXT_MUTED="#c792ad",
            TEXT_DANGER="#ff7a8a",
            TEXT_ERROR="#f87171",
            BORDER="#5a3950",
            TOPBAR_BG="#261a2e",
            COVER_HOVER_BG="#7b5670",
            STATUS_BADGE_TEXT="#f2ddff",
            STATUS_BADGE_BG="#5b3a72",
        ),
        fonts=ThemeFonts(
            FONT_TITLE=("Nunito", 13, "bold"),
            FONT_BODY=("Quicksand", 12),
            FONT_SMALL=("Quicksand", 11),
            FONT_H1=("Nunito", 20, "bold"),
            FONT_H2=("Nunito", 15, "bold"),
            FONT_LOGO=("Nunito", 18, "bold"),
        ),
    ),
    "dark_mode": Theme(
        name="dark_mode",
        colors=ThemeColors(
            BG="#0f1115",
            SIDEBAR_BG="#141925",
            CARD_BG="#1b2230",
            WHITE="#ffffff",
            PINK="#4f8cff",
            PINK_LIGHT="#29344a",
            PINK_MID="#3a4b69",
            PINK_DARK="#a9c7ff",
            PINK_SOFT="#1f293a",
            PINK_HOVER_SOFT="#4a5f84",
            PINK_ACCENT_HOVER="#73a9ff",
            PINK_DANGER="#d45f5f",
            PINK_DANGER_HOVER="#bf4f4f",
            TEXT="#e7eef9",
            TEXT_MUTED="#9cabc3",
            TEXT_DANGER="#ff8f8f",
            TEXT_ERROR="#f87171",
            BORDER="#2f394d",
            TOPBAR_BG="#121824",
            COVER_HOVER_BG="#2d3a54",
            STATUS_BADGE_TEXT="#cfdeff",
            STATUS_BADGE_BG="#2b3b5b",
        ),
        fonts=ThemeFonts(
            FONT_TITLE=("Nunito", 13, "bold"),
            FONT_BODY=("Quicksand", 12),
            FONT_SMALL=("Quicksand", 11),
            FONT_H1=("Nunito", 20, "bold"),
            FONT_H2=("Nunito", 15, "bold"),
            FONT_LOGO=("Nunito", 18, "bold"),
        ),
    ),
}

DEFAULT_THEME_NAME = "pink"
MIN_FONT_SCALE = 0.8
MAX_FONT_SCALE = 1.4
DEFAULT_FONT_SCALE = 1.0


def list_themes() -> tuple[str, ...]:
    return tuple(THEMES.keys())


def _normalize_theme_name(theme_name: str) -> str:
    return theme_name.strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_theme_name(theme_name: str) -> str:
    normalized = _normalize_theme_name(theme_name)
    if normalized not in THEMES:
        raise ValueError(
            f"Unknown theme '{theme_name}'. Available themes: {', '.join(list_themes())}"
        )
    return normalized


def _load_initial_theme_name() -> str:
    requested = os.getenv("VNMANAGER_THEME")
    if not requested:
        return DEFAULT_THEME_NAME
    return _resolve_theme_name(requested)


def _normalize_font_scale(font_scale: float) -> float:
    scale = float(font_scale)
    if scale < MIN_FONT_SCALE:
        return MIN_FONT_SCALE
    if scale > MAX_FONT_SCALE:
        return MAX_FONT_SCALE
    return scale


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = hex_color.strip().lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _relative_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def _effective_colors() -> ThemeColors:
    if not _high_contrast_mode:
        return _active_theme.colors

    base = _active_theme.colors
    if _relative_luminance(base.BG) < 0.45:
        return replace(
            base,
            TEXT="#ffffff",
            TEXT_MUTED="#e5e7eb",
            TEXT_DANGER="#ffb4b4",
            TEXT_ERROR="#ff8a8a",
            BORDER="#e2e8f0",
            STATUS_BADGE_TEXT="#ffffff",
        )
    return replace(
        base,
        TEXT="#111111",
        TEXT_MUTED="#1f2937",
        TEXT_DANGER="#8b0000",
        TEXT_ERROR="#b00020",
        BORDER="#4b5563",
        STATUS_BADGE_TEXT="#111111",
    )


def _scaled_font(font_value: tuple) -> tuple:
    if len(font_value) < 2 or not isinstance(font_value[1], (int, float)):
        return font_value
    scaled_size = max(8, int(round(font_value[1] * _font_scale)))
    return (font_value[0], scaled_size, *font_value[2:])


def _effective_fonts() -> ThemeFonts:
    base = _active_theme.fonts
    return ThemeFonts(
        FONT_TITLE=_scaled_font(base.FONT_TITLE),
        FONT_BODY=_scaled_font(base.FONT_BODY),
        FONT_SMALL=_scaled_font(base.FONT_SMALL),
        FONT_H1=_scaled_font(base.FONT_H1),
        FONT_H2=_scaled_font(base.FONT_H2),
        FONT_LOGO=_scaled_font(base.FONT_LOGO),
    )


_LEGACY_COLOR_EXPORTS = (
    "BG",
    "SIDEBAR_BG",
    "CARD_BG",
    "WHITE",
    "PINK",
    "PINK_LIGHT",
    "PINK_MID",
    "PINK_DARK",
    "PINK_SOFT",
    "PINK_HOVER_SOFT",
    "PINK_ACCENT_HOVER",
    "PINK_DANGER",
    "PINK_DANGER_HOVER",
    "TEXT",
    "TEXT_MUTED",
    "TEXT_DANGER",
    "TEXT_ERROR",
    "BORDER",
    "TOPBAR_BG",
    "COVER_HOVER_BG",
    "STATUS_BADGE_TEXT",
    "STATUS_BADGE_BG",
)

_LEGACY_FONT_EXPORTS = (
    "FONT_TITLE",
    "FONT_BODY",
    "FONT_SMALL",
    "FONT_H1",
    "FONT_H2",
    "FONT_LOGO",
)

_active_theme_name = _load_initial_theme_name()
_active_theme = THEMES[_active_theme_name]
_font_scale = DEFAULT_FONT_SCALE
_high_contrast_mode = False


#helps to avoid having to change all the old code that imports these directly from theme.py, while still allowing dynamic theme switching
BG: str = _active_theme.colors.BG
SIDEBAR_BG: str = _active_theme.colors.SIDEBAR_BG
CARD_BG: str = _active_theme.colors.CARD_BG
WHITE: str = _active_theme.colors.WHITE
PINK: str = _active_theme.colors.PINK
PINK_LIGHT: str = _active_theme.colors.PINK_LIGHT
PINK_MID: str = _active_theme.colors.PINK_MID
PINK_DARK: str = _active_theme.colors.PINK_DARK
PINK_SOFT: str = _active_theme.colors.PINK_SOFT
PINK_HOVER_SOFT: str = _active_theme.colors.PINK_HOVER_SOFT
PINK_ACCENT_HOVER: str = _active_theme.colors.PINK_ACCENT_HOVER
PINK_DANGER: str = _active_theme.colors.PINK_DANGER
PINK_DANGER_HOVER: str = _active_theme.colors.PINK_DANGER_HOVER
TEXT: str = _active_theme.colors.TEXT
TEXT_MUTED: str = _active_theme.colors.TEXT_MUTED
TEXT_DANGER: str = _active_theme.colors.TEXT_DANGER
TEXT_ERROR: str = _active_theme.colors.TEXT_ERROR
BORDER: str = _active_theme.colors.BORDER
TOPBAR_BG: str = _active_theme.colors.TOPBAR_BG
COVER_HOVER_BG: str = _active_theme.colors.COVER_HOVER_BG
STATUS_BADGE_TEXT: str = _active_theme.colors.STATUS_BADGE_TEXT
STATUS_BADGE_BG: str = _active_theme.colors.STATUS_BADGE_BG

FONT_TITLE: tuple = _active_theme.fonts.FONT_TITLE
FONT_BODY: tuple = _active_theme.fonts.FONT_BODY
FONT_SMALL: tuple = _active_theme.fonts.FONT_SMALL
FONT_H1: tuple = _active_theme.fonts.FONT_H1
FONT_H2: tuple = _active_theme.fonts.FONT_H2
FONT_LOGO: tuple = _active_theme.fonts.FONT_LOGO

def _sync_legacy_exports() -> None:
    effective_colors = _effective_colors()
    effective_fonts = _effective_fonts()
    for name in _LEGACY_COLOR_EXPORTS:
        globals()[name] = getattr(effective_colors, name)
    for name in _LEGACY_FONT_EXPORTS:
        globals()[name] = getattr(effective_fonts, name)


_sync_legacy_exports()


def get_active_theme() -> Theme:
    return _active_theme


def get_active_theme_name() -> str:
    return _active_theme_name


def get_font_scale() -> float:
    return _font_scale


def get_high_contrast_mode() -> bool:
    return _high_contrast_mode


def set_active_theme(theme_name: str) -> Theme:
    global _active_theme_name, _active_theme
    resolved_name = _resolve_theme_name(theme_name)
    _active_theme_name = resolved_name
    _active_theme = THEMES[resolved_name]
    _sync_legacy_exports()
    return _active_theme


def set_font_scale(font_scale: float) -> float:
    global _font_scale
    _font_scale = _normalize_font_scale(font_scale)
    _sync_legacy_exports()
    return _font_scale


def set_high_contrast_mode(enabled: bool) -> bool:
    global _high_contrast_mode
    _high_contrast_mode = bool(enabled)
    _sync_legacy_exports()
    return _high_contrast_mode


def color(name: str) -> str:
    return getattr(_effective_colors(), name)


def font(name: str) -> tuple:
    return getattr(_effective_fonts(), name)
