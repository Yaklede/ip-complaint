from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import RequestPrincipal
from app.core.errors import ApiException
from app.core.serialization import canonical_json_bytes, make_json_safe
from app.models.entities import AttributionLink, Case, CaseEvent, Document, Evidence, NormalizedEvent
from app.models.enums import DocumentStatus, EvidenceStatus
from app.schemas.cases import ExportResponse, FreezeResponse
from app.services.audit import AuditLogService
from app.services.generated_output_storage import GeneratedOutputStorage
from app.services.manifest import (
    build_case_manifest,
    build_export_bundle_metadata,
    compute_sha256_for_json,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceService:
    def __init__(
        self,
        session: Session,
        generated_output_storage: GeneratedOutputStorage | None = None,
    ) -> None:
        self._session = session
        self._audit = AuditLogService(session)
        self._generated_output_storage = generated_output_storage

    def freeze_case(self, case_id: UUID, principal: RequestPrincipal) -> FreezeResponse:
        case, events, attribution_links, existing_evidence, documents = self._load_case_context(case_id)
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

    def prepare_export_bundle(self, case_id: UUID, principal: RequestPrincipal) -> ExportResponse:
        if self._generated_output_storage is None:
            raise ApiException(
                status_code=500,
                code="EXPORT_STORAGE_NOT_CONFIGURED",
                message="Generated output storage is not configured",
            )

        case, events, _, evidence, documents = self._load_case_context(case_id)
        exportable_evidence = [item for item in evidence if item.frozen_at is not None]
        if not exportable_evidence:
            raise ApiException(
                status_code=409,
                code="CASE_NOT_FROZEN",
                message="Case must be frozen before export metadata can be prepared",
            )

        generated_at = utcnow()
        export_metadata = build_export_bundle_metadata(
            case=case,
            events=events,
            evidence=exportable_evidence,
            documents=documents,
            generated_at=generated_at,
        )
        next_version = int(
            self._session.scalar(
                select(func.max(Document.version_no)).where(
                    Document.case_id == case_id,
                    Document.doc_type == "export_bundle",
                )
            )
            or 0
        ) + 1
        document = Document(
            case_id=case_id,
            doc_type="export_bundle",
            status=DocumentStatus.DRAFT,
            version_no=next_version,
            storage_uri=f"pending://cases/{case.case_no}/bundle-v{next_version}.json",
            checksum_sha256="pending",
            generated_from_json=export_metadata,
            generated_at=generated_at,
        )
        self._session.add(document)
        self._session.flush()

        export_payload = make_json_safe(
            {
                "bundle_id": document.id,
                "bundle_type": "evidence_export_bundle",
                **export_metadata,
            }
        )
        payload_bytes = canonical_json_bytes(export_payload)
        manifest_checksum = compute_sha256_for_json(export_payload)
        stored_bundle = self._generated_output_storage.store(
            category="export-bundles",
            case_no=case.case_no,
            generated_at=generated_at,
            output_id=document.id,
            payload_bytes=payload_bytes,
            content_type="application/json",
            extension="json",
            checksum_sha256=manifest_checksum,
        )
        document.storage_uri = stored_bundle.object_uri
        document.checksum_sha256 = manifest_checksum
        document.generated_from_json = export_payload

        for item in exportable_evidence:
            item.status = EvidenceStatus.EXPORTED
            item.exported_at = generated_at

        self._audit.append(
            actor=principal.actor,
            action="cases.export.prepare",
            entity_type="case",
            entity_id=case.id,
            after={
                "caseNo": case.case_no,
                "bundleId": str(document.id),
                "exportedEvidenceCount": len(exportable_evidence),
                "manifestChecksum": manifest_checksum,
                "storageUri": stored_bundle.object_uri,
            },
        )
        self._session.commit()

        return ExportResponse(
            bundle_id=document.id,
            exported_evidence_count=len(exportable_evidence),
            manifest_checksum=manifest_checksum,
            status="packaged",
        )

    def _load_case_context(
        self,
        case_id: UUID,
    ) -> tuple[Case, list[NormalizedEvent], list[AttributionLink], list[Evidence], list[Document]]:
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
        evidence = self._session.scalars(
            select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at.asc())
        ).all()
        documents = self._session.scalars(
            select(Document).where(Document.case_id == case_id).order_by(Document.generated_at.desc())
        ).all()
        return case, events, attribution_links, evidence, documents
