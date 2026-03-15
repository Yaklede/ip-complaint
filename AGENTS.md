## 0. 목표

이 저장소의 목표는 다음을 구현하는 것이다.

- 자사 시스템 로그를 수집/정규화한다.
- IP, 계정, 단말, 세션, 도메인 요청을 상관분석한다.
- **내부 귀속**인 경우 `IP -> PC -> 계정/사용자`를 연결한다.
- 사건 단위로 증거를 고정(freeze)하고 해시를 부여한다.
- 사건 요약서와 고소장 초안을 생성한다.
- 외부 공인 IP 사건은 `성명불상` 상태로 유지하고 추가 조회 필요를 명시한다.

## 1. 반드시 먼저 읽을 파일

작업 전 아래 순서로 반드시 읽는다.

1. `README.md`
2. `PRD.md`
3. `docs/architecture.md`
4. `docs/data-model.md`
5. `docs/api-spec.md`
6. `docs/security-and-compliance.md`
7. `docs/implementation-plan.md`
8. `docs/backlog.md`

## 2. 절대 어기면 안 되는 가드레일

### 2.1 외부 실명 특정 금지
외부 공인 IP에 대해 다음을 구현하지 않는다.

- 실명 자동 추정
- 주민등록번호/주소/전화번호 추정
- 통신사·플랫폼 가입자 정보 조회를 흉내내는 기능
- 불법 스크래핑/우회/침투를 통한 신원확인 기능

외부 사건은 아래 형태만 허용한다.

- `actor_type = EXTERNAL_UNKNOWN`
- `display_name = 성명불상`
- `attribution_grade = D`
- `next_step = 통신사/플랫폼/수사기관 조회 필요`

### 2.2 자동 제출 금지
다음 기능은 구현하지 않는다.

- 경찰/KISA/보호위원회/법원/검찰 자동 제출
- 사람 승인 없는 자동 신고
- 법률 결론 자동 확정

### 2.3 공격 기능 금지
다음은 비범위이며 구현 금지다.

- 포트스캔/취약점 스캔
- 익스플로잇
- 계정 탈취
- 강제 차단/보복 로직
- IP 추적을 빙자한 위치추적/디바이스 해킹

## 3. 기술 원칙

### 3.1 아키텍처
기본 아키텍처는 다음을 따른다.

- Frontend: React + TypeScript
- API: FastAPI
- DB: PostgreSQL
- Search: OpenSearch
- Evidence Vault: MinIO
- Background jobs: Redis 기반 큐(후속 단계)

### 3.2 구현 순서
반드시 아래 순서로 구현한다.

#### Phase 1
- 프로젝트 스캐폴딩
- 인증/권한 기본틀
- 소스 커넥터 인터페이스
- Canonical Event 모델
- 사건/증거/감사로그 DB
- 검색/상관분석 기본 API
- 사건 생성/조회/증거 freeze API
- 기본 UI(사건 목록, 사건 상세, 타임라인)

#### Phase 2
- 귀속 엔진
- DHCP/VPN/AD/EDR/CMDB 매핑
- 신뢰도 등급(A/B/C/D)
- 문서 생성(사건요약서, 증거목록, 고소장 초안)
- 승인 워크플로우

#### Phase 3
- 규칙 엔진
- 자동 알림/자동 사건 생성
- 신고·통지 준비 체크리스트
- 운영 대시보드
- 성능/보안/감사 강화

## 4. 코딩 스타일

### 4.1 Backend
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic 사용
- 타입힌트 필수
- 함수는 작고 테스트 가능하게 유지
- 비즈니스 로직은 `services/` 또는 `domain/`에 둔다
- API 라우터에서 복잡한 로직을 직접 처리하지 않는다

### 4.2 Frontend
- TypeScript strict mode
- 컴포넌트는 container/presentational 분리
- API 타입은 OpenAPI 기반으로 생성 가능하게 유지
- 민감정보는 기본 마스킹 표시
- 사건 상세 화면에서 증거 원문 접근은 권한 확인 후 허용

