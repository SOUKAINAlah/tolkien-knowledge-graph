from src.api.mediawiki import get_page_categories

def guess_type_from_categories(title: str) -> str:
    cats = [c.lower() for c in get_page_categories(title)]

    # Person (characters)
    if any(("characters" in c) or ("character" in c) for c in cats):
        return "Person"

    # Organization (councils, groups, factions)
    if any(
        ("council" in c)
        or ("organization" in c)
        or ("organisations" in c)
        or ("factions" in c)
        or ("groups" in c)
        for c in cats
    ):
        return "Organization"

    # Place (lots of Tolkien Gateway categories use these words)
    if any(
        ("places" in c)
        or ("place" in c)
        or ("locations" in c)
        or ("realms" in c)
        or ("realm" in c)
        or ("lands" in c)
        or ("rivers" in c)
        or ("mountains" in c)
        or ("forests" in c)
        or ("cities" in c)
        or ("towns" in c)
        or ("villages" in c)
        or ("regions" in c)
        for c in cats
    ):
        return "Place"

    return "Thing"

