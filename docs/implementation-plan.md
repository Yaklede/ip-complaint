# Implementation Plan

## 1. 목표

이 문서는 코딩 에이전트가 실제 구현에 들어갈 수 있도록 단계별 작업 순서와 저장소 구조를 정의한다.

## 2. 추천 저장소 구조

```text
incident-attribution-suite/
├─ AGENTS.md
├─ README.md
├─ PRD.md
├─ apps/
│  ├─ api/
│  │  ├─ app/
│  │  │  ├─ api/
│  │  │  ├─ core/
│  │  │  ├─ db/
│  │  │  ├─ domain/
│  │  │  ├─ models/
│  │  │  ├─ repositories/
│  │  │  ├─ schemas/
│  │  │  ├─ services/
│  │  │  └─ main.py
│  │  ├─ tests/
│  │  └─ alembic/
│  └─ web/
│     ├─ src/
│     │  ├─ app/
│     │  ├─ pages/
│     │  ├─ widgets/
│     │  ├─ entities/
│     │  ├─ features/
│     │  └─ shared/
├─ packages/
│  ├─ contracts/
│  └─ ui/
├─ docs/
├─ infra/
│  └─ docker-compose.yml
└─ scripts/
```

## 3. Phase 1 상세 작업

### 3.1 Backend Skeleton
- FastAPI app bootstrapping
- settings/config
- db session
- health endpoint
- base exception model
- auth stub + role model

### 3.2 Database
- `docs/schema.sql` 기반 모델링
- Alembic 초기 migration
- seed data for roles/source types

### 3.3 Ingestion MVP
- raw artifact 등록 API
- Canonical Event 저장
- simple parser interface
- local file/object storage adapter

### 3.4 Case MVP
- 사건 생성
- 사건 상세 조회
- 사건 상태 변경
- 사건과 이벤트 연결

### 3.5 Evidence MVP
- freeze endpoint
- manifest 생성
- SHA-256 저장
- export metadata 저장

### 3.6 UI MVP
- 로그인 후 기본 레이아웃
- 사건 목록
- 사건 상세
- 검색 패널
- 타임라인 탭
- 증거 탭

## 4. Phase 2 상세 작업

- 귀속 엔진 서비스
- 자산/사용자/계정 엔티티 UI
- 문서 생성 템플릿 엔진
- 문서 승인 워크플로우
- 귀속 근거 카드
- 사건 export bundle

## 5. Phase 3 상세 작업

- 룰 엔진 CRUD
- 알림/사건 승격
- SLA/운영 대시보드
- 규정 준수 체크리스트
- 배치/큐 기반 비동기 작업
- 성능 튜닝

## 6. 8주 일정 예시

### Week 1
- repo scaffold
- docker compose
- backend/web boot
- schema & migrations

### Week 2
- ingestion MVP
- raw artifact storage
- normalized event persistence

### Week 3
- search correlate API
- case service
- UI case list/detail

### Week 4
- evidence freeze
- audit logging
- role guard

### Week 5
- attribution engine v1
- asset/user resolution
- confidence scoring

### Week 6
- document generation v1
- complaint template
- review workflow

### Week 7
- rules/alerts
- dashboards
- policy checklist

### Week 8
- hardening
- tests
- docs
- release candidate

## 7. 테스트 전략

### 단위 테스트
- parser
- score calculator
- case state transitions
- document rendering
- masking utilities

### 통합 테스트
- ingest -> case -> freeze 흐름
- attribution resolution
- document generation
- audit log emission

### E2E 테스트
- 사건 검색
- 사건 생성
- freeze
- 문서 생성
- 승인

## 8. Definition of Done

각 작업은 아래를 만족해야 완료다.

- 코드 구현
- 테스트 작성/통과
- API/문서 갱신
- 감사로그 고려
- 권한 체크 고려
- 예외 처리 포함

## 9. 구현 우선순위

P0:
- DB, ingest, case, evidence, audit, health

P1:
- attribution, doc generation, review flow

P2:
- alerts, rules, dashboards, optimization

## 10. 리스크 메모

- OpenSearch 없이도 MVP 진행 가능하도록 Postgres fallback query 설계 고려
- 문서 엔진은 HTML -> PDF 변환 또는 DOCX 렌더링 중 하나를 선택
- MinIO object lock은 운영환경 capability 확인 필요
