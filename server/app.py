from flask import Flask, request, Response
import requests

FUSEKI_SPARQL = "http://localhost:3030/tolkien/sparql"
BASE = "https://yourkg.org/resource/"  # même base que ton KG

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
    # Si le client demande explicitement du RDF
    return ("text/turtle" in accept) or ("application/x-turtle" in accept) or ("application/n-triples" in accept)

def normalize_id(rid: str) -> str:
    # normalisation minimale (comme ton KG)
    rid = (rid or "").strip()
    rid = rid.replace(" ", "_")
    return rid

@app.get("/")
def home():
    return """
    <h2>Tolkien KG Linked Data Interface</h2>
    <p>Try: <a href="/resource/Elrond">/resource/Elrond</a></p>
    <p>Or Turtle: <code>curl -H "Accept: text/turtle" http://localhost:5000/resource/Elrond</code></p>
    """

@app.get("/resource/<path:rid>")
def resource(rid: str):
    rid = normalize_id(rid)
    uri = f"{BASE}{rid}"

    # ---------------- TURTLE (CONSTRUCT) ----------------
    if wants_turtle():
        # Robuste: récupère triples du default graph OU de n'importe quel named graph
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

    # ---------------- HTML (SELECT) ----------------
    # Label : default graph + named graphs
    q_label = PREFIXES + f"""
SELECT ?label WHERE {{
  {{
    <{uri}> rdfs:label ?label .
  }} UNION {{
    GRAPH ?g {{ <{uri}> rdfs:label ?label . }}
  }}
}}
LIMIT 1
"""

    # Outgoing : default graph + named graphs
    q_out = PREFIXES + f"""
SELECT ?p ?o WHERE {{
  {{
    <{uri}> ?p ?o .
  }} UNION {{
    GRAPH ?g {{ <{uri}> ?p ?o . }}
  }}
}}
ORDER BY ?p
LIMIT 200
"""

    # Incoming : default graph + named graphs
    q_in = PREFIXES + f"""
SELECT ?s ?p WHERE {{
  {{
    ?s ?p <{uri}> .
  }} UNION {{
    GRAPH ?g {{ ?s ?p <{uri}> . }}
  }}
}}
ORDER BY ?p ?s
LIMIT 200
"""

    label_res = sparql_query(q_label)
    out_res = sparql_query(q_out)
    in_res = sparql_query(q_in)

    # si Fuseki répond pas / erreur
    if label_res.status_code != 200:
        return Response(label_res.text, status=503, mimetype="text/plain")
    if out_res.status_code != 200:
        return Response(out_res.text, status=503, mimetype="text/plain")
    if in_res.status_code != 200:
        return Response(in_res.text, status=503, mimetype="text/plain")

    label_json = label_res.json()
    out_json = out_res.json()
    in_json = in_res.json()

    label = None
    try:
        bindings = label_json["results"]["bindings"]
        if bindings and "label" in bindings[0]:
            label = bindings[0]["label"]["value"]
    except Exception:
        label = None
    if not label:
        label = rid.replace("_", " ")

    def fmt_term(b):
        """Make HTML for a SPARQL JSON binding term"""
        v = b["value"]
        t = b["type"]

        if t == "uri":
            # Link internal resources nicely
            if v.startswith(BASE):
                local = v.split("/resource/")[1]
                return f'<a href="/resource/{local}">{local}</a>'
            return f'<a href="{v}">{v}</a>'

        # literal
        lang = b.get("xml:lang")
        dt = b.get("datatype")
        extra = ""
        if lang:
            extra = f" <small>@{lang}</small>"
        elif dt:
            extra = f" <small>^^{dt}</small>"
        return f"{v}{extra}"

    outgoing_rows = []
    for row in out_json.get("results", {}).get("bindings", []):
        outgoing_rows.append((fmt_term(row["p"]), fmt_term(row["o"])))

    incoming_rows = []
    for row in in_json.get("results", {}).get("bindings", []):
        incoming_rows.append((fmt_term(row["p"]), fmt_term(row["s"])))

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{label}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    code {{ background:#f2f2f2; padding:2px 6px; border-radius:4px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f7f7f7; text-align: left; }}
    .meta {{ color:#444; }}
  </style>
</head>
<body>
  <h2>{label}</h2>
  <p class="meta"><b>URI:</b> <code>{uri}</code></p>
  <p class="meta">
    <a href="/resource/{rid}">HTML</a> |
    <span>Turtle via Accept header</span>
    &nbsp; (try: <code>curl -H "Accept: text/turtle" http://localhost:5000/resource/{rid}</code>)
  </p>

  <h3>Properties (outgoing)</h3>
  <table>
    <tr><th>Predicate</th><th>Object</th></tr>
    {''.join([f"<tr><td>{p}</td><td>{o}</td></tr>" for p,o in outgoing_rows]) or "<tr><td colspan=2>No data</td></tr>"}
  </table>

  <h3>Incoming properties</h3>
  <table>
    <tr><th>Predicate</th><th>Subject</th></tr>
    {''.join([f"<tr><td>{p}</td><td>{s}</td></tr>" for p,s in incoming_rows]) or "<tr><td colspan=2>No data</td></tr>"}
  </table>
</body>
</html>
"""
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

