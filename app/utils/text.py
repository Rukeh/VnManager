import re

MAX_DESCRIPTION_LENGTH = 300


def clean_description(text):
    """
    Strips VNDB BBCode markup from a description string and truncates it.
    Args:
        text: Raw description string from the VNDB API, or None.
    Returns:
        A plain-text string, truncated to ~300 characters.
    """
    if not text:
        return "No description available."
    text = re.sub(r'\[url=[^\]]*\](.*?)\[/url\]', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\[/?[a-zA-Z][^\]]*\]', '', text)
    text = text.strip()
    if len(text) > MAX_DESCRIPTION_LENGTH:
        text = text[:MAX_DESCRIPTION_LENGTH].rsplit(' ', 1)[0] + '...'
    return text