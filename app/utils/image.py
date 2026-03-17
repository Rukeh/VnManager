import os
import sys
import hashlib
import requests
import customtkinter
from PIL import Image, ImageDraw
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

_session = requests.Session()
_session.headers.update({
    "User-Agent": "VnManager/1.0",
    "Connection": "close",
})

_executor = ThreadPoolExecutor(max_workers=2)
_bytes_cache: dict[str, bytes] = {}
_cache_main_only = [False]


def _get_cover_cache_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "VnManager", "covers")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
        return os.path.join(base, "vnmanager", "covers")


_COVER_CACHE_DIR = _get_cover_cache_dir()


def _url_to_cache_path(url: str) -> str:
    filename = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(_COVER_CACHE_DIR, filename)


_cover_cache_max = [500]


def set_cover_cache_max(limit: int) -> None:
    _cover_cache_max[0] = limit


def set_cache_main_only(enabled: bool) -> None:
    _cache_main_only[0] = bool(enabled)


def _evict_oldest(max_files: int) -> None:
    try:
        files = [
            os.path.join(_COVER_CACHE_DIR, f)
            for f in os.listdir(_COVER_CACHE_DIR)
        ]
        if len(files) <= max_files:
            return
        files.sort(key=lambda p: os.path.getmtime(p))
        for path in files[:len(files) - max_files]:
            os.remove(path)
    except OSError:
        pass


def _fetch_bytes(url: str, cache_context: str = "main") -> bytes:
    should_write_cache = (cache_context == "main") or (not _cache_main_only[0])

    if url in _bytes_cache:
        return _bytes_cache[url]

    cache_path = _url_to_cache_path(url)
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            data = f.read()
        _bytes_cache[url] = data
        return data

    response = _session.get(url, timeout=5)
    response.raise_for_status()
    data = response.content

    if should_write_cache:
        _bytes_cache[url] = data
        try:
            os.makedirs(_COVER_CACHE_DIR, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(data)
            _evict_oldest(_cover_cache_max[0])
        except OSError:
            pass

    return data


def load_image_from_url(url, size=(150, 200), radius=10, cache_context: str = "main"):
    """
    Fetches an image from a URL and returns it as a CTkImage.
    Fetches at 2x the display size so images stay sharp on HiDPI/4K screens.
    Args:
        url(str):  Direct URL to the image
        size(tuple): (width, height) logical display size. Defaults to (150, 200)

    Returns:
        A CTkImage on success, or None if the request fails
    """
    try:
        data = _fetch_bytes(url, cache_context=cache_context)
        fetch_size = (size[0] * 2, size[1] * 2)
        img = Image.open(BytesIO(data)).convert("RGBA")
        img = img.resize(fetch_size, Image.BILINEAR)
        img = round_image(img, radius * 2)
        img.load()
        return customtkinter.CTkImage(img, size=size)
    except Exception:
        return None

def submit_image_task(fn, *args):
    return _executor.submit(fn, *args)

def round_image(img: Image.Image, radius: int) -> Image.Image:
    """
    Returns a copy of img with rounded corners, using an alpha mask.
    """
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, *img.size), radius=radius, fill=255)
    result = img.convert("RGBA")
    result.putalpha(mask)
    return result

def async_load_with_hover(label, url: str, size: tuple, images: dict, cache_context: str = "main") -> None:
    """
    Fetches an image at 2x resolution, generates a dimmed version for hover,
    and applies the normal version to the label. Intended to be run in a thread
    via submit_image_task. Images are fetched at 2x size for HiDPI sharpness,
    but CTkImage is told to display at the original logical size.

    Populates images["normal"] and images["dimmed"] with CTkImage instances,
    then schedules a UI update on the main thread via label.after().

    Args:
        label:  The CTkLabel to update once the image is loaded.
        url:    Direct URL to the image.
        size:   (width, height) logical display size.
        images: Dict with "normal" and "dimmed" keys to populate.
    """
    try:
        data = _fetch_bytes(url, cache_context=cache_context)
        fetch_size = (size[0] * 2, size[1] * 2)
        img_pil = Image.open(BytesIO(data)).convert("RGBA")
        img_pil = img_pil.resize(fetch_size, Image.BILINEAR)
        img_pil = round_image(img_pil, 20)
    except Exception:
        return

    overlay = Image.new("RGBA", img_pil.size, (0, 0, 0, 110))
    dimmed_rgba = Image.alpha_composite(img_pil, overlay)

    images["normal"] = customtkinter.CTkImage(img_pil, size=size)
    images["dimmed"] = customtkinter.CTkImage(dimmed_rgba, size=size)

    def _apply():
        if label.winfo_exists():
            label.configure(image=images["normal"], text="")
            label.image = images["normal"]

    label.after(0, _apply)

def cover_size_for_width(window_width: int, context: str = "card") -> tuple[int, int]:
    """
    Returns a (width, height) cover size scaled to the given window width and render context.
    Args:
        window_width: The current width of the window in pixels.
        context:      One of "card", "list", "grid", or "detail".
    Returns:
        A (width, height) tuple for use when fetching or resizing a cover image.
    """
    if context == "card":
        if window_width < 900:
            return (110, 147)
        elif window_width < 1400:
            return (135, 180)
        else:
            return (165, 220)
    elif context == "list":
        if window_width < 800:
            return (120, 145)
        elif window_width < 1200:
            return (165, 200)
        else:
            return (195, 236)
    elif context == "grid":
        if window_width < 700:
            return (130, 158)
        else:
            return (165, 200)
    elif context == "detail":
        if window_width < 500:
            return (120, 165)
        elif window_width < 750:
            return (160, 220)
        else:
            return (200, 275)
    return (90, 120)