### 4.3 공통
- 모든 변경은 감사로그 대상이 되도록 고려
- 시간은 DB에 UTC로 저장하고 UI에서 KST 병기
- 이벤트 원문(raw)은 절대 수정하지 않는다
- 문서 생성 결과물은 원본 입력(JSON snapshot)과 함께 저장

## 5. 데이터 모델 규칙

### 5.1 Canonical Event 필수 필드
최소 다음 필드는 모든 정규화 이벤트에 매핑한다.

- `event_time`
- `source_type`
- `event_type`
- `src_ip`
- `dst_ip`
- `hostname`
- `username`
- `session_id`
- `request_host`
- `request_path`
- `status_code`
- `bytes_sent`
- `raw_artifact_id`

### 5.2 Attribution 규칙
내부 귀속은 최소 두 개 이상의 독립 증거가 일치해야 상위 등급을 부여한다.

예시:
- A: DHCP + EDR + AD 로그인 + 자산관리 일치
- B: VPN 계정 + 디바이스 인증서 + EDR 일치
- C: 공용PC 또는 NAT 뒤 다중 후보
- D: 외부 공인 IP만 존재

실명 자동 기입은 A/B 등급만 허용한다.

## 6. 문서 생성 규칙

문서 생성은 템플릿 기반으로만 구현한다.

- 자유 생성형 LLM 출력에 의존하지 않는다.
- 구조화 데이터(JSON snapshot) -> 템플릿 렌더링 방식 사용
- 문서에는 반드시 `귀속 신뢰도`, `검토 필요`, `자동생성 일시`를 표기한다.
- 고소장 초안은 승인 전까지 워터마크 또는 상태 필드(`DRAFT`)를 유지한다.

## 7. 보안 규칙

- 원본 로그는 MinIO Object Lock 또는 불변 보관을 전제로 설계
- SHA-256 해시 저장
- 내보내기(export) 시점에도 별도 해시 기록
- 문서/증거 열람도 감사로그에 남김
- PII 최소수집 원칙 준수
- 역할 기반 접근통제(RBAC) 기본 제공

## 8. 테스트 규칙

최소 다음 테스트를 작성한다.

- 정규화 파서 단위 테스트
- 귀속 엔진 점수화 테스트
- 사건 생성/증거 freeze API 통합 테스트
- 문서 생성 스냅샷 테스트
- 권한 테스트
- 감사로그 생성 테스트

## 9. 작업 산출물 형식

새 기능을 추가할 때마다 아래를 같이 갱신한다.

- 관련 API 스펙
- DB 마이그레이션
- 테스트
- 문서(`docs/`)
- 필요한 경우 샘플 이벤트 payload

## 9.1 커밋 원칙

- 작업은 의미 있는 단위로 잘게 나눠 진행한다.
- 각 작업 단위는 가능하면 코드, 테스트, 문서까지 한 번에 맞춘 뒤 커밋한다.
- 하나의 커밋에 서로 다른 관심사의 큰 변경을 섞지 않는다.
- 세션 종료 전에는 진행된 작업을 논리적인 커밋들로 정리한다.

## 10. 구현 중 의사결정 원칙

모호하면 아래 우선순위를 따른다.

1. `PRD.md`
2. `docs/security-and-compliance.md`
3. `docs/architecture.md`
4. `docs/data-model.md`
5. `docs/api-spec.md`

충돌 시 더 보수적이고 법적/감사적으로 안전한 방향을 선택한다.

## 11. 첫 번째 작업 지시

처음 작업할 때는 다음만 수행한다.

1. FastAPI 프로젝트 생성
2. PostgreSQL 연결
3. `schema.sql` 기준 Alembic 초기 마이그레이션 생성
4. `GET /healthz`
5. `POST /v1/events:ingest`
6. `POST /v1/cases`
7. `GET /v1/cases/{caseId}`
8. `POST /v1/cases/{caseId}/freeze`
9. pytest 기반 기본 테스트
10. Docker Compose로 로컬 실행 가능 상태 만들기

이 단계에서는 문서 생성과 OpenSearch 고도화는 후순위로 둔다.
