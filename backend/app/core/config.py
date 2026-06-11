from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Gita Learning"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://gita:gita@127.0.0.1:5432/gita_learning"
    secret_key: str = "change-this-in-production"
    access_token_minutes: int = 60
    allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8001"
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_bucket: str = "gita-learning"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    max_upload_mb: int = 100

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.app_env.lower() != "production":
            return self

        if self.secret_key == "change-this-in-production":
            raise ValueError("secret_key must be changed in production")

        if self.minio_access_key == "minioadmin" or self.minio_secret_key == "minioadmin":
            raise ValueError("MinIO credentials must be changed in production")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
