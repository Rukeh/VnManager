import requests


def search_vns(title):
    """
    Searches VnDB for visual novels matching the given title
    Returns a list of results from the VNDB Kana API.
    """
    url = "https://api.vndb.org/kana/vn"
    payload = {
        "filters": ["search", "=", title],
        "fields": "id, title, alttitle, released, languages, platforms, image.url, length, description, rating",
        "results": 50,
    }
    response = requests.post(url=url, json=payload)
    response.raise_for_status()
    return response.json()["results"]