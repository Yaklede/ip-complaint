# API Specification (Human-Readable)

기계 판독 가능한 스펙은 `docs/openapi.yaml`을 참고한다.

## 1. 인증/권한

- 권장: OIDC Bearer Token
- 최소 역할:
  - `investigator`
  - `lead`
  - `legal_reviewer`
  - `privacy_reviewer`
  - `admin`
  - `auditor`

민감 엔드포인트는 역할 제한을 둔다.

## 2. 주요 엔드포인트

### 2.1 Health
- `GET /healthz`
- 목적: 서비스 생존/의존성 확인
- 현재 구현:
  - `status`, `service`, `version`, `dependencies` 반환
  - DB readiness는 실제 질의로 확인
  - OpenSearch/MinIO/Redis는 TCP 기반 best-effort readiness 확인

### 2.2 Event Ingest
- `POST /v1/events:ingest`
- 목적: raw artifact 등록 및 정규화 이벤트 적재
- 입력:
  - source_name
  - source_type
  - collected_at
  - payload 또는 object reference
- 출력:
  - raw_artifact_id
  - normalized_event_count
  - checksum_sha256
  - event_ids

### 2.3 Search Correlation
- `POST /v1/search/correlate`
- 목적: IP/계정/호스트/세션 기준 상관분석
- 입력:
  - query_type (`ip`, `username`, `hostname`, `session`, `domain`)
  - query_value
  - time_from
  - time_to
- 출력:
  - related_events
  - related_cases
  - candidate_assets
  - candidate_users
  - attribution_preview
- 현재 구현:
  - `ip`, `username`, `hostname`, `session`, `domain` 질의를 지원
  - DB 기준으로 관련 이벤트/사건과 candidate asset/user summary를 반환
  - 외부 공인 IP 질의는 항상 `EXTERNAL_UNKNOWN` / `성명불상` / `D` 등급으로 유지
  - 내부 후보가 단일 사용자로 수렴한 경우에만 보수적 preview(`C`)를 반환

### 2.4 Create Case
- `POST /v1/cases`
- 목적: 사건 생성
- 입력:
  - title
  - summary
  - primary_ip
  - event_ids 또는 seed_event_ids
  - notes
  - severity
- 출력:
  - case_id
  - case_no
  - status

### 2.5 Get Case
- `GET /v1/cases/{caseId}`
- 목적: 사건 상세 조회
- 출력:
  - case summary
  - related events summary
  - timeline
  - attribution links
  - evidence list
  - documents
- 현재 구현 메모:
  - 외부 공인 IP 사건은 `displayName=성명불상`, `confidenceGrade=D`, `nextStep=통신사/플랫폼/수사기관 조회 필요`

### 2.6 Update Case
- `PATCH /v1/cases/{caseId}`
- 목적: 상태/담당자/심각도/태그 갱신
- 현재 구현:
  - `title`, `summary`, `status`, `severity`, `assignee` 수정 가능
  - 변경 전/후 상태를 audit log에 기록

### 2.7 Freeze Evidence
- `POST /v1/cases/{caseId}/freeze`
- 목적: 관련 증거 고정 및 manifest 생성
- 출력:
  - bundle_id
  - frozen_evidence_count
  - manifest_checksum
  - status
- 현재 구현:
  - linked event/raw artifact reference를 snapshot하여 manifest JSON 생성
  - SHA-256 checksum 계산 후 `documents`에 `evidence_manifest` / `DRAFT`로 기록
  - audit log append 수행

### 2.8 Generate Document
- `POST /v1/cases/{caseId}/documents`
- 목적: 사건요약/증거목록/고소장 초안 생성
- 입력:
  - doc_type (`case_summary`, `evidence_manifest`, `complaint_draft`)
  - template_version
- 출력:
  - document_id
  - status
  - checksum_sha256

### 2.9 Review Document
- `POST /v1/documents/{documentId}/review`
- 목적: 승인/반려/수정요청
- 입력:
  - action (`approve`, `reject`, `request_changes`)
  - comment

### 2.10 Alerts
- `GET /v1/alerts`
- `POST /v1/alerts/{alertId}/promote`

### 2.11 Prepare Export Bundle
- `POST /v1/cases/{caseId}/export`
- 목적: freeze된 증거 기준으로 draft export bundle을 생성
- 출력:
  - bundle_id
  - exported_evidence_count
  - manifest_checksum
  - status
- 현재 구현:
  - 실제 ZIP이나 최종 법률 문서는 생성하지 않음
  - input snapshot, evidence/document references, package plan을 포함한 `DRAFT` JSON bundle을 저장
  - 생성된 bundle storage URI와 checksum을 `documents`에 기록
  - 포함된 evidence는 `EXPORTED` / `exported_at` 상태로 갱신
  - freeze 이전 사건에는 `409 CASE_NOT_FROZEN` 반환
  - audit log append 수행

## 3. 에러 모델

모든 에러는 아래 구조를 따른다.

```json
{
  "error": {
    "code": "CASE_NOT_FOUND",
    "message": "Case not found",
    "details": {}
  }
}
```

## 4. 권한 모델 예시

| Endpoint | Investigator | Lead | Legal | Privacy | Admin | Auditor |
|---|---|---:|---:|---:|---:|---:|
| Search correlate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create case | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Freeze evidence | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Generate documents | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Approve complaint draft | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Source management | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

## 5. API 설계 원칙

- ID는 UUID 사용
- 시간은 RFC3339 UTC
- 긴 작업은 job resource로 비동기화 가능
- 문서 생성/증거 export는 추후 job queue 기반으로 확장 가능
- ingest는 idempotency key 지원 권장
- 검색은 pagination + filter + sort 지원

## 6. 향후 확장 엔드포인트

- `POST /v1/rules`
- `PATCH /v1/rules/{ruleId}`
- `GET /v1/assets/{assetId}`
- `GET /v1/users/{userId}`
- `POST /v1/cases/{caseId}/export`
- `GET /v1/audit-logs`
