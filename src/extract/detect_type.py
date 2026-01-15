import mwparserfromhell
from src.api.mediawiki import get_page_wikitext

def detect_infobox_name(title: str) -> str | None:
    """
    Returns the first template name starting with 'infobox' found in the page wikitext.
    Example: 'infobox character', 'infobox place', ...
    """
    wikitext = get_page_wikitext(title)
    code = mwparserfromhell.parse(wikitext)

    for tpl in code.filter_templates():
        name = str(tpl.name).strip().lower()
        if name.startswith("infobox"):
            return name
    return None
