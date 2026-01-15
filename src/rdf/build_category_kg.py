import time
from rdflib import Graph
from src.api.list_category_pages import get_category_members
from src.rdf.build_rdf import build_entity_rdf

def build_category_kg(category: str, limit: int = 20, sleep_s: float = 1.0) -> Graph:
    titles = get_category_members(category, limit=limit)

    g = Graph()
    ok, fail = 0, 0

    for i, title in enumerate(titles, start=1):
        try:
            print(f"[{i}/{len(titles)}] Building RDF for: {title}")
            g += build_entity_rdf(title)
            ok += 1
        except Exception as e:
            print(f"❌ Failed for {title}: {e}")
            fail += 1

        time.sleep(sleep_s)  # be nice to the wiki server

    print(f"✅ Done. OK={ok}, FAIL={fail}")
    return g

if __name__ == "__main__":
    category = "Third Age characters"
    g = build_category_kg(category, limit=200, sleep_s=1.0)

    out = "data/rdf/category_characters_200.ttl"
    g.serialize(destination=out, format="turtle")
    print(f"✅ KG written to: {out}")
