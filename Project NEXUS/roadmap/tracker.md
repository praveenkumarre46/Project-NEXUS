# NEXUS — Project Tracker

> **How to use:** edit this file in pull requests. Change `[ ]` to `[x]` only when the **Evidence** exists (a merged PR, a committed file or a recorded result). A box ticked without evidence does not count (docs, 04.28.05: a gate "must not be marked complete based on a demonstration that lacks repeatable tests").
> Status values: `[ ]` not started · `[~]` in progress · `[x]` done with evidence · `[!]` blocked.
> Parent: [`00-phase-plan.md`](00-phase-plan.md) · Detail: [`phase-0-foundation.md`](phase-0-foundation.md) · Diagrams: [`architecture.md`](architecture.md)

## 1. Dashboard

| Phase | Weeks | Goal | Gate | Detailed roadmap | Status |
|---|---|---|---|---|---|
| P0 | 1 | Foundation and environment | none | [written](phase-0-foundation.md) | `[ ]` |
| P1 | 2 | Contracts and persistence | Gate 1 | [written](phase-1-contracts-persistence.md) | `[ ]` |
| P2 | 3–4 | First vertical slice | Gate 2 | [written](phase-2-first-vertical-slice.md) | `[ ]` |
| P3 | 5–6 | Safe side effects | Gate 3 | [written](phase-3-safe-side-effects.md) | `[ ]` |
| P4 | 7–8 | Local AI and memory | Gate 4 | [written](phase-4-local-ai-and-memory.md) | `[ ]` |
| P5 | 9 | User-facing workflows | none | [written](phase-5-user-facing-workflows.md) | `[ ]` |
| P6 | 10 | Team integration | Gate 5 | [written](phase-6-team-integration.md) | `[ ]` |
| P7 | 11–12 | Hardening and release candidate | Gate 6 | [written](phase-7-hardening-and-release.md) | `[ ]` |

**Team:** Dev A = ______ · Dev B = ______ · Dev C = ______ (fill in) · **Start date:** ______ (fill in)

---

## 2. Phase 0 — Foundation and environment

Primary owners this phase: **BE = Dev A · WB = Dev B · AI = Dev C**. Detail for every step: [`phase-0-foundation.md`](phase-0-foundation.md).

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P0-00 | Team facts, accounts, designated host chosen | All | `[ ]` | | |
| P0-01a | Git/GitHub learning + practice PR — Dev A | A | `[ ]` | | |
| P0-01b | Git/GitHub learning + practice PR — Dev B | B | `[ ]` | | |
| P0-01c | Git/GitHub learning + practice PR — Dev C | C | `[ ]` | | |
| P0-02 | Private GitHub repo created, collaborators added | A | `[ ]` | | |
| P0-02b | Branch-protection capability on free plan checked and recorded | A | `[ ]` | | Docs want 1 reviewer + checks passing |
| P0-03 | Repository skeleton merged (folders + READMEs, no Python modules) | A | `[ ]` | | |
| P0-03b | Dependency-direction rules written | A | `[ ]` | | |
| P0-04 | CONTRIBUTING.md + PR template merged | A | `[ ]` | | |
| P0-04b | Daily-sync questions + rotation rules agreed | All | `[ ]` | | |
| P0-05 | Coding standards doc + tools chosen (D-04) | All | `[ ]` | | |
| P0-06a | WSL 2 + Ubuntu working — Dev A | A | `[ ]` | | |
| P0-06b | WSL 2 + Ubuntu working — Dev B | B | `[ ]` | | |
| P0-06c | WSL 2 + Ubuntu working — Dev C | C | `[ ]` | | |
| P0-06d | WSL resource limits (`.wslconfig`) checked and recorded, per developer | All | `[ ]` | | |
| P0-07a | Python venv + pinned dev deps + green checks — Dev A | A | `[ ]` | | |
| P0-07b | Same — Dev B | B | `[ ]` | | |
| P0-07c | Same — Dev C | C | `[ ]` | | |
| P0-07d | Python version + dependency approach decided (D-01, D-02) | A | `[ ]` | | |
| P0-07e | Version matrix started | A | `[ ]` | | |
| P0-08a | PostgreSQL running, dev + test DBs, separate credentials — Dev A | A | `[ ]` | | |
| P0-08b | Same — Dev B | B | `[ ]` | | |
| P0-08c | Same — Dev C | C | `[ ]` | | |
| P0-08d | Native vs Compose decided (D-03) | A | `[ ]` | | |
| P0-08e | PostgreSQL confirmed not reachable from another PC | A+B | `[ ]` | | |
| P0-09 | `.gitignore`, `.env.example`, configuration reference started | A | `[ ]` | | |
| P0-09b | Confirmed no secrets in git history | All | `[ ]` | | |
| P0-10a | Hardware inventory (Windows PowerShell) of designated host | C | `[ ]` | | |
| P0-10b | Exact GPU model + dedicated VRAM confirmed (not from AdapterRAM) | C | `[ ]` | | |
| P0-10c | Baseline 1 (idle) recorded | C | `[ ]` | | |
| P0-10d | Baseline 2 (PostgreSQL running) recorded; full backend baseline carried to P2 | C | `[ ]` | | |
| P0-10e | `host-readiness.md` sections 1–2 filled | C | `[ ]` | | |
| P0-11a | Local Windows → WSL reachability tested | A+B | `[ ]` | | |
| P0-11b | Second PC → host reachability tested | A+B | `[ ]` | | |
| P0-11c | Networking mode (NAT/mirrored) recorded, D-05 | A+B | `[ ]` | | |
| P0-11d | Temporary firewall/portproxy rules removed | A+B | `[ ]` | | |
| P0-11e | Sleep / restart / network-change behaviour observed and recorded | A+B | `[ ]` | | |
| P0-12 | Local-model smoke test (**optional — needs team OK**) | C | `[ ]` | | Result: GPU works / CPU only / blocked |
| P0-13a | Draft: task lifecycle, IDs, error format | All | `[ ]` | | |
| P0-13b | Draft: `search_files` tool contract + scope | B+A | `[ ]` | | |
| P0-13c | Draft: planner interface + fixture list | C+A | `[ ]` | | |
| P0-14a | ADR template + ADR-001…008 | A | `[ ]` | | |
| P0-14b | `docs/roadmap/team.md` | A | `[ ]` | | |
| P0-15a | `docs/setup.md` + troubleshooting written | A | `[ ]` | | |
| P0-15b | Clean-clone validation by Dev B | B | `[ ]` | | |
| P0-15c | Clean-clone validation by Dev C | C | `[ ]` | | |
| P0-16a | P0 exit checklist reviewed | All | `[ ]` | | |
| P0-16b | Rotation hand-off done (A→B, B→C, C→A) | All | `[ ]` | | |
| P0-16c | Retrospective held | All | `[ ]` | | |

### P0 exit criteria

- [ ] Repo + agreed structure + READMEs merged
- [ ] Branching, PR template, review rules, coding standards merged
- [ ] Tooling choices recorded
- [ ] All three can clone, install pinned dev deps and run checks green
- [ ] Python version + dependency approach recorded; version matrix started
- [ ] PostgreSQL works for all three; dev and test DBs separate with different credentials
- [ ] PostgreSQL not reachable from another PC
- [ ] `.env.example` + `.gitignore` committed; no secrets committed
- [ ] Host hardware, exact GPU model and VRAM, WSL limits documented
- [ ] LAN reachability from a second PC tested; mode recorded
- [ ] Three draft agreements exist, each with open questions
- [ ] ADRs for D-01…D-08 with honest statuses
- [ ] Clean-clone setup validated by someone other than the author
- [ ] (If accepted) smoke-test result recorded
- [ ] Carried-over items listed with owners

---

## 2b. Phase 1 — Contracts and persistence

