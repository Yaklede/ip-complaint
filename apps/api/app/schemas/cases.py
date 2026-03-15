from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AliasChoices, Field

from app.models.enums import ActorType, CaseStatus, DocumentStatus, EvidenceStatus
from app.schemas.base import CamelModel
from app.schemas.events import NormalizedEventResponse


class CreateCaseRequest(CamelModel):
    title: str
    summary: str | None = None
    primary_ip: str | None = None
    event_ids: Annotated[
        list[UUID],
        Field(
            default_factory=list,
            validation_alias=AliasChoices("eventIds", "seedEventIds", "event_ids", "seed_event_ids"),
        ),
    ]
    notes: str | None = None
    severity: str | None = None


class CaseResponse(CamelModel):
    id: UUID
    case_no: str
    title: str
    status: CaseStatus
    severity: str
    primary_ip: str | None = None
    confidence_grade: str | None = None
    external_actor_label: str | None = None
    summary: str | None = None
    opened_at: datetime


class RelatedEventsSummary(CamelModel):
    total_count: int
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    source_types: list[str]
    event_types: list[str]


class AttributionLinkResponse(CamelModel):
    id: UUID
    actor_type: ActorType
    display_name: str
    observed_ip: str | None = None
    confidence_score: float
    confidence_grade: str
    rationale: str | None = None
    next_step: str | None = None


class EvidenceResponse(CamelModel):
    id: UUID
    evidence_type: str
    raw_artifact_id: UUID | None = None
    normalized_event_id: UUID | None = None
    object_uri: str | None = None
    sha256: str
    status: EvidenceStatus
    frozen_at: datetime | None = None
    created_at: datetime


class DocumentResponse(CamelModel):
    id: UUID
    doc_type: str
    status: DocumentStatus
    version_no: int
    storage_uri: str | None = None
    checksum_sha256: str
    generated_at: datetime


class CaseDetailResponse(CamelModel):
    id: UUID
    case_no: str
    title: str
    status: CaseStatus
    severity: str
    primary_ip: str | None = None
    confidence_grade: str | None = None
    external_actor_label: str | None = None
    summary: str | None = None
    opened_at: datetime
    related_events_summary: RelatedEventsSummary
    timeline: list[NormalizedEventResponse]
    attribution_links: list[AttributionLinkResponse]
    evidence: list[EvidenceResponse]
    documents: list[DocumentResponse]


class CaseListResponse(CamelModel):
    items: list[CaseResponse]
    total: int


class FreezeResponse(CamelModel):
    bundle_id: UUID
    frozen_evidence_count: int
    manifest_checksum: str
    status: str
