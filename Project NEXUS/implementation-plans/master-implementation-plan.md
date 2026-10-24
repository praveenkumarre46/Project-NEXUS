# Project NEXUS — Master Implementation Plan

## Executive Summary

Project NEXUS is a 3-developer, local-first AI companion: a FastAPI and PostgreSQL backend, a terminal CLI and a native Windows bridge, targeting WSL 2 and native Windows. The timeline is 12 weeks, split into Phases 0–7 with Gates 1–6. This Master Implementation Plan indexes the eight phase plans from the environment foundation to the release candidate.

Each phase plan lists sub-tasks with Intent, Expected Outcomes, Todo List, Relevant Context and Status. Plans contain no code-level detail.

## Source-of-Truth Rule

- [`roadmap/phase-N-*.md`](../roadmap/00-phase-plan.md) and [`roadmap/tracker.md`](../roadmap/tracker.md) govern the work. The specifications in `specification/` back them up.
- Every `phase-N-implementation-plan.md` follows the Roadmap steps and the tracker IDs (`P0-00` … `P7-21`). Where a plan and the Roadmap disagree, the Roadmap wins unless the Roadmap itself is wrong against the specs. Such cases are recorded in [`reports/spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md) (items R1–R7) and need a team decision.
- Owners are assigned by the team. The rotation in `roadmap/00-phase-plan.md` is a suggestion only.

---

## Phase Implementation Plan Index

The Gate column uses the project gates from `roadmap/00-phase-plan.md` and tracker §5. The CI pipeline also has five gates labelled A–E (Phase 7). Always write "Gate 6" or "CI Gate A" to avoid confusion.

| Phase | Title | Week(s) | Gate | Decision IDs | Tracker rows | Plan File | Status |
|---|---|---|---|---|---|---|---|
| **Phase 0** | Foundation & Environment | 1 | none (Week 1 checklist) | D-01–D-08 | P0-00 … P0-16c | [`phase-0-implementation-plan.md`](phase-0-implementation-plan.md) | `[ ] pending` |
| **Phase 1** | Contracts & Persistence | 2 | **Gate 1** (contracts agreed) | D-09–D-22 | P1-00 … P1-26 | [`phase-1-implementation-plan.md`](phase-1-implementation-plan.md) | `[ ] pending` |
| **Phase 2** | First Vertical Slice | 3–4 | **Gate 2** (first vertical slice works) | D-23–D-39 | P2-00 … P2-31 | [`phase-2-implementation-plan.md`](phase-2-implementation-plan.md) | `[ ] pending` |
| **Phase 3** | Safe Side Effects | 5–6 | **Gate 3** (safe side effects) | D-40–D-55 | P3-00 … P3-27 | [`phase-3-implementation-plan.md`](phase-3-implementation-plan.md) | `[ ] pending` |
| **Phase 4** | Local AI & Memory | 7–8 | **Gate 4** (AI and memory integrated; fallback clause allowed) | D-56–D-70 | P4-00 … P4-25 | [`phase-4-implementation-plan.md`](phase-4-implementation-plan.md) | `[ ] pending` |
| **Phase 5** | User-Facing Workflows | 9 | none; feeds Gate 5 | D-71–D-84 | P5-00 … P5-21 | [`phase-5-implementation-plan.md`](phase-5-implementation-plan.md) | `[ ] pending` |
| **Phase 6** | Team Integration | 10 | **Gate 5** (team integration) | D-85–D-94 | P6-00 … P6-19 | [`phase-6-implementation-plan.md`](phase-6-implementation-plan.md) | `[ ] pending` |
| **Phase 7** | Hardening & Release Candidate | 11–12 | **Gate 6** (release candidate) | D-95–D-104 | P7-00 … P7-21 | [`phase-7-implementation-plan.md`](phase-7-implementation-plan.md) | `[ ] pending` |

---

## Execution Dependency Map

```
Phase 0  Foundation, repo tooling, hardware facts
  │
  ▼
Phase 1  Frozen contracts + DB persistence + auth skeleton ──► Gate 1
  │
  ▼
Phase 2  CLI → backend → bridge: scoped file search ──► Gate 2
  │
  ▼
Phase 3  Policy, approvals, create_file, launch_application, journal ──► Gate 3
  │
  ▼
Phase 4  Local model runtime, validated plans, memory ──► Gate 4
  │
  ▼
Phase 5  History, results, artifacts, read_document, JSON output  (no gate; feeds Gate 5)
  │
  ▼
Phase 6  Three users / three devices, isolation, concurrency ──► Gate 5
  │
  ▼
Phase 7  Workflows A–F, security matrix, backup, CI/CD, sign-off ──► Gate 6
```

---

## Implementation Rules & Invariants

1. **Independent sub-task execution**: every sub-task is executable, testable and verifiable on its own.
2. **Evidence-driven advancement**: a phase or gate is complete only when repeatable tests pass and evidence is logged in [`roadmap/tracker.md`](../roadmap/tracker.md). A demonstration without repeatable tests does not count (04.28.05).
3. **No breaking phase boundaries**: features from a later phase (for example live AI in Phase 2, or multi-user sharing in Phase 3) are not introduced early. Each plan lists what is excluded.
4. **ADR record keeping**: decisions D-01 to D-104 each get an ADR in `docs/decisions/` with an honest status (Open, Provisional, Confirmed or Blocked). Open items are not settled without an ADR. Items that stay Open at the time they are needed are listed in the phase's evidence report.
5. **Deterministic fallbacks**: deterministic planning and execution stay functional when AI inference or remote bridges are unavailable.
6. **State and contract vocabulary is fixed by the specs**:
   - Task states: `QUEUED, RUNNING, WAITING_FOR_APPROVAL, INTERRUPTED` (active) and `SUCCEEDED, FAILED, CANCELLED` (terminal). `PARTIALLY_SUCCEEDED` is never added; `PARTIAL_SUCCESS` is a result classification only.
   - Step states: `PENDING, READY, WAITING_FOR_APPROVAL, DISPATCHED, RUNNING, SUCCEEDED, FAILED, REJECTED, UNCERTAIN, CANCELLED`. `UNCERTAIN` is a step state, not a task state.
   - Routes use the `/v1` prefix. The end-to-end test folder is `tests/end_to_end/`. The repository layout follows 04.04.02.
   - The error catalogue is the 15-code list in 04.08.09. New codes enter through the contract change process.
7. **Open items that need a team decision before they block work** (see `reports/spec-crosscheck-findings.md`):
   - D-23 wire casing of task states, D-24 bridge envelope field names (`schema_version` in 03.12 vs `tool_schema_version` and `attempt_id` in 04.08 and 03.30), D-25 error-code reconciliation with the 03.32 filesystem codes.
   - D-14 token format, D-75 `--output json`, D-76 polling vs SSE, D-29 → D-47 → D-94 bridge journal storage, D-07 where the specs live in the repository.
   - Risk-tier naming: Tiers 0–3 (03.11, ADR-011) vs five tiers (Product Vision 1.4).
   - R1: the Roadmap says 66 documents, 65 are present. R7: cancel command naming (`nexus task <id> --cancel` in 03.16 vs `nexus cancel <id>` in the Roadmap).