Owners: **team assigns** every step (suggested stream rotation in `00-phase-plan.md`: BE = Dev B · WB = Dev C · AI = Dev A). Detail for every step: [`phase-1-contracts-persistence.md`](phase-1-contracts-persistence.md).

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P1-00 | Entry check: P0 outputs present, D-01..D-03 settled, AI-validation owner named | All | `[ ]` | | Blocks P1-07 and P1-15 |
| P1-01 | Learning: HTTP, JSON, contracts, five layers (each dev) | All | `[ ]` | | |
| P1-02 | Learning: SQL, constraints, transactions, row locks (each dev) | All | `[ ]` | | |
| P1-03 | Learning: typed validation (each dev) | All | `[ ]` | | |
| P1-04 | Learning: pytest fixtures, parametrize, contract tests (each dev) | All | `[ ]` | | |
| P1-05 | Learning: passwords, hashing, tokens, credentials (each dev) | All | `[ ]` | | |
| P1-06 | Learning: FastAPI essentials (each dev) | All | `[ ]` | | |
| P1-07a | ADR D-09 ID format | | `[ ]` | | |
| P1-07b | ADR D-10 validation approach + unknown-field behaviour | | `[ ]` | | |
| P1-07c | ADR D-11 DB access + migration tool | | `[ ]` | | |
| P1-07d | ADR D-12 API framework | | `[ ]` | | |
| P1-07e | ADR D-15 password hashing library | | `[ ]` | | |
| P1-07f | Dependency PR merged with lock; version matrix updated | | `[ ]` | | |
| P1-08 | Vocabulary: IDs, timestamps, enums, error catalogue with emitter/terminal/retry/recovery | | `[ ]` | | Read 04.08.09 table |
| P1-09a | Task + step state machine contract (transition table copied from 03.29) | | `[ ]` | | |
| P1-09b | Pure `state_machine.py` + full transition-matrix tests | | `[ ]` | | |
| P1-09c | ADR D-18 interruption / approval expiry / cancel representation | | `[ ]` | | |
| P1-10 | Public API contract + valid/invalid examples | | `[ ]` | | |
| P1-11 | Planner contract + examples | | `[ ]` | | |
| P1-12 | Bridge protocol contract + ADR D-17 (polling, Provisional) | | `[ ]` | | |
| P1-13 | `search_files` + generic tool schema contract | | `[ ]` | | |
| P1-14 | Contract-test harness over shared example files | All | `[ ]` | | |
| P1-15 | Migration workflow + `docs/operations/database.md` | | `[ ]` | | Read 04.05.06 safety checks |
| P1-16 | Initial schema migration + data-model doc | | `[ ]` | | Read 03.10.11 |
| P1-17 | PostgreSQL integration tests (constraints, atomic claim, duplicate, restart) | | `[ ]` | | |
| P1-18a | ADR D-13 auth method (closes PC-04) | All | `[ ]` | | Local accounts = docs' provisional recommendation |
| P1-18b | ADR D-14 token lifecycle | | `[ ]` | | |
| P1-18c | Users, hashing, login, rate limit, disable, protected-route dependency | | `[ ]` | | Non-author review |
| P1-18d | Test: no secrets in logs | | `[ ]` | | |
| P1-19a | Authorization sequence function (10 steps from 04.09) | | `[ ]` | | |
| P1-19b | Multi-user isolation + revocation tests | | `[ ]` | | |
| P1-20a | ADR D-16 device credential + enrollment | | `[ ]` | | |
| P1-20b | Backend register / list / revoke device | | `[ ]` | | |
| P1-20c | Windows credential-storage approach verified on Windows | | `[ ]` | | [Verify] |
| P1-21a | Bridge prototype: authenticate, heartbeat, capabilities, poll loop with backoff + jitter | | `[ ]` | | Native Windows |
| P1-21b | Backend bridge routes at prototype level | | `[ ]` | | |
| P1-21c | 15 bridge integration scenarios copied from 04.10.12 and classified P1/P2 | | `[ ]` | | |
| P1-22a | Planner interface + `MockPlanner` | | `[ ]` | | |
| P1-22b | Application-side plan validator + fixtures | | `[ ]` | | |
| P1-23 | CI pipeline (D-21): lint, types, unit, contract, PostgreSQL integration | | `[ ]` | | Read 04.04.05; GitHub Actions limits [Verify] |
| P1-24a | Open decisions recorded (D-09..D-22 + tables from 03.10.11, 03.29.16, 04.09.11, 04.10.13) | All | `[ ]` | | |
| P1-24b | PC-01 and PC-05 answered or deferred with a phase | All | `[ ]` | | |
| P1-25 | Contract freeze: consumer review, security review, tag, CHANGELOG | All | `[ ]` | | |
| P1-26 | Gate 1 review, tracker update, P2 entry list, hand-off pairing, retrospective | All | `[ ]` | | |

### P1 / Gate 1 exit criteria

- [ ] Identifiers, timestamps, task states, step states documented and enforced by a tested pure state-machine module
- [ ] Error catalogue complete (emitter / terminal / retry / recovery per code)
- [ ] Public API, planner, bridge and tool contracts committed as five separate layers with valid and invalid examples used by tests
- [ ] Contract baseline approved by all three + a security reviewer; change process exists
- [ ] Migration workflow creates the schema from empty and upgrades the previous revision on all three PCs
- [ ] Database tests on real PostgreSQL prove constraints, atomic claim, duplicate arbitration, restart persistence
- [ ] Authentication and ownership tested with two users; revocation immediate
- [ ] Device enrollment, authentication, heartbeat, capabilities and revocation work
- [ ] Mock planner output passes the validator; invalid fixtures rejected
- [ ] CI runs unit, contract and PostgreSQL integration tests on every PR
- [ ] D-09..D-22 recorded with honest statuses
- [ ] Hardware inventory exists and an AI-validation owner is named
- [ ] Carried-over items and P2 entry list in the tracker with owners

---

## 2c. Phase 2 — First vertical slice

Owners: **team assigns** every step (suggested stream rotation in `00-phase-plan.md`: BE = Dev C · WB = Dev A · AI = Dev B). Detail for every step: [`phase-2-first-vertical-slice.md`](phase-2-first-vertical-slice.md). The docs' own 12-day schedule (04.07.11) is a docs estimate, not a commitment; if bridge transport, device authentication or recovery design is unresolved, extend the milestone rather than bypass boundaries.

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P2-00 | Entry check: P1 outputs present, blocking ADRs settled, ≥2 Windows PCs with native bridge environment | All | `[ ]` | | Blocks P2-06 onward |
| P2-01 | Learning: FastAPI service layering (each dev) | All | `[ ]` | | |
| P2-02 | Learning: PostgreSQL idempotency, claims, fencing (each dev) | All | `[ ]` | | |
| P2-03 | Learning: native Windows Python, paths, links, TOCTOU (each dev) | All | `[ ]` | | Windows parts on real Windows |
| P2-04 | Learning: failure thinking, reconciliation, fault injection (each dev) | All | `[ ]` | | |
| P2-05 | Learning: building a CLI (each dev) | All | `[ ]` | | |
| P2-06 | Contract confirmation; resolve D-23, D-24, D-25, D-26; fixtures; tag `contracts-v0.2` | All | `[ ]` | | Docs inconsistencies |
| P2-07 | ADR D-34 CLI framework; stubs for D-27..D-33, D-35..D-39 | | `[ ]` | | |
| P2-08 | Schema additions (tasks, steps, attempts, audit) via new migration | | `[ ]` | | Claim columns come in P2-20 |
| P2-09 | State-transition service | | `[ ]` | | |
| P2-10 | `POST /v1/tasks` + idempotency | | `[ ]` | | |
| P2-11 | Task queries (`GET` task, steps, result, list) | | `[ ]` | | D-37 |
| P2-12 | PostgreSQL integration and failure tests — checkpoint A | | `[ ]` | | |
| P2-13 | Deterministic planner and `search_files` handler | | `[ ]` | | |
| P2-14 | Proposal validation, registry, capability descriptions, invalid-plan fixtures | | `[ ]` | | Bridge never called on invalid input |
| P2-15 | Bridge: config, startup, device auth, protocol handling, tool registry | | `[ ]` | | Native Windows; D-39 |
| P2-16 | `search_files` + Windows path safety | | `[ ]` | | D-30, D-31; non-author review |
| P2-17 | Bridge operation journal + deduplication | | `[ ]` | | D-29 |
| P2-18 | Windows security tests (9 negative + 7 WP-03 + 03.32 groups) | | `[ ]` | | Run on ≥2 PCs |
| P2-19 | Bridge transport: poll, ack, result, correlation — checkpoint B | | `[ ]` | | D-32 |
| P2-20 | Worker, atomic claim, lease, fencing | | `[ ]` | | D-27, D-28 |
| P2-21 | Dispatch pipeline with persisted intent — checkpoint C | | `[ ]` | | D-33 |
| P2-22 | Recovery and reconciliation, fault-injection suite — checkpoint D | All | `[ ]` | | Failure matrix doc |
| P2-23 | Minimal cancellation request | | `[ ]` | | D-18 |
| P2-24 | Admission control, limits, fairness | | `[ ]` | | D-38 |
| P2-25 | CLI foundation: login, session storage, devices, status | | `[ ]` | | D-35 |
| P2-26 | CLI task commands: run, task, steps/result/watch, cancel, history | | `[ ]` | | D-36, D-37 |
| P2-27 | Observability, audit, no-secrets-in-logs test | | `[ ]` | | Logging doc not read |
| P2-28 | End-to-end on ≥2 Windows PCs over LAN + measurements + Baseline 2 | All | `[ ]` | | |
| P2-29 | Acceptance matrix (15) + negative tests (9) complete | All | `[ ]` | | |
| P2-30 | Three-user scenario (checkpoint E), clean-setup reproduction, release evidence report | All | `[ ]` | | |
| P2-31 | Security review, Gate 2 review, tracker update, P3 entry list, hand-off, retrospective | All | `[ ]` | | |

