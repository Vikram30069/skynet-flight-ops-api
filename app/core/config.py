import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Skynet API"
    API_V1_STR: str = "/api/v1"
    
    # Secret key for JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey_please_change_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./skynet.db"
    )

    class Config:
        case_sensitive = True

settings = Settings()
