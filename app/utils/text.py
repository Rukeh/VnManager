import re


def clean_description(text, MAX_DESCRIPTION_LENGTH=9999):
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

def get_clean_tags(vn: dict, max_tags: int = 4, include_spoilers: bool = False) -> list[str]:
    """
    Returns a filtered, sorted list of tag name strings from a VN dict.
    Filters out spoilers (unless include_spoilers=True), lies, and sorts by rating desc.
    """
    tags = vn.get("tags") or []
    tags = [t for t in tags if not t.get("lie") and (include_spoilers or t.get("spoiler", 0) == 0)]
    tags.sort(key=lambda t: t.get("rating", 0), reverse=True)
    return [t["name"] for t in tags[:max_tags]]