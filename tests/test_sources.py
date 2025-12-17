"""
Tests for course-related graph analytics endpoints, including
cycle detection and shortest prerequisite path computation.
"""

import os
import sys

# Ensure project root is in the Python path when running inside Docker
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from fastapi.testclient import TestClient  # type: ignore
from app.main import app  # type: ignore


client = TestClient(app)


def test_prerequisite_cycles_endpoint():
    """
    Verify that the cycles-detection endpoint responds and
    returns a list of cycle structures.
    """
    response = client.get("/api/courses/prerequisites/cycles", params={"limit": 5})
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if data:  # only validate structure if cycles exist
        assert "courses" in data[0]


def test_shortest_path_endpoint():
    """
    Ensure that the shortest-path endpoint returns the expected
    response structure, regardless of whether a path exists.
    """
    response = client.get(
        "/api/courses/path/shortest",
        params={"from_course": "ACCY 201", "to_course": "ACCY 301"},
    )
    assert response.status_code == 200

    data = response.json()
    assert "from_course" in data
    assert "to_course" in data
    assert "path" in data
    assert "length" in data
    assert isinstance(data["path"], list)
