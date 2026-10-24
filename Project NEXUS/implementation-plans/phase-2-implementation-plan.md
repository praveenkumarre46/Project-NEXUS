# Phase 2 (First Vertical Slice) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-2-first-vertical-slice.md`](../roadmap/phase-2-first-vertical-slice.md) (Steps 0–31) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2c (P2-00 … P2-31). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal (Gate 2): a user submits a file-search request in the terminal. NEXUS persists a task, routes it to the **explicitly selected** Windows device, searches **only an approved directory**, records the result and shows it. Planning is **deterministic; there is no live AI**.

The 9-step flow (04.06): CLI submits request, target device and client request ID → FastAPI authenticates and validates → PostgreSQL persists the task and enforces idempotency → orchestrator claims the task and prepares a registered search operation → policy engine validates ownership, device, tool and directory scope → Windows bridge authenticates and validates local restrictions → filesystem tool searches only the configured test directory → PostgreSQL persists the step outcome and final status → CLI shows task ID, summary and any error.

Decisions settled here: D-23 to D-39. Owners are assigned by the team (suggested rotation: BE = Dev C, WB = Dev A, AI = Dev B). Auth, authorization, filesystem and recovery changes need a non-author security review.

Excluded from Phase 2: live AI, semantic memory, document summarization, file creation and application launching (Phase 3), approval flow, GUI automation, broad multi-step plans, unrestricted commands. The docs' 12-day schedule (04.07.11) is an estimate, not a commitment. If bridge transport, device authentication or recovery design is unresolved, the milestone is extended instead of bypassing boundaries.

Conventions: `/v1` routes; state names from 03.29; unresolved wire casing (D-23) and envelope names (D-24) are settled in Sub-Task 2.

---

## Sub-Tasks

### Sub-Task 1: Entry check and learning blocks (Steps 0–5)
- **Intent**: Confirm Phase 1 delivered what Phase 2 needs and give every developer the background for the vertical slice.
- **Expected Outcomes**:
  - Phase 1 outputs present, blocking ADRs settled, at least two Windows PCs with a native bridge environment (blocks P2-06 onward).
  - Each developer completes learning blocks: FastAPI service layering; PostgreSQL idempotency, claims and fencing; native Windows Python, paths, links and TOCTOU (Windows parts on real Windows); failure thinking, reconciliation and fault injection; building a CLI.
- **Todo List**:
  - [ ] Run the entry check (P2-00).
  - [ ] Each developer completes the five learning blocks (P2-01 to P2-05).
- **Relevant Context**:
  - Roadmap Steps 0–5; tracker P2-00 … P2-05
- **Status**: `[ ] pending`

---

### Sub-Task 2: Contract confirmation, gap fixes and early ADRs (Steps 6, 7; D-23 to D-26, D-34, D-27 to D-33 and D-35 to D-39 stubs)
- **Intent**: Fix the cross-document inconsistencies in the contracts before code depends on them, and turn open decisions into Provisional ADRs.
- **Expected Outcomes**:
  - D-23 (status casing on the wire; 03.16 and 03.9 use lower-case, 04.08 upper-case; map once at the API boundary), D-24 (envelope field names; the final envelope carries both a stable `operation_id` and a new `attempt_id` per attempt), D-25 (error-code reconciliation of the 15-code catalogue, the 11 filesystem codes in 03.32 and the 03.9 categories; codes nothing in Phase 2 emits are deferred), D-26 (logical directory IDs for tests, e.g. `nexus_test_documents`; same ID on every PC, different path) are each recorded as an ADR with the contract change and a CHANGELOG entry.
  - PC-05 answered for Phase 2: one read-only test directory per PC.
  - Task-submission contract confirmed against the six 04.06 validation rules. Duplicate-submission contract confirmed (same ID and normalized request returns the existing task; same ID with different request or device returns a stable conflict; concurrent duplicates arbitrated by a database constraint; an API timeout does not prove rejection). "Normalized request" is defined. Storing a hash of the normalized request is suggested.
  - Lifecycle contract confirmed against the Phase 1 state machine. Partial success is a result classification, not a state.
  - `search_files` contract confirmed: `directory_id`, bounded `query`, bounded `max_results`; results with stable result ID, display name, path relative to the logical directory, size, mtime, per-entry status and a `truncated` flag. No absolute paths to the backend or AI.
  - Shared fixtures (valid requests, invalid arguments, authorization failures, failure scenarios) and configuration setting names listed (names only, no defaults). Bridge transport details, dependency versions and Open DB field types are not frozen.
  - Baseline tagged (suggested `contracts-v0.2`) after the Phase 1 change process.
  - ADR for D-34 (CLI framework and HTTP client; criteria: beginner-friendly, subcommands, testable, no hidden global state). ADR stubs with status **Open** for D-27 to D-33 and D-35 to D-39, with the question, the docs' position, evidence needed, owner and the step that settles it. Tracker decision register updated.
