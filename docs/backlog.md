# Backlog

## Epic 1. Foundation
- [x] monorepo scaffold 생성
- [x] FastAPI 앱 초기화
- [x] React 앱 초기화
- [x] Docker Compose 작성
- [ ] Postgres/OpenSearch/MinIO 연결
- [x] 환경설정 로더 작성

## Epic 2. Data & Ingestion
- [x] source registry 모델 구현
- [x] raw artifact 업로드 API
- [x] parser 인터페이스
- [x] canonical event 모델 구현
- [x] sample parsers: nginx, waf, vpn
- [x] ingest audit log 작성

## Epic 3. Case Management
- [x] case schema/model/service
- [x] case create/get/update API
- [x] case list/filter API
- [x] UI case list page
- [x] UI case detail page

## Epic 4. Search & Correlation
- [ ] correlate API
- [ ] IP search
- [ ] username search
- [ ] hostname search
- [ ] domain/path search
- [ ] candidate asset/user cards

## Epic 5. Evidence Vault
- [x] freeze case endpoint
- [x] manifest JSON 생성
- [ ] evidence list UI
- [ ] export metadata
- [x] checksum validation

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
- [x] RBAC middleware
- [x] audit log append
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
- [x] `GET /healthz`
- [x] `POST /v1/events:ingest`
- [x] `POST /v1/cases`
- [x] `GET /v1/cases/{caseId}`
- [x] `POST /v1/cases/{caseId}/freeze`
- [x] migration + tests + compose

## Codex 실행 지시용 체크
- [x] AGENTS.md 읽기
- [x] PRD.md 반영
- [x] schema.sql 기준으로 모델 생성
- [x] openapi.yaml 기준 라우팅 스켈레톤 생성
- [x] pytest 기본 통과
