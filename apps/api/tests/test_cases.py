from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AttributionLink, AuditLog, Case, Document, Evidence


def _ingest_seed_event(client: TestClient, sample_event_payload: list[dict[str, object]]) -> str:
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
    return response.json()["eventIds"][0]


def test_post_cases_creates_case_from_seed_event(
    client: TestClient, sample_event_payload: list[dict[str, object]]
) -> None:
    event_id = _ingest_seed_event(client, sample_event_payload)

    response = client.post(
        "/v1/cases",
        json={
            "title": "외부 관리자 경로 접근",
            "summary": "반복된 외부 접근에 대한 조사",
            "seedEventIds": [event_id],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["caseNo"].startswith("INC-")
    assert body["primaryIp"] == "203.0.113.10"
    assert body["confidenceGrade"] == "D"
    assert body["externalActorLabel"] == "성명불상"


def test_external_public_actor_remains_external_unknown(
    client: TestClient, db_session: Session, sample_event_payload: list[dict[str, object]]
) -> None:
    event_id = _ingest_seed_event(client, sample_event_payload)
    create_response = client.post(
        "/v1/cases",
        json={
            "title": "외부 행위자 보수 표기 확인",
            "primaryIp": "203.0.113.10",
            "eventIds": [event_id],
        },
    )
    case_id = create_response.json()["id"]

    case_row = db_session.get(Case, UUID(case_id))
    assert case_row is not None
    assert case_row.external_actor_label == "성명불상"
    assert case_row.confidence_grade == "D"

    attribution = db_session.scalar(
        select(AttributionLink)
        .where(AttributionLink.case_id == UUID(case_id))
        .order_by(AttributionLink.created_at.desc())
    )
    assert attribution is not None
    assert attribution.actor_type.value == "EXTERNAL_UNKNOWN"
    assert attribution.display_name == "성명불상"
    assert attribution.confidence_grade == "D"
    assert attribution.next_step == "통신사/플랫폼/수사기관 조회 필요"


def test_get_case_returns_summary_related_events_and_links(
    client: TestClient, sample_event_payload: list[dict[str, object]]
) -> None:
    event_id = _ingest_seed_event(client, sample_event_payload)
    create_response = client.post(
        "/v1/cases",
        json={
            "title": "사건 상세 조회 검증",
            "eventIds": [event_id],
        },
    )
    case_id = create_response.json()["id"]

    response = client.get(f"/v1/cases/{case_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["relatedEventsSummary"]["totalCount"] == 1
    assert body["timeline"][0]["eventType"] == "http_request"
    assert body["attributionLinks"][0]["displayName"] == "성명불상"
    assert body["evidence"] == []
    assert body["documents"] == []


def test_patch_case_updates_fields_and_writes_audit_log(
    client: TestClient, db_session: Session, sample_event_payload: list[dict[str, object]]
) -> None:
    event_id = _ingest_seed_event(client, sample_event_payload)
    create_response = client.post(
        "/v1/cases",
        json={
            "title": "수정 전 사건",
            "eventIds": [event_id],
        },
    )
    case_id = create_response.json()["id"]

    response = client.patch(
        f"/v1/cases/{case_id}",
        json={
            "title": "수정 후 사건",
            "summary": "조사 메모를 포함한 수정 요약",
            "status": "INVESTIGATING",
            "severity": "high",
            "assignee": "ir-team",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "수정 후 사건"
    assert body["summary"] == "조사 메모를 포함한 수정 요약"
    assert body["status"] == "INVESTIGATING"
    assert body["severity"] == "high"
    assert body["assignee"] == "ir-team"

    audit_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == "cases.update").order_by(AuditLog.created_at.desc())
    )
    assert audit_entry is not None
    assert audit_entry.before_json["title"] == "수정 전 사건"
    assert audit_entry.after_json["title"] == "수정 후 사건"


def test_post_freeze_creates_manifest_evidence_and_audit_log(
    client: TestClient, db_session: Session, sample_event_payload: list[dict[str, object]]
) -> None:
    event_id = _ingest_seed_event(client, sample_event_payload)
    create_response = client.post(
        "/v1/cases",
        json={
            "title": "freeze 동작 검증",
            "eventIds": [event_id],
        },
    )
    case_id = create_response.json()["id"]

    response = client.post(f"/v1/cases/{case_id}/freeze")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "completed"
    assert body["frozenEvidenceCount"] == 2

    assert (
        db_session.scalar(select(Evidence).where(Evidence.case_id == UUID(case_id)).limit(1))
        is not None
    )
    document = db_session.scalar(
        select(Document)
        .where(Document.case_id == UUID(case_id))
        .order_by(Document.generated_at.desc())
    )
    assert document is not None
    assert document.doc_type == "evidence_manifest"
    assert document.status.value == "DRAFT"
    assert document.checksum_sha256 == body["manifestChecksum"]

    audit_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == "cases.freeze").order_by(AuditLog.created_at.desc())
    )
    assert audit_entry is not None
    assert audit_entry.entity_type == "case"


def test_post_export_prepares_metadata_bundle_and_audit_log(
    client: TestClient, db_session: Session, sample_event_payload: list[dict[str, object]]
) -> None:
    event_id = _ingest_seed_event(client, sample_event_payload)
    create_response = client.post(
        "/v1/cases",
        json={
            "title": "export 동작 검증",
            "eventIds": [event_id],
        },
    )
    case_id = create_response.json()["id"]

    freeze_response = client.post(f"/v1/cases/{case_id}/freeze")
    assert freeze_response.status_code == 202

    response = client.post(f"/v1/cases/{case_id}/export")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "packaged"
    assert body["exportedEvidenceCount"] == 2

    document = db_session.scalar(
        select(Document)
        .where(Document.case_id == UUID(case_id), Document.doc_type == "export_bundle")
        .order_by(Document.generated_at.desc())
    )
    assert document is not None
    assert document.status.value == "DRAFT"
    assert document.checksum_sha256 == body["manifestChecksum"]
    assert document.generated_from_json["bundle_state"] == "DRAFT"
    assert document.generated_from_json["package_plan"]["bundle_format"] == "json-package"
    assert len(document.generated_from_json["input_snapshot"]["evidence"]) == 2
    assert document.storage_uri is not None

    export_file = Path(urlparse(document.storage_uri).path)
    assert export_file.exists()
    bundle_payload = json.loads(export_file.read_text(encoding="utf-8"))
    assert bundle_payload["bundle_type"] == "evidence_export_bundle"
    assert bundle_payload["bundle_id"] == str(document.id)

    evidence_rows = db_session.scalars(
        select(Evidence).where(Evidence.case_id == UUID(case_id)).order_by(Evidence.created_at.asc())
    ).all()
    assert len(evidence_rows) == 2
    assert all(item.status.value == "EXPORTED" for item in evidence_rows)
    assert all(item.exported_at is not None for item in evidence_rows)

    audit_entry = db_session.scalar(
        select(AuditLog)
        .where(AuditLog.action == "cases.export.prepare")
        .order_by(AuditLog.created_at.desc())
    )
    assert audit_entry is not None
    assert audit_entry.entity_type == "case"
    assert audit_entry.after_json["storageUri"] == document.storage_uri