- **Todo List**:
  - [ ] Resolve D-23, D-24, D-25, D-26 and tag `contracts-v0.2` (P2-06).
  - [ ] Write the D-34 ADR and Open stubs for D-27 to D-33 and D-35 to D-39 (P2-07).
  - [ ] Confirm the six submission rules, duplicate rules, lifecycle and `search_files` contracts each have valid and invalid examples.
- **Relevant Context**:
  - Roadmap Steps 6, 7 and §2; tracker P2-06, P2-07
  - Specs: 04.06, 04.07 WP-01, 03.12, 03.16, 03.9, 03.30, 03.32, 04.08
- **Status**: `[ ] pending`

---

### Sub-Task 3: Persistence, state-transition service and task API (Steps 8–12)
- **Intent**: Task, step, attempt and audit records exist with ownership and ID constraints. Submission and queries work without Windows and without the AI runtime (checkpoint A).
- **Expected Outcomes**:
  - A new migration (never editing the Phase 1 migration) adds missing fields for `tasks`, `task_steps`, `task_step_attempts` and `audit_events`. Constraints: every task has an owner and an explicit target device, a durable initial state, UNIQUE(`owner_user_id`, `client_request_id`). Identity separation: `task_id`, `step_id`, `operation_id` (stable across retries), `attempt_id` (new per attempt), `device_id`, `worker_id`. Claim columns are left out until D-27 is settled in Sub-Task 7. The step stores enough to reconstruct intent. The audit table is append-only in application code. Data-model document and the ER diagram updated.
  - A state-transition service wrapping the pure state machine: loads in a short transaction, asks the pure module, writes the new state and event row, commits. Enforces the 03.9 invariants (every transition persisted before reported, terminal states not reopened, SUCCEEDED only after finished operations and verification, recovery starts from persisted state). Progress is derived from persisted step state.
  - `POST /v1/tasks`: user from the auth context only; validation, owner-only device targeting without leaking other users' devices, a supported-capability lookup, normalization and fingerprint, insert at QUEUED, commit. Acceptance is returned only after the commit succeeds. Duplicates arbitrated by the unique constraint. A queue-full path returns a stable capacity error. Audit rows for accepted, rejected and conflict. No work runs inside the request.
  - Query routes `GET /v1/tasks/{task_id}`, `/steps`, `/result`, `GET /v1/tasks` with progress derived from persisted steps, filtered step bodies, results grounded in recorded operation results that distinguish verified success, partial success, definite failure, cancellation and uncertain. Lists are bounded and paginated (D-37 ADR). Another user's task returns the same response as a non-existent one.
  - Real-PostgreSQL tests: PostgreSQL unavailable during submission (no false acceptance); concurrent same-key submissions leave one row; same key with a different device conflicts; cross-user read denied; illegal transition rejected with nothing persisted; stale-worker update written as `xfail` until Sub-Task 7; backend restart with a queued task. Mutation checks: dropping the unique constraint fails the concurrency test and removing the owner filter fails the cross-user test.
- **Todo List**:
  - [ ] Schema additions via new migration and models (P2-08).
  - [ ] State-transition service (P2-09).
  - [ ] `POST /v1/tasks` with idempotency (P2-10).
  - [ ] Task query routes and pagination ADR D-37 (P2-11).
  - [ ] Persistence integration and failure tests, checkpoint A (P2-12).
- **Relevant Context**:
  - Roadmap Steps 8–12; tracker P2-08 … P2-12
  - Specs: 04.06, 03.10, 03.16, 03.9, 03.15, 04.11.04, 03.30.02
- **Status**: `[ ] pending`

---

