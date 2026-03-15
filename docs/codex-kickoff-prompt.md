# Codex Kickoff Prompt

아래 프롬프트를 그대로 복사해서 코딩 에이전트에 전달하면 된다.

---

You are implementing this repository from the planning package.

Read these files in order before editing anything:

1. `AGENTS.md`
2. `PRD.md`
3. `docs/architecture.md`
4. `docs/data-model.md`
5. `docs/api-spec.md`
6. `docs/security-and-compliance.md`
7. `docs/implementation-plan.md`
8. `docs/backlog.md`

Your task for the first pass:

1. Create a monorepo scaffold with:
   - `apps/api`
   - `apps/web`
   - `packages/contracts`
   - `infra`
2. In `apps/api`, implement:
   - FastAPI app
   - config/settings
   - SQLAlchemy models for the core tables in `docs/schema.sql`
   - Alembic initial migration
   - endpoints:
     - `GET /healthz`
     - `POST /v1/events:ingest`
     - `POST /v1/cases`
     - `GET /v1/cases/{caseId}`
     - `POST /v1/cases/{caseId}/freeze`
3. Add pytest tests for the above endpoints and one service-level test for SHA-256 manifest generation.
4. In `infra`, create `docker-compose.yml` for:
   - postgres
   - opensearch
   - minio
   - redis
   - api
   - web
5. Do not implement any feature that:
   - deanonymizes external public IP users
   - auto-files complaints/reports
   - performs offensive security actions
6. Keep the implementation minimal but runnable.
7. Update documentation if file paths or implementation details differ from the plan.

Output expectations:
- a clear file tree
- commands to run locally
- what is implemented vs stubbed
- any assumptions you made

Important domain rules:
- external public IP actors must remain `EXTERNAL_UNKNOWN` / `성명불상`
- only internal A/B grade attribution may auto-populate a real internal user in drafts
- all generated documents must remain draft/review-gated
- all evidence actions must be auditable

---