### P2 / Gate 2 exit criteria

- [ ] Authenticated task submission persisted; task ID returned
- [ ] Bridge receives an authenticated operation
- [ ] Scoped file search returns a structured result
- [ ] Result and state persisted and visible in the CLI
- [ ] Duplicate-submission and unauthorized-device tests pass
- [ ] Task API and migration work on a clean setup
- [ ] Idempotency holds under concurrency (PostgreSQL)
- [ ] Planner produces only a registered search operation
- [ ] Backend and bridge validation both work
- [ ] Search stays in scope (Windows tests on ≥2 PCs)
- [ ] Duplicate-delivery, disconnection and lost-response tests exist and pass
- [ ] Recovery never blindly repeats an uncertain operation
- [ ] Cross-user and cross-device authorization tests pass
- [ ] Workflow runs across the intended LAN topology
- [ ] Setup, execution and troubleshooting reproducible by a non-author
- [ ] No critical or high security defect open
- [ ] All 15 acceptance scenarios and 9 negative tests have evidence
- [ ] Release evidence report lists untested scenarios
- [ ] D-23..D-39 recorded with honest statuses
- [ ] Full Baseline 2 from P0 recorded; P3 entry list in the tracker

---

## 2d. Phase 3 — Safe side effects

Owners: **team assigns** every step (suggested stream rotation in `00-phase-plan.md`: BE = Dev A · WB = Dev B · AI = Dev C). Detail for every step: [`phase-3-safe-side-effects.md`](phase-3-safe-side-effects.md). The docs state that "each tool must have a reviewed contract, explicit failure behavior and tests before it is enabled" (03.23.12); no Tier 1 tool is enabled in production until its evidence exists. Gate 3 requires repeatable tests, not demonstrations (04.28.05).

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P3-00 | Entry check: P2 outputs present, blocking ADRs settled, ≥2 Windows PCs available | All | `[ ]` | | Blocks P3-06 onward |
| P3-01 | Learning: policy engines, risk tiers, deny-by-default | All | `[ ]` | | |
| P3-02 | Learning: approval state machine, PostgreSQL concurrency, fingerprints | All | `[ ]` | | |
| P3-03 | Learning: `create_file` safety, atomic creation, TOCTOU | All | `[ ]` | | Windows parts on native Windows |
| P3-04 | Learning: application launching and session boundaries | All | `[ ]` | | Windows parts on native Windows |
| P3-05 | Learning: configuration categories, versioning, secrets isolation | All | `[ ]` | | |
| P3-06 | Contract confirmation: operation envelope, approval record, policy decision, error codes, state additions, CLI commands; tag `contracts-v0.3` | All | `[ ]` | | |
| P3-07 | ADR stubs D-40..D-55; D-18 superseded by D-48 | | `[ ]` | | |
| P3-08 | Schema additions: `approvals`, `permission_grants`, `policy_decisions`, `configuration_versions` | | `[ ]` | | |
| P3-09 | Policy engine: 8-layer precedence, fail closed, audit-persistence gate | | `[ ]` | | Non-author security review |
| P3-10 | Risk classification, tool policy, PC-06 ADR | All | `[ ]` | | Answers PC-06 |
| P3-11 | Tool registry: `create_file` and `launch_application` contracts, startup validation | | `[ ]` | | |
| P3-12 | Approval lifecycle: DB, state machine, API routes, atomic decisions, expiry, revocation | | `[ ]` | | Non-author security review; D-40, D-42, D-50 |
| P3-13 | Pre-dispatch L8 revalidation wired into dispatch pipeline; fingerprint check | | `[ ]` | | |
| P3-14 | Prompt-injection and policy-bypass adversarial tests | All | `[ ]` | | Security regression CI gate |
| P3-15 | CLI: approval commands, clarification flow, watch shows WAITING_FOR_APPROVAL | | `[ ]` | | |
| P3-16 | Bridge operation journal hardening for Tier 1 tools (D-47 finalized) | | `[ ]` | | Native Windows; real-hardware evidence |
| P3-17 | `create_file` reconciliation and verification | | `[ ]` | | |
| P3-18 | `create_file` bridge implementation (path validation, no silent overwrite, D-43, D-44) | | `[ ]` | | Non-author security review; ≥2 PCs |
| P3-19 | `launch_application` bridge implementation (allowlist, session check, D-45, D-46) | | `[ ]` | | Native Windows |
| P3-20 | Full fault-injection suite extended to Tier 1 tools + approval races | All | `[ ]` | | Extends P2 failure matrix |
| P3-21 | Full cancellation semantics (D-48 finalized) | | `[ ]` | | |
| P3-22 | Disconnection behaviour and revocation propagation (PC-07, D-49, D-54) | | `[ ]` | | Answers PC-07 |
| P3-23 | Permission and configuration management CLI; startup validation hardening; D-52, D-55 | | `[ ]` | | |
| P3-24 | Observability: structured logs, health endpoints, `nexus diagnostics`; D-53 | | `[ ]` | | |
| P3-25 | P3 acceptance matrix (15 scenarios) + fault-matrix rows complete on ≥2 Windows PCs | All | `[ ]` | | |
| P3-26 | Release evidence report, clean-setup reproduction, milestone sign-off | All | `[ ]` | | |
| P3-27 | Security review, Gate 3 review, tracker update, P4 entry list, hand-off, retrospective | All | `[ ]` | | |

### P3 / Gate 3 exit criteria

- [ ] Tool policy and approval enforcement work end to end
- [ ] Safe file creation, no silent overwrite
- [ ] Operation dedup and recovery rules in place for every new tool
- [ ] Cancellation and disconnection behaviour correct
- [ ] Tests for lost responses and uncertain outcomes exist and pass
- [ ] Policy engine passes 8-layer precedence tests; fails closed when unavailable
- [ ] Approval bound to exact normalized operation; expiry, rejection and invalidation prevent dispatch
- [ ] Pre-dispatch L8 revalidation runs for every Tier 1 operation
- [ ] Prompt-injection adversarial tests pass
- [ ] Bridge journal handles `create_file` and `launch_application` unresolved outcomes
- [ ] `create_file` reconciliation resolves or honestly preserves UNCERTAIN
- [ ] `launch_application` allowlist enforced; no arbitrary executable path
- [ ] Zero unauthorized side effects in security test suite
- [ ] PC-06 and PC-07 answered with ADRs
- [ ] D-40..D-55 recorded with honest statuses
- [ ] 15 acceptance scenarios and P3 fault-matrix rows have evidence
- [ ] Release evidence report exists with untested scenarios listed
- [ ] Permission inspection, revocation and config management CLI work
- [ ] No critical or high security defect open

---




---

## 2e. Phase 4 — Local AI and memory

