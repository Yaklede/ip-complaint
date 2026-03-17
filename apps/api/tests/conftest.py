from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_db_engine
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}",
        opensearch_url="",
        minio_endpoint="",
        redis_url="",
        raw_artifact_storage_backend="filesystem",
        raw_artifact_storage_dir=str(tmp_path / "raw-artifacts"),
        generated_output_storage_dir=str(tmp_path / "generated-outputs"),
        auth_default_actor="pytest",
        auth_default_roles="investigator,lead,admin,auditor,legal_reviewer,privacy_reviewer",
    )


@pytest.fixture
def client(settings: Settings) -> Generator[TestClient, None, None]:
    engine = create_db_engine(settings.database_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(client: TestClient) -> Generator[Session, None, None]:
    session_factory = client.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_event_payload() -> list[dict[str, object]]:
    return [
        {
            "eventTime": "2026-03-15T03:11:20Z",
            "eventType": "http_request",
            "srcIp": "203.0.113.10",
            "dstIp": "10.0.2.15",
            "hostname": "api-prod-02",
            "requestHost": "api.example.com",
            "requestPath": "/admin/export",
            "statusCode": 403,
            "bytesSent": 512,
            "ruleName": "admin_path_access",
        }
    ]
