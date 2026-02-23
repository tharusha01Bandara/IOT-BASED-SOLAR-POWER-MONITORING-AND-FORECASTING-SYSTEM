"""
Application Configuration Module

This module handles all application settings using Pydantic Settings.
Environment variables are loaded from .env file and validated at startup.
"""

from functools import lru_cache
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are validated using Pydantic and can be accessed
    throughout the application via dependency injection.
    """
    
    # Application metadata
    app_name: str = Field(default="Solar Monitoring System", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # MongoDB configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    mongodb_db_name: str = Field(default="solar_monitoring", alias="MONGODB_DB_NAME")
    mongodb_max_pool_size: int = Field(default=50, alias="MONGODB_MAX_POOL_SIZE")
    mongodb_min_pool_size: int = Field(default=10, alias="MONGODB_MIN_POOL_SIZE")
    
    # Collection names
    collection_readings: str = Field(default="readings_raw", alias="COLLECTION_READINGS")
    collection_predictions: str = Field(default="predictions", alias="COLLECTION_PREDICTIONS")
    
    # CORS settings (stored as strings, parsed to lists)
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="*", alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", alias="CORS_ALLOW_HEADERS")
    
    # API configuration
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")
    max_query_minutes: int = Field(default=10080, alias="MAX_QUERY_MINUTES")  # 1 week default
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is one of the allowed values"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v_upper
    
    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string to list"""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def get_cors_methods_list(self) -> List[str]:
        """Parse CORS methods from comma-separated string to list"""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",")]
    
    def get_cors_headers_list(self) -> List[str]:
        """Parse CORS headers from comma-separated string to list"""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    This function is cached to avoid reloading environment variables
    on every request. Use this as a FastAPI dependency.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Export settings instance for direct import if needed
settings = get_settings()