Owners: **team assigns** every step (suggested stream rotation in `00-phase-plan.md`: BE = Dev B · WB = Dev C · AI = Dev A). Detail for every step: [`phase-4-local-ai-and-memory.md`](phase-4-local-ai-and-memory.md). Gate 4 has an explicit fallback clause (04.28.05): "Validated local runtime and model, OR a documented blocker and tested fallback." If the AMD GPU is incompatible or performance is unacceptable, the gate is passed with a documented blocker and a CPU fallback or alternative plan — not by ignoring the problem.

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P4-00 | Entry check: P3 outputs present, blocking ADRs settled, host hardware carried item assigned | All | `[ ]` | | Blocks P4-06 onward |
| P4-01 | Learning: local inference, runtime/model/mode/contract separation | All | `[ ]` | | |
| P4-02 | Learning: structured plan representation and DAG dependencies | All | `[ ]` | | |
| P4-03 | Learning: memory ownership, retrieval and context assembly | All | `[ ]` | | |
| P4-04 | Learning: evaluation layers, hard safety gates, non-determinism | All | `[ ]` | | |
| P4-05 | Learning: performance measurement and AMD GPU specifics | All | `[ ]` | | |
| P4-06 | Hardware inventory completion and GPU/runtime compatibility check (P0 carried item); settle D-58, D-70 | | `[ ]` | | C owns; fills host-readiness §3–6 |
| P4-07 | Runtime selection, installation, smoke test; settle D-56, D-68; answer PC-03 | | `[ ]` | | |
| P4-08 | Model benchmark (4-layer evaluation dataset); settle D-57, D-59, D-67, D-69 | All | `[ ]` | | All review safety results |
| P4-09 | Model adapter + inference service + `MockProvider`; settle D-60 baseline | | `[ ]` | | No live model in CI |
| P4-10 | Structured plan contract (multi-step, DAG, D-61); tag `contracts-v0.4` | All | `[ ]` | | |
| P4-11 | Plan validation pipeline (10 layers, cycle detection, scope check) | | `[ ]` | | |
| P4-12 | Dependency-aware execution orchestration and replanning; settle D-62 | | `[ ]` | | |
| P4-13 | Multi-step context and grounded response assembly | | `[ ]` | | |
| P4-14 | Planning evaluation dataset + scoring pipeline; confirm D-67 thresholds | All | `[ ]` | | All contribute cases |
| P4-15 | Memory schema, CRUD service, API routes, lifecycle; settle D-63, D-64 | | `[ ]` | | |
| P4-16 | Lexical retrieval (PostgreSQL FTS); D-65 first step; settle D-66 Provisional | | `[ ]` | | Cross-user isolation test is release-blocking |
| P4-17 | Context assembly and budget enforcement (priority order from 03.34.07) | | `[ ]` | | |
| P4-18 | Semantic/embedding retrieval — only if lexical evaluation shows a need; settle D-65 final | | `[ ]` | | Skip if lexical sufficient |
| P4-19 | Memory CLI commands (list, show, update, delete) | | `[ ]` | | |
| P4-20 | Adversarial evaluation: prompt injection, scope adherence, model safety, hard gates | All | `[ ]` | | All review; zero unauthorized ops required |
| P4-21 | CLI AI commands and honest failure messages (model-unavailable path) | | `[ ]` | | |
| P4-22 | Performance benchmark: model runtime, concurrency, combined workload; settle D-60 final | | `[ ]` | | Designated host + ≥2 Windows PCs |
| P4-23 | End-to-end acceptance matrix (15 P4 scenarios) | All | `[ ]` | | On designated host with real model |
| P4-24 | Release evidence report, clean-setup reproduction, host-readiness baseline update | All | `[ ]` | | |
| P4-25 | Security review, Gate 4 review, tracker update, P5 entry list, hand-off, retrospective | All | `[ ]` | | |

### P4 / Gate 4 exit criteria

- [ ] Validated local runtime and model (or documented blocker + tested fallback)
- [ ] AMD GPU verified or CPU fallback honestly documented
- [ ] Model selected with a 4-layer benchmark on the designated host; D-57 ADR explains choice
- [ ] Model adapter isolates runtime; `MockProvider` allows CI without a live model
- [ ] Structured plans + application-side validation (10-layer pipeline)
- [ ] Multi-step plan DAG: cycle detection, invalid-tool rejection, scope-expansion rejection
- [ ] Dependency-aware execution: failed prerequisite blocks dependent steps
- [ ] Replanning within scope only; D-62 settled
- [ ] User-scoped memory and retrieval: CRUD, ownership enforced, deletion respected
- [ ] Context assembly uses D-59 token budget and priority order
- [ ] Lexical retrieval tested against evaluation dataset; D-65 ADR records choice
- [ ] Zero unauthorized memory cross-user exposure
- [ ] Evaluation pipeline produces reproducible reports; D-67 thresholds confirmed
- [ ] Prompt-injection and unsupported-action tests pass; zero hard-gate failures
- [ ] Evidence-grounded summaries; honest failures; model-unavailable path tested
- [ ] Three-user concurrency benchmarked; D-60 settled
- [ ] All 15 acceptance scenarios pass
- [ ] D-56..D-70 recorded with honest statuses
- [ ] Evidence report with untested scenarios listed
- [ ] No critical or high security defect open

---

## 2f. Phase 5 — User-facing workflows

Owners: **team assigns** every step (suggested stream rotation in `00-phase-plan.md`: BE = Dev C · WB = Dev A · AI = Dev B). Detail for every step: [`phase-5-user-facing-workflows.md`](phase-5-user-facing-workflows.md). P5 has **no independent gate** — all outputs feed Gate 5 at P6. Unfinished items become carried-over items for P6.

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P5-00 | Entry check: P4 outputs present, blocking ADRs settled, D-29/D-47 journal Confirmed | All | `[ ]` | | Blocks P5-12 onward |
| P5-01 | Learning: document extraction, parsing limits, hostile docs | All | `[ ]` | | |
| P5-02 | Learning: task history, audit trail, three replay modes | All | `[ ]` | | |
| P5-03 | Learning: artifact concepts, result vs. evidence, verification levels | All | `[ ]` | | |
| P5-04 | Learning: CLI UX principles and three user-observable states | All | `[ ]` | | |
| P5-05 | Learning: context resolution, follow-up safety | All | `[ ]` | | |
| P5-06 | CLI command vocabulary alignment; settle D-75, D-84, D-36; tag `contracts-v0.5` | All | `[ ]` | | |
| P5-07 | Task progress display and `--watch` mode; settle D-76 | | `[ ]` | | |
| P5-08 | Results: partial success, UNCERTAIN outcomes, artifact references in CLI | | `[ ]` | | |
| P5-09 | Artifact schema, API extension and retention rules; settle D-77 | | `[ ]` | | |
| P5-10 | Task history CLI: searchable timeline; settle D-81, D-37 | | `[ ]` | | |
| P5-11 | Task event table and security audit trail; settle D-78, D-79, D-80 | | `[ ]` | | |
| P5-12 | `read_document` tool contract and bridge; settle D-71, D-72, D-74 | | `[ ]` | | Non-author security review; ≥2 Windows PCs |
| P5-13 | Resource limits, hostile-document tests, error codes; settle D-82 | | `[ ]` | | Native Windows |
| P5-14 | Chunking, context budgeting and document retrieval; settle D-73 | | `[ ]` | | |
| P5-15 | Source attribution and answer verification | | `[ ]` | | |
| P5-16 | Follow-up context resolution and ambiguity handling; settle D-83 | | `[ ]` | | |
| P5-17 | Error messages, recovery guidance and exit-code contract; finalize D-84 | | `[ ]` | | |
| P5-18 | Machine-readable output finalization and schema documentation; finalize D-75 | | `[ ]` | | |
| P5-19 | End-to-end acceptance matrix (15 P5 scenarios) | All | `[ ]` | | Designated host + ≥2 Windows PCs |
| P5-20 | Release evidence report, clean-setup reproduction and baseline update | All | `[ ]` | | |
| P5-21 | Hand-off review, tracker update and P6 entry list | All | `[ ]` | | No gate; check Gate 5 prerequisites |

### P5 contribution to Gate 5 exit criteria

