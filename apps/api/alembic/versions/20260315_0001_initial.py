"""Initial Phase 1 schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260315_0001"
down_revision = None
branch_labels = None
depends_on = None


source_type = sa.Enum(
    "WEB",
    "WAF",
    "VPN",
    "AD",
    "EDR",
    "DHCP",
    "NAT",
    "FW",
    "DB",
    "APP",
    "OTHER",
    name="source_type",
)
actor_type = sa.Enum(
    "INTERNAL_USER",
    "EXTERNAL_UNKNOWN",
    "SERVICE_ACCOUNT",
    "SYSTEM",
    name="actor_type",
)
case_status = sa.Enum(
    "NEW",
    "TRIAGED",
    "INVESTIGATING",
    "READY_FOR_REVIEW",
    "READY_FOR_EXPORT",
    "CLOSED",
    "REJECTED",
    name="case_status",
)
evidence_status = sa.Enum("PENDING", "FROZEN", "EXPORTED", name="evidence_status")
document_status = sa.Enum("DRAFT", "UNDER_REVIEW", "APPROVED", "REJECTED", name="document_status")


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    source_type.create(bind, checkfirst=True)
    actor_type.create(bind, checkfirst=True)
    case_status.create(bind, checkfirst=True)
    evidence_status.create(bind, checkfirst=True)
    document_status.create(bind, checkfirst=True)

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("type", source_type, nullable=False),
        sa.Column("parser_name", sa.Text()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "ingest_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("collected_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("parser_version", sa.Text()),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "raw_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("ingest_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingest_batches.id")),
        sa.Column("object_uri", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("collected_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("parser_version", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_no", sa.Text(), unique=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text()),
        sa.Column("department", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("account_name", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "account_name"),
    )
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_tag", sa.Text(), nullable=False, unique=True),
        sa.Column("hostname", sa.Text(), nullable=False),
        sa.Column("serial_number", sa.Text()),
        sa.Column("device_type", sa.Text(), nullable=False, server_default="workstation"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("primary_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "ip_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ip", postgresql.INET(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("asn", sa.Text()),
        sa.Column("carrier", sa.Text()),
        sa.Column("geolocation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_vpn", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_tor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_cloud", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "asset_network_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("ip", postgresql.INET(), nullable=False),
        sa.Column("macaddr", postgresql.MACADDR()),
        sa.Column("vlan", sa.Text()),
        sa.Column("switch_port", sa.Text()),
        sa.Column("ssid", sa.Text()),
        sa.Column("lease_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("lease_end", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("source_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "normalized_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_artifacts.id"), nullable=False),
        sa.Column("event_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text()),
        sa.Column("src_ip", postgresql.INET()),
        sa.Column("dst_ip", postgresql.INET()),
        sa.Column("hostname", sa.Text()),
        sa.Column("username", sa.Text()),
        sa.Column("session_id", sa.Text()),
        sa.Column("request_method", sa.Text()),
        sa.Column("request_host", sa.Text()),
        sa.Column("request_path", sa.Text()),
        sa.Column("status_code", sa.Integer()),
        sa.Column("bytes_sent", sa.BigInteger()),
        sa.Column("rule_name", sa.Text()),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("checksum_sha256", sa.String(length=64)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("severity", sa.Text(), nullable=False, server_default="medium"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("condition_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", "version"),
    )
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rules.id")),
        sa.Column("opened_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("primary_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("normalized_events.id")),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_no", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", case_status, nullable=False, server_default="NEW"),
        sa.Column("severity", sa.Text(), nullable=False, server_default="medium"),
        sa.Column("summary", sa.Text()),
        sa.Column("opened_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("primary_ip", postgresql.INET()),
        sa.Column("primary_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id")),
        sa.Column("primary_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("external_actor_label", sa.Text()),
        sa.Column("confidence_grade", sa.Text()),
        sa.Column("assignee", sa.Text()),
        sa.Column("created_by", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "case_events",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("normalized_events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "attribution_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_type", actor_type, nullable=False),
        sa.Column("observed_ip", postgresql.INET()),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id")),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("grade", sa.Text(), nullable=False, server_default="D"),
        sa.Column("rationale", sa.Text()),
        sa.Column("evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("engine_version", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.Text(), nullable=False),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_artifacts.id")),
        sa.Column("normalized_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("normalized_events.id")),
        sa.Column("object_uri", sa.Text()),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", evidence_status, nullable=False, server_default="PENDING"),
        sa.Column("frozen_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("exported_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.Text(), nullable=False),
        sa.Column("status", document_status, nullable=False, server_default="DRAFT"),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("storage_uri", sa.Text()),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("generated_from_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("case_id", "doc_type", "version_no"),
    )
    op.create_table(
        "review_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("assignee", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("due_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("idx_normalized_events_time", "normalized_events", ["event_time"])
    op.create_index("idx_normalized_events_src_ip_time", "normalized_events", ["src_ip", "event_time"])
    op.create_index("idx_normalized_events_username_time", "normalized_events", ["username", "event_time"])
    op.create_index("idx_asset_network_bindings_ip_window", "asset_network_bindings", ["ip", "lease_start", "lease_end"])
    op.create_index("idx_cases_status_opened", "cases", ["status", "opened_at"])
    op.create_index("idx_evidence_case", "evidence", ["case_id", "created_at"])
    op.create_index("idx_documents_case", "documents", ["case_id", "generated_at"])
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_entity", table_name="audit_logs")
    op.drop_index("idx_documents_case", table_name="documents")
    op.drop_index("idx_evidence_case", table_name="evidence")
    op.drop_index("idx_cases_status_opened", table_name="cases")
    op.drop_index("idx_asset_network_bindings_ip_window", table_name="asset_network_bindings")
    op.drop_index("idx_normalized_events_username_time", table_name="normalized_events")
    op.drop_index("idx_normalized_events_src_ip_time", table_name="normalized_events")
    op.drop_index("idx_normalized_events_time", table_name="normalized_events")

    for table_name in [
        "audit_logs",
        "review_tasks",
        "documents",
        "evidence",
        "attribution_links",
        "case_events",
        "cases",
        "alerts",
        "rules",
        "normalized_events",
        "asset_network_bindings",
        "ip_observations",
        "assets",
        "accounts",
        "users",
        "raw_artifacts",
        "ingest_batches",
        "sources",
    ]:
        op.drop_table(table_name)

    bind = op.get_bind()
    document_status.drop(bind, checkfirst=True)
    evidence_status.drop(bind, checkfirst=True)
    case_status.drop(bind, checkfirst=True)
    actor_type.drop(bind, checkfirst=True)
    source_type.drop(bind, checkfirst=True)
