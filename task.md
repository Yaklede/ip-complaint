## Task Tracker

### Context
- Date: 2026-03-16
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
- Completed: Split work into logical commits and updated repo guidance.
- Current batch:
  1. raw artifact storage abstraction
  2. parser registry abstraction
  3. ingest path verification
- Completed current batch:
  - raw artifact storage backends added (`filesystem`, optional `minio`)
  - parser registry added with `nginx`, `waf`, `vpn` parser slots
  - ingest path now writes immutable-style raw artifact content and stores storage metadata
  - verified `pytest apps/api/tests` after ingest changes

### Remaining Work
- [ ] Wire real Postgres/OpenSearch/MinIO persistence paths instead of metadata/readiness-only integration.
- [ ] Add missing case update flow and richer case management UI/actions.
- [ ] Add correlate/search APIs and candidate asset/user cards.
- [ ] Add evidence list UI details, export metadata flow, and export packaging.
- [ ] Implement attribution engine inputs and A/B/C/D scoring rules.
- [ ] Implement document generation templates, review API, and document list/download UI.
- [ ] Add masking utilities, approval workflow, retention settings, and admin surfaces.
- [ ] Add alerts/rules/dashboard work after the above.

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
  - Implement case update flow in API first, then expose minimal UI actions.
