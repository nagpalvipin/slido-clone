"""
Main FastAPI application entry point.

FastAPI application with events, polls, questions, and WebSocket support.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import Base, engine
from src.api import events

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Slido Clone API - Phase 3.3 Implementation"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "database": "connected"
    }