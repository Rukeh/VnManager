import requests
import customtkinter
from PIL import Image
from io import BytesIO


def load_image_from_url(url, size = (150, 200)):
    """
    Fetches an image from a URL and returns it as a CTkImage
    Args:
        url(str):  Direct URL to the image
        size(tuple): (width, height) tuple for the returned image. Defaults to (150, 200)

    Returns:
        A CTkImage on success, or None if the request fails
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return customtkinter.CTkImage(img, size=size)
    except Exception:
        return None