import re

WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]")

def extract_wikilinks(text: str):
    """
    Returns list of tuples: (target_title, display_text_or_none)
    Example: 'Lord of [[Rivendell]]' -> [('Rivendell', None)]
             '[[Half-elven|Half-elf]]' -> [('Half-elven', 'Half-elf')]
    """
    links = []
    for m in WIKI_LINK_RE.finditer(text):
        target = m.group(1).strip()
        display = m.group(2).strip() if m.group(2) else None
        links.append((target, display))
    return links

def strip_wikilinks(text: str) -> str:
    """
    Replace [[X|Y]] by Y and [[X]] by X (keep readable text).
    """
    def repl(m):
        target = m.group(1).strip()
        display = m.group(2).strip() if m.group(2) else None
        return display if display else target

    return WIKI_LINK_RE.sub(repl, text).strip()
