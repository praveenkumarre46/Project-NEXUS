# Phase 1 (Contracts & Persistence) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-1-contracts-persistence.md`](../roadmap/phase-1-contracts-persistence.md) (Steps 0–26) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2b (P1-00 … P1-26). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal (Gate 1): one agreed vocabulary and one set of message shapes, a database created from scratch by a migration, a minimal authenticated API, a bridge that can enroll and stay connected, and a mock planner. Everything is covered by tests so Phase 2 can build the first vertical slice without arguing about shapes.

Phase 1 is **not**: end-to-end task submission, a CLI, real file search, a real model, approvals or file writing.

Decisions settled here: D-09 to D-22. Owners are assigned by the team (suggested rotation: BE = Dev B, WB = Dev C, AI = Dev A). Security-sensitive work (authentication, authorization, device credentials) must be reviewed by someone who is not the author.

Conventions that apply to every sub-task:
- Task states: `QUEUED, RUNNING, WAITING_FOR_APPROVAL, INTERRUPTED` (active); `SUCCEEDED, FAILED, CANCELLED` (terminal). `PARTIALLY_SUCCEEDED` must not be added (04.08.06, 03.29).
- Step states: `PENDING, READY, WAITING_FOR_APPROVAL, DISPATCHED, RUNNING, SUCCEEDED, FAILED, REJECTED, UNCERTAIN, CANCELLED`. `DISPATCHED` is not `RUNNING`. `UNCERTAIN` is not `FAILED` and is not a task state.
- API routes use the `/v1` prefix.
- Wire casing of states (D-23) and envelope field names (D-24) stay open. Phase 1 records them as drafts and Phase 2 settles them.
- Contract folders are `contracts/{api,bridge,tools,events}`. Test folders are `tests/{unit,integration,contract,security,reliability,end_to_end}`.

---

## Sub-Tasks

### Sub-Task 1: Entry check and learning blocks (Steps 0–6)
- **Intent**: Confirm Phase 0 delivered what Phase 1 needs, and give every developer the minimum background for the work.
- **Expected Outcomes**:
  - P0 outputs verified: repo, skeleton, D-01 to D-03 settled, hardware inventory started, an AI-validation owner named (blocks P1-07 and P1-15).
  - Each developer has completed the six learning blocks: HTTP/REST/JSON and the five contract layers; SQL, constraints, transactions and row locks; typed validation; pytest fixtures, parametrize and contract tests; passwords, hashing, tokens and credentials; FastAPI essentials.
- **Todo List**:
  - [ ] Run the entry check (P1-00).
  - [ ] Each developer completes learning blocks 1–6 (P1-01 to P1-06).
  - [ ] Name the AI-validation owner.
- **Relevant Context**:
  - Roadmap Steps 0–6; tracker P1-00 … P1-06
- **Status**: `[ ] pending`

---

### Sub-Task 2: Dependency and format decisions (Step 7, D-09, D-10, D-11, D-12, D-15)
- **Intent**: Settle the library and format decisions and record them as ADRs, each with an honest status.
- **Expected Outcomes**:
  - ADRs for D-09 (identifier format; opaque, no embedded permissions, UUID or another format), D-10 (typed-validation approach and unknown-field behaviour per boundary; Pydantic is a candidate), D-11 (database access library and migration tool; SQLAlchemy and Alembic are candidates), D-12 (FastAPI confirmation) and D-15 (password hashing library and parameters).
  - Dependencies added to `pyproject.toml` with a lock file. The version matrix is updated. One dependency PR is merged.
- **Todo List**:
  - [ ] Write ADRs for D-09, D-10, D-11, D-12, D-15 (P1-07a to P1-07e).
  - [ ] Merge the dependency PR with the lock file and update the version matrix (P1-07f).
- **Relevant Context**:
  - Roadmap Step 7 and §2 decision table; tracker P1-07a … P1-07f
  - Specs: 04.08.13 (open decisions), 04.09
- **Status**: `[ ] pending`

---

