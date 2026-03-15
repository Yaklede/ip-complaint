from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.policy import (
    EXTERNAL_UNKNOWN_DISPLAY_NAME,
    EXTERNAL_UNKNOWN_NEXT_STEP,
)
from app.db.base import Base
from app.db.types import IPAddressType, JSONType, MacAddressType
from app.models.enums import ActorType, CaseStatus, DocumentStatus, EvidenceStatus, SourceType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


source_type_enum = SAEnum(SourceType, name="source_type")
actor_type_enum = SAEnum(ActorType, name="actor_type")
case_status_enum = SAEnum(CaseStatus, name="case_status")
evidence_status_enum = SAEnum(EvidenceStatus, name="evidence_status")
document_status_enum = SAEnum(DocumentStatus, name="document_status")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    type: Mapped[SourceType] = mapped_column(source_type_enum, nullable=False)
    parser_name: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ingest_batches: Mapped[list["IngestBatch"]] = relationship(back_populates="source")
    raw_artifacts: Mapped[list["RawArtifact"]] = relationship(back_populates="source")
    normalized_events: Mapped[list["NormalizedEvent"]] = relationship(back_populates="source")


class IngestBatch(Base):
    __tablename__ = "ingest_batches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parser_version: Mapped[str | None] = mapped_column(Text)
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[Source] = relationship(back_populates="ingest_batches")
    raw_artifacts: Mapped[list["RawArtifact"]] = relationship(back_populates="ingest_batch")