- [ ] Task progress from persisted state; partial/UNCERTAIN outcomes rendered accurately
- [ ] Artifact records with verification status; file stays on target device
- [ ] Task history searchable; ownership enforced; security audit trail records authorization decisions
- [ ] `read_document` registered, bridged and tested on supported formats
- [ ] Document injection tests pass; extracted text cannot override policy
- [ ] Source attribution validated against actually supplied chunks
- [ ] Follow-up context resolves explicit references; clarifies ambiguous ones
- [ ] Machine-readable `--output json` stable and validated
- [ ] All 15 P5 acceptance scenarios have evidence
- [ ] D-71..D-84 recorded with honest statuses
- [ ] Release evidence report with untested scenarios listed
- [ ] No critical or high security defect open

---

## 2g. Phase 6 — Team integration

Owners: **team assigns** every step (suggested stream rotation in `00-phase-plan.md`: BE = Dev A · WB = Dev B · AI = Dev C). Detail for every step: [`phase-6-team-integration.md`](phase-6-team-integration.md). Gate 5 requires repeatable tests on the actual three-PC deployment — a demonstration without repeatable tests does not count (04.28.05).

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P6-00 | Entry check: P5 outputs present, all three accounts and devices enrollable | All | `[ ]` | | Blocks P6-09 |
| P6-01 | Learning: four ownership boundaries and isolation model | All | `[ ]` | | |
| P6-02 | Learning: round-robin scheduling, resource limits and starvation | All | `[ ]` | | |
| P6-03 | Learning: LAN networking, WSL 2 modes and port policy | All | `[ ]` | | |
| P6-04 | Learning: device availability and scheduling under disconnection | All | `[ ]` | | |
| P6-05 | Learning: fairness metrics and Gate 5 acceptance criteria | All | `[ ]` | | |
| P6-06 | DB isolation audit, authorization review; settle D-88, D-91; tag `contracts-v0.6` | All | `[ ]` | | Non-author security review |
| P6-07 | LAN deployment: bind address, port policy, firewall, WSL networking; settle D-85 | | `[ ]` | | Needs ≥2 PCs |
| P6-08 | Three-user enrollment, startup procedure, PC-02 answer; settle D-87, D-89 | All | `[ ]` | | |
| P6-09 | Cross-user isolation tests (15 scenarios from 03.37.10) | All | `[ ]` | | All three PCs required |
| P6-10 | Concurrent task submission and round-robin scheduler validation | All | `[ ]` | | All three PCs required |
| P6-11 | Per-user and per-device resource limits under load; settle D-90 | | `[ ]` | | Designated host + all PCs |
| P6-12 | Backend restart while all three users have tasks running | All | `[ ]` | | |
| P6-13 | Bridge disconnect/reconnect under concurrent workload; settle D-94 | | `[ ]` | | Native Windows |
| P6-14 | Fairness and starvation tests; settle D-92 | All | `[ ]` | | All three PCs required |
| P6-15 | Performance under three-user workload; settle D-93 | | `[ ]` | | Designated host + all PCs |
| P6-16 | Network security and TLS decision; settle D-86 | | `[ ]` | | Non-author security review |
| P6-17 | Reproducible setup: clean-install for each developer | All | `[ ]` | | Non-author validation |
| P6-18 | Gate 5 acceptance matrix (15 P6 scenarios) | All | `[ ]` | | All three PCs simultaneously |
| P6-19 | Security review, Gate 5 review, release evidence report, hand-off to P7 | All | `[ ]` | | |

### P6 / Gate 5 exit criteria

- [ ] Three registered users and devices
- [ ] Cross-user and cross-device isolation tests pass
- [ ] Concurrent task and shared-resource tests pass
- [ ] Restart, disconnect and recovery scenarios tested
- [ ] Reproducible setup confirmed by a non-author
- [ ] LAN deployment: host address, port policy, firewall, WSL mode documented and tested
- [ ] Database authorization audit complete; no unfiltered query found
- [ ] Device ownership enforced; no cross-user device targeting
- [ ] Round-robin fairness tested under three-user load
- [ ] Performance benchmark complete; D-90 confirmed
- [ ] Network security minimum requirements met; D-86 settled honestly
- [ ] All 15 P6 acceptance scenarios pass
- [ ] PC-02 answered
- [ ] D-85..D-94 recorded with honest statuses
- [ ] Release evidence report with untested scenarios listed
- [ ] No critical or high security defect open

---

## 2h. Phase 7 — Hardening and release candidate

Owners: **team assigns** every step — no developer can independently declare the whole system release-ready (03.40.9). Detail for every step: [`phase-7-hardening-and-release.md`](phase-7-hardening-and-release.md). Gate 6 requires actual evidence for all items — a demonstration without repeatable tests does not count (04.28.5).

| ID | Step | Owner | Status | Evidence (link or file) | Notes |
|---|---|---|---|---|---|
| P7-00 | Learning: release readiness and definition of done | All | `[ ]` | | |
| P7-01 | Learning: CI/CD pipeline gates and deterministic-testing policy; settle D-95, D-96 stubs | All | `[ ]` | | |
| P7-02 | Learning: backup, RPO and RTO; settle D-97, D-98, D-99 stubs | All | `[ ]` | | |
| P7-03 | Learning: packaging, versioning and upgrade classes; settle D-100, D-101, D-102 stubs | All | `[ ]` | | |
| P7-04 | Learning: threat-model review; identify new vs. carried-from-P2–P6 security items | All | `[ ]` | | |
| P7-05 | E2E acceptance workflows A (search/summarize), B (create file), C (uncertain-op recovery) | All | `[ ]` | | All three PCs required |
| P7-06 | E2E acceptance workflows D (approval/cancellation), E (three-user isolation), F (memory lifecycle) | All | `[ ]` | | All three PCs required for E |
| P7-07 | Security hardening review — five-layer checklist with cross-component reviewer | All | `[ ]` | | Non-author review required |
| P7-08 | Security acceptance matrix — 12 items with evidence | All | `[ ]` | | |
| P7-09 | Prompt-injection regression suite — 8 adversarial scenarios | | `[ ]` | | Primary: AI/context developer |
| P7-10 | Backup implementation and automation; settle D-97, D-98, D-99 | | `[ ]` | | Primary: backend developer |
| P7-11 | Backup-and-restore rehearsal — required exercises; two developers follow independently | All | `[ ]` | | Isolated test data only |
| P7-12 | Uncertain-operation reconciliation after restore | All | `[ ]` | | Bridge + backend together |
| P7-13 | Revocation and deletion-record safety after restore | All | `[ ]` | | Cross-component review |
| P7-14 | CI/CD pipeline — all five gates running; settle D-95, D-96 | All | `[ ]` | | |
| P7-15 | Packaging, versioning and compatibility matrix; settle D-100, D-101, D-102 | All | `[ ]` | | |
| P7-16 | Upgrade workflow and rollback procedures; bridge upgrade test; settle D-103 | All | `[ ]` | | Rehearsal required |
| P7-17 | Installation documentation: clean-install + reproducible setup; settle D-104 | All | `[ ]` | | Non-author validation |
| P7-18 | Reliability experiments — 10 scenarios with written records | All | `[ ]` | | |
| P7-19 | Performance and model-quality measurements on actual hardware | All | `[ ]` | | AMD GPU on actual host |
| P7-20 | Release candidate preparation — 25-item + 21-item checklists; release evidence report | All | `[ ]` | | |
| P7-21 | Gate 6 — Release candidate review and team sign-off | All | `[ ]` | | All three sign off |

### P7 / Gate 6 exit criteria