### Sub-Task 3: Canonical vocabulary and error catalogue (Step 8, D-19)
- **Intent**: One place defines the words every layer uses.
- **Expected Outcomes**:
  - A shared vocabulary document in `contracts/README.md` (or `docs/architecture/vocabulary.md`, wherever D-07 put the specs).
  - Identifiers: `user_id, device_id, task_id, step_id, operation_id, attempt_id, request_id, client_request_id, approval_id, policy_version`. For each: who creates it, where it is stored, which layers may see it. Rules: opaque, never encode permissions, never proof of authority.
  - Timestamps are UTC, ISO 8601.
  - Planner outcomes: `PROPOSED, CLARIFICATION_REQUIRED, UNSUPPORTED`. Bridge response statuses: `SUCCEEDED, FAILED, REJECTED, RUNNING, UNCERTAIN`.
  - Error catalogue of the 15 codes in 04.08.09: `INVALID_ARGUMENT, AUTHENTICATION_REQUIRED, ACCESS_DENIED, POLICY_DENIED, APPROVAL_REQUIRED, APPROVAL_EXPIRED, DEVICE_UNAVAILABLE, DEPENDENCY_UNAVAILABLE, CONTRACT_VERSION_UNSUPPORTED, OPERATION_TIMEOUT, OPERATION_OUTCOME_UNCERTAIN, FILE_NOT_FOUND, FILE_ALREADY_EXISTS, FILESYSTEM_SCOPE_DENIED, INTERNAL_ERROR`.
  - Each code has: emitter, terminal or not, whether retry is meaningful, recovery procedure, and a user-facing message that reveals nothing sensitive. Cell values come from the 04.08.09 table, not from invention. Codes proposed elsewhere (03.32 filesystem codes, `DEVICE_OPERATION_FAILED`) are listed as D-25 reconciliation items, not silently added.
  - Rule: errors are typed, stable codes, not exception text. A separate list of internal-only details (stack traces, SQL) that must never reach a client.
- **Todo List**:
  - [ ] Write the identifiers and timestamps section.
  - [ ] Write the enum sections (planner outcomes, bridge statuses).
  - [ ] Write the error catalogue with all five columns filled from 04.08.09 (P1-08).
  - [ ] Reviewer from a different stream approves.
- **Relevant Context**:
  - Roadmap Step 8; tracker P1-08
  - Specs: 04.08.04, 04.08.09, 04.08.06
- **Status**: `[ ] pending`

---

### Sub-Task 4: Task and step state-machine contract (Step 9, D-18)
- **Intent**: Fix the legal states and transitions in one pure piece of logic used by both the database layer and the API.
- **Expected Outcomes**:
  - The transition table copied verbatim from 03.29.04 (17 rows) into the contract documentation, together with the step-level table and the six forbidden transitions: `SUCCEEDED`/`FAILED` → `RUNNING`; `CANCELLED` → `QUEUED`; `WAITING_FOR_APPROVAL` → `SUCCEEDED` without execution; `INTERRUPTED` → `SUCCEEDED` without reconciliation; any state → `SUCCEEDED` on a model or bridge claim alone; any state → `CANCELLED` while an external effect is unresolved.
  - Principles recorded: persist before dispatch; unknown is a valid outcome; transitions are centralized; a transition and its event commit in one transaction.
  - `nexus_core/domain/state_machine.py` is pure Python with no database, HTTP or framework imports. It answers whether a transition is allowed and gives the reason when forbidden.
  - Tests cover every allowed transition, every forbidden transition and every state pair not in the table (generated with parametrize). Each of the six forbidden rules has a named test.
  - ADR for D-18 (Provisional): what "interrupted" means, what happens at approval expiry, and whether "cancel requested" is a separate field or a state. A separate field keeps the state list exactly as the docs state it (suggestion; the team decides).
- **Todo List**:
  - [ ] Copy the 03.29 transition tables into the contracts (P1-09a).
  - [ ] Implement `state_machine.py` and the full matrix tests (P1-09b).
  - [ ] Write the D-18 ADR (P1-09c).
- **Relevant Context**:
  - Roadmap Step 9; tracker P1-09a/b/c
  - Specs: 03.29 (authoritative lifecycle), 04.08.06
  - Known spec conflicts: 04.08 and 03.15 add other state names. Record them as D-23 inputs and follow 03.29.
- **Status**: `[ ] pending`

---

