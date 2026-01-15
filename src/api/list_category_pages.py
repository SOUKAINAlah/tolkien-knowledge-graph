import requests

API_URL = "https://tolkiengateway.net/w/api.php"
HEADERS = {"User-Agent": "TolkienKGBot/1.0 (student project)"}

def get_category_members(category: str, limit: int = 50) -> list[str]:
    titles = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": limit,
        "format": "json"
    }

    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()

    for page in data["query"]["categorymembers"]:
        titles.append(page["title"])

    return titles


if __name__ == "__main__":
    pages = get_category_members("Third Age characters", limit=20)
    print("Found pages:")
    for p in pages:
        print("-", p)