class RawArtifact(Base):
    __tablename__ = "raw_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    ingest_batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingest_batches.id"))
    object_uri: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parser_version: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[Source] = relationship(back_populates="raw_artifacts")
    ingest_batch: Mapped[IngestBatch | None] = relationship(back_populates="raw_artifacts")
    normalized_events: Mapped[list["NormalizedEvent"]] = relationship(back_populates="raw_artifact")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_no: Mapped[str | None] = mapped_column(Text, unique=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="user")
    owned_assets: Mapped[list["Asset"]] = relationship(
        back_populates="owner_user", foreign_keys="Asset.owner_user_id"
    )
    primary_assets: Mapped[list["Asset"]] = relationship(
        back_populates="primary_user", foreign_keys="Asset.primary_user_id"
    )
    reviewed_documents: Mapped[list["Document"]] = relationship(
        back_populates="reviewed_by_user", foreign_keys="Document.reviewed_by"
    )


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("provider", "account_name"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    account_name: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="accounts")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_tag: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    hostname: Mapped[str] = mapped_column(Text, nullable=False)
    serial_number: Mapped[str | None] = mapped_column(Text)
    device_type: Mapped[str] = mapped_column(Text, default="workstation", nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    primary_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    owner_user: Mapped[User | None] = relationship(
        back_populates="owned_assets", foreign_keys=[owner_user_id]
    )
    primary_user: Mapped[User | None] = relationship(
        back_populates="primary_assets", foreign_keys=[primary_user_id]
    )


class IPObservation(Base):
    __tablename__ = "ip_observations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ip: Mapped[str] = mapped_column(IPAddressType(), nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    asn: Mapped[str | None] = mapped_column(Text)
    carrier: Mapped[str | None] = mapped_column(Text)
    geolocation_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    is_vpn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_tor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cloud: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AssetNetworkBinding(Base):
    __tablename__ = "asset_network_bindings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    ip: Mapped[str] = mapped_column(IPAddressType(), nullable=False)
    macaddr: Mapped[str | None] = mapped_column(MacAddressType())
    vlan: Mapped[str | None] = mapped_column(Text)
    switch_port: Mapped[str | None] = mapped_column(Text)
    ssid: Mapped[str | None] = mapped_column(Text)
    lease_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    raw_artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_artifacts.id"), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(Text)
    src_ip: Mapped[str | None] = mapped_column(IPAddressType())
    dst_ip: Mapped[str | None] = mapped_column(IPAddressType())
    hostname: Mapped[str | None] = mapped_column(Text)
    username: Mapped[str | None] = mapped_column(Text)
    session_id: Mapped[str | None] = mapped_column(Text)
    request_method: Mapped[str | None] = mapped_column(String(16))
    request_host: Mapped[str | None] = mapped_column(Text)
    request_path: Mapped[str | None] = mapped_column(Text)
    status_code: Mapped[int | None] = mapped_column(Integer)
    bytes_sent: Mapped[int | None] = mapped_column(Integer)
    rule_name: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[Source] = relationship(back_populates="normalized_events")
    raw_artifact: Mapped[RawArtifact] = relationship(back_populates="normalized_events")

    @property
    def source_type(self) -> SourceType | None:
        if self.source is None:
            return None
        return self.source.type


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("name", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text, default="medium", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    condition_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rules.id"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    primary_event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("normalized_events.id"))
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_no: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CaseStatus] = mapped_column(case_status_enum, default=CaseStatus.NEW, nullable=False)
    severity: Mapped[str] = mapped_column(Text, default="medium", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    primary_ip: Mapped[str | None] = mapped_column(IPAddressType())
    primary_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"))
    primary_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    external_actor_label: Mapped[str | None] = mapped_column(Text)
    confidence_grade: Mapped[str | None] = mapped_column(String(8))
    assignee: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    case_events: Mapped[list["CaseEvent"]] = relationship(back_populates="case")
    attribution_links: Mapped[list["AttributionLink"]] = relationship(back_populates="case")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="case")
    documents: Mapped[list["Document"]] = relationship(back_populates="case")


class CaseEvent(Base):
    __tablename__ = "case_events"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("normalized_events.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    case: Mapped[Case] = relationship(back_populates="case_events")
    event: Mapped[NormalizedEvent] = relationship()


class AttributionLink(Base):
    __tablename__ = "attribution_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    actor_type: Mapped[ActorType] = mapped_column(actor_type_enum, nullable=False)
    observed_ip: Mapped[str | None] = mapped_column(IPAddressType())
    asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("accounts.id"))
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    grade: Mapped[str] = mapped_column(String(8), default="D", nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list, nullable=False)
    engine_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    case: Mapped[Case] = relationship(back_populates="attribution_links")
    asset: Mapped[Asset | None] = relationship()
    user: Mapped[User | None] = relationship()
    account: Mapped[Account | None] = relationship()

    @property
    def display_name(self) -> str:
        if self.actor_type == ActorType.EXTERNAL_UNKNOWN:
            return EXTERNAL_UNKNOWN_DISPLAY_NAME
        if self.user is not None and self.user.display_name:
            return self.user.display_name
        if self.account is not None and self.account.account_name:
            return self.account.account_name
        return self.actor_type.value

    @property
    def confidence_grade(self) -> str:
        return self.grade

    @property
    def next_step(self) -> str | None:
        if self.actor_type == ActorType.EXTERNAL_UNKNOWN:
            return EXTERNAL_UNKNOWN_NEXT_STEP
        return None


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(Text, nullable=False)
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_artifacts.id"))
    normalized_event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("normalized_events.id"))
    object_uri: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[EvidenceStatus] = mapped_column(
        evidence_status_enum, default=EvidenceStatus.PENDING, nullable=False
    )
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    case: Mapped[Case] = relationship(back_populates="evidence")
    raw_artifact: Mapped[RawArtifact | None] = relationship()
    normalized_event: Mapped[NormalizedEvent | None] = relationship()


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("case_id", "doc_type", "version_no"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        document_status_enum, default=DocumentStatus.DRAFT, nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    storage_uri: Mapped[str | None] = mapped_column(Text)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_from_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    case: Mapped[Case] = relationship(back_populates="documents")
    reviewed_by_user: Mapped[User | None] = relationship(back_populates="reviewed_documents")


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    task_type: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
