"""Application configuration using Pydantic Settings."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL database connection string",
    )

    # Security
    JWT_SECRET: str = Field(
        ...,
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token expiration time in minutes",
    )

    # Azure Blob Storage
    AZURE_BLOB_CONNECTION_STRING: str = Field(
        ...,
        description="Azure Blob Storage connection string",
    )
    AZURE_BLOB_CONTAINER_ORIGINAL: str = Field(
        default="media-original",
        description="Container name for original media (Cool tier)",
    )
    AZURE_BLOB_CONTAINER_PREVIEW: str = Field(
        default="media-preview",
        description="Container name for preview media (Hot tier)",
    )

    # OpenAI
    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API key for Vision and Embeddings",
    )
    OPENAI_VISION_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model for vision API",
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model for embeddings",
    )
    OPENAI_MAX_TOKENS: int = Field(
        default=300,
        description="Maximum tokens for OpenAI Vision API responses",
    )

    # AI Worker settings
    AI_WORKER_ENABLED: bool = Field(
        default=True,
        description="Enable/disable AI worker processing",
    )
    AI_BATCH_SIZE: int = Field(
        default=10,
        description="Number of media items to process per batch",
    )
    AI_TAGGING_INTERVAL_SECONDS: int = Field(
        default=120,
        description="Interval in seconds between tagging job runs",
    )
    AI_MAX_CONCURRENT_REQUESTS: int = Field(
        default=3,
        description="Maximum concurrent OpenAI API requests",
    )
    AI_MAX_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Maximum retry attempts for failed AI processing",
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level",
    )


# Global settings instance
settings = Settings()
