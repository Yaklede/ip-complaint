# Incident Attribution Suite

자사 서비스/도메인에 대한 비정상 접근, 데이터 열람·반출 시도, 관리자 경로 접근, 인증 우회 정황을
상관분석하여 **IP → 단말(PC) → 계정/사용자 → 증거 패키지 → 고소장 초안**까지 연결하는
내부 조사·증거관리 시스템의 기획 패키지입니다.

이 저장소는 바로 개발을 시작할 수 있도록 다음을 포함합니다.

- `PRD.md`: 제품 요구사항 정의서
- `AGENTS.md`: Codex/코딩 에이전트용 작업 규칙
- `AGNETS.md`: 오타 호환용 복제본(표준 파일명은 `AGENTS.md`)
- `docs/`: 아키텍처, 데이터 모델, API, UX, 구현계획, 보안/컴플라이언스 문서
- `docs/openapi.yaml`: 백엔드 API 초안
- `docs/schema.sql`: PostgreSQL 스키마 초안
- `infra/docker-compose.yml`: 로컬 개발용 의존 서비스 초안

## 핵심 원칙

1. **내부 귀속(Internal attribution)** 은 DHCP/NAT/VPN/AD/EDR/CMDB 등 자사 보유 데이터로만 수행한다.
2. **외부 공인 IP의 실명 추정/자동 특정은 금지**한다.
3. 외부 사건의 피행위자는 기본적으로 `성명불상`으로 두고, 통신사·플랫폼·수사기관 조회 필요 상태로 관리한다.
4. 고소장/신고서/사건요약은 **자동 생성 가능**, **자동 제출은 금지**한다.
5. 모든 산출물은 **원본 증거, 해시, 감사로그, 승인흐름**을 동반해야 한다.

## 추천 기술 스택

- Frontend: React + TypeScript + Vite
- Backend API: FastAPI + Pydantic v2 + SQLAlchemy 2.x
- DB: PostgreSQL
- Search/Correlation: OpenSearch
- Object Storage(Evidence Vault): MinIO(S3 호환)
- Queue/Cache: Redis
- Infra(로컬): Docker Compose
- Auth: OIDC/SAML 연동 가능한 RBAC 구조

## Codex 시작 순서

1. `AGENTS.md`
2. `PRD.md`
3. `docs/architecture.md`
4. `docs/data-model.md`
5. `docs/api-spec.md`
6. `docs/implementation-plan.md`
7. `docs/backlog.md`

그 다음, `docs/codex-kickoff-prompt.md`의 프롬프트를 코딩 에이전트에 전달하면 됩니다.

## 비범위(Non-goals)

- 공격용 스캐너, 익스플로잇, 침입 자동화
- 외부 IP의 불법적 실명 식별
- 수사기관/통신사 권한을 가장하는 기능
- 무인 자동 고소/자동 신고
- 법률 판단을 사람 검토 없이 확정하는 기능

## 참고

본 문서는 2026-03-15 기준 요구사항 정리용이며, 실제 제출 문서와 운영 정책은 법무/개인정보보호 책임자/보안책임자의 최종 검토를 거쳐야 합니다.