### Sub-Task 4: Deterministic planner, proposal validation and tool registry (Steps 13, 14)
- **Intent**: Unsupported or invalid operations are rejected without ever contacting the bridge.
- **Expected Outcomes**:
  - `DeterministicSearchPlanner` next to `MockPlanner`, with explicit supported request forms (suggestion: exactly one form such as `search <term> in <directory_id>`). Anything else returns `UNSUPPORTED` or `CLARIFICATION_REQUIRED`. The planner cannot set `risk_tier`, `approved`, `user_id`, device ownership or permissions; the backend assigns task, step and operation IDs. Policy-override attempts ("search C:\\") never expand scope.
  - Extended validator: schema, tool registered and enabled, schema version supported, argument schema (bounded query, `max_results` within the server maximum), directory ID known and authorized, device owned and eligible, limits within server maxima. Unknown fields rejected at security boundaries.
  - Backend tool registry with `tool_name, schema_version, description, input_schema, output_schema, risk_tier, required_permissions, timeout_policy, retry_policy, enabled`. Only `search_files` is registered (Tier 0). A model cannot register tools or change risk tiers. Capability descriptions limited to relevant registered tools and revalidated at dispatch against the bridge's last report.
  - Invalid-plan fixtures: unknown tool, invalid arguments, scope-expansion attempt, missing arguments, unauthorized device target, excessive `max_results`, malformed proposal. A mock bridge with a call counter proves it is never called for invalid proposals.
- **Todo List**:
  - [ ] Deterministic planner and `search_files` handler (P2-13).
  - [ ] Validator, registry, capability descriptions and invalid-plan fixtures (P2-14).
- **Relevant Context**:
  - Roadmap Steps 13, 14; tracker P2-13, P2-14
  - Specs: 04.06 planner section, 04.07 WP-04, 03.12, 04.08
- **Status**: `[ ] pending`

---

### Sub-Task 5: Windows bridge runtime, `search_files` and journal (Steps 15–17; D-29, D-30, D-31, D-39)
- **Intent**: The native Windows bridge starts under the intended user, validates every operation independently and searches only inside a configured logical directory.
- **Expected Outcomes**:
  - Validated local configuration (backend endpoint, poll interval, directory mapping, logging). The device credential is never in the config file. Directory mapping entries: `directory_id, configured_path, allowed_operations, enabled, limits, configuration_version`, held on the bridge only. Each developer maps the test directory ID to their own folder.
  - D-39 recorded Provisional (Python source vs packaged executable). Startup sequence per 04.21.09 ending in readiness reporting only for validated capabilities. Not run as administrator. Authentication failure means no operations are accepted.
  - Protocol handling validates protocol version, tool name, schema version, target device, arguments, deadline; security-sensitive unknown fields fail closed. Only registered and locally enabled tools run. No generic command endpoint.
  - `search_files` using the 03.32 eight-step validation sequence, never authorizing on a string prefix. MVP path-type rules: UNC denied by default, device namespaces rejected, environment variables not expanded, alternate data streams rejected, reparse points and links not followed. D-30 (path-resolution facilities) is spiked on Windows and recorded Provisional. D-31 limits (depth, results, duration, hidden/system files, query length, cancellation checks) start conservative, are configuration with server maxima, and are measured in Sub-Task 9. Results contain bounded relative-path metadata, a `truncated` flag and per-entry status, with no file contents, no absolute paths and no logging of private paths. Non-author review.
  - Operation journal with D-29 recorded Provisional after a spike (a small local database is only a candidate). Per-operation record and the five repeated-ID cases of 03.30.05 (match, completed, in progress, previously uncertain, mismatching parameters rejected). Restart sequence per 03.30.11. Local records are not authorization. Retention periods stay Open.
  - Windows security tests marked `windows`: the 9 negative tests of 04.06 (three completed after transport exists), the 7 WP-03 failure tests, and the 03.32 groups including sibling-prefix confusion, case, alternate forms and link/junction escapes. Isolated temp directories only. They pass on at least two PCs and fail when a check is deliberately broken.
- **Todo List**:
  - [ ] Bridge configuration, startup, device authentication, protocol handling and tool registry (P2-15).
  - [ ] `search_files` and Windows path safety with D-30 and D-31 ADRs (P2-16).
  - [ ] Operation journal and deduplication with D-29 ADR (P2-17).
  - [ ] Windows security tests on at least two PCs (P2-18).
- **Relevant Context**:
  - Roadmap Steps 15–18; tracker P2-15 … P2-18
  - Specs: 03.32, 03.30.05, 03.30.11, 03.12, 04.21.09, 04.06, 04.07 WP-03
  - Native Windows, not WSL.
- **Status**: `[ ] pending`

