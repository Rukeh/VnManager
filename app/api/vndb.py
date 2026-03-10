import requests


def search_vns(title: str = "", tag_groups: list = None) -> list:
    """
    Searches VnDB for visual novels matching the given title and/or tag groups.
    Returns a list of results from the VNDB Kana API.
    Args:
        title:      Title query string. Can be empty if tag_groups are provided.
        tag_groups: List of lists of VNDB tag ID strings.
                    Each inner list is OR'd together, outer list is AND'd.
                    e.g. [["g17", "g542"], ["g34"]] -> (g17 OR g542) AND g34
    """
    url = "https://api.vndb.org/kana/vn"
    fields = "id, title, alttitle, released, languages, platforms, image.url, length, length_minutes, description, rating, tags.name, tags.rating, tags.spoiler, tags.lie, image.sexual"

    has_tags = any(g for g in (tag_groups or []))
    parts = []

    if title:
        parts.append(["search", "=", title])

    for group in (tag_groups or []):
        group = [tid for tid in group if tid]
        if not group:
            continue
        tag_filters = [["tag", "=", tid] for tid in group]
        if len(tag_filters) == 1:
            parts.append(tag_filters[0])
        else:
            parts.append(["or"] + tag_filters)

    if not parts:
        return []
    elif len(parts) == 1:
        final_filter = parts[0]
    else:
        final_filter = ["and"] + parts

    payload = {
        "filters": final_filter,
        "fields": fields,
        "results": 35 if has_tags else 50,
        "sort": "rating" if has_tags else "searchrank",
    }
    if has_tags:
        payload["reverse"] = True

    response = requests.post(url=url, json=payload)
    response.raise_for_status()
    return response.json()["results"]


def search_tags(query: str) -> list:
    """
    Searches VNDB for tags matching the given query string.
    Returns a list of {"id": "gXX", "name": "..."} dicts, sorted by search rank.
    """
    url = "https://api.vndb.org/kana/tag"
    payload = {
        "filters": ["search", "=", query],
        "fields": "id, name",
        "results": 12,
        "sort": "searchrank",
    }
    response = requests.post(url=url, json=payload)
    response.raise_for_status()
    return response.json()["results"]