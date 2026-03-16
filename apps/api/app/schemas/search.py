from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from app.models.enums import ActorType
from app.schemas.base import CamelModel
from app.schemas.cases import CaseResponse
from app.schemas.events import NormalizedEventResponse


class CorrelateQueryType(str, Enum):
    IP = "ip"
    USERNAME = "username"
    HOSTNAME = "hostname"
    SESSION = "session"
    DOMAIN = "domain"


class CorrelateRequest(CamelModel):
    query_type: CorrelateQueryType
    query_value: str
    time_from: datetime
    time_to: datetime


class CandidateAssetResponse(CamelModel):
    id: UUID
    asset_tag: str
    hostname: str
    device_type: str
    owner_display_name: str | None = None
    primary_user_display_name: str | None = None
    observed_ips: list[str]
    matched_by: list[str]


class CandidateUserResponse(CamelModel):
    id: UUID
    username: str
    display_name: str
    email: str | None = None
    department: str | None = None
    matched_by: list[str]


class AttributionPreviewResponse(CamelModel):
    actor_type: ActorType
    display_name: str
    observed_ip: str | None = None
    confidence_score: float
    confidence_grade: str
    rationale: str | None = None
    next_step: str | None = None


class CorrelateResponse(CamelModel):
    related_events: list[NormalizedEventResponse]
    related_cases: list[CaseResponse]
    candidate_assets: list[CandidateAssetResponse]
    candidate_users: list[CandidateUserResponse]
    attribution_preview: AttributionPreviewResponse | None = None
