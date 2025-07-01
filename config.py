"""
Configuration module for the QSR Assistant backend.
Centralized configuration to avoid hardcoded values.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for environment-specific settings."""

    # API Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "500"))

    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str = os.getenv("REACT_APP_ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    # File Upload Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "../uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf"}

    # Search Configuration
    SEARCH_SIMILARITY_THRESHOLD: float = float(
        os.getenv("SEARCH_SIMILARITY_THRESHOLD", "0.3")
    )
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
    ]

    # Database Configuration
    DOCUMENTS_DB: str = os.getenv("DOCUMENTS_DB", "../documents.json")
    VECTOR_CACHE_SIZE: int = int(os.getenv("VECTOR_CACHE_SIZE", "1000"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_DEBUG: bool = os.getenv("ENABLE_DEBUG", "false").lower() == "true"

    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))

    @classmethod
    def get_cors_config(cls) -> Dict[str, Any]:
        """Get CORS configuration."""
        return {
            "allow_origins": cls.CORS_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

    @classmethod
    def get_upload_config(cls) -> Dict[str, Any]:
        """Get file upload configuration."""
        return {
            "upload_dir": cls.UPLOAD_DIR,
            "max_file_size": cls.MAX_FILE_SIZE,
            "allowed_extensions": cls.ALLOWED_EXTENSIONS,
        }

    @classmethod
    def get_openai_config(cls) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            "api_key": cls.OPENAI_API_KEY,
            "model": cls.OPENAI_MODEL,
            "temperature": cls.OPENAI_TEMPERATURE,
            "max_tokens": cls.OPENAI_MAX_TOKENS,
        }

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return os.getenv("NODE_ENV") == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment."""
        return os.getenv("NODE_ENV") == "development" or cls.ENABLE_DEBUG


# Create a global config instance
config = Config()