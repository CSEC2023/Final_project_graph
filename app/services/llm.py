import os
from typing import Tuple, Dict, Any

from app.database.neo4j import neo4j_client

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SAFE_TEMPLATES = [
    # (trigger substrings), cypher, params_builder
    (["most prerequisites", "max prerequisites"], """
        MATCH (c:Course)
        OPTIONAL MATCH (c)-[:REQUIRES]->(p:Course)
        RETURN c.code AS course, count(p) AS prereq_count
        ORDER BY prereq_count DESC
        LIMIT 10
    """, lambda q: ({})),
    (["courses without prerequisites", "no prerequisites"], """
        MATCH (c:Course)
        WHERE NOT (c)-[:REQUIRES]->(:Course)
        RETURN c.code AS course
        ORDER BY course
        LIMIT 20
    """, lambda q: ({})),
    (["shortest path"], """
        // expects: "shortest path from X to Y"
        WITH $from AS from_code, $to AS to_code
        MATCH (start:Course {code: from_code}), (end:Course {code: to_code})
        MATCH p = shortestPath((start)-[:REQUIRES*0..10]->(end))
        RETURN [n IN nodes(p) | n.code] AS path, size(nodes(p)) AS length
    """, lambda q: _extract_from_to(q)),
]

def _extract_from_to(question: str) -> Dict[str, Any]:
    # Very simple parser: look for quotes "ACCY 201" etc.
    import re
    codes = re.findall(r'"([^"]+)"', question)
    if len(codes) >= 2:
        return {"from": codes[0], "to": codes[1]}
    # fallback defaults
    return {"from": "ACCY 201", "to": "ACCY 301"}

def _template_router(question: str) -> Tuple[str, Dict[str, Any], str]:
    qlow = question.lower()
    for triggers, cypher, params_builder in SAFE_TEMPLATES:
        if any(t in qlow for t in triggers):
            params = params_builder(question)
            return cypher, params, "template"
    # default template: basic stats
    return """
        MATCH (c:Course)
        RETURN count(c) AS total_courses
    """, {}, "default-template"

def _openai_to_cypher(question: str) -> Tuple[str, Dict[str, Any], str]:
    """
    Uses OpenAI to generate Cypher, but still applies a safety filter:
    - Only allow queries starting with MATCH / CALL gds / RETURN / WITH
    - Disallow write ops (CREATE/MERGE/DELETE/SET)
    """
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    schema = """
    Schema:
    Nodes: (:Course {code}), (:Student {id,name}), (:Professor {id,name})
    Rels: (:Course)-[:REQUIRES]->(:Course),
          (:Student)-[:HAS_PASSED {grade}]->(:Course),
          (:Professor)-[:TEACHES]->(:Course)
    """

    prompt = f"""
You are a Neo4j Cypher expert.
Generate ONE read-only Cypher query to answer the user question.
Rules:
- READ ONLY (no CREATE, MERGE, DELETE, SET, DROP)
- Prefer LIMIT 20
- Return useful columns
{schema}
Question: {question}
Cypher:
""".strip()

    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    cypher = (resp.output_text or "").strip()

    # Safety filter
    banned = ["create", "merge", "delete", "set", "drop", "remove", "call dbms", "apoc."]
    low = cypher.lower()
    if any(b in low for b in banned):
        # fallback to templates
        return _template_router(question)[0], {}, "fallback-template (unsafe llm)"

    if not (low.startswith("match") or low.startswith("with") or low.startswith("call")):
        return _template_router(question)[0], {}, "fallback-template (invalid llm)"

    return cypher, {}, "openai"

def nl_to_cypher(question: str) -> Tuple[str, Dict[str, Any], str]:
    if OPENAI_API_KEY:
        try:
            return _openai_to_cypher(question)
        except Exception:
            return _template_router(question)
    return _template_router(question)

def run_llm_query(question: str):
    cypher, params, mode = nl_to_cypher(question)
    recs = neo4j_client.run(cypher, **params)
    # Make records JSON-friendly
    out = []
    for r in recs:
        row = {}
        for k, v in r.items():
            # nodes/lists handled as-is; most results are primitives
            row[k] = v
        out.append(row)
    return cypher, params, out, mode
