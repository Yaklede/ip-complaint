CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_type') THEN
        CREATE TYPE source_type AS ENUM ('WEB','WAF','VPN','AD','EDR','DHCP','NAT','FW','DB','APP','OTHER');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'actor_type') THEN
        CREATE TYPE actor_type AS ENUM ('INTERNAL_USER','EXTERNAL_UNKNOWN','SERVICE_ACCOUNT','SYSTEM');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'case_status') THEN
        CREATE TYPE case_status AS ENUM ('NEW','TRIAGED','INVESTIGATING','READY_FOR_REVIEW','READY_FOR_EXPORT','CLOSED','REJECTED');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'evidence_status') THEN
        CREATE TYPE evidence_status AS ENUM ('PENDING','FROZEN','EXPORTED');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_status') THEN
        CREATE TYPE document_status AS ENUM ('DRAFT','UNDER_REVIEW','APPROVED','REJECTED');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    type source_type NOT NULL,
    parser_name TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingest_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    collected_at TIMESTAMPTZ NOT NULL,
    parser_version TEXT,
    event_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    ingest_batch_id UUID REFERENCES ingest_batches(id),
    object_uri TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    parser_version TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_no TEXT UNIQUE,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    email TEXT,
    department TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider TEXT NOT NULL,
    account_name TEXT NOT NULL,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(provider, account_name)
);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_tag TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    serial_number TEXT,
    device_type TEXT NOT NULL DEFAULT 'workstation',
    owner_user_id UUID REFERENCES users(id),
    primary_user_id UUID REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ip_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip INET NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('PRIVATE','PUBLIC')),
    first_seen_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    asn TEXT,
    carrier TEXT,
    geolocation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_vpn BOOLEAN NOT NULL DEFAULT FALSE,
    is_tor BOOLEAN NOT NULL DEFAULT FALSE,
    is_cloud BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS asset_network_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    ip INET NOT NULL,
    macaddr MACADDR,
    vlan TEXT,
    switch_port TEXT,
    ssid TEXT,
    lease_start TIMESTAMPTZ NOT NULL,
    lease_end TIMESTAMPTZ NOT NULL,
    source_event_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS normalized_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    raw_artifact_id UUID NOT NULL REFERENCES raw_artifacts(id),
    event_time TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT,
    src_ip INET,
    dst_ip INET,
    hostname TEXT,
    username TEXT,
    session_id TEXT,
    request_method TEXT,
    request_host TEXT,
    request_path TEXT,
    status_code INTEGER,
    bytes_sent BIGINT,
    rule_name TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    checksum_sha256 TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL DEFAULT 'medium',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    condition_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES rules(id),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'open',
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    score NUMERIC(5,2) NOT NULL DEFAULT 0,
    primary_event_id UUID REFERENCES normalized_events(id),
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_no TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    status case_status NOT NULL DEFAULT 'NEW',
    severity TEXT NOT NULL DEFAULT 'medium',
    summary TEXT,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    primary_ip INET,
    primary_asset_id UUID REFERENCES assets(id),
    primary_user_id UUID REFERENCES users(id),
    external_actor_label TEXT,
    confidence_grade TEXT,
    assignee TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS case_events (
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES normalized_events(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, event_id)
);

CREATE TABLE IF NOT EXISTS attribution_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    actor_type actor_type NOT NULL,
    observed_ip INET,
    asset_id UUID REFERENCES assets(id),
    user_id UUID REFERENCES users(id),
    account_id UUID REFERENCES accounts(id),
    confidence_score NUMERIC(5,4) NOT NULL DEFAULT 0,
    grade TEXT NOT NULL DEFAULT 'D',
    rationale TEXT,
    evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    engine_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    raw_artifact_id UUID REFERENCES raw_artifacts(id),
    normalized_event_id UUID REFERENCES normalized_events(id),
    object_uri TEXT,
    sha256 TEXT NOT NULL,
    status evidence_status NOT NULL DEFAULT 'PENDING',
    frozen_at TIMESTAMPTZ,
    exported_at TIMESTAMPTZ,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    status document_status NOT NULL DEFAULT 'DRAFT',
    version_no INTEGER NOT NULL DEFAULT 1,
    storage_uri TEXT,
    checksum_sha256 TEXT NOT NULL,
    generated_from_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewed_by UUID REFERENCES users(id),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(case_id, doc_type, version_no)
);

CREATE TABLE IF NOT EXISTS review_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    assignee TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    before_json JSONB,
    after_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_normalized_events_time ON normalized_events (event_time DESC);
CREATE INDEX IF NOT EXISTS idx_normalized_events_src_ip_time ON normalized_events (src_ip, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_normalized_events_username_time ON normalized_events (username, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_asset_network_bindings_ip_window ON asset_network_bindings (ip, lease_start, lease_end);
CREATE INDEX IF NOT EXISTS idx_cases_status_opened ON cases (status, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence (case_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_case ON documents (case_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id, created_at DESC);