- [ ] Acceptance Workflows A, B, C, D, E, F all pass with written acceptance records. (P7-05, P7-06)
- [ ] Security hardening review complete; each of the five layers has a cross-component review. (P7-07)
- [ ] All 12 security-acceptance items evidenced. (P7-08)
- [ ] Prompt-injection regression suite (8 scenarios) passes. (P7-09)
- [ ] Backup runs, produces a verified protected copy outside the designated host; D-97, D-98, D-99 settled. (P7-10)
- [ ] All required backup-and-restore exercises documented; at least two developers can independently follow the procedure. (P7-11)
- [ ] Uncertain-operation reconciliation after restore demonstrated. (P7-12)
- [ ] Revocation and memory-deletion safety after restore demonstrated. (P7-13)
- [ ] CI/CD pipeline with all five gates running on PRs; D-95, D-96 settled. (P7-14)
- [ ] All components have discoverable versions; compatibility matrix exists; D-100, D-101, D-102 settled. (P7-15)
- [ ] Upgrade and rollback procedures documented and rehearsed; D-103 settled. (P7-16)
- [ ] Installation documentation reproduced successfully by a non-author; D-104 settled. (P7-17)
- [ ] All 10 reliability experiments recorded with evidence. (P7-18)
- [ ] Performance measurements on actual hardware recorded; AI acceptance evidence complete; AMD GPU behavior documented on the actual machine. (P7-19)
- [ ] 25-item MVP evidence checklist complete with evidence; 21-item sign-off checklist complete; all 10 release blockers resolved; release evidence report exists. (P7-20)
- [ ] All three developers have signed off in `docs/releases/p7-signoff.md`. (P7-21)
- [ ] D-95..D-104 recorded with honest statuses.
- [ ] No critical or high-severity security defect unresolved at release.

---

## 3. Decision register

Statuses are the docs' five values (04.27.02): **Confirmed · Provisional · Open · Blocked · Deferred**.

