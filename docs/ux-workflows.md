# UX & Workflows

## 1. 화면 목록

1. 로그인 / SSO 진입
2. 대시보드
3. 사건 목록
4. 사건 상세
5. 검색/상관분석 패널
6. IP 상세
7. 자산 상세
8. 사용자 상세
9. 증거 금고
10. 문서 생성/검토
11. 운영관리

## 2. 사건 목록 화면

### 목적
- 진행 중 사건을 빠르게 훑고 우선순위를 정함

### 필수 컬럼
- 사건번호
- 제목
- 상태
- 중요도
- 관측 IP
- 내부/외부
- 귀속 등급
- 담당자
- 생성시각
- 최근 업데이트

### 필터
- 상태
- 중요도
- 내부/외부
- 귀속 등급
- 기간
- 태그
- 담당자

## 3. 사건 상세 화면

### Header
- 사건번호
- 제목
- 상태 변경 드롭다운
- 중요도
- 담당자
- 태그
- freeze 버튼
- 문서 생성 버튼

### Summary Card
- 핵심 사실 5줄
- 관련 도메인
- 관련 사용자/자산
- 피해 추정
- 다음 권장 조치

### Attribution Card
- 관측 IP
- 내부/외부
- 귀속 등급
- 후보 사용자/자산
- 신뢰도 점수
- 근거 증거 수
- 불확실성 이유

### Timeline Tab
- 시간순 이벤트
- source icon
- event type
- request path / auth / data access 요약
- raw link

### Evidence Tab
- freeze 상태
- 증거 개수
- 해시
- export manifest
- 열람/다운로드 기록

### Documents Tab
- 문서 종류
- 버전
- 상태(DRAFT/APPROVED)
- 생성 시각
- 검토자
- 다운로드

### Audit Tab
- 누가 무엇을 했는지
- 사건 수정/열람/export/승인 기록

## 4. 검색/상관분석 패널

### 입력
- query type: IP / username / hostname / session / domain
- value
- time range
- optional filters

### 출력
- 관련 이벤트 수
- 관련 사건 수
- 후보 자산
- 후보 사용자
- attribution preview
- 추천 액션: `사건 생성`, `기존 사건에 추가`

## 5. 문서 생성 플로우

1. 조사자가 사건에서 문서 생성 클릭
2. 문서 종류 선택
3. 시스템이 snapshot 검증
4. DRAFT 생성
5. 법무/개인정보 담당 검토
6. 승인 시 APPROVED
7. export 가능

## 6. 외부 사건 표시 규칙

외부 사건 화면은 다음 표시를 강제한다.

- Actor label: `성명불상`
- Badge: `외부 공인IP`
- Note: `통신사/플랫폼/수사기관 조회 필요`

## 7. 마스킹 규칙

- 이메일: 기본 일부 마스킹
- 전화번호: 마지막 2~4자리 제외 마스킹
- 주민번호/고유식별정보: 전체 마스킹 또는 미표시
- raw payload 내 민감값은 toggle + 권한 체크
