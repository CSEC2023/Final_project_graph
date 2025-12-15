import os
from typing import Optional
from neo4j import GraphDatabase, Driver

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class Neo4jClient:
    """Simple Neo4j driver wrapper (lazy init)."""

    def __init__(self) -> None:
        self._driver: Optional[Driver] = None

    def connect(self) -> None:
        if self._driver is None:
            self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # optional but nice:
            try:
                self._driver.verify_connectivity()
            except Exception:
                # keep app alive; /health will show error until ready
                pass

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def run(self, query: str, **params):
        self.connect()
        assert self._driver is not None
        with self._driver.session() as session:
            return list(session.run(query, **params))


neo4j_client = Neo4jClient()
