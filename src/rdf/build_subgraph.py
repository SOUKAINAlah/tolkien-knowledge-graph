from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from src.rdf.build_rdf import build_entity_rdf, entity_uri, slugify
from src.extract.detect_type import detect_infobox_name
from src.extract.detect_type_by_category import guess_type_from_categories


SCHEMA = Namespace("https://schema.org/")

# Propriétés qu'on suit pour trouver les voisins
FOLLOW_PROPERTIES = {
    SCHEMA.location,
    SCHEMA.memberOf,
    SCHEMA.additionalType,
}

def guess_schema_type_from_infobox(infobox_name: str | None):
    if infobox_name is None:
        return SCHEMA.Thing

    if "character" in infobox_name:
        return SCHEMA.Person
    if "place" in infobox_name or "location" in infobox_name:
        return SCHEMA.Place
    if "organization" in infobox_name or "council" in infobox_name or "faction" in infobox_name:
        return SCHEMA.Organization

    return SCHEMA.Thing


def build_min_entity(title: str) -> Graph:
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("rdfs", RDFS)

    s = entity_uri(title)

    # title in API should have spaces
    api_title = title.replace("_", " ")
    guessed = guess_type_from_categories(api_title)

    rdf_type = {
        "Person": SCHEMA.Person,
        "Place": SCHEMA.Place,
        "Organization": SCHEMA.Organization,
        "Thing": SCHEMA.Thing,
    }[guessed]

    g.add((s, RDF.type, rdf_type))
    g.add((s, RDFS.label, Literal(api_title, lang="en")))
    g.add((s, SCHEMA.url, URIRef(f"https://tolkiengateway.net/wiki/{slugify(title)}")))

    return g



def extract_titles_from_uris(g: Graph) -> set[str]:
    """
    From triples like <.../resource/Rivendell>, extract 'Rivendell' as title.
    """
    titles = set()
    for s, p, o in g:
        if p in FOLLOW_PROPERTIES and isinstance(o, URIRef):
            uri = str(o)
            if "/resource/" in uri:
                title = uri.split("/resource/")[1]
                titles.add(title)
    return titles

if __name__ == "__main__":
    seed = "Elrond"

    # 1) Build seed entity (rich)
    g = build_entity_rdf(seed)

    # 2) Extract linked titles
    linked_titles = extract_titles_from_uris(g)
    print(f"Seed '{seed}' links to {len(linked_titles)} entities:")
    for t in sorted(list(linked_titles))[:20]:
        print("-", t)

    # 3) Add minimal entities for linked titles
    for t in linked_titles:
        g += build_min_entity(t)

    # 4) Save subgraph
    out = "data/rdf/subgraph_elrond.ttl"
    g.serialize(destination=out, format="turtle")
    print(f"✅ Subgraph written to: {out}")