### Sub-Task 5: Public API, planner, bridge and tool contracts (Steps 10–13, D-17, D-19, D-20)
- **Intent**: Define the four message contracts as separate layers with valid and invalid examples.
- **Expected Outcomes**:
  - `contracts/api/`: task submission request (`client_request_id, target_device_id, request`), task acceptance response (`task_id, status=QUEUED, request_id, created_at`), error response (typed code plus `request_id`, provisional per D-19). `user_id` is derived from the session and never accepted from the body. Duplicate `client_request_id` with the same payload returns the existing task; a different payload returns a conflict. Task submission is specified here but implemented in Phase 2.
  - Minimum Phase 1 endpoints identified (login, a protected "who am I" route, device registration). D-20 (payload limits, pagination, older-schema support) is decided or recorded as "Open — revisit at Gate 2". The docs give no numeric values.
  - `contracts/tools/` planner contract: `proposal_version, outcome, objective, target_device_id, steps[]` with `step_id, tool_name, tool_schema_version, arguments, depends_on`. A proposal is advice and is never a bridge command. Invalid cases: unknown tool, malformed or missing arguments, nonexistent dependency, device not owned, injected instructions. Dependency rule (reject cycles) decided.
  - `contracts/bridge/`: operation envelope (`protocol_version, operation_id, attempt_id, task_id, step_id, target_device_id, tool_name, tool_schema_version, arguments, deadline`), response statuses, and proposed routes under `/v1/bridge/`: `session`, `heartbeat`, `capabilities`, `poll`, `operations/{operation_id}/ack`, `operations/{operation_id}/result`, `GET operations/{operation_id}`. Whether a separate session route is needed is decided. ADR D-17 records authenticated outbound polling as **Provisional**. Unsupported `protocol_version` yields `CONTRACT_VERSION_UNSUPPORTED`. Unknown-field behaviour per direction goes into D-10. Numeric polling defaults stay Open.
  - `contracts/tools/` `search_files` plus the generic tool schema header. The backend refers to directories by logical ID only and never sends raw paths. Results are bounded. Tool-result and error payload schemas are drafted as Provisional (D-19). No other tool is specified in Phase 1.
  - Every message has at least one valid and two invalid examples.
- **Todo List**:
  - [ ] Write the public API contract and examples (P1-10).
  - [ ] Write the planner contract and examples (P1-11).
  - [ ] Write the bridge contract and the D-17 ADR (P1-12).
  - [ ] Write the `search_files` and generic tool contract (P1-13).
  - [ ] Each contract is reviewed by the other two developers.
- **Relevant Context**:
  - Roadmap Steps 10–13; tracker P1-10 … P1-13
  - Specs: 04.08.05, 04.08.07, 04.08.08, 04.10, 03.16, 03.12, 03.30, 03.32
  - Open conflicts to record, not resolve: D-23 (status casing), D-24 (envelope names: 03.12 uses `schema_version` and has no `attempt_id`; 04.08 and 03.30 use `tool_schema_version` and `attempt_id`).
- **Status**: `[ ] pending`

---

### Sub-Task 6: Contract-test harness and shared fixtures (Step 14)
- **Intent**: Turn the contract documents into executable enforcement.
- **Expected Outcomes**:
  - One loader discovers example files under `contracts/**/` using the `*.valid-*.json` and `*.invalid-*.json` convention and parametrizes tests over them.
  - Tests cover the 04.08.12 list: public API (valid/invalid requests, duplicate and payload conflict, auth and ownership, stable error structure); lifecycle; planner; bridge (schema validation, operation and attempt correlation, unknown protocol and tool rejection, timeout and uncertain outcome); cross-component fixtures (happy path, authorization denial, disconnected device, lost response and reconciliation). Cross-component fixtures not yet implementable are marked skipped or xfail with the phase that will implement them, never faked as passing.
  - Pytest markers: `unit`, `integration`, `contract`.
  - A test fails if a contract file has no example or an example is not referenced by a test.
  - `pytest -m contract` is green on all three PCs, and a deliberately broken example turns it red.
- **Todo List**:
  - [ ] Build the loader and parametrized tests (P1-14).
  - [ ] Add the "no orphan contract / example" test.
  - [ ] Verify the red/green check on all three PCs.
