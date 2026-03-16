from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from app.core.serialization import canonical_json_bytes, make_json_safe
from app.models.entities import AttributionLink, Case, Document, Evidence, NormalizedEvent


def compute_sha256_for_json(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def build_case_manifest(
    *,
    case: Case,
    events: list[NormalizedEvent],
    evidence: list[Evidence],
    attribution_links: list[AttributionLink],
    documents: list[Document],
    generated_at: datetime,
) -> dict[str, Any]:
    manifest = {
        "generated_at": generated_at,
        "case": {
            "id": case.id,
            "case_no": case.case_no,
            "title": case.title,
            "status": case.status,
            "severity": case.severity,
            "summary": case.summary,
            "primary_ip": case.primary_ip,
            "external_actor_label": case.external_actor_label,
            "confidence_grade": case.confidence_grade,
            "opened_at": case.opened_at,
        },
        "events": [
            {
                "id": event.id,
                "event_time": event.event_time,
                "source_type": event.source_type,
                "event_type": event.event_type,
                "src_ip": event.src_ip,
                "dst_ip": event.dst_ip,
                "hostname": event.hostname,
                "username": event.username,
                "session_id": event.session_id,
                "request_host": event.request_host,
                "request_path": event.request_path,
                "status_code": event.status_code,
                "bytes_sent": event.bytes_sent,
                "raw_artifact_id": event.raw_artifact_id,
                "checksum_sha256": event.checksum_sha256,
            }
            for event in events
        ],
        "evidence": [
            {
                "id": item.id,
                "evidence_type": item.evidence_type,
                "raw_artifact_id": item.raw_artifact_id,
                "normalized_event_id": item.normalized_event_id,
                "object_uri": item.object_uri,
                "sha256": item.sha256,
                "status": item.status,
                "frozen_at": item.frozen_at,
            }
            for item in evidence
        ],
        "attribution_links": [
            {
                "id": link.id,
                "actor_type": link.actor_type,
                "display_name": link.display_name,
                "observed_ip": link.observed_ip,
                "confidence_score": link.confidence_score,
                "confidence_grade": link.confidence_grade,
                "rationale": link.rationale,
                "next_step": link.next_step,
            }
            for link in attribution_links
        ],
        "documents": [
            {
                "id": document.id,
                "doc_type": document.doc_type,
                "status": document.status,
                "version_no": document.version_no,
                "checksum_sha256": document.checksum_sha256,
                "generated_at": document.generated_at,
            }
            for document in documents
        ],
    }
    return make_json_safe(manifest)


def build_export_bundle_metadata(
    *,
    case: Case,
    events: list[NormalizedEvent],
    evidence: list[Evidence],
    documents: list[Document],
    generated_at: datetime,
) -> dict[str, Any]:
    payload = {
        "generated_at": generated_at,
        "bundle_state": "DRAFT",
        "case": {
            "id": case.id,
            "case_no": case.case_no,
            "title": case.title,
            "status": case.status,
            "severity": case.severity,
            "primary_ip": case.primary_ip,
        },
        "input_snapshot": {
            "events": [
                {
                    "id": event.id,
                    "event_time": event.event_time,
                    "event_type": event.event_type,
                    "src_ip": event.src_ip,
                    "dst_ip": event.dst_ip,
                    "hostname": event.hostname,
                    "username": event.username,
                    "session_id": event.session_id,
                    "request_host": event.request_host,
                    "request_path": event.request_path,
                    "raw_artifact_id": event.raw_artifact_id,
                    "checksum_sha256": event.checksum_sha256,
                }
                for event in events
            ],
            "evidence": [
                {
                    "id": item.id,
                    "evidence_type": item.evidence_type,
                    "raw_artifact_id": item.raw_artifact_id,
                    "normalized_event_id": item.normalized_event_id,
                    "object_uri": item.object_uri,
                    "sha256": item.sha256,
                    "status": item.status,
                    "frozen_at": item.frozen_at,
                }
                for item in evidence
            ],
            "documents": [
                {
                    "id": document.id,
                    "doc_type": document.doc_type,
                    "status": document.status,
                    "version_no": document.version_no,
                    "storage_uri": document.storage_uri,
                    "checksum_sha256": document.checksum_sha256,
                    "generated_at": document.generated_at,
                }
                for document in documents
            ],
        },
        "package_plan": {
            "bundle_format": "metadata-only",
            "final_legal_filing_generated": False,
            "requires_review": True,
            "evidence_count": len(evidence),
            "document_count": len(documents),
        },
    }
    return make_json_safe(payload)
