from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import RequestPrincipal
from app.core.errors import ApiException
from app.models.entities import AttributionLink, Case, CaseEvent, Document, Evidence, NormalizedEvent
from app.models.enums import DocumentStatus, EvidenceStatus
from app.schemas.cases import FreezeResponse
from app.services.audit import AuditLogService
from app.services.manifest import build_case_manifest, compute_sha256_for_json


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._audit = AuditLogService(session)

    def freeze_case(self, case_id: UUID, principal: RequestPrincipal) -> FreezeResponse:
        case = self._session.get(Case, case_id)
        if case is None:
            raise ApiException(status_code=404, code="CASE_NOT_FOUND", message="Case not found")

        events = self._session.scalars(
            select(NormalizedEvent)
            .join(CaseEvent, CaseEvent.event_id == NormalizedEvent.id)
            .where(CaseEvent.case_id == case_id)
            .options(
                selectinload(NormalizedEvent.source),
                selectinload(NormalizedEvent.raw_artifact),
            )
            .order_by(NormalizedEvent.event_time.asc())
        ).all()
        attribution_links = self._session.scalars(
            select(AttributionLink)
            .where(AttributionLink.case_id == case_id)
            .options(selectinload(AttributionLink.user), selectinload(AttributionLink.account))
            .order_by(AttributionLink.created_at.asc())
        ).all()
        existing_evidence = self._session.scalars(
            select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at.asc())
        ).all()
        evidence_by_event = {
            item.normalized_event_id: item for item in existing_evidence if item.normalized_event_id is not None
        }
        evidence_by_artifact = {
            item.raw_artifact_id: item for item in existing_evidence if item.raw_artifact_id is not None
        }

        frozen_at = utcnow()
        for event in events:
            if event.id not in evidence_by_event:
                evidence = Evidence(
                    case_id=case_id,
                    evidence_type="NORMALIZED_EVENT",
                    normalized_event_id=event.id,
                    object_uri=f"event://{event.id}",
                    sha256=event.checksum_sha256 or compute_sha256_for_json(event.payload_json),
                    status=EvidenceStatus.FROZEN,
                    frozen_at=frozen_at,
                    metadata_json={"eventTime": event.event_time.isoformat()},
                )
                self._session.add(evidence)
                existing_evidence.append(evidence)
                evidence_by_event[event.id] = evidence

            raw_artifact = event.raw_artifact
            if raw_artifact is not None and raw_artifact.id not in evidence_by_artifact:
                artifact_evidence = Evidence(
                    case_id=case_id,
                    evidence_type="RAW_ARTIFACT",
                    raw_artifact_id=raw_artifact.id,
                    object_uri=raw_artifact.object_uri,
                    sha256=raw_artifact.sha256,
                    status=EvidenceStatus.FROZEN,
                    frozen_at=frozen_at,
                    metadata_json={"collectedAt": raw_artifact.collected_at.isoformat()},
                )
                self._session.add(artifact_evidence)
                existing_evidence.append(artifact_evidence)
                evidence_by_artifact[raw_artifact.id] = artifact_evidence

        for evidence in existing_evidence:
            evidence.status = EvidenceStatus.FROZEN
            evidence.frozen_at = frozen_at

        self._session.flush()

        documents = self._session.scalars(
            select(Document).where(Document.case_id == case_id).order_by(Document.generated_at.desc())
        ).all()
        manifest = build_case_manifest(
            case=case,
            events=events,
            evidence=existing_evidence,
            attribution_links=attribution_links,
            documents=documents,
            generated_at=frozen_at,
        )
        manifest_checksum = compute_sha256_for_json(manifest)
        next_version = int(
            self._session.scalar(
                select(func.max(Document.version_no)).where(
                    Document.case_id == case_id, Document.doc_type == "evidence_manifest"
                )
            )
            or 0
        ) + 1
        document = Document(
            case_id=case_id,
            doc_type="evidence_manifest",
            status=DocumentStatus.DRAFT,
            version_no=next_version,
            storage_uri=f"manifest://cases/{case.case_no}/evidence-manifest-v{next_version}.json",
            checksum_sha256=manifest_checksum,
            generated_from_json=manifest,
            generated_at=frozen_at,
        )
        self._session.add(document)
        self._session.flush()

        self._audit.append(
            actor=principal.actor,
            action="cases.freeze",
            entity_type="case",
            entity_id=case.id,
            after={
                "caseNo": case.case_no,
                "bundleId": str(document.id),
                "frozenEvidenceCount": len(existing_evidence),
                "manifestChecksum": manifest_checksum,
            },
        )
        self._session.commit()

        return FreezeResponse(
            bundle_id=document.id,
            frozen_evidence_count=len(existing_evidence),
            manifest_checksum=manifest_checksum,
            status="completed",
        )