- **Relevant Context**:
  - Roadmap Step 14; tracker P1-14
  - Specs: 04.08.12, 04.05.08
- **Status**: `[ ] pending`

---

### Sub-Task 7: Migration workflow and initial PostgreSQL schema (Steps 15–17)
- **Intent**: The database can be created from nothing and upgraded by the same reviewed path, and its behaviour is proven on real PostgreSQL.
- **Expected Outcomes**:
  - `migrations/` initialised with the D-11 tool. The connection string lives in configuration, never in migration files.
  - `docs/operations/database.md`: separate dev and test databases with different credentials; tests never touch the shared database; each schema change is a new reviewed migration and merged migrations are never edited; how to create, apply, inspect and (dev only) roll back. The 04.05.06 startup safety checks are read from the spec and listed, not guessed.
  - Initial schema limited to what Phases 1–2 use (suggestion, recorded as a decision): `users, user_sessions` (if D-14 stores sessions), `devices, device_credentials, tasks, task_steps, task_step_attempts, task_events, audit_events`. `approvals` and `memories` wait for Phases 3 and 4.
  - Docs column names reused. Constraints: UNIQUE(`owner_user_id`, `client_request_id`), UNIQUE(`task_id`, `step_number`), UNIQUE(`operation_id`), UNIQUE(`task_step_id`, `attempt_number`). State columns have a CHECK in addition to the Python state machine. Audit-relevant records are not cascade-deleted. Only credential hashes are stored. No full documents, prompts or secrets in task or audit rows.
  - The 10-row open-decisions table at 03.10.11 is copied into the decision register. `docs/architecture/data-model.md` is written.
  - PostgreSQL integration tests on a real test database: each constraint; a state CHECK; user deletion does not delete audit trail; the atomic claim test (two concurrent claims, exactly one wins); duplicate-submission arbitration at the repository layer; restart persistence. Tests never use dev or shared databases.
  - Migrating an empty database to head, and a database at the previous revision to head, both succeed on all three PCs.
- **Todo List**:
  - [ ] Initialise migrations and write `docs/operations/database.md` (P1-15).
  - [ ] Write the initial schema migration and `docs/architecture/data-model.md` (P1-16).
  - [ ] Build the PostgreSQL test fixture and all schema tests (P1-17).
  - [ ] Verify empty-to-head and previous-to-head on all three PCs.
- **Relevant Context**:
  - Roadmap Steps 15–17; tracker P1-15, P1-16, P1-17
  - Specs: 03.10 (data model), 04.05.06, 04.04.08
  - Not SQLite: tests must run on real PostgreSQL.
- **Status**: `[ ] pending`

---

