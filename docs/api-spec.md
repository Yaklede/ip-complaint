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

### 2.4 Create Case
- `POST /v1/cases`
- 목적: 사건 생성
- 입력:
  - title
  - primary_ip
  - seed_event_ids
  - notes
- 출력:
  - case_id
  - case_no
  - status

### 2.5 Get Case
- `GET /v1/cases/{caseId}`
- 목적: 사건 상세 조회
- 출력:
  - case summary
  - timeline
  - attribution links
  - evidence list
  - documents
  - audit summary

### 2.6 Update Case
- `PATCH /v1/cases/{caseId}`
- 목적: 상태/담당자/심각도/태그 갱신

### 2.7 Freeze Evidence
- `POST /v1/cases/{caseId}/freeze`
- 목적: 관련 증거 고정 및 manifest 생성
- 출력:
  - bundle_id
  - frozen_evidence_count
  - manifest_checksum

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