| ID | Decision | Status | Decided in | Evidence | Owner | Notes |
|---|---|---|---|---|---|---|
| D-01 | Python version | Open | P0-07 | | A | |
| D-02 | Dependency manager / lock approach | Open | P0-07 | | A | |
| D-03 | PostgreSQL: native vs Docker Compose | Open | P0-08 | | A | Compose is only a candidate in docs |
| D-04 | Formatter / linter / type checker / test library | Open | P0-05 | | All | |
| D-05 | WSL networking mode | Open | P0-11 | | A+B | Must be validated on actual machines |
| D-06 | Host topology (Option A provisional) | Provisional | P0-10…12 | | All | Docs: provisional default is Option A |
| D-07 | Where specs/roadmap live in repo | Open | P0-03 | | A | `.docx` diff poorly in git |
| D-08 | Repo host: GitHub private free plan | **Confirmed** | P0-02 | User answer | — | Limits of free plan to be checked |
| D-09 | Identifier format (opaque; UUID or another) | Open | P1-07a, P1-08 | | | Docs leave it open (04.08.13) |
| D-10 | Typed-validation approach + unknown-field behaviour per boundary | Open | P1-07b | | | Pydantic is a candidate only |
| D-11 | DB access library + migration tool | Open | P1-07c | | | SQLAlchemy / Alembic are candidates only |
| D-12 | API framework (FastAPI) | Open | P1-07d | | | Architecture assumes it; needs ADR |
| D-13 | MVP authentication method (closes PC-04) | Open | P1-18a | | | Docs' provisional recommendation: local NEXUS accounts |
| D-14 | CLI token lifecycle + revocation | Open | P1-18b | | | |
| D-15 | Password hashing library + parameters | Open | P1-07e | | | Docs require hashing, name no algorithm |
| D-16 | Device credential mechanism + enrollment handshake | Open | P1-20a | | | Open until transport + credential storage chosen (04.10.03) |
| D-17 | Bridge transport: authenticated outbound polling | Provisional | P1-12 | Docs 04.10.13 | | Persistent connection only if measured need |
| D-18 | Interruption, approval expiry, cancel-request representation | Open | P1-09c | | | |
| D-19 | Error-catalogue structure, tool-result and error payload schemas | Open | P1-08, P1-13 | | | |
| D-20 | Payload limits, pagination, older-schema support duration | Open | P1-10, P1-12 | | | Docs give no values |
| D-21 | CI platform and what runs where | Open | P1-23 | | | GitHub Actions likely; limits [Verify] |
| D-22 | Disconnected operation (closes PC-01) | Open | P1-24b | | | |
| D-23 | Task status casing on the wire (`queued` vs `QUEUED`) | Open | P2-06 | | | Docs inconsistent: 03.16/03.9 lower-case, 04.08 upper-case |
| D-24 | Bridge envelope field names (`schema_version` vs `tool_schema_version`; `attempt_id`, `step_id`) | Open | P2-06 | | | 03.12 vs 03.30/04.08 |
| D-25 | Error-code reconciliation (03.32 filesystem codes, 03.9 `DEVICE_OPERATION_FAILED` vs 04.08 catalogue) | Open | P2-06 | | | |
| D-26 | Logical directory ID(s) for tests; answers PC-05 for P2 | Open | P2-06 | | | 04.06 example `nexus_test_documents` is illustrative |
| D-27 | Claim fields: on task row vs separate table; claim strategy | Open | P2-20 | | | 04.11: required behaviour, implementation to validate |
| D-28 | Lease duration, heartbeat interval, renewal policy | Open | P2-20, P2-28 | | | Choose from measurements |
| D-29 | Bridge operation journal storage + retention | Open | P2-17 | | | Local database is a candidate only |
| D-30 | Windows APIs/libraries for safe path resolution | Open | P2-16 | | | 03.32.15 #6 |
| D-31 | `search_files` limits: depth, results, duration, hidden/system files | Open | P2-16, P2-28 | | | No numbers in docs |
| D-32 | Poll interval, request timeout, heartbeat, deadline form, credential auth mechanism | Open | P2-19, P2-28 | | | Polling stays Provisional (D-17) |
| D-33 | `search_files` timeout + retry policy | Open | P2-21 | | | Per-tool (03.30.08) |
| D-34 | CLI framework + HTTP client library | Open | P2-07 | | | 03.16.15 #6 |
| D-35 | CLI token storage, exit codes, watch interval, output conventions | Open | P2-25, P2-26 | | | |
| D-36 | Device selection: explicit vs displayed overridable default | Open | P2-26 | | | |
| D-37 | Pagination style for task lists | Open | P2-11 | | | |
| D-38 | Concurrency, queue limits and fairness approach | Open | P2-24 | | | Round-robin is a docs "proposed baseline" |
| D-39 | Bridge distribution + startup on Windows (source vs packaged) | Open | P2-15 | | | 04.21.18 |
| D-40 | Approval expiry duration (default and minimum) | Open | P3-12 | | | "Team should choose based on expected usage and consequences of stale consent" (04.18.05) |
| D-41 | Whether the task owner is always the approver, or whether any administrative role may approve | Open | P3-12 | | | Docs default: task owner only for MVP (03.23.07) |
| D-42 | Approval state values (`PENDING, APPROVED, REJECTED, EXPIRED, INVALIDATED`) — confirm or extend | Open | P3-12 | | | Proposed (04.18.06) |
| D-43 | `create_file` idempotency strategy: safe create-if-absent, temp-then-rename, or other; OS atomic primitives | Open | P3-18 | | | "Must be designed and tested rather than assumed" (03.30.06) |
| D-44 | `create_file` content size limit and output-format restrictions | Open | P3-18 | | | Docs require enforcement of output limits and no silent overwrite (03.31.06) |
| D-45 | `launch_application` allowlist for P3: which application IDs to register and their local executables | Open | P3-19 | | | Bridge owner decides local executables (04.20.05, 03.36.12) |
| D-46 | Application launching: confirm-launch-only vs verify-started; verification method | Open | P3-19 | | | 03.36.13 |
| D-47 | Bridge operation journal: finalize storage technology (D-29 Provisional from P2) and retention period for P3 tools | Open | P3-16 | | | Requires evidence on real Windows hardware |
| D-48 | Full cancellation representation for in-flight bridge operations (supersedes D-18) | Open | P3-21 | | | 03.15.06, 04.11.08 |
| D-49 | Disconnection policy: how long before a dispatched operation moves to UNCERTAIN when bridge stops heartbeating | Open | P3-22 | | | Measured from D-28 lease interval (03.15.08) |
| D-50 | Approval operation fingerprint algorithm: fields included and format | Open | P3-12 | | | "Calculated from a deterministic representation" (03.30.07) |
| D-51 | Permission grant schema: fields in the logical grant record | Open | P3-08 | | | "Logical model, not a finalized database schema" (04.20.06) |
| D-52 | Configuration versioning scheme for policy and directory-mapping changes | Open | P3-08 | | | 04.20.09, 03.20.09 |
| D-53 | Health and readiness endpoint schema and exposure policy | Open | P3-24 | | | "Exact response schema and exposure policy remain to be finalized" (03.19.05) |
| D-54 | Revocation propagation delay: maximum acceptable time for permission/device revocation to reach the bridge | Open | P3-22 | | | "Team must define the maximum acceptable delay" (04.20.08) |
| D-55 | Who is authorized to change shared policy and how emergency revocation works when the host is unavailable | Open | P3-23 | | | 03.23.10 |
| D-56 | Inference runtime selection (e.g., Ollama or alternative) | Open | P4-07 | | | Ollama is a candidate only (03.13.5, 04.13.05) |
| D-57 | Primary model selection (name, version, quantization) | Open | P4-08 | | | "Select using measurements on the target machine" (03.13.5, 04.03.11) |
| D-58 | Execution mode: GPU-accelerated, CPU, or hybrid fallback | Open | P4-06 | | | AMD GPU must be verified (04.13.08, 03.27.8) |
| D-59 | Model context-length limit and token budget for NEXUS context assembly | Open | P4-09 | | | "Configure appropriate to measured memory usage" (03.13.11) |
| D-60 | Maximum concurrent inference requests (proposed baseline: 1 until benchmarked) | Open | P4-22 | | | "Benchmark before increasing" (03.27.7) |
| D-61 | Plan schema contract: fields, versioning, step-key format, dependency representation | Open | P4-10 | | | "Final representation to be finalized" (03.35.3) |
| D-62 | Replanning rules: when replanning is allowed and how many times | Open | P4-12 | | | "Controlled replanning rather than blindly continuing" (03.35.8) |
| D-63 | Memory auto-save policy: explicit-only or user-configurable suggestions | Open | P4-15 | | | "Exact rules remain an open product decision" (03.14.3) |
| D-64 | Memory scope for MVP: personal-only or any shared project memory | Open | P4-15 | | | Docs recommend: default to private user memory (03.34.03) |
| D-65 | Retrieval implementation: PostgreSQL FTS first; embedding model and storage deferred until measured | Open | P4-16, P4-18 | | | "Choose only after prototype demonstrates meaningful improvement" (03.14.5) |
| D-66 | Ranking strategy: signals to use and relative weights | Open | P4-16 | | | "Proposed, not confirmed algorithm" (03.34.06) |
| D-67 | Planning evaluation pass thresholds (schema validity, planning correctness, safety gate) | Open | P4-08 | | | "Finalize after collecting baseline" (04.14.10) |
| D-68 | CPU fallback policy: when to use it and with what stricter limits | Open | P4-07 | | | "CPU fallback needs its own benchmark" (04.13.08) |
| D-69 | Model lifecycle: how model changes are versioned, reviewed and rolled back | Open | P4-08 | | | 04.13.10 |
| D-70 | Where the model runtime process lives: WSL2 or native Windows | Open | P4-06 | | | "Exact choice remains open until compatibility is verified" (04.13.08) |
| D-71 | `read_document` supported format list for P5 | Open | P5-12 | | | "Finalize after testing extraction libraries against representative files" (03.33.02) |
| D-72 | Extraction library choices and known limitations per supported format | Open | P5-12 | | | "Each supported format must have a tested extraction contract" (03.33.16) |
| D-73 | Chunking strategy and token-budget unit (chars vs. model tokens) | Open | P5-14 | | | "Benchmark simpler boundary-aware strategy first" (03.33.06) |
| D-74 | Document persistence policy: transient-per-task vs. retained/indexed text | Open | P5-12 | | | Docs initial recommendation: "process without automatically storing full contents permanently" (03.33.11) |
| D-75 | CLI default output mode and `--output json` schema versioning | Open | P5-06, P5-18 | | | "Schemas are documented and versioned" (03.38.11) |
| D-76 | CLI polling interval, `--watch` debounce and SSE/WebSocket upgrade condition | Open | P5-07 | | | "Polling initially; SSE only if measured need" (03.38.7) |
| D-77 | Artifact storage strategy for MVP: PostgreSQL metadata + file stays on target device | Open | P5-09 | | | Docs recommended approach (04.17.04 "Recommended MVP decision") |
| D-78 | Task event table structure: dedicated `task_events` vs. alongside `audit_events` | Open | P5-11 | | | 04.19.15 |
| D-79 | Per-task sequence number for deterministic timeline ordering | Open | P5-11 | | | 04.19.15 |
| D-80 | Retention periods: task history, security audit events, operational logs | Open | P5-11 | | | 04.19.15 |
| D-81 | Replay workflow in P5 MVP: Mode A only vs. enabling Mode B (diagnostic) | Open | P5-10 | | | "Mode A is essential for MVP; Mode B recommended next" (04.19.07) |
| D-82 | Document change detection strategy: re-read per task vs. metadata check vs. fingerprint | Open | P5-13 | | | "Choose simplest strategy that meets accuracy requirements" (03.33.11) |
| D-83 | Context-resolution order implementation for follow-up requests and ambiguity policy | Open | P5-16 | | | "Proposed resolution order, not final" (03.38.9) |
| D-84 | CLI error wording and exit-code finalization aligned with shared error catalogue | Open | P5-06, P5-17 | | | "Exact numeric assignments remain open" (03.16.12); extends D-35 |
| D-85 | Designated host LAN address: static DHCP reservation vs. stable local hostname vs. other | Open | P6-07 | | | "Team should select the simplest reliable option" (03.22.11) |
| D-86 | TLS for LAN communication: required now vs. defer if network is genuinely trusted and isolated | Open | P6-16 | | | "If credentials and sensitive data cross a network where interception is a concern, use properly configured TLS" (03.22.08) |
| D-87 | Device sharing for P6 MVP: owner-only or explicit grant model | Open | P6-08 | | | Docs provisional: "owner-only unless an explicit device-sharing feature is designed and tested" (03.37.4, 03.22.06) |
| D-88 | PostgreSQL row-level security: application-only authorization vs. RLS as defense-in-depth | Open | P6-06 | | | "Do not claim database-enforced isolation unless it has been configured and tested" (03.37.7) |
| D-89 | Startup and shutdown documented procedure: exact service order and health checks | Open | P6-08 | | | "One documented startup and shutdown procedure" (03.22.10) |
| D-90 | Three-user concurrency limits confirmed: per-user active tasks, per-device operations, inference concurrency | Open | P6-11 | | | "Finalize after benchmarking three-user workload" (03.28.05, 04.12.05); extends D-60 |
| D-91 | Shared project memory for P6: defer to P7 or explicitly out of MVP scope | Open | P6-06 | | | Docs: "safer choice is to keep personal memory private and defer shared project memory" (03.37.5) |
| D-92 | Priority aging: implement in P6 or defer until starvation tests show a need | Open | P6-14 | | | "Implement priority aging only if tests show that chosen priority classes can starve lower-priority work" (03.28.06) |
| D-93 | PostgreSQL-backed scheduler vs. separate broker: decision point after P6 load tests | Open | P6-15 | | | "Consider a separate broker only when measurements demonstrate PostgreSQL coordination is no longer adequate" (03.28.09, 04.12.10) |
| D-94 | Bridge local persistence for operation outcomes: SQLite vs. in-memory vs. other | Open | P6-13 | | | "Whether the bridge will persist operation outcomes in a local SQLite database or use another durable mechanism remains open" (03.22.09) |
| D-95 | CI platform and provider: GitHub Actions or alternative within zero-budget constraint | Open | P7-01, P7-14 | | | "The specific CI provider and deployment automation tool remain open decisions" (04.22.2); extends D-21 |
| D-96 | Windows runner for native bridge tests: hosted runner vs. self-hosted within zero-budget; what tests run if unavailable | Open | P7-01, P7-14 | | | "Can the selected platform provide an appropriate native Windows runner within the zero-budget constraint?" (04.22.17 question 2) |
| D-97 | RPO target: maximum acceptable data loss in time, based on actual use and zero-budget infrastructure | Open | P7-02, P7-10 | | | "Must reflect how often the team uses NEXUS, how costly task-history loss would be" (04.25.2) |
| D-98 | RTO target: time to restore a defined level of service after a disaster, based on measured restore time | Open | P7-02, P7-10 | | | "Recovery time and data loss should be measured during exercises before committing to targets" (04.25.10) |
| D-99 | Backup storage location: another authorized team machine, encrypted external drive, or other zero-budget option | Open | P7-02, P7-10 | | | "A backup stored only on the designated host does not protect against loss of that host" (04.25.3) |
| D-100 | Backend packaging: Python package or container image for initial team deployment | Open | P7-03, P7-15 | | | "Choose the simplest format that can be installed and upgraded reliably in the actual environment" (04.23.2) |
| D-101 | CLI and bridge packaging: Python app or standalone executable for P7 MVP | Open | P7-03, P7-15 | | | "A standalone executable can be considered later" (04.23.2) |
| D-102 | Version scheme for applications, protocols and tools; what counts as a breaking change per component | Open | P7-03, P7-15 | | | "Semantic versioning is a candidate; team must document what counts as a breaking change for each component" (04.23.3) |
| D-103 | Upgrade and rollback: which updates require a maintenance window or draining active work; which recovery actions require a manual operator | Open | P7-16 | | | 04.23.16 questions 8 and 9 |
| D-104 | Bridge distribution and upgrade procedure for the three computers | Open | P7-17 | | | 04.23.16 question 6; extends D-39 |


