"""
Unit tests for Pydantic models (pure Python logic, no DB calls).
"""

import pytest
from app.models.student import EligibilityResponse, CourseSequenceResponse


def test_eligibility_response_model():
    """Unit test: ensure EligibilityResponse validates and serializes correctly."""
    model = EligibilityResponse(
        student_id="s1",
        course_id="ACCY 301",
        eligible=False,
        missing_prerequisites=["ACCY 201", "ACCY 202"]
    )

    assert model.student_id == "s1"
    assert model.eligible is False
    assert len(model.missing_prerequisites) == 2


def test_course_sequence_response_model():
    """Unit test: ensure CourseSequenceResponse accepts nested lists."""
    model = CourseSequenceResponse(
        student_id="s2",
        target_course="ACCY 301",
        sequence=[["ACCY 201"], ["ACCY 202"], ["ACCY 301"]]
    )

    assert model.target_course == "ACCY 301"
    assert isinstance(model.sequence, list)
    assert model.sequence[0] == ["ACCY 201"]
    assert len(model.sequence) == 3
