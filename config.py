from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str

    # Supabase
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    JWT_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()