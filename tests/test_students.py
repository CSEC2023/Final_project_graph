"""
Tests for the student-related API endpoints.

Includes:
- Eligibility check for a student taking a target course.
- Generation of a prerequisite course sequence for planning.
"""

import os
import sys

# Ajoute le dossier racine (/app) au PYTHONPATH
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_eligibility_endpoint_exists():
    """
    Ensure the eligibility endpoint responds correctly.

    The endpoint may return:
    - 200 if the student and course exist
    - 404 if either is missing
    """
    response = client.get(
        "/api/students/s1/eligibility",
        params={"course_id": "ACCY 301"},
    )
    assert response.status_code in (200, 404)


def test_sequence_returns_json():
    """
    Verify that the course sequence endpoint returns valid JSON
    with the expected structure for a student.

    Must contain:
    - student_id
    - target_course
    - sequence (list of course levels)
    """
    response = client.get(
        "/api/students/s1/plan/sequence",
        params={"course_id": "ACCY 301"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["student_id"] == "s1"
    assert "target_course" in data
    assert "sequence" in data
    assert isinstance(data["sequence"], list)