---

### Sub-Task 6: Bridge transport integration (Step 19, D-32)
- **Intent**: Replace the Phase 1 "no work" poll with real delivery, acknowledgement and result submission with correlation (checkpoint B).
- **Expected Outcomes**:
  - Routes under `/v1/bridge/`: `session`, `heartbeat`, `poll`, `capabilities`, `operations/{id}/ack`, `operations/{id}/result`, and `GET operations/{id}` for reconciliation. Device-facing routes stay separate from user routes.
  - Poll returns only operations for the authenticated device whose dispatch intent is persisted. Result carries `operation_id, attempt_id, device_id, protocol_version, status, error_code, bounded result_summary, evidence, started_at, finished_at`.
  - Backend validates device, operation and attempt ownership; mismatches are rejected and the discrepancy is recorded. Transport timeout is distinct from tool failure (dispatch, execution and result-recording timeouts map to different recovery paths).
  - D-32 recorded with measurements over the LAN topology (poll interval, request timeout, heartbeat interval, deadline representation). Polling stays Provisional.
  - Phase 1 bridge scenarios marked "P2" run (delivery, ack, result, lost response, revoked device, duplicate delivery).
  - Checkpoint B: the operation reaches the correct bridge and an unauthorized target is rejected. A wrong device cannot fetch or post a result for another's operation; duplicate result posts are idempotent.
- **Todo List**:
  - [ ] Implement poll, ack, result and operation-status routes with correlation (P2-19).
  - [ ] Measure and record D-32.
  - [ ] Run the Phase 2 bridge integration scenarios.
- **Relevant Context**:
  - Roadmap Step 19; tracker P2-19
  - Specs: 04.10, 03.12, 03.30, 03.16
- **Status**: `[ ] pending`

---

### Sub-Task 7: Orchestrator — worker, claim, lease, fencing, dispatch pipeline and recovery (Steps 20–22; D-27, D-28, D-33)
- **Intent**: Exactly one worker progresses a task, a stale worker cannot overwrite newer state, uncertain operations are never blindly replayed, and no transaction waits on an external call.
- **Expected Outcomes**:
  - Worker logic separate from HTTP handlers, initially in-process. D-27 (claim fields on the task row vs a separate table) decided after a spike with a migration. Atomic claim verified by affected-row count; generation incremented on every claim; every state-changing path checks the fencing token. D-28 (lease duration, heartbeat interval, renewal) set conservatively and Provisional until measured. Lease expiry is never treated as proof that no side effect occurred. The `xfail` stale-worker test is un-marked and passes.
  - Eligibility separated from capacity. A task waiting for an offline device never holds a worker slot and is never rerouted.
  - Dispatch pipeline per 04.11.07 and 03.30.03: claim → load authoritative data → deterministic proposal → validation → recheck authorization and policy → persist operation intent and commit → dispatch via poll → record ack and result → verify identity, correlation and in-scope results → persist through legal transitions. SUCCEEDED only after a valid, correlated result and successful persist. No generic handler that marks every error FAILED; worker error classification per 04.11.07. D-33 (timeout, retry, backoff for `search_files`) recorded. Retries keep `operation_id` and get a new `attempt_id`.
  - Recovery: backend-restart recovery (7 steps), crash-point matrix (before commit, after commit before execution, after intent before dispatch, after dispatch before response, after execution before persistence, after persistence before client receives it, while awaiting approval — Phase 3), reconciliation protocol (7 steps), device-disconnect handling. A fault-injecting fake transport can drop, delay or duplicate a response and fail a DB write. The 14 scenarios of 04.11.11 and 14 scenarios of 03.30.13 are each run, or listed as not applicable with the phase that covers them (approval to Phase 3, restore to Phase 7). `docs/testing/p2-failure-matrix.md` records pass, fail or not-applicable per row.
  - Checkpoint C: submit → worker → bridge → persisted SUCCEEDED → `GET` shows results. Tests assert real state, not only HTTP status.
- **Todo List**:
  - [ ] Worker, atomic claim, lease and fencing with D-27, D-28 ADRs (P2-20).
  - [ ] Dispatch pipeline with persisted intent and D-33 (P2-21).
  - [ ] Recovery, reconciliation and fault-injection suite; failure matrix (P2-22).
- **Relevant Context**:
  - Roadmap Steps 20–22; tracker P2-20, P2-21, P2-22
  - Specs: 04.11, 03.15.05, 03.15.07, 03.15.08, 03.30.03, 03.30.06, 03.30.08, 03.30.10, 03.30.13
