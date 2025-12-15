"""
Main FastAPI application entry point.

This module configures the FastAPI app, initializes routers, and exposes
a basic health check endpoint used to verify API and Neo4j connectivity.

Routers included:
- Students router (eligibility, planning, paths)
- Courses router (prerequisite graph utilities)
- Analytics router (graph statistics, advanced analysis)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.neo4j import neo4j_client
from app.routers import analytics, courses, gds, llm, ml, students


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Connect to Neo4j on startup and close the connection on shutdown."""
    _ = fastapi_app  # keep signature explicit for FastAPI, silence pylint
    neo4j_client.connect()
    try:
        yield
    finally:
        neo4j_client.close()


app = FastAPI(
    title="University Course Prerequisite Planner",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Return API and Neo4j connectivity status."""
    try:
        records = neo4j_client.run("RETURN 1 AS ok")
        ok = bool(records and records[0].get("ok"))
        return {"status": "ok" if ok else "error", "neo4j": ok}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return {"status": "error", "neo4j": False, "details": str(exc)}


app.include_router(students.router)
app.include_router(courses.router)
app.include_router(analytics.router)
app.include_router(gds.router)
app.include_router(ml.router)
app.include_router(llm.router)
