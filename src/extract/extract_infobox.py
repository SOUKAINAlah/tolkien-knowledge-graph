import mwparserfromhell
from src.api.mediawiki import get_page_wikitext


def extract_infobox_params(wikitext: str, template_name: str = "infobox character") -> dict:
    """
    Extract parameters from a given infobox template in the wikitext.
    Returns a dict: {param_name: param_value_as_string}
    """
    code = mwparserfromhell.parse(wikitext)

    for tpl in code.filter_templates():
        name = str(tpl.name).strip().lower()
        if name == template_name.lower():
            params = {}
            for p in tpl.params:
                key = str(p.name).strip()
                value = str(p.value).strip()
                params[key] = value
            return params

    return {}


if __name__ == "__main__":
    title = "Elrond"
    wikitext = get_page_wikitext(title)

    params = extract_infobox_params(wikitext, "infobox character")

    print(f"Infobox params found: {len(params)}")
    for k in list(params.keys())[:15]:
        print(f"- {k} = {params[k][:80]}{'...' if len(params[k]) > 80 else ''}")