- **Status**: `[ ] pending`

---

### Sub-Task 8: Cancellation and admission control (Steps 23, 24; D-18, D-38)
- **Intent**: Users can request cancellation without the system ever claiming a cancel that did not happen, and the shared backend answers "queue full" honestly.
- **Expected Outcomes**:
  - D-18 reused or settled for how a cancel request is represented. `POST /v1/tasks/{id}/cancel` responds "cancellation requested", which is not a durable state. Behaviour per 03.15.06 (queued, running before dispatch, in-progress, uncertain, already completed). The task becomes CANCELLED only after execution is known to have stopped or not to proceed. The worker checks for cancellation before every dispatch. `search_files` mid-run cancellation support is stated in the tool contract. Tests: cancel queued, cancel racing dispatch, cancel after completion keeps results, other user's cancel denied.
  - Limits as validated configuration: maximum active claims, per-user active tasks, per-device operations, DB connection pool, queue size. Admission control separate from execution scheduling. Fairness baseline of round-robin by user, kept simple until the multi-user test shows starvation. D-38 ADR records what was measured. Tests: capacity error, burst does not starve a second user, per-device limit respected, limits validated at startup.
- **Todo List**:
  - [ ] Minimal cancellation request (P2-23).
  - [ ] Admission control, limits and fairness with D-38 ADR (P2-24).
- **Relevant Context**:
  - Roadmap Steps 23, 24; tracker P2-23, P2-24
  - Specs: 03.15.06, 04.11.06, 04.11.08, 04.11.09
- **Status**: `[ ] pending`

---

### Sub-Task 9: CLI and observability (Steps 25–27; D-35, D-36, D-37)
- **Intent**: A CLI that treats itself as untrusted, shows honest status, and a way to explain any failure from persisted records.
- **Expected Outcomes**:
  - CLI package in `apps/cli/` using the D-34 library and importing contract types only. Commands per spec 03.16 and 04.09: `nexus login`, `nexus logout`, `nexus devices`, `nexus status`, `nexus run "<request>" --device <id>`, `nexus task <id>` with `--steps`, `--result`, `--watch`, and `nexus history`. Cancellation is exposed as `nexus task <id> --cancel` per 03.16. Roadmap Step 26 and tracker P2-26 name it `nexus cancel <id>`. The command name is confirmed with the team and the discrepancy is recorded. Approve, reject and memory commands are not built here.
  - D-35 ADR (token storage, exit codes, watch interval, output conventions). Credentials never in URLs, logs or terminal output; logout invalidates server-side. Distinct stable exit codes for success, accepted-but-running, and failure. Human-readable default; machine mode is `--output json` with only valid JSON on stdout and diagnostics on stderr (D-75 is still open; confirm the flag with the team). Explicit device target (D-36), shown if defaulted and overridable; an offline device is reported and never rerouted. The task ID is printed only after durable acceptance, with a retry path using the same `client_request_id` on timeout. Interrupting `--watch` does not cancel the task and says so. Uncertain is never rendered as success or plain failure.
  - Observability: correlation chain `request_id → task_id → step_id → operation_id → attempt_id` on logs and rows; state transitions, timeouts, error codes and recovery decisions recorded; never log passwords, credentials, document contents or unnecessary paths; a no-secrets-in-logs test for submission, bridge poll and result; a diagnostic that prints a task's chain; only the `nexus diagnostics` parts needed for the Gate 2 troubleshooting guide. Field names are reconciled with spec 03.19 (Logging, Observability and Operational Diagnostics) before finalizing.
  - Tests with a fake backend and golden-file JSON tests.
- **Todo List**:
  - [ ] CLI foundation: login, logout, devices, status, token storage (P2-25).
  - [ ] CLI task commands: run, task, steps, result, watch, cancel, history (P2-26).
  - [ ] Observability, audit and the no-secrets-in-logs test (P2-27).
- **Relevant Context**:
  - Roadmap Steps 25–27; tracker P2-25, P2-26, P2-27
  - Specs: 03.16, 04.09, 03.19, 04.11.10, 04.21.14
- **Status**: `[ ] pending`

---

