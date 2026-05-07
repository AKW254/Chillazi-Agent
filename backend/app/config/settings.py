from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
     # ============= APP SETTINGS =============
    app_name: str = "Chillazi Agent"
    app_version: str = "1.0.0"
    environment: str = "development"  # development, staging, production
    debug: bool = False
    # Logging
    LOG_LEVEL: str = "INFO"
     # ============= SECURITY =============
    jwt_secret_key: str  # REQUIRED - must be set via .env
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # CORS Settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # ============= DATABASE =============
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_pass: str
    db_echo: bool = False  # SQL logging

    # ============= AI API KEYS =============
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = Field(
        default="google/gemma-4-26b-a4b-it:free",
        validation_alias="OPENROUTER_MODEL_NAME",
    )
    mistral_api_key: str | None = None
    mistral_model: str | None = Field(
        default=None,
        validation_alias="MISTRAL_MODEL_NAME",
    )
 # ============= EMAIL SETTINGS =============
    email_host: str | None = None
    email_port: int | None = None
    email_user: str | None = None
    email_pass: str | None = None
    


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )

    @field_validator("debug", mode="before")
    @classmethod
    def _parse_debug_value(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
                return False
        return value

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string or return list"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins


settings = Settings()