---

## 4. Open questions from the documentation

Source: Product Vision §1.7. Do not treat any as decided.

| ID | Question | Planned phase | Status | Answer / link |
|---|---|---|---|---|
| PC-01 | Must NEXUS work when disconnected from the shared backend? | P1 | Open | |
| PC-02 | Where do backend, PostgreSQL and model runtime run? | P0 | Open | |
| PC-03 | Local model per PC vs shared inference? | P4 | Open | |
| PC-04 | How do users authenticate in the MVP? | P1 | Open | |
| PC-05 | Default permitted directories and applications? | P1–P3 | Open | |
| PC-06 | Which actions run automatically vs need approval? | P3 | Open | |
| PC-07 | Task behaviour if the target PC goes offline? | P3 | Open | |
| PC-08 | What context is shared across devices? | P4 | Open | |
| PC-09 | Real GPU, disk and RAM of the machines? | P0 | Open | |
| PC-10 | Which document formats does the MVP support? | P5 | Open | |

---

## 5. Gate checklist

Source: Consolidated Plan 04.28.05. A gate is passed only with repeatable tests.

| Gate | After phase | Required (summary of the docs) | Passed |
|---|---|---|---|
| Gate 1 | P1 | Shared identifiers and task/step states · API and bridge message contracts · initial tool schemas and error catalogue · DB migration workflow · hardware inventory started and AI validation owner assigned | `[ ]` |
| Gate 2 | P2 | Authenticated task submission, persisted, task ID returned · bridge receives authenticated operation · scoped file search returns structured result · result and state persisted and visible in CLI · duplicate-submission and unauthorized-device tests pass | `[ ]` |
| Gate 3 | P3 | Tool policy + approval enforcement · safe file creation, no silent overwrite · operation dedup + recovery rules · cancellation + disconnection behaviour · tests for lost responses and uncertain outcomes | `[ ]` |
| Gate 4 | P4 | Validated local runtime and model, or documented blocker + tested fallback · structured plans + application-side validation · user-scoped memory and retrieval · prompt-injection and unsupported-action tests · evidence-grounded summaries, honest failures | `[ ]` |
| Gate 5 | P6 | Three registered users/devices · cross-user/device isolation · concurrent task tests · restart/disconnect/recovery · reproducible setup | `[ ]` |
| Gate 6 | P7 | Full acceptance suite · no unresolved critical/high security defects · backup restoration + upgrade/recovery rehearsal · measured performance and model quality · docs · explicit team sign-off | `[ ]` |

---

## 6. MVP acceptance checklist (15 items)

Source: Final Architecture Decision Closure 04.27.06. Ticking here does not run a test — tick only with test evidence.

| # | Item | Phase(s) | Done |
|---|---|---|---|
| 1 | Authenticated users and private user data | P1–P2 | `[ ]` |
| 2 | Device registration, ownership and revocation | P1–P2 | `[ ]` |
| 3 | Terminal CLI for requests, status, history, approval, cancellation | P2–P5 | `[ ]` |
| 4 | Durable task and step lifecycle with duplicate-submission protection | P1–P2 | `[ ]` |
| 5 | Authenticated native Windows bridge | P2 | `[ ]` |
| 6 | Registered tool catalogue and independent bridge-side validation | P3 | `[ ]` |
| 7 | Scoped file search and supported document reading | P2, P5 | `[ ]` |
| 8 | Safe file creation in an approved workspace, no silent overwrite | P3 | `[ ]` |
| 9 | Allowlisted application launching | P3 | `[ ]` |
| 10 | Risk-based permissions and operation-bound approvals | P3 | `[ ]` |
| 11 | Operation journals, bounded retries, uncertain-outcome recovery | P3 | `[ ]` |
| 12 | Local AI planning with structured-output validation | P4 | `[ ]` |
| 13 | Explicit user-controlled memory and relevant context retrieval | P4 | `[ ]` |
| 14 | Three-user integration, logs, diagnostics, protected backups | P6–P7 | `[ ]` |
| 15 | Installation, upgrade, recovery and testing documentation | P0, P7 | `[ ]` |

> The phase column is **my mapping** from the plan, not stated in the documents. Adjust it if you disagree.

---

## 7. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 | Full 15-item MVP vs 12 weeks, beginner/intermediate Python | To assess | High | Decide cut order before it is needed; gates require evidence | All | Open |
| R-02 | AMD GPU/runtime incompatible; local AI shape changes | Unknown | High | P0 smoke test; docs' CPU fallback | C | Open |
| R-03 | Single host is a single point of failure | Likely | High | Backups, runbooks, consider Option B | All | Open |
| R-04 | Role rotation adds ramp-up cost | Likely | Medium | Pairing at every hand-off | All | Open |
| R-05 | WSL networking blocks LAN access | Unknown | High | P0 Step 11 early test | A+B | Open |
| R-06 | Free GitHub plan may not enforce branch protection | Unknown | Low | Team agreement + PR template | A | Open |
| R-07 | 16 GB host shared by WSL, PostgreSQL, backend, model | Unknown | High | Baselines in P0; measure in P4 | C | Open |
| R-08 | Setup instructions only work for their author | Likely | Medium | Clean-clone check by another developer | B,C | Open |

"Likelihood: To assess/Unknown" is deliberate — I have no evidence to rate these.

---

## 8. Carried-over items

Items P0 could not finish. Each needs an owner and a target phase.

| Item | From | Owner | Target phase | Status |
|---|---|---|---|---|
| Full Baseline 2 (backend + PostgreSQL + small workload) | P0-10d | C | P2 (after an API exists) | `[ ]` |
| Host-readiness sections 3–6 (benchmark, combined workload, decision, approval) | P0-10e / 12 | C→A | P4 | `[ ]` |
| Permanent firewall rules for real service ports | P0-11 | A | P6 | `[ ]` |
| Shared integration database | P0-08 | A | P6 | `[ ]` |

---

## 9. Change log

| Date | Change | By |
|---|---|---|
| (fill) | Tracker created with P0 detail | |
| (fill) | P1 detail added: section 2b, D-09..D-22, Gate 1 criteria | |
| (fill) | P2 detail added: section 2c, D-23..D-39, Gate 2 criteria | |
| (fill) | P3 detail added: section 2d, Gate 3 criteria | |
| (fill) | D-40..D-55 added to decision register (P3 decisions) | |
| (fill) | P4 detail added: section 2e, D-56..D-70, Gate 4 criteria; P4 dashboard row set to written | |
| (fill) | P5 detail added: section 2f, D-71..D-84, Gate 5 criteria (P5 contribution); P5 dashboard row set to written | |
| (fill) | P6 detail added: section 2g, D-85..D-94, Gate 5 exit criteria; P6 dashboard row set to written | |
| (fill) | P7 detail added: section 2h, D-95..D-104, Gate 6 exit criteria; P7 dashboard row set to written | |