### Sub-Task 10: End-to-end over the LAN, acceptance matrix, three-user scenario (Steps 28–30)
- **Intent**: Prove the whole slice on the intended topology, close all 15 acceptance scenarios and 9 negative tests, and record everything honestly.
- **Expected Outcomes**:
  - End-to-end on at least two Windows PCs over the LAN using the Phase 0 networking mode (D-05), without broad firewall rules. Fixed 04.21.04 order (repository, dependencies, PostgreSQL, backend, bridge install, device enrollment, smoke test). The smoke test runs a permitted read-only search on the designated directory and confirms cross-user and cross-device access is denied.
  - Measurements recorded in `docs/operations/p2-measurements.md`: poll round trip and idle load, search duration against tree size, lease against operation time, DB connection use, CPU and memory of backend, PostgreSQL and bridge. These settle D-28, D-31, D-32, D-33 and D-38. Phase 0's "Full Baseline 2" is completed.
  - Acceptance matrix of 15 scenarios from 04.06 (valid search; same ID and payload; same ID changed payload; unauthenticated; unauthorized device; unknown tool; invalid directory scope; bridge offline before dispatch; response lost after dispatch; backend restart with a pending task; two workers claim one task; cross-user read; excessive matches; model runtime unavailable; PostgreSQL unavailable) each with a passing automated test or dated manual result, in `docs/testing/p2-acceptance.md`. The row order is checked against 04.06 before relying on numbers. All 9 negative tests closed.
  - Three-user scenario (checkpoint E): concurrent tasks, isolation, a burst that does not stop the others; the report states how many Windows PCs were used.
  - Clean-setup reproduction by a developer who did not write the instructions. Release evidence report in `docs/releases/p2-evidence.md`: commit and migration versions, environment and dependency versions, test results, Windows bridge results, multi-user results, known defects, unresolved decisions, untested scenarios. Troubleshooting guide by layer and stable error code. Milestone sign-off checklist from 04.07. Any critical or high security issue blocks sign-off.
- **Todo List**:
  - [ ] End-to-end on two Windows PCs plus measurements and Baseline 2 (P2-28).
  - [ ] Complete the 15-scenario acceptance matrix and 9 negative tests (P2-29).
  - [ ] Three-user scenario, clean-setup reproduction and release evidence report (P2-30).
- **Relevant Context**:
  - Roadmap Steps 28–30; tracker P2-28, P2-29, P2-30
  - Specs: 04.06, 04.07, 04.21.04, 04.21.05, 04.21.12, 04.21.13
- **Status**: `[ ] pending`

---

### Sub-Task 11: Security review, Gate 2 review and hand-off (Step 31)
- **Intent**: Pass Gate 2 on repeatable tests and prepare Phase 3.
- **Expected Outcomes**:
  - A non-author security review of authentication, authorization, filesystem and recovery changes. Checklist: no client-supplied authority fields, no absolute paths leave the bridge, no secrets in logs, bodies or DB, all device routes authenticate and are device-scoped, unknown fields fail closed, errors do not leak other users' existence, no path marks SUCCEEDED without a correlated persisted result, no path blindly retries an uncertain operation. Findings recorded by severity. Critical and high defects fixed first.
  - Gate 2 checklist (tracker P2 exit criteria) satisfied, including: authenticated task submission persisted; bridge receives an authenticated operation; scoped search returns a structured result; result visible in the CLI; duplicate-submission and unauthorized-device tests; idempotency under concurrency on PostgreSQL; planner produces only a registered search operation; search stays in scope on two PCs; duplicate-delivery, disconnection and lost-response tests; recovery never repeats an uncertain operation; cross-user and cross-device tests; LAN topology; non-author reproduction; all 15 acceptance and 9 negative tests; D-23 to D-39 recorded; full Baseline 2.
  - Tracker updated (P2 rows, decisions, risks, carried-over items, MVP checklist items only with test evidence). Hand-off pairing and retrospective held.
  - Phase 3 entry list: approval flow and risk tiers, `create_file` and `launch_application` contracts, bridge journal hardening, automated reconciliation, dedup retention, full cancellation and disconnection behaviour, PC-06 and PC-07, deferred items.
- **Todo List**:
  - [ ] Security review and findings by severity.
  - [ ] Run the Gate 2 review (P2-31).
  - [ ] Update the tracker, write the Phase 3 entry list, hold hand-off and retrospective.
- **Relevant Context**:
  - Roadmap Step 31 and §5; tracker P2-31 and Gate 2 exit criteria
  - Specs: 04.07 review rules, 04.28.05
- **Status**: `[ ] pending`
