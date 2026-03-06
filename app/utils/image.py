import requests
import customtkinter
from PIL import Image, ImageDraw, ImageEnhance
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

_session = requests.Session()
_session.headers.update({
    "User-Agent": "VnManager/1.0",
    "Connection": "close",
})

_executor = ThreadPoolExecutor(max_workers=4)

def load_image_from_url(url, size = (150, 200), radius=10):
    """
    Fetches an image from a URL and returns it as a CTkImage
    Args:
        url(str):  Direct URL to the image
        size(tuple): (width, height) tuple for the returned image. Defaults to (150, 200)

    Returns:
        A CTkImage on success, or None if the request fails
    """
    try:
        response = _session.get(url, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        img = round_image(img, radius)
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

def async_load_with_hover(label, url: str, size: tuple, images: dict) -> None:
    """
    Fetches an image, generates a dimmed version for hover, and applies
    the normal version to the label. Intended to be run in a thread via
    submit_image_task.

    Populates images["normal"] and images["dimmed"] with CTkImage instances,
    then schedules a UI update on the main thread via label.after().

    Args:
        label:  The CTkLabel to update once the image is loaded.
        url:    Direct URL to the image.
        size:   (width, height) tuple for the image.
        images: Dict with "normal" and "dimmed" keys to populate.
    """
    try:
        response = _session.get(url, timeout=5)
        img_pil = Image.open(BytesIO(response.content)).convert("RGBA")
        img_pil = img_pil.resize(size, Image.LANCZOS)
        img_pil = round_image(img_pil, 10)
    except Exception:
        return

    dimmed_rgb = ImageEnhance.Brightness(img_pil.convert("RGB")).enhance(0.6)
    dimmed_rgba = dimmed_rgb.convert("RGBA")
    dimmed_rgba.putalpha(img_pil.getchannel("A"))

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
            return (72, 96)
        elif window_width < 1400:
            return (90, 120)
        else:
            return (112, 150)
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