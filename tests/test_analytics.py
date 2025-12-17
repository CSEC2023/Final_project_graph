"""
Test suite for analytics-related API endpoints.

This module focuses on verifying that the analytics system correctly
summarizes high-level information about the course graph, including
course count, student count, and prerequisite statistics.
"""

import os
import sys

from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.main import app  # noqa: E402


client = TestClient(app)


def test_courses_summary_works():
    """
    Ensure that the /api/analytics/courses/summary endpoint responds correctly.

    The response should include key aggregate statistics about the course graph:
    - total_courses
    - total_students
    - avg_prerequisites
    - max_prerequisites
    - courses_without_prerequisites
    """
    headers = {"X-API-Key": os.getenv("API_KEY", "changeme")}

    response = client.get("/api/analytics/courses/summary", headers=headers)
    assert response.status_code == 200

    data = response.json()

    assert "total_courses" in data
    assert "total_students" in data
    assert "avg_prerequisites" in data
    assert "max_prerequisites" in data
    assert "courses_without_prerequisites" in data
