from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import RequestPrincipal
from app.models.entities import IngestBatch, NormalizedEvent, RawArtifact, Source
from app.models.enums import SourceType
from app.schemas.events import IngestRequest, IngestResponse
from app.services.audit import AuditLogService
from app.services.manifest import compute_sha256_for_json


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class IngestService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._audit = AuditLogService(session)

    def ingest(self, payload: IngestRequest, principal: RequestPrincipal) -> IngestResponse:
        source = self._get_or_create_source(payload.source_name, payload.source_type)
        collected_at = ensure_utc(payload.collected_at)
        records = self._extract_records(payload.payload)

        batch = IngestBatch(
            source=source,
            collected_at=collected_at,
            parser_version=payload.parser_version or "mvp-pass-through",
        )
        self._session.add(batch)
        self._session.flush()

        artifact_id = uuid.uuid4()
        artifact_checksum = compute_sha256_for_json(payload.payload)
        raw_artifact = RawArtifact(
            id=artifact_id,
            source=source,
            ingest_batch=batch,
            object_uri=f"raw://{source.name}/{collected_at:%Y/%m/%d}/{artifact_id}.json",
            sha256=artifact_checksum,
            collected_at=collected_at,
            parser_version=batch.parser_version,
            metadata_json={
                "payload_kind": "string" if isinstance(payload.payload, str) else "record_list",
                "record_count": len(records),
            },
        )
        self._session.add(raw_artifact)
        self._session.flush()

        created_events: list[NormalizedEvent] = []
        for record in records:
            event = self._build_event(
                record=record,
                source=source,
                raw_artifact=raw_artifact,
                fallback_time=collected_at,
            )
            self._session.add(event)
            created_events.append(event)

        batch.event_count = len(created_events)
        self._session.flush()

        self._audit.append(
            actor=principal.actor,
            action="events.ingest",
            entity_type="raw_artifact",
            entity_id=raw_artifact.id,
            after={
                "sourceName": source.name,
                "sourceType": source.type.value,
                "rawArtifactId": str(raw_artifact.id),
                "normalizedEventCount": len(created_events),
            },
        )
        self._session.commit()

        return IngestResponse(
            raw_artifact_id=raw_artifact.id,
            normalized_event_count=len(created_events),
            checksum_sha256=artifact_checksum,
            event_ids=[event.id for event in created_events],
        )

    def _get_or_create_source(self, name: str, source_type: SourceType) -> Source:
        source = self._session.scalar(select(Source).where(Source.name == name))
        if source is not None:
            return source

        source = Source(
            name=name,
            type=source_type,
            parser_name="mvp-pass-through",
            config_json={},
        )
        self._session.add(source)
        self._session.flush()
        return source

    def _extract_records(self, payload: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item if isinstance(item, dict) else {"message": str(item)} for item in payload]

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return [{"message": payload}]

        if isinstance(decoded, list):
            return [item if isinstance(item, dict) else {"message": str(item)} for item in decoded]
        if isinstance(decoded, dict):
            return [decoded]
        return [{"message": str(decoded)}]

    def _build_event(
        self,
        *,
        record: dict[str, Any],
        source: Source,
        raw_artifact: RawArtifact,
        fallback_time: datetime,
    ) -> NormalizedEvent:
        event_payload = record.copy()
        event_time = self._coerce_datetime(
            self._value(record, "event_time", "eventTime", "timestamp", "time"), fallback_time
        )
        event_snapshot = {
            "event_time": event_time,
            "source_type": source.type.value,
            "event_type": self._value(record, "event_type", "eventType", "type", default="raw_ingest"),
            "src_ip": self._value(record, "src_ip", "srcIp", "client_ip", "clientIp"),
            "dst_ip": self._value(record, "dst_ip", "dstIp", "server_ip", "serverIp"),
            "hostname": self._value(record, "hostname", "host", "server"),
            "username": self._value(record, "username", "user", "account"),
            "session_id": self._value(record, "session_id", "sessionId"),
            "request_method": self._value(record, "request_method", "requestMethod", "method"),
            "request_host": self._value(record, "request_host", "requestHost", "host_header"),
            "request_path": self._value(record, "request_path", "requestPath", "path", "url_path"),
            "status_code": self._coerce_int(
                self._value(record, "status_code", "statusCode", "status")
            ),
            "bytes_sent": self._coerce_int(self._value(record, "bytes_sent", "bytesSent", "bytes")),
            "severity": self._value(record, "severity", default="info"),
            "rule_name": self._value(record, "rule_name", "ruleName"),
            "payload_json": event_payload,
        }
        checksum = compute_sha256_for_json(event_snapshot)

        return NormalizedEvent(
            source=source,
            raw_artifact=raw_artifact,
            event_time=event_time,
            event_type=event_snapshot["event_type"],
            severity=event_snapshot["severity"],
            src_ip=event_snapshot["src_ip"],
            dst_ip=event_snapshot["dst_ip"],
            hostname=event_snapshot["hostname"],
            username=event_snapshot["username"],
            session_id=event_snapshot["session_id"],
            request_method=event_snapshot["request_method"],
            request_host=event_snapshot["request_host"],
            request_path=event_snapshot["request_path"],
            status_code=event_snapshot["status_code"],
            bytes_sent=event_snapshot["bytes_sent"],
            rule_name=event_snapshot["rule_name"],
            payload_json=event_payload,
            checksum_sha256=checksum,
        )

    def _value(self, payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in payload and payload[key] not in ("", None):
                return payload[key]
        return default

    def _coerce_datetime(self, value: Any, fallback: datetime) -> datetime:
        if value is None:
            return ensure_utc(fallback)
        if isinstance(value, datetime):
            return ensure_utc(value)
        if isinstance(value, str):
            return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        return ensure_utc(fallback)

    def _coerce_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)
