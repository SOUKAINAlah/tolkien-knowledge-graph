from src.api.mediawiki import get_page_categories

title = "Rivendell"
cats = get_page_categories(title)
print("Categories for:", title)
for c in cats:
    print("-", c)
