from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog
from app.services.audit import AuditLogService
from app.services.manifest import compute_sha256_for_json


def test_manifest_sha256_generation_is_stable() -> None:
    payload = {
        "case": {"id": "abc", "title": "Example"},
        "events": [{"id": "evt-1", "srcIp": "203.0.113.10"}],
    }

    checksum_a = compute_sha256_for_json(payload)
    checksum_b = compute_sha256_for_json(
        {
            "events": [{"srcIp": "203.0.113.10", "id": "evt-1"}],
            "case": {"title": "Example", "id": "abc"},
        }
    )

    assert checksum_a == checksum_b
    assert len(checksum_a) == 64


def test_audit_log_service_appends_row(db_session: Session) -> None:
    service = AuditLogService(db_session)

    service.append(
        actor="pytest",
        action="unit.audit",
        entity_type="case",
        before={"status": "NEW"},
        after={"status": "INVESTIGATING"},
    )
    db_session.commit()

    entry = db_session.scalar(select(AuditLog).where(AuditLog.action == "unit.audit"))
    assert entry is not None
    assert entry.actor == "pytest"
    assert entry.before_json == {"status": "NEW"}
    assert entry.after_json == {"status": "INVESTIGATING"}
