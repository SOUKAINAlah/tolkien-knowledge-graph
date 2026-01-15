from flask import Flask, request, Response, render_template
import requests
from urllib.parse import quote

FUSEKI_SPARQL = "http://localhost:3030/tolkien/sparql"
BASE = "https://yourkg.org/resource/"

app = Flask(__name__)

PREFIXES = """
PREFIX schema: <https://schema.org/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:    <http://www.w3.org/2002/07/owl#>
"""

def sparql_query(query: str, accept: str = "application/sparql-results+json") -> requests.Response:
    return requests.post(
        FUSEKI_SPARQL,
        data={"query": query},
        headers={"Accept": accept},
        timeout=30,
    )

def wants_turtle() -> bool:
    accept = (request.headers.get("Accept") or "").lower()
    return ("text/turtle" in accept) or ("application/x-turtle" in accept) or ("application/n-triples" in accept)

def normalize_id(rid: str) -> str:
    rid = (rid or "").strip().replace(" ", "_")
    return rid

def to_local_path(uri: str) -> str:
    # https://yourkg.org/resource/Elrond -> /resource/Elrond
    if uri.startswith(BASE):
        return "/resource/" + uri.split("/resource/")[1]
    return uri

def parse_bindings(res_json: dict, vars_: list[str]) -> list[dict]:
    out = []
    for row in res_json.get("results", {}).get("bindings", []):
        item = {}
        for v in vars_:
            if v in row:
                item[v] = row[v]["value"]
        out.append(item)
    return out

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/list/<type_name>")
def list_entities(type_name: str):
    # On supporte Person, Place, Organization, Event
    allowed = {"Person", "Place", "Organization", "Event"}
    if type_name not in allowed:
        return Response("Unknown type. Use Person|Place|Organization|Event", status=400)

    q = PREFIXES + f"""
SELECT ?s ?label WHERE {{
  ?s a schema:{type_name} ;
     rdfs:label ?label .
  FILTER(lang(?label) = "en")
}}
ORDER BY ?label
LIMIT 200
"""
    r = sparql_query(q)
    if r.status_code != 200:
        return Response(r.text, status=503, mimetype="text/plain")

    items = parse_bindings(r.json(), ["s", "label"])
    # Convert to local /resource links
    for it in items:
        it["href"] = to_local_path(it["s"])

    return render_template("list.html", type_name=type_name, items=items)

@app.get("/search")
def search():
    qtext = (request.args.get("q") or "").strip()
    if not qtext:
        return render_template("search.html", q="", items=[])

    # Sécuriser la chaîne AVANT le f-string
    safe_q = qtext.replace('"', '\\"')

    q = PREFIXES + f"""
SELECT ?s ?label WHERE {{
  ?s rdfs:label ?label .
  FILTER(lang(?label) = "en")
  FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{safe_q}")))
}}
ORDER BY ?label
LIMIT 200
"""
    r = sparql_query(q)
    if r.status_code != 200:
        return Response(r.text, status=503, mimetype="text/plain")

    items = parse_bindings(r.json(), ["s", "label"])
    for it in items:
        it["href"] = to_local_path(it["s"])

    return render_template("search.html", q=qtext, items=items)


@app.get("/resource/<path:rid>")
def resource(rid: str):
    rid = normalize_id(rid)
    uri = f"{BASE}{quote(rid)}"

    if wants_turtle():
        construct = PREFIXES + f"""
CONSTRUCT {{
  <{uri}> ?p ?o .
  ?s ?p2 <{uri}> .
}}
WHERE {{
  {{
    <{uri}> ?p ?o .
  }} UNION {{
    ?s ?p2 <{uri}> .
  }} UNION {{
    GRAPH ?g {{ <{uri}> ?p ?o . }}
  }} UNION {{
    GRAPH ?g {{ ?s ?p2 <{uri}> . }}
  }}
}}
"""
        r = sparql_query(construct, accept="text/turtle")
        return Response(r.text, status=r.status_code, mimetype="text/turtle")

    # HTML view
    q_label = PREFIXES + f"""
SELECT ?label WHERE {{
  {{ <{uri}> rdfs:label ?label . }}
  UNION
  {{ GRAPH ?g {{ <{uri}> rdfs:label ?label . }} }}
}}
LIMIT 1
"""
    q_out = PREFIXES + f"""
SELECT ?p ?o WHERE {{
  {{ <{uri}> ?p ?o . }}
  UNION
  {{ GRAPH ?g {{ <{uri}> ?p ?o . }} }}
}}
ORDER BY ?p
LIMIT 300
"""
    q_in = PREFIXES + f"""
SELECT ?s ?p WHERE {{
  {{ ?s ?p <{uri}> . }}
  UNION
  {{ GRAPH ?g {{ ?s ?p <{uri}> . }} }}
}}
ORDER BY ?p ?s
LIMIT 300
"""
    label_res = sparql_query(q_label)
    out_res = sparql_query(q_out)
    in_res = sparql_query(q_in)

    if label_res.status_code != 200:
        return Response(label_res.text, status=503, mimetype="text/plain")

    label = rid.replace("_", " ")
    try:
        b = label_res.json()["results"]["bindings"]
        if b and "label" in b[0]:
            label = b[0]["label"]["value"]
    except Exception:
        pass

    out_json = out_res.json() if out_res.status_code == 200 else {"results": {"bindings": []}}
    in_json = in_res.json() if in_res.status_code == 200 else {"results": {"bindings": []}}

    def fmt_term(term):
        v = term["value"]
        t = term["type"]
        if t == "uri":
            if v.startswith(BASE):
                local = v.split("/resource/")[1]
                return f'<a href="/resource/{local}">{local}</a>'
            return f'<a href="{v}">{v}</a>'
        lang = term.get("xml:lang")
        dt = term.get("datatype")
        extra = f" <small>@{lang}</small>" if lang else (f" <small>^^{dt}</small>" if dt else "")
        return f"{v}{extra}"

    outgoing = [(fmt_term(row["p"]), fmt_term(row["o"])) for row in out_json["results"]["bindings"]]
    incoming = [(fmt_term(row["p"]), fmt_term(row["s"])) for row in in_json["results"]["bindings"]]

    html = render_template("resource.html", label=label, rid=rid, uri=uri, outgoing=outgoing, incoming=incoming)
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
