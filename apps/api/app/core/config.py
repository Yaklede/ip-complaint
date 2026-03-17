from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="IAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Incident Attribution API"
    app_env: str = "development"
    debug: bool = False
    api_version: str = "0.1.0"

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/incident_db"
    opensearch_url: str = "http://localhost:9200"
    minio_endpoint: str = "http://localhost:9000"
    redis_url: str = "redis://localhost:6379/0"
    raw_artifact_storage_backend: Literal["filesystem", "minio"] = "filesystem"
    raw_artifact_storage_dir: str = "./data/raw-artifacts"
    generated_output_storage_dir: str = "./data/generated-outputs"
    minio_access_key: str = "minio"
    minio_secret_key: str = "minio123"
    minio_bucket: str = "incident-raw-artifacts"
    generated_output_bucket: str = "incident-generated-outputs"
    minio_secure: bool = False

    auth_default_actor: str = "system"
    auth_default_roles: str = Field(
        default="investigator,lead,admin,auditor,legal_reviewer,privacy_reviewer"
    )

    case_number_prefix: str = "INC"

    @property
    def auth_default_role_list(self) -> list[str]:
        return [role.strip() for role in self.auth_default_roles.split(",") if role.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
