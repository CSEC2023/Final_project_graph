"""
Data seeding script for the prerequisite planner.

This script is meant to run inside the Docker container and:
- clears the Neo4j database;
- creates constraints and indexes;
- loads courses and REQUIRES relationships from the CSV file;
- creates demo students and professors for testing.
"""

import csv
import os
from pathlib import Path

from neo4j import GraphDatabase

# This script runs INSIDE the Docker container.
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

CSV_PATH = Path("scripts/uiuc-prerequisites.csv")


def get_driver():
    """Create and return a Neo4j driver instance."""
    print(f"Connecting to Neo4j at {NEO4J_URI} as {NEO4J_USER}...")
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def create_constraints_and_indexes(driver):
    """Create constraints and indexes for Course and Student."""
    print("Creating constraints and indexes...")
    statements = [
        # Unicity of courses
        """
        CREATE CONSTRAINT course_code_unique
        IF NOT EXISTS
        FOR (c:Course)
        REQUIRE c.code IS UNIQUE
        """,
        # Unicity of students
        """
        CREATE CONSTRAINT student_id_unique
        IF NOT EXISTS
        FOR (s:Student)
        REQUIRE s.id IS UNIQUE
        """,
        # Useful index for course code queries
        """
        CREATE INDEX course_code_index
        IF NOT EXISTS
        FOR (c:Course)
        ON (c.code)
        """,
         # NEW: index on Student(id)
        """
        CREATE INDEX student_id_index
        IF NOT EXISTS
        FOR (s:Student)
        ON (s.id)
        """,
    ]
    with driver.session() as session:
        for stmt in statements:
            session.run(stmt)
    print("Constraints and indexes created.")


def clear_database(driver):
    """Remove all nodes and relationships from the database."""
    print("Clearing database...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Database cleared.")


def load_courses_and_prereqs(driver):
    """Load courses and REQUIRES relationships from the CSV file."""
    print(f"Loading CSV from {CSV_PATH.absolute()}")

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH.absolute()}")

    created_rel = 0
    seen_courses = set()

    with driver.session() as session, CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            course_code = (row["Course"] or "").strip()
            if not course_code:
                continue

            # Ensure course node
            session.run(
                "MERGE (c:Course {code: $course_code})",
                course_code=course_code,
            )
            seen_courses.add(course_code)

            # Columns "0".."9" for prerequisites
            for i in range(10):
                col_name = str(i)
                prereq_raw = row.get(col_name, "")
                prereq_code = (prereq_raw or "").strip()

                if not prereq_code:
                    continue
                if prereq_code.lower() in {"none", "nan", "n/a"}:
                    continue

                session.run(
                    """
                    MERGE (c:Course {code: $course_code})
                    MERGE (p:Course {code: $prereq_code})
                    MERGE (c)-[:REQUIRES]->(p)
                    """,
                    course_code=course_code,
                    prereq_code=prereq_code,
                )
                created_rel += 1

    print(f"Seeded {len(seen_courses)} courses and {created_rel} REQUIRES relationships.")


def create_fake_students(driver):
    """Create a couple of demo students and HAS_PASSED relationships."""
    print("Creating demo students...")
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Course)
            WITH c ORDER BY c.code
            LIMIT 6
            RETURN collect(c.code) AS codes
            """
        )
        record = result.single()
        if not record:
            print("No courses found to create fake students.")
            return

        codes = record["codes"]
        if len(codes) < 3:
            print("Not enough courses to create meaningful students.")
            return

        session.run(
            """
            MERGE (s1:Student {id: "s1", name: "Alice"})
            MERGE (s2:Student {id: "s2", name: "Bob"})
            WITH s1, s2
            MATCH (c1:Course {code: $c1})
            MATCH (c2:Course {code: $c2})
            MATCH (c3:Course {code: $c3})
            MERGE (s1)-[:HAS_PASSED {grade: "A"}]->(c1)
            MERGE (s1)-[:HAS_PASSED {grade: "B"}]->(c2)
            MERGE (s2)-[:HAS_PASSED {grade: "A"}]->(c1)
            MERGE (s2)-[:HAS_PASSED {grade: "A"}]->(c2)
            MERGE (s2)-[:HAS_PASSED {grade: "B"}]->(c3)
            """,
            c1=codes[0],
            c2=codes[1],
            c3=codes[2],
        )

    print("Demo students s1 and s2 created.")


def create_professors(driver):
    """Create demo professors and TEACHES relationships."""
    print("Creating demo professors...")
    with driver.session() as session:
        # On prend quelques cours pour les assigner à des profs
        result = session.run(
            """
            MATCH (c:Course)
            WITH c ORDER BY c.code
            LIMIT 9
            RETURN collect(c.code) AS codes
            """
        )
        record = result.single()
        if not record:
            print("No courses found to assign professors.")
            return

        codes = record["codes"]
        if len(codes) < 3:
            print("Not enough courses to create professors.")
            return

        session.run(
            """
            MERGE (p1:Professor {id: "p1", name: "Dr. Smith"})
            MERGE (p2:Professor {id: "p2", name: "Dr. Johnson"})
            MERGE (p3:Professor {id: "p3", name: "Dr. Lee"})

            // p1 enseigne les 3 premiers cours
            WITH p1, p2, p3
            MATCH (c1:Course {code: $c1})
            MATCH (c2:Course {code: $c2})
            MATCH (c3:Course {code: $c3})
            MATCH (c4:Course {code: $c4})
            MATCH (c5:Course {code: $c5})
            MATCH (c6:Course {code: $c6})
            MATCH (c7:Course {code: $c7})
            MATCH (c8:Course {code: $c8})
            MATCH (c9:Course {code: $c9})

            MERGE (p1)-[:TEACHES]->(c1)
            MERGE (p1)-[:TEACHES]->(c2)
            MERGE (p1)-[:TEACHES]->(c3)

            MERGE (p2)-[:TEACHES]->(c4)
            MERGE (p2)-[:TEACHES]->(c5)
            MERGE (p2)-[:TEACHES]->(c6)

            MERGE (p3)-[:TEACHES]->(c7)
            MERGE (p3)-[:TEACHES]->(c8)
            MERGE (p3)-[:TEACHES]->(c9)
            """,
            c1=codes[0],
            c2=codes[1],
            c3=codes[2],
            c4=codes[3],
            c5=codes[4],
            c6=codes[5],
            c7=codes[6],
            c8=codes[7],
            c9=codes[8],
        )

    print("Demo professors created with TEACHES relationships.")


def main():
    """Run the full seeding pipeline."""
    driver = get_driver()
    try:
        clear_database(driver)
        create_constraints_and_indexes(driver)
        load_courses_and_prereqs(driver)
        create_fake_students(driver)
        create_professors(driver)
    finally:
        driver.close()
        print("Done.")


if __name__ == "__main__":
    main()
