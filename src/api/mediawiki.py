import requests

API_URL = "https://tolkiengateway.net/w/api.php"

HEADERS = {
    "User-Agent": "TolkienKGBot/1.0 (student project)"
}

def get_page_wikitext(title: str) -> str:
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json"
    }

    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data["parse"]["wikitext"]["*"]

def get_page_categories(title: str) -> list[str]:
    params = {
        "action": "query",
        "titles": title,
        "prop": "categories",
        "cllimit": "max",
        "format": "json"
    }

    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()
    pages = data["query"]["pages"]
    page_id = next(iter(pages.keys()))
    page = pages[page_id]

    cats = []
    for c in page.get("categories", []):
        # format: "Category:Something"
        cats.append(c["title"])
    return cats
