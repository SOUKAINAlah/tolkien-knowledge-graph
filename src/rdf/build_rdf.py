from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from src.api.mediawiki import get_page_wikitext
from src.extract.extract_infobox import extract_infobox_params
from src.extract.wiki_links import extract_wikilinks, strip_wikilinks
import re

SCHEMA = Namespace("https://schema.org/")
BASE = "https://yourkg.org/resource/"


def slugify(title: str) -> str:
    title = title.strip()
    title = title.replace(" ", "_")
    title = re.sub(r"[^A-Za-z0-9_()-]", "", title)  # keep simple safe chars
    return title

def entity_uri(title: str) -> URIRef:
    return URIRef(BASE + slugify(title))


def build_entity_rdf(title: str) -> Graph:
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("rdfs", RDFS)

    subject = entity_uri(title)

    # --- 1) Type, label, source URL ---
    g.add((subject, RDF.type, SCHEMA.Person))
    g.add((subject, RDFS.label, Literal(title, lang="en")))
    g.add((subject, SCHEMA.url, URIRef(
        f"https://tolkiengateway.net/wiki/{slugify(title)}"
    )))

    # --- 2) Infobox extraction ---
    wikitext = get_page_wikitext(title)
    params = extract_infobox_params(wikitext, "infobox character")

    # --- 3) Mapping infobox -> RDF ---

    if "name" in params:
        g.add((subject, SCHEMA.name,
               Literal(strip_wikilinks(params["name"]), lang="en")))

    if "titles" in params:
        g.add((subject, SCHEMA.jobTitle,
               Literal(strip_wikilinks(params["titles"]), lang="en")))

        for target, _ in extract_wikilinks(params["titles"]):
            g.add((subject, SCHEMA.location, entity_uri(target)))

    if "people" in params:
        g.add((subject, SCHEMA.additionalType,
               Literal(strip_wikilinks(params["people"]), lang="en")))

        for target, _ in extract_wikilinks(params["people"]):
            g.add((subject, SCHEMA.additionalType, entity_uri(target)))

    if "affiliation" in params:
        links = extract_wikilinks(params["affiliation"])
        if links:
            for target, _ in links:
                g.add((subject, SCHEMA.memberOf, entity_uri(target)))
        else:
            g.add((subject, SCHEMA.memberOf,
                   Literal(strip_wikilinks(params["affiliation"]), lang="en")))

    if "location" in params:
        for target, _ in extract_wikilinks(params["location"]):
            g.add((subject, SCHEMA.location, entity_uri(target)))

    if "image" in params:
        g.add((subject, SCHEMA.image,
               Literal(strip_wikilinks(params["image"]), lang="en")))

    return g


if __name__ == "__main__":
    title = "Elrond"
    graph = build_entity_rdf(title)

    output_path = "data/rdf/elrond.ttl"
    graph.serialize(destination=output_path, format="turtle")

    print(f"✅ RDF written to: {output_path}")
    print(graph.serialize(format="turtle")[:800])
