import os

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers():
    """Return default headers with API key."""
    return {"X-API-Key": os.getenv("API_KEY", "changeme")}


def test_gds_top_courses():
    """Test GDS top courses endpoint."""
    r = client.get(
        "/api/gds/top-courses?algorithm=pagerank&top_k=3",
        headers=_headers(),
    )
    assert r.status_code == 200
    data = r.json()
    assert "results" in data


def test_ml_recommendations():
    """Test ML recommendations endpoint."""
    r = client.get(
        "/api/ml/recommendations?student_id=s1&top_k=3",
        headers=_headers(),
    )
    assert r.status_code in (200, 404)  # depends on seeded data
    if r.status_code == 200:
        assert "recommendations" in r.json()


def test_llm_query_templates():
    """Test LLM query endpoint."""
    r = client.post(
        "/api/llm/query",
        json={"question": "courses without prerequisites"},
        headers=_headers(),
    )
    assert r.status_code == 200
    data = r.json()
    assert "cypher" in data
    assert "result" in data
