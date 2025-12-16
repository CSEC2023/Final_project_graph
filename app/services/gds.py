from __future__ import annotations

from typing import Literal

from app.database.neo4j import neo4j_client


GRAPH_NAME = "courseGraph"


def ensure_course_graph() -> None:
    """Create the GDS course graph if it does not exist."""
    exists_q = """
    CALL gds.graph.exists($name) YIELD exists
    RETURN exists
    """
    recs = neo4j_client.run(exists_q, name=GRAPH_NAME)
    exists = bool(recs and recs[0]["exists"])
    if exists:
        return

    project_q = """
    CALL gds.graph.project(
      $name,
      'Course',
      { REQUIRES: { orientation: 'NATURAL' } }
    )
    YIELD graphName
    RETURN graphName
    """
    neo4j_client.run(project_q, name=GRAPH_NAME)


def top_courses(algorithm: Literal["pagerank", "degree"], top_k: int = 10):
    """Return top-ranked courses using a GDS algorithm."""
    ensure_course_graph()

    if algorithm == "pagerank":
        q = """
        CALL gds.pageRank.stream($name)
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).code AS course, score
        ORDER BY score DESC
        LIMIT $k
        """
    else:
        q = """
        CALL gds.degree.stream($name)
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).code AS course, score
        ORDER BY score DESC
        LIMIT $k
        """

    recs = neo4j_client.run(q, name=GRAPH_NAME, k=top_k)
    return [{"course": r["course"], "score": float(r["score"])} for r in recs]
