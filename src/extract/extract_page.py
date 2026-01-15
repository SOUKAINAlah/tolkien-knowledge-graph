from src.api.mediawiki import get_page_wikitext

if __name__ == "__main__":
    title = "Elrond"
    wikitext = get_page_wikitext(title)

    print("=== WIKITEXT (first 600 chars) ===")
    print(wikitext[:600])
