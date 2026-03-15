from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import SourceType
from app.schemas.base import CamelModel


class IngestRequest(CamelModel):
    source_name: str
    source_type: SourceType
    collected_at: datetime
    payload: str | list[dict[str, Any]]
    parser_version: str | None = None


class IngestResponse(CamelModel):
    raw_artifact_id: UUID
    normalized_event_count: int
    checksum_sha256: str
    event_ids: list[UUID]


class NormalizedEventResponse(CamelModel):
    id: UUID
    event_time: datetime
    source_type: SourceType | None = None
    event_type: str
    src_ip: str | None = None
    dst_ip: str | None = None
    hostname: str | None = None
    username: str | None = None
    session_id: str | None = None
    request_host: str | None = None
    request_path: str | None = None
    status_code: int | None = None
    bytes_sent: int | None = None
    raw_artifact_id: UUID
