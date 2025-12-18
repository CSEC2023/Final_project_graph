import os
import joblib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

MODEL_PATH = os.getenv("MODEL_PATH", "scripts/model.joblib")

def fetch_training_data(driver, negatives_per_positive: int = 3, max_positives: int = 500):
    """
    Build a balanced supervised dataset.
    Positives: existing (Student)-[:HAS_PASSED]->(Course)
    Negatives: sampled (Student, Course) pairs with NO HAS_PASSED edge
    Features:
      1) prereq_ratio_passed (0..1)
      2) student_passed_count
      3) course_prereq_count
    Label:
      y = 1 for positive, 0 for negative
    """

    q = """
    // --- Positives ---
    MATCH (s:Student)-[:HAS_PASSED]->(c:Course)
    WITH s, c
    LIMIT $max_pos

    // prereqs of c (distinct)
    OPTIONAL MATCH (c)-[:REQUIRES*1..10]->(p:Course)
    WITH s, c, collect(DISTINCT p) AS prereqs

    // passed courses by s
    OPTIONAL MATCH (s)-[:HAS_PASSED]->(pc:Course)
    WITH s, c, prereqs, collect(DISTINCT pc) AS passed

    WITH
      s.id AS student_id,
      c.code AS course_id,
      size(passed) AS student_passed_count,
      size(prereqs) AS course_prereq_count,
      CASE
        WHEN size(prereqs) = 0 THEN 1.0
        ELSE toFloat(size([p IN prereqs WHERE p IN passed])) / toFloat(size(prereqs))
      END AS prereq_ratio_passed
    RETURN student_id, course_id, student_passed_count, course_prereq_count, prereq_ratio_passed
    """

    with driver.session() as session:
        pos = list(session.run(q, max_pos=max_positives))

    positives = []
    for r in pos:
        positives.append((
            [float(r["prereq_ratio_passed"]), int(r["student_passed_count"]), int(r["course_prereq_count"])],
            1
        ))

    if not positives:
        raise RuntimeError("No positive HAS_PASSED examples found. Run seed_data.py to create demo students.")

    # --- Negatives: sample pairs without HAS_PASSED ---
    qneg = """
    MATCH (s:Student)
    MATCH (c:Course)
    WHERE NOT (s)-[:HAS_PASSED]->(c)
    WITH s, c
    ORDER BY rand()
    LIMIT $limit

    OPTIONAL MATCH (c)-[:REQUIRES*1..10]->(p:Course)
    WITH s, c, collect(DISTINCT p) AS prereqs

    OPTIONAL MATCH (s)-[:HAS_PASSED]->(pc:Course)
    WITH s, c, prereqs, collect(DISTINCT pc) AS passed

    RETURN
      s.id AS student_id,
      c.code AS course_id,
      size(passed) AS student_passed_count,
      size(prereqs) AS course_prereq_count,
      CASE
        WHEN size(prereqs) = 0 THEN 1.0
        ELSE toFloat(size([p IN prereqs WHERE p IN passed])) / toFloat(size(prereqs))
      END AS prereq_ratio_passed
    """

    neg_limit = min(len(positives) * negatives_per_positive, 2000)

    with driver.session() as session:
        neg = list(session.run(qneg, limit=neg_limit))

    negatives = []
    for r in neg:
        negatives.append((
            [float(r["prereq_ratio_passed"]), int(r["student_passed_count"]), int(r["course_prereq_count"])],
            0
        ))

    data = positives + negatives
    X = np.array([d[0] for d in data], dtype=float)
    y = np.array([d[1] for d in data], dtype=int)
    return X, y

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        X, y = fetch_training_data(driver, negatives_per_positive=5, max_positives=500)
    finally:
        driver.close()

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = LogisticRegression(max_iter=500)
    model.fit(X_train, y_train)

    y_proba = model.predict_proba(X_test)[:, 1] if len(set(y_test)) > 1 else np.zeros_like(y_test, dtype=float)
    y_pred = (y_proba >= 0.5).astype(int)

    print("=== Classification report ===")
    print(classification_report(y_test, y_pred, zero_division=0))

    if len(set(y_test)) > 1:
        print("ROC-AUC:", roc_auc_score(y_test, y_proba))

    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

if __name__ == "__main__":
    main()
