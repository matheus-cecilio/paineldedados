from functools import lru_cache
from pydantic import BaseModel
import os

class Settings(BaseModel):
    env: str = os.getenv("ENV", "development")
    app_name: str = os.getenv("APP_NAME", "Painel Automatizado de Dados")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    backend_cors_origins: str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:8501,http://localhost:8000")

    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_jwks_url: str = os.getenv("SUPABASE_JWKS_URL", "")
    supabase_jwt_aud: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    api_auth_bypass: bool = os.getenv("API_AUTH_BYPASS", "false").lower() == "true"

    frontend_webhook_url: str = os.getenv("FRONTEND_WEBHOOK_URL", "")

@lru_cache
def get_settings() -> Settings:
    return Settings()
