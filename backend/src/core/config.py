"""
Application configuration settings.

Handles environment-based configuration for the FastAPI application.
"""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database
    database_url: str = "sqlite:///./slido_clone.db"

    # API Configuration
    api_title: str = "Slido Clone API"
    api_version: str = "1.0.0"
    api_description: str = "Live Q&A and Polls Application"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000", 
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ]

    # Security
    secret_key: str = "your-secret-key-change-in-production"

    # Performance
    max_poll_options: int = 10
    max_question_length: int = 1000
    websocket_timeout: int = 300  # 5 minutes

    # Real-time requirements (constitutional <100ms)
    max_broadcast_latency_ms: int = 100

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
