import requests
import customtkinter
from PIL import Image, ImageDraw
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

_session = requests.Session()
_session.headers.update({"User-Agent": "VnManager/1.0"})

_executor = ThreadPoolExecutor(max_workers=10)

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