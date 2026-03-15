from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import RequestPrincipal
from app.core.errors import ApiException
from app.core.policy import (
    EXTERNAL_UNKNOWN_DISPLAY_NAME,
    EXTERNAL_UNKNOWN_GRADE,
    EXTERNAL_UNKNOWN_NEXT_STEP,
    is_external_public_ip,
)
from app.models.entities import AttributionLink, Case, CaseEvent, Document, Evidence, NormalizedEvent
from app.models.enums import ActorType, CaseStatus
from app.schemas.cases import (
    AttributionLinkResponse,
    CaseDetailResponse,
    CaseListResponse,
    CaseResponse,
    CreateCaseRequest,
    DocumentResponse,
    EvidenceResponse,
    RelatedEventsSummary,
)
from app.schemas.events import NormalizedEventResponse
from app.services.audit import AuditLogService


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CaseService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._audit = AuditLogService(session)

    def list_cases(
        self, *, status: str | None = None, severity: str | None = None, page: int = 1, page_size: int = 20
    ) -> CaseListResponse:
        query = select(Case).order_by(Case.opened_at.desc())
        count_query = select(func.count()).select_from(Case)

        if status:
            query = query.where(Case.status == CaseStatus(status))
            count_query = count_query.where(Case.status == CaseStatus(status))
        if severity:
            query = query.where(Case.severity == severity)
            count_query = count_query.where(Case.severity == severity)

        items = self._session.scalars(
            query.offset(max(page - 1, 0) * page_size).limit(page_size)
        ).all()
        total = int(self._session.scalar(count_query) or 0)
        return CaseListResponse(items=[CaseResponse.model_validate(item) for item in items], total=total)

    def create_case(self, payload: CreateCaseRequest, principal: RequestPrincipal) -> CaseResponse:
        related_events = self._load_events(payload.event_ids)
        primary_ip = payload.primary_ip or self._derive_primary_ip(related_events)
        case = Case(
            case_no=self._next_case_number(),
            title=payload.title,
            summary=payload.summary or payload.notes or self._default_summary(related_events),
            status=CaseStatus.NEW,
            severity=payload.severity or "medium",
            primary_ip=primary_ip,
            created_by=principal.actor,
        )

        if is_external_public_ip(primary_ip):
            case.external_actor_label = EXTERNAL_UNKNOWN_DISPLAY_NAME
            case.confidence_grade = EXTERNAL_UNKNOWN_GRADE

        self._session.add(case)
        self._session.flush()

        for event in related_events:
            self._session.add(CaseEvent(case_id=case.id, event_id=event.id))

        if is_external_public_ip(primary_ip):
            self._session.add(
                AttributionLink(
                    case_id=case.id,
                    actor_type=ActorType.EXTERNAL_UNKNOWN,
                    observed_ip=primary_ip,
                    confidence_score=0,
                    grade=EXTERNAL_UNKNOWN_GRADE,
                    rationale=EXTERNAL_UNKNOWN_NEXT_STEP,
                    evidence_json=[
                        {
                            "type": "EXTERNAL_PUBLIC_IP",
                            "details": "No internal attribution evidence is available in Phase 1.",
                        }
                    ],
                    engine_version="phase1-conservative",
                )
            )

        self._audit.append(
            actor=principal.actor,
            action="cases.create",
            entity_type="case",
            entity_id=case.id,
            after={
                "caseNo": case.case_no,
                "title": case.title,
                "primaryIp": case.primary_ip,
                "eventIds": [str(event.id) for event in related_events],
            },
        )
        self._session.commit()
        self._session.refresh(case)
        return CaseResponse.model_validate(case)

    def get_case(self, case_id: UUID) -> CaseDetailResponse:
        case = self._session.get(Case, case_id)
        if case is None:
            raise ApiException(status_code=404, code="CASE_NOT_FOUND", message="Case not found")

        events = self._session.scalars(
            select(NormalizedEvent)
            .join(CaseEvent, CaseEvent.event_id == NormalizedEvent.id)
            .where(CaseEvent.case_id == case_id)
            .options(selectinload(NormalizedEvent.source))
            .order_by(NormalizedEvent.event_time.asc())
        ).all()
        attribution_links = self._session.scalars(
            select(AttributionLink)
            .where(AttributionLink.case_id == case_id)
            .options(selectinload(AttributionLink.user), selectinload(AttributionLink.account))
            .order_by(AttributionLink.created_at.asc())
        ).all()
        evidence = self._session.scalars(
            select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at.desc())
        ).all()
        documents = self._session.scalars(
            select(Document).where(Document.case_id == case_id).order_by(Document.generated_at.desc())
        ).all()

        return CaseDetailResponse(
            **CaseResponse.model_validate(case).model_dump(),
            related_events_summary=self._build_related_events_summary(events),
            timeline=[NormalizedEventResponse.model_validate(event) for event in events],
            attribution_links=[
                AttributionLinkResponse.model_validate(link) for link in attribution_links
            ],
            evidence=[EvidenceResponse.model_validate(item) for item in evidence],
            documents=[DocumentResponse.model_validate(item) for item in documents],
        )

    def _load_events(self, event_ids: list[UUID]) -> list[NormalizedEvent]:
        if not event_ids:
            return []

        events = self._session.scalars(
            select(NormalizedEvent)
            .where(NormalizedEvent.id.in_(event_ids))
            .options(selectinload(NormalizedEvent.source))
        ).all()
        found_ids = {event.id for event in events}
        missing = [str(event_id) for event_id in event_ids if event_id not in found_ids]
        if missing:
            raise ApiException(
                status_code=404,
                code="EVENTS_NOT_FOUND",
                message="One or more event IDs were not found",
                details={"missingEventIds": missing},
            )
        return events

    def _derive_primary_ip(self, events: list[NormalizedEvent]) -> str | None:
        for event in events:
            if event.src_ip:
                return event.src_ip
        return None

    def _default_summary(self, events: list[NormalizedEvent]) -> str:
        if not events:
            return "Seed case created without linked events."
        return f"Seed case created from {len(events)} normalized event(s)."

    def _next_case_number(self) -> str:
        year = utcnow().year
        total = int(self._session.scalar(select(func.count()).select_from(Case)) or 0) + 1
        return f"INC-{year}-{total:06d}"

    def _build_related_events_summary(self, events: list[NormalizedEvent]) -> RelatedEventsSummary:
        if not events:
            return RelatedEventsSummary(total_count=0, source_types=[], event_types=[])

        source_types = sorted({event.source_type.value for event in events if event.source_type is not None})
        event_types = sorted({event.event_type for event in events})
        return RelatedEventsSummary(
            total_count=len(events),
            first_seen_at=events[0].event_time,
            last_seen_at=events[-1].event_time,
            source_types=source_types,
            event_types=event_types,
        )
