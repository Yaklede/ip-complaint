from __future__ import annotations

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
    assert (
        db_session.scalar(
            select(RawArtifact).where(RawArtifact.id == UUID(body["rawArtifactId"]))
        )
        is not None
    )
    assert (
        db_session.scalar(
            select(NormalizedEvent).where(NormalizedEvent.id == UUID(body["eventIds"][0]))
        )
        is not None
    )
    audit_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == "events.ingest").order_by(AuditLog.created_at.desc())
    )
    assert audit_entry is not None
    assert audit_entry.entity_type == "raw_artifact"
