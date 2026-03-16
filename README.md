# Incident Attribution Suite

자사 시스템 로그를 수집·정규화하고, 사건 단위의 증거 보존과 보수적 귀속 정리를 수행하는 내부 조사용 Phase 1 기반 저장소입니다. 현재 저장소에는 FastAPI API, React/Vite 웹 셸, 공유 contracts 패키지, 로컬 Docker Compose 구성이 포함됩니다.

## Safety Guardrails

1. 외부 공인 IP 사용자의 실명 추정 또는 자동 특정은 구현하지 않습니다.
2. 외부 사건은 `EXTERNAL_UNKNOWN` / `성명불상` / `D` 등급 / `통신사/플랫폼/수사기관 조회 필요` 상태를 유지합니다.
3. 자동 신고·자동 고소·자동 제출 기능은 구현하지 않습니다.
4. 공격, 스캔, 익스플로잇, 강제 차단, counter-hacking 기능은 구현하지 않습니다.
5. 생성 문서와 freeze 산출물은 모두 `DRAFT` 또는 review-gated 상태로만 다룹니다.

## Repository Layout

- `apps/api`: FastAPI, SQLAlchemy 2.x, Alembic, pytest
- `apps/web`: React + TypeScript + Vite
- `packages/contracts`: API/web 공유 타입
- `infra/docker-compose.yml`: postgres, opensearch, minio, redis, api, web
- `docs/`: PRD, 아키텍처, 데이터 모델, API, 보안 문서

## Local Run

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./apps/api[dev]
cd apps/api
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
npm install
npm run dev --workspace @incident-attribution/web
```

### Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

기본 주소:

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Web: `http://localhost:5173`
- OpenSearch: `http://localhost:9200`
- MinIO console: `http://localhost:9001`

## Test Commands

```bash
source .venv/bin/activate
pytest apps/api/tests
```

## Environment Variables

### API

- `IAS_DATABASE_URL`: SQLAlchemy database URL
- `IAS_OPENSEARCH_URL`: OpenSearch endpoint for readiness checks
- `IAS_MINIO_ENDPOINT`: MinIO endpoint for readiness checks
- `IAS_REDIS_URL`: Redis endpoint for readiness checks
- `IAS_RAW_ARTIFACT_STORAGE_BACKEND`: `filesystem` 또는 `minio`
- `IAS_RAW_ARTIFACT_STORAGE_DIR`: filesystem backend raw artifact 저장 경로
- `IAS_AUTH_DEFAULT_ACTOR`: placeholder middleware actor name
- `IAS_AUTH_DEFAULT_ROLES`: placeholder middleware role list
- `IAS_MINIO_ACCESS_KEY`: MinIO access key
- `IAS_MINIO_SECRET_KEY`: MinIO secret key
- `IAS_MINIO_BUCKET`: raw artifact bucket name
- `IAS_MINIO_SECURE`: MinIO HTTPS 여부

예시 파일: [`apps/api/.env.example`](/Users/jimin/Desktop/study/ip-complaint/apps/api/.env.example)

### Web

- `VITE_API_BASE_URL`: frontend가 호출할 API base URL

예시 파일: [`apps/web/.env.example`](/Users/jimin/Desktop/study/ip-complaint/apps/web/.env.example)

## Implemented In Phase 1

- `GET /healthz`
- `POST /v1/events:ingest`
- `POST /v1/search/correlate`
- `GET /v1/cases`
- `POST /v1/cases`
- `PATCH /v1/cases/{caseId}`
- `GET /v1/cases/{caseId}`
- `POST /v1/cases/{caseId}/freeze`
- SQLAlchemy 모델과 Alembic 초기 마이그레이션
- raw artifact filesystem/MinIO storage abstraction과 parser registry
- 이벤트 ingest, 상관분석, 케이스 생성/조회/수정, evidence freeze, manifest SHA-256, audit log append 서비스
- 최소 React app shell, 사건 목록 placeholder, 사건 상세 placeholder, draft 경고 배너

## Stubbed Or Deferred

- OpenSearch 기반 실제 색인/검색 고도화
- MinIO object lock 기반 immutable storage hardening
- Redis background jobs
- 내부 귀속 엔진(A/B/C 계산, DHCP/VPN/AD/EDR/CMDB 매핑)
- 문서 템플릿 렌더링과 승인 워크플로우
- alerts/rules, export bundle ZIP, path-level correlation UI

## Known Limitations

- Phase 1 ingest는 raw artifact를 filesystem 또는 MinIO에 immutable-style로 저장하지만, OpenSearch 색인은 아직 연결하지 않았습니다.
- correlate API는 현재 DB 직접 조회 기반이며 path 단위 검색과 dedicated search index는 아직 없습니다.
- freeze는 manifest JSON snapshot과 document metadata를 DB에 기록하지만 외부 제출용 최종 문서는 생성하지 않습니다.
- RBAC는 header 기반 placeholder middleware이며 실제 OIDC/SAML 연동은 후속 단계입니다.
- 웹 UI는 placeholder 중심이며 사건 생성/수정 폼은 아직 없습니다.
- Docker Compose의 `api`/`web` 서비스는 컨테이너 시작 시 의존성을 설치하므로 초기 기동 시간이 길 수 있습니다.
