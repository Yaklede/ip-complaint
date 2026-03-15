# Backlog

## Epic 1. Foundation
- [ ] monorepo scaffold 생성
- [ ] FastAPI 앱 초기화
- [ ] React 앱 초기화
- [ ] Docker Compose 작성
- [ ] Postgres/OpenSearch/MinIO 연결
- [ ] 환경설정 로더 작성

## Epic 2. Data & Ingestion
- [ ] source registry 모델 구현
- [ ] raw artifact 업로드 API
- [ ] parser 인터페이스
- [ ] canonical event 모델 구현
- [ ] sample parsers: nginx, waf, vpn
- [ ] ingest audit log 작성

## Epic 3. Case Management
- [ ] case schema/model/service
- [ ] case create/get/update API
- [ ] case list/filter API
- [ ] UI case list page
- [ ] UI case detail page

## Epic 4. Search & Correlation
- [ ] correlate API
- [ ] IP search
- [ ] username search
- [ ] hostname search
- [ ] domain/path search
- [ ] candidate asset/user cards

## Epic 5. Evidence Vault
- [ ] freeze case endpoint
- [ ] manifest JSON 생성
- [ ] evidence list UI
- [ ] export metadata
- [ ] checksum validation

## Epic 6. Attribution Engine
- [ ] DHCP binding model/parser
- [ ] VPN login model/parser
- [ ] AD login model/parser
- [ ] EDR asset enrichment model
- [ ] confidence scoring engine
- [ ] grade A/B/C/D rules

## Epic 7. Documents
- [ ] snapshot builder
- [ ] case summary template
- [ ] evidence manifest template
- [ ] complaint draft template
- [ ] document review API
- [ ] document list/download UI

## Epic 8. Security & Governance
- [ ] RBAC middleware
- [ ] audit log append
- [ ] masking utilities
- [ ] approval workflow
- [ ] retention policy config
- [ ] admin settings UI

## Epic 9. Alerts & Rules
- [ ] rule model
- [ ] rule CRUD
- [ ] alert model
- [ ] promote alert to case
- [ ] dashboard widgets

## P0 이번 주 즉시 작업
- [ ] `GET /healthz`
- [ ] `POST /v1/events:ingest`
- [ ] `POST /v1/cases`
- [ ] `GET /v1/cases/{caseId}`
- [ ] `POST /v1/cases/{caseId}/freeze`
- [ ] migration + tests + compose

## Codex 실행 지시용 체크
- [ ] AGENTS.md 읽기
- [ ] PRD.md 반영
- [ ] schema.sql 기준으로 모델 생성
- [ ] openapi.yaml 기준 라우팅 스켈레톤 생성
- [ ] pytest 기본 통과
