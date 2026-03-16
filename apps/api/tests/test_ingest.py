from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog, NormalizedEvent, RawArtifact, Source


def test_post_events_ingest_creates_records_and_audit_log(
    client: TestClient, db_session: Session, sample_event_payload: list[dict[str, object]]
) -> None:
    response = client.post(
        "/v1/events:ingest",
        json={
            "sourceName": "waf-prod",
            "sourceType": "WAF",
            "collectedAt": "2026-03-15T03:15:00Z",
            "payload": sample_event_payload,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["normalizedEventCount"] == 1
    assert len(body["eventIds"]) == 1

    assert db_session.scalar(select(Source).where(Source.name == "waf-prod")) is not None
    raw_artifact = db_session.scalar(
        select(RawArtifact).where(RawArtifact.id == UUID(body["rawArtifactId"]))
    )
    assert raw_artifact is not None
    assert (
        db_session.scalar(
            select(NormalizedEvent).where(NormalizedEvent.id == UUID(body["eventIds"][0]))
        )
        is not None
    )
    assert raw_artifact.metadata_json["storage"]["backend"] == "filesystem"
    artifact_path = Path(raw_artifact.object_uri.removeprefix("file://"))
    assert artifact_path.exists()
    assert '"ruleName":"admin_path_access"' in artifact_path.read_text(encoding="utf-8")

    audit_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == "events.ingest").order_by(AuditLog.created_at.desc())
    )
    assert audit_entry is not None
    assert audit_entry.entity_type == "raw_artifact"
