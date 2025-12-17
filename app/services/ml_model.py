import os
import joblib
from app.database.neo4j import neo4j_client

MODEL_PATH = os.getenv("MODEL_PATH", "scripts/model.joblib")

_model = None

def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            # Model not trained yet
            return None
        _model = joblib.load(MODEL_PATH)
    return _model

def _compute_features(student_id: str, course_id: str):
    q = """
    MATCH (s:Student {id: $student_id})
    MATCH (c:Course {code: $course_id})

    OPTIONAL MATCH (c)-[:REQUIRES*1..10]->(p:Course)
    WITH s, c, collect(DISTINCT p) AS prereqs

    OPTIONAL MATCH (s)-[:HAS_PASSED]->(pc:Course)
    WITH prereqs, collect(DISTINCT pc) AS passed

    RETURN
      size(passed) AS student_passed_count,
      size(prereqs) AS course_prereq_count,
      CASE
        WHEN size(prereqs) = 0 THEN 1.0
        ELSE toFloat(size([p IN prereqs WHERE p IN passed])) / toFloat(size(prereqs))
      END AS prereq_ratio_passed
    """
    recs = neo4j_client.run(q, student_id=student_id, course_id=course_id)
    if not recs:
        return None
    r = recs[0]
    feats = {
        "prereq_ratio_passed": float(r["prereq_ratio_passed"] or 0.0),
        "student_passed_count": int(r["student_passed_count"] or 0),
        "course_prereq_count": int(r["course_prereq_count"] or 0),
    }
    return feats

def predict_pass_probability(student_id: str, course_id: str):
    feats = _compute_features(student_id, course_id)
    if feats is None:
        # student or course missing
        return 0.0, {"error": "Student or course not found"}

    model = _load_model()
    if model is None:
        # fallback heuristic if model missing
        proba = min(1.0, max(0.0, feats["prereq_ratio_passed"]))
        return proba, {**feats, "mode": "heuristic (model not trained)"}

    X = [[feats["prereq_ratio_passed"], feats["student_passed_count"], feats["course_prereq_count"]]]
    proba = float(model.predict_proba(X)[0][1])
    return proba, {**feats, "mode": "logreg"}
