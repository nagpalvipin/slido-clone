"""
Main FastAPI application entry point.

This is a minimal stub to make tests fail initially (TDD approach).
Implementation will be added in Phase 3.3.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Slido Clone API",
    description="Live Q&A and Polls Application",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Slido Clone API - TDD Implementation"}

# TODO: Add routers in Phase 3.3
# app.include_router(events.router, prefix="/api/v1")
# app.include_router(polls.router, prefix="/api/v1") 
# app.include_router(questions.router, prefix="/api/v1")
# app.include_router(websocket.router, prefix="/ws")