## Task Tracker

### Context
- Date: 2026-03-15
- Workspace: `/Users/jimin/Desktop/study/ip-complaint`
- Repo note: `AGENTS.md` is now present and is the active instruction file.

### Source Of Truth Read
1. `AGENTS.md`
2. `README.md`
3. `PRD.md`
4. `docs/architecture.md`
5. `docs/data-model.md`
6. `docs/api-spec.md`
7. `docs/security-and-compliance.md`
8. `docs/implementation-plan.md`
9. `docs/backlog.md`
10. `docs/openapi.yaml`
11. `docs/schema.sql`

### Guardrails To Preserve
- Never identify or guess the real-world identity of an external public IP user.
- External public IP actors must remain `EXTERNAL_UNKNOWN` / `성명불상` / grade `D`.
- Do not implement automatic complaint/report filing.
- Do not implement offensive, scanning, exploitation, forced blocking, or counter-hacking features.
- Keep generated legal/report documents in `DRAFT` or review-gated state.
- Every evidence action must be auditable.
- Split work into small logical units and make commits per completed unit.

### Current Status
- Completed: Read required documents and extracted scope.
- Completed: Confirmed repository is scaffold-only and requires full Phase 1 foundation setup.
- Completed: Created initial monorepo directory scaffold.
- Completed: Added backend app skeleton, models, services, routers, and Alembic initial migration.
- Completed: Added frontend shell, shared contracts, env examples, and local runtime wiring.
- Completed: Verified `pytest apps/api/tests` (8 passed).
- Completed: Verified `npm run build --workspace @incident-attribution/web`.
- In progress: Split current work into logical commits and finalize status docs.

### Remaining Work
- [x] Inspect existing `infra/docker-compose.yml` and repository constraints.
- [x] Create monorepo scaffold: `apps/api`, `apps/web`, `packages/contracts`, `infra`.
- [x] Implement FastAPI app bootstrap, config, db session, models, migration, services, and endpoints.
- [x] Implement minimal React + TypeScript web shell.
- [x] Implement shared contracts package.
- [x] Update docker compose for local dependencies and app services.
- [x] Add pytest coverage for required endpoints/services/guardrails.
- [x] Update documentation and README with run/test/env/limitations.
- [ ] Commit completed work in logical units.

### Compact Resume Notes
- Re-read before resuming if context is compacted:
  - `task.md`
  - `AGENTS.md`
  - `PRD.md`
  - `docs/architecture.md`
  - `docs/data-model.md`
  - `docs/api-spec.md`
  - `docs/security-and-compliance.md`
  - `docs/openapi.yaml`
  - `docs/schema.sql`
- Immediate next step:
  - Update backlog/tracker status one more time and create logical git commits.