### Sub-Task 8: Authentication, authorization and device enrollment (Steps 18–20, D-13, D-14, D-16)
- **Intent**: Only authenticated users reach protected routes, users see only their own data, and a Windows bridge can be enrolled and later prove its identity.
- **Expected Outcomes**:
  - ADR D-13: local NEXUS accounts (the docs' provisional recommendation; closes PC-04). If the team rejects it, work stops until the team decides. ADR D-14: one coherent token lifecycle (issue, lifetime, revocation, logout). The token format is not named in the docs and is decided here. CLI-side token storage is Phase 2.
  - Controlled initial account creation (an admin command on the host, no open registration, no shared default password). Login uses the D-15 hash, a generic failure message for unknown user and wrong password, rate limiting, and a respected account-disable flag. One protected-route dependency is the only way a route learns the user, otherwise `AUTHENTICATION_REQUIRED`. Client-supplied `user_id`, `device_id`, `risk_tier` and `approved` are never trusted.
  - A test proves no passwords, tokens or raw device credentials appear in logs. Tests: correct login, wrong password, unknown user (same message), disabled account, expired token, revoked token, rate limit.
  - The 04.09 **10-step authorization sequence** implemented as one function in `nexus_core/security/`, with the sequence copied from the spec into its documentation. Repository functions take the authenticated user ID as a required argument. Owner-only device targeting with no information leak. Multi-user tests: user A cannot list, read, target, revoke or enroll against user B's device or read B's tasks. Revocation takes effect on the next request. A mutation check (removing an owner filter) makes a test fail.
  - Device registration separated from authentication. Backend endpoints to register, list and revoke a device. Unique per-device credential, independently revocable, stored only as a hash or verifier. Revocation sets `revoked_at` and does not delete rows. A revoked device does not become trusted by reconnecting. ADR D-16 records the credential format and enrollment handshake as Provisional. Windows credential storage (Windows Credential Manager is a candidate) is verified on a real Windows machine (P1-20c).
  - The 10-row open-decisions table at 04.09.11 is copied into the decision register.
  - All security-sensitive code is reviewed by a non-author.
- **Todo List**:
  - [ ] ADRs D-13 and D-14 (P1-18a, P1-18b).
  - [ ] Users, hashing, login, rate limit, disable flag and protected-route dependency (P1-18c).
  - [ ] Test that secrets are absent from logs (P1-18d).
  - [ ] Authorization sequence function (P1-19a).
  - [ ] Multi-user isolation and revocation tests (P1-19b).
  - [ ] ADR D-16 (P1-20a).
  - [ ] Backend register, list and revoke device (P1-20b).
  - [ ] Verify Windows credential storage on Windows (P1-20c).
- **Relevant Context**:
  - Roadmap Steps 18–20; tracker P1-18a … P1-20c
  - Specs: 04.09, 04.10.03, 03.11 / Authentication, Authorization and Security Model
- **Status**: `[ ] pending`

---

### Sub-Task 9: Bridge enrollment and connectivity prototype (Step 21)
- **Intent**: A minimal Windows-side process that enrolls, authenticates, sends heartbeats, reports capabilities and polls. It does nothing else.
- **Expected Outcomes**:
  - `apps/windows_bridge/` as a plain Python program with a separate transport module and a main loop. It imports contract types only, never backend internals.
  - The loop authenticates, sends a heartbeat, publishes capabilities (protocol version and an empty or stub tool list), polls, and on an empty poll sleeps with backoff and jitter. Interval is configuration. Backend unavailability does not crash the bridge.
  - Backend bridge routes at prototype level (session, heartbeat, capabilities, poll). They authenticate, update `last_seen_at`, store the capability report and return no work. Heartbeat proves liveness only. A revoked state beats a heartbeat. Capability reports are advisory.
  - The 15 bridge integration scenarios in 04.10.12 are copied into `tests/integration/bridge_scenarios.md` and classified as exercisable in Phase 1 (registration, authentication, heartbeat, capabilities, revoked device, backend unavailable) or Phase 2 (delivery, ack, result, lost response).
  - Tests: success path, wrong credential, revoked device, backend unavailable, duplicate heartbeat harmless.
  - From a second Windows PC, the bridge enrolls and shows as online with a recent `last_seen_at`. Revoking makes the next authentication fail. If Phase 0 networking findings say this cannot work, the team stops and raises it instead of opening firewall rules.
- **Todo List**:
  - [ ] Bridge prototype: authenticate, heartbeat, capabilities, poll loop with backoff and jitter (P1-21a).
  - [ ] Backend bridge routes at prototype level (P1-21b).
  - [ ] Copy and classify the 15 integration scenarios (P1-21c).
  - [ ] Run the enroll-and-revoke exercise on a second Windows PC.
- **Relevant Context**:
  - Roadmap Step 21; tracker P1-21a/b/c
  - Specs: 04.10.04, 04.10.12, 04.09
  - Native Windows, not WSL.
- **Status**: `[ ] pending`

---

### Sub-Task 10: Mock planner and plan validator (Step 22)
- **Intent**: Exercise the planner contract with no AI.
- **Expected Outcomes**:
  - A small planner interface in `nexus_core/ai/` taking the request plus permitted context and returning a Step 11 proposal.
  - `MockPlanner`: a deterministic fixture table. A known request returns a fixed valid `search_files` proposal. An ambiguous request returns `CLARIFICATION_REQUIRED`. An unsupported request returns `UNSUPPORTED`.
  - An application-side plan validator checks: schema valid, tool registered, arguments match the tool schema, dependencies reference existing steps, target device is owned. It returns a validated plan or typed errors.
  - Fixtures from 04.05.08: valid plans, malformed model output, unknown tools, missing or invalid arguments, clarification, unauthorized device targets are built now. Approval-required, model timeout and injection fixtures are listed with the phase that implements them (Phases 3 and 4).
  - Tests never claim real-model quality.
- **Todo List**:
  - [ ] Planner interface and `MockPlanner` (P1-22a).
  - [ ] Plan validator and fixtures (P1-22b).
  - [ ] Feed every fixture through the validator and check the expected result.
- **Relevant Context**:
  - Roadmap Step 22; tracker P1-22a/b
  - Specs: 04.08.07, 04.05.08
- **Status**: `[ ] pending`

---

### Sub-Task 11: Continuous integration (Step 23, D-21)
- **Intent**: Contract and integration tests run automatically on every PR.
- **Expected Outcomes**:
  - The CI table in 04.04.05 (9 rows) is read and its stages are copied into the ADR for D-21. CI stages A–E from 04.22.04 are noted for Phase 7.
  - A pipeline (GitHub Actions is the likely choice since the repo is on GitHub; the free-plan limits are verified before committing): install from the lock file; format, lint and type checks; unit tests; contract tests; PostgreSQL integration tests against a PostgreSQL service started in the job. A smoke import job for `apps/windows_bridge/` on a Windows runner is added if the free plan supports it.
  - CI uses throwaway test credentials and never prints secrets. The check is required for merge if branch protection allows it, otherwise it is a team rule.
  - One green run and one red run are recorded as evidence.
- **Todo List**:
  - [ ] Read 04.04.05 and write the D-21 ADR (P1-23).
  - [ ] Build the workflow and verify one green and one red run.
  - [ ] Verify GitHub Actions free-plan limits.
- **Relevant Context**:
  - Roadmap Step 23; tracker P1-23
  - Specs: 04.04.05, 04.22
- **Status**: `[ ] pending`

---

### Sub-Task 12: Open-decision register, contract freeze and Gate 1 review (Steps 24–26, D-22)
- **Intent**: Record what is not settled, freeze the contract baseline with a change process, and pass Gate 1 with repeatable tests.
- **Expected Outcomes**:
  - Decision register contains every item not yet Confirmed (D-09 to D-22 plus the open-decision tables from 03.10.11, 03.29.16, 04.09.11 and 04.10.13), each with status, owner, evidence needed and revisit condition. Nothing is Confirmed without linked evidence.
  - PC-01 (must NEXUS work when disconnected from the shared backend? D-22) and PC-05 (default permitted directories and applications) are answered or deferred to a named phase in the tracker.
  - Contract freeze following the six steps of 04.08.13: draft, consumer review, fixtures, security review by a non-author, baseline approval by all three (tag such as `contracts-v0.1`), controlled changes. Outcomes written to `contracts/CHANGELOG.md`. The 04.04.04 approval checklist is run on each contract.
  - Gate 1 checklist (tracker P1 exit criteria) run on repeatable tests, not a demo: pure state machine tested; error catalogue complete; five separate contract layers with examples used by tests; baseline approved; migration creates schema from empty and upgrades the previous revision on all three PCs; real-PostgreSQL tests pass; two-user auth and ownership tested with immediate revocation; device enrollment, heartbeat, capabilities and revocation work; mock planner output passes the validator; CI runs on every PR; D-09 to D-22 recorded; hardware inventory exists and an AI-validation owner is named.
  - Tracker updated, Phase 2 entry list written (task submission endpoint, CLI, bridge delivery/ack/result, real `search_files`, polling interval measurement, CLI token storage, full Baseline 2), hand-off pairing done (suggested BE = Dev C, WB = Dev A, AI = Dev B) and a retrospective held.
- **Todo List**:
  - [ ] Complete the decision register (P1-24a).
  - [ ] Answer or defer PC-01 and PC-05 (P1-24b).
  - [ ] Run the contract freeze and tag the baseline (P1-25).
  - [ ] Run the Gate 1 review, update the tracker, write the Phase 2 entry list, hold hand-off and retrospective (P1-26).
- **Relevant Context**:
  - Roadmap Steps 24–26 and §5; tracker P1-24a … P1-26 and Gate 1 exit criteria
  - Specs: 04.27, 04.08.13, 04.04.04, 04.28.05
- **Status**: `[ ] pending`
