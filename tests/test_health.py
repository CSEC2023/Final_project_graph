"""
Tests for the /health endpoint of the FastAPI application.

These tests verify that:
- The endpoint responds successfully.
- The Neo4j connection check returns the expected fields.
"""

import os
import sys

# Add project root (/app) to PYTHONPATH so we can import app.main
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_ok():
    """
    Ensure the /health endpoint returns a 200 status code
    and the expected structure with Neo4j connection status.
    """
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["neo4j"] is True

def test_docs_available():
    """Ensure that Swagger UI (/docs) is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200