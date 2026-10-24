# Spec ↔ Roadmap ↔ Implementation-Plan Cross-Check

Scope: all `specification/word/*.docx` (read via subagents; key facts re-verified directly in 04.08 and in the converted dumps), `roadmap/*.md`, and the nine `*-implementation-plan.md` files.

## 1. Verdict

| Layer | Verdict |
|---|---|
| `roadmap/` (phases 0–7, tracker, architecture) | Consistent with the specs on every point checked. Used as the source of truth. |
| `*-implementation-plan.md` (as originally written) | Contradicted the Roadmap and specs. Replaced by the rewrite that accompanies this file. |
| Readiness | Phase 0 could start immediately. Phases 1–7 must use the rewritten plans. |

## 2. Roadmap ↔ spec facts that were verified

| Item | Verified value | Source |
|---|---|---|
| Task states | `QUEUED, RUNNING, WAITING_FOR_APPROVAL, INTERRUPTED` (active); `SUCCEEDED, FAILED, CANCELLED` (terminal). `PARTIALLY_SUCCEEDED` must not be added. | 04.08.06, 03.29 |
| Step states | `PENDING, READY, WAITING_FOR_APPROVAL, DISPATCHED, RUNNING, SUCCEEDED, FAILED, REJECTED, UNCERTAIN, CANCELLED`. `UNCERTAIN` is a step state, not a task state. | 04.08.06, 03.29 |
| Planner outcomes | `PROPOSED, CLARIFICATION_REQUIRED, UNSUPPORTED` | 04.08.07 |
| Bridge response statuses | `SUCCEEDED, FAILED, REJECTED, RUNNING, UNCERTAIN` | 04.08.08 |
| Bridge request envelope | `protocol_version, operation_id, attempt_id, task_id, step_id, target_device_id, tool_name, tool_schema_version, arguments, deadline` | 04.08.08 |
| Error catalogue (15 codes) | `INVALID_ARGUMENT, AUTHENTICATION_REQUIRED, ACCESS_DENIED, POLICY_DENIED, APPROVAL_REQUIRED, APPROVAL_EXPIRED, DEVICE_UNAVAILABLE, DEPENDENCY_UNAVAILABLE, CONTRACT_VERSION_UNSUPPORTED, OPERATION_TIMEOUT, OPERATION_OUTCOME_UNCERTAIN, FILE_NOT_FOUND, FILE_ALREADY_EXISTS, FILESYSTEM_SCOPE_DENIED, INTERNAL_ERROR` | 04.08.09 |
| API route prefix | `/v1` (no document uses `/api/v1`) | 03.16, 03.9 |
| Folder layout | `apps/{api,cli,windows_bridge}`, `nexus_core/{domain,services,execution,tools,ai,memory,security,infrastructure/{database,model_adapters,bridge_transport},observability}`, `contracts/{api,bridge,tools,events}`, `tests/{unit,integration,contract,security,reliability,end_to_end}`, `deploy/config`, `docs/{architecture,decisions,testing,operations}`, `migrations`, `scripts` | 04.04.02 |
| Decision ID ranges | P0 D-01–08 · P1 D-09–22 · P2 D-23–39 · P3 D-40–55 · P4 D-56–70 · P5 D-71–84 · P6 D-85–94 · P7 D-95–104 | `roadmap/tracker.md` §3 |

## 3. Defects found in the original implementation plans

1. Decision IDs did not match the tracker (e.g. D-23 "CLI library"; real D-23 is status casing, CLI framework is D-34).
2. Task states invented (`AWAITING_APPROVAL`, `COMPLETED`, `UNCERTAIN` as a task state).
3. `/api/v1` used instead of `/v1`.
4. CLI commands invented (`nexus auth login`, `nexus task submit`); documented set is `login/logout/devices/run/task/history/approvals/approve/reject/memory/diagnostics/data export`.
5. `--json` used; documented flag is `--output json` (D-75, still open).
6. Open decisions treated as settled (bridge SQLite as "D-25"; cryptographic approval tokens). Real position: journal storage is provisional (D-29, D-47, D-94); approvals bind to an operation fingerprint (D-50).
7. SSE planned in Phase 5; docs say polling first, SSE only if a need is measured (D-76).
8. Folder layout added `nexus_core/data`, `nexus_core/policy`, `nexus_core/logging`, `tests/e2e`; agreed layout is in §2.
9. Tracker section references wrong (e.g. §2c vs §2d, §2f vs §2g).
10. Entire Roadmap steps omitted (GitHub repo, WSL 2, hardware inventory, LAN test, claim/lease/fencing, dispatch pipeline, fault injection, 10-layer plan validation, replanning, TLS, backend-restart test, 12-item security matrix, sign-off checklists, and others).

## 4. Open items that remain open (do not settle in code without an ADR)

| Item | Where tracked |
|---|---|
| Task-status casing on the wire (`queued` vs `QUEUED`) | D-23 |
| Bridge envelope field names across 03.12 / 03.30 / 04.08 | D-24 |
| Error-code reconciliation with 03.32 filesystem codes | D-25 |
| Token format for CLI sessions | D-14 |
| Risk-tier naming (Tiers 0–3 in 03.11/ADR-011 vs five tiers in Product Vision 1.4) | decide in P3 Step 10 / ADR |
| Lease, heartbeat, poll, timeout numbers | D-28, D-32, D-33 |
| Journal storage | D-29 → D-47 → D-94 |
| Specs location in repo | D-07 |

## 5. Roadmap issues to fix or watch

| # | Issue | Action |
|---|---|---|
| R1 | `phase-0-foundation.md` and `00-phase-plan.md` say 66 documents; `specification/word/` contains 65 `.docx` files. | Identify the missing document, or correct the count. |
| R2 | Phase 1 Step 8 says the docs' per-code owner / terminal / retry / recovery cells were not extracted. | Fill from 04.08.09 table 5 when drafting the catalogue. |
| R3 | Phase 1 D-21 says CI table 04.04.05 was not read. | Read 04.04.05 (9-row CI table) at Step 23. |
| R4 | Phase 5 Step 8 and tracker P5-08 mention `PARTIAL_SUCCESS` while the state machine forbids a partial task state. | Treat it as a CLI result-presentation category derived from step outcomes, not a task state. Record in the P5 ADR. |
| R5 | Tracker has blank team names and start date. | Fill in P0 Step 0. |
| R6 | Phase 4 `--steps` display list omits `WAITING_FOR_APPROVAL`, `REJECTED`, `CANCELLED` step states. | Use the full 10-state list from 04.08.06. |
| R7 | Cancel command name differs. Specs (03.16) use `nexus task <id> --cancel`; Roadmap Phase 2 Step 26 and tracker P2-26 use `nexus cancel <id>`. | Team confirms one name in Phase 2 Step 26. Record in D-35. |
