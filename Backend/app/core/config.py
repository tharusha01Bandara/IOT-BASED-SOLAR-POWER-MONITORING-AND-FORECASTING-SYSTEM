"""
Application Configuration Module
"""

from functools import lru_cache
from typing import List
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 🔥 IMPORTANT: Point to Backend folder (where .env is located)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
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
    collection_model_runs: str = Field(default="model_runs", alias="COLLECTION_MODEL_RUNS")

    # ML Model configuration
    model_dir: str = Field(default="app/ml_models", alias="MODEL_DIR")
    model_versions_dir: str = Field(default="app/ml_models/versions", alias="MODEL_VERSIONS_DIR")
    model_current_pointer: str = Field(default="app/ml_models/current_model.json", alias="MODEL_CURRENT_POINTER")

    # Retraining configuration
    retrain_enabled: bool = Field(default=True, alias="RETRAIN_ENABLED")
    retrain_days: int = Field(default=7, alias="RETRAIN_DAYS")
    retrain_interval_hours: int = Field(default=24, alias="RETRAIN_INTERVAL_HOURS")
    retrain_time: str = Field(default="18:30", alias="RETRAIN_TIME")
    timezone: str = Field(default="Asia/Colombo", alias="TIMEZONE")
    mae_threshold_percent: float = Field(default=10.0, alias="MAE_THRESHOLD_PERCENT")

    # CORS settings
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="*", alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", alias="CORS_ALLOW_HEADERS")

    # API configuration
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")
    max_query_minutes: int = Field(default=10080, alias="MAX_QUERY_MINUTES")

    # LLM configuration
    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_api_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/openai", alias="LLM_API_URL")
    llm_api_path: str = Field(default="/chat/completions", alias="LLM_API_PATH")
    llm_model: str = Field(default="gemini-2.0-flash", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=500, alias="LLM_MAX_TOKENS")
    llm_timeout_seconds: int = Field(default=20, alias="LLM_TIMEOUT_SECONDS")

    # Validate log level
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v

    # CORS helpers
    def get_cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_cors_methods_list(self) -> List[str]:
        return ["*"] if self.cors_allow_methods == "*" else [m.strip() for m in self.cors_allow_methods.split(",")]

    def get_cors_headers_list(self) -> List[str]:
        return ["*"] if self.cors_allow_headers == "*" else [h.strip() for h in self.cors_allow_headers.split(",")]

    # 🔥 THIS IS THE FIX
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",   # ✅ Points to Backend/.env
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",)
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()