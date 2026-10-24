# Phase 3 (Safe Side Effects) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-3-safe-side-effects.md`](../roadmap/phase-3-safe-side-effects.md) (Steps 0–27) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2d (P3-00 … P3-27). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal (Gate 3): NEXUS can safely perform Tier 1 operations — creating a new file in an approved workspace and launching an allowlisted application — with risk-based policy enforcement, human approval for consequential operations, operation identity and deduplication hardening, full cancellation and disconnection behaviour, and recovery that never blindly repeats an uncertain side effect.

Decisions settled here: D-40 to D-55 (plus PC-06 and PC-07). D-18 (cancellation representation) is finalized by D-48. Owners are assigned by the team (suggested rotation: BE = Dev A, WB = Dev B, AI = Dev C). No Tier 1 tool is enabled in production until its contract, failure behaviour and tests exist (03.23.12). Gate 3 requires repeatable tests, not demonstrations.

Excluded from Phase 3: live AI planning and semantic memory (Phase 4), `read_document` (Phase 5), GUI/UI automation, administrative policy UI, shared-resource quotas (Phase 6), log aggregation dashboards, backup and restore (Phase 7), third-party tool plugins.

Deliberate deviations from the Roadmap wording, to be confirmed in Sub-Task 1:
- Roadmap Step 23 lists an "approval signing key". Approvals are bound to an operation fingerprint (D-50), and the docs name no signing key. Include a signing key only if the team decides it is needed.
- The Roadmap adds a `WAITING_FOR_CLARIFICATION` task state. The 03.29 state machine has no such state. Add it only through the contract change process, with the state machine and its tests updated together (04.18.02 proposes a distinct category).
- Cancel command naming (`nexus cancel <id>` vs `nexus task <id> --cancel`) follows the Phase 2 decision (D-35).
- Risk-tier naming (Tiers 0–3 in 03.11 and ADR-011 vs five tiers in Product Vision 1.4) is settled in Sub-Task 4.

---

## Sub-Tasks

### Sub-Task 1: Entry check, learning blocks, contract confirmation and ADR stubs (Steps 0–7)
- **Intent**: Confirm Phase 2 delivered what Phase 3 needs, and freeze the Phase 3 contracts before any code depends on them.
- **Expected Outcomes**:
  - Phase 2 outputs present, blocking ADRs settled, at least two Windows PCs available (blocks P3-06 onward).
  - Each developer completes learning blocks on policy engines, risk tiers and deny-by-default; approval state machines, PostgreSQL concurrency and fingerprints; `create_file` safety, atomic creation and TOCTOU; application launching and session boundaries; configuration categories, versioning and secrets isolation.
  - Contracts confirmed and tagged (suggested `contracts-v0.3`):
    - Operation envelope arguments for `create_file` (`directory_id, relative_path, content, if_exists` with default `reject`) and `launch_application` (`app_id`, optional validated arguments, verify condition).
    - Approval record (`approval_id, task_id, step_id, operation_id, operation_fingerprint, approved_user_id, target_device_id, tool_name, tool_schema_version, normalized_arguments, resource_scope, risk_tier, policy_version, requested_at, expires_at, decided_at, decision, decided_by`), with decision values `PENDING, APPROVED, REJECTED, EXPIRED, INVALIDATED` (D-42) and a note on which fields the CLI reads and which the backend derives.
    - Policy decision record (`policy_decision_id, operation_id, user_id, device_id, tool_name, policy_version, decision (ALLOW/REQUIRE_APPROVAL/DENY), risk_tier, reason_code, decided_at`).
    - New error codes aligned with the catalogue columns (emitter, terminal, retry, recovery): `APPROVAL_REJECTED, APPROVAL_INVALIDATED, DESTINATION_ALREADY_EXISTS, APPLICATION_NOT_ALLOWLISTED, APPLICATION_LAUNCH_FAILED, POLICY_UNAVAILABLE, AUDIT_PERSISTENCE_FAILED`. `APPROVAL_REQUIRED` and `APPROVAL_EXPIRED` already exist in the 15-code catalogue.
    - Decision on whether `WAITING_FOR_APPROVAL` suffices or a distinct clarification state is added (see deviations above).
    - CLI additions in line with spec 03.16 and 04.18.03: `nexus approvals`, `nexus approve <approval-id>`, `nexus reject <approval-id>`, `nexus permissions list`, `nexus directories list`, `nexus diagnostics`. Names are proposals until aligned.
  - ADR stubs (status Open) for D-40 to D-55, each with the question, the docs' position, evidence needed, owner and the settling step. Tracker decision register updated. D-18 closed by D-48 when its ADR exists.
- **Todo List**:
  - [ ] Entry check (P3-00) and learning blocks (P3-01 to P3-05).
  - [ ] Confirm the contracts above and tag `contracts-v0.3` (P3-06).
  - [ ] Create ADR stubs D-40 to D-55 (P3-07).
- **Relevant Context**:
  - Roadmap Steps 0–7 and §2; tracker P3-00 … P3-07
  - Specs: 03.23, 03.31, 04.18, 03.30.04, 03.16, 04.20
- **Status**: `[ ] pending`

---

### Sub-Task 2: Schema additions for approvals, permissions, policy decisions and configuration versions (Step 8; D-51, D-52)
- **Intent**: The database carries approvals, permission grants, policy decisions and configuration versions before any Tier 1 operation can be dispatched.
- **Expected Outcomes**:
  - A new migration (previous migrations are never edited) adds `approvals` (all contract fields; UNIQUE(`operation_id`) so only one active approval exists per operation; status changes are updates with a generation check, never deletes), `permission_grants` (`grant_id, user_id, device_id, tool_name, resource_scope, granted_by, granted_at, expires_at, revoked_at, policy_version`, per the D-51 logical model), `policy_decisions` and `configuration_versions` (`component, version, updated_at, updated_by, checksum`).
  - Indices for `approvals(task_id, status)`, `approvals(operation_id)`, `permission_grants(user_id, device_id, tool_name)`.
  - Data-model document and ER diagram updated. A fresh database migrates to head and the previous revision upgrades. Constraint tests prove UNIQUE(`operation_id`).
- **Todo List**:
  - [ ] Write and test the migration (P3-08).
  - [ ] Update the data-model document and ER diagram.
- **Relevant Context**:
  - Roadmap Step 8; tracker P3-08
  - Specs: 04.18.04, 04.20.06, 04.20.09, 03.10
- **Status**: `[ ] pending`

---

### Sub-Task 3: Policy engine (Step 9)
- **Intent**: One testable function embodies the 8-layer precedence. Every authorization path calls it and fails closed.
- **Expected Outcomes**:
  - A policy-engine module in `nexus_core/security/` (or the path agreed in Phase 0) that takes the authenticated user, task, target device, registry tool definition, normalized arguments, resource scope and current approval state, and returns a typed decision: ALLOW, REQUIRE_APPROVAL or DENY with a reason code.
  - Eight layers in strict order: L1 hard prohibitions; L2 tool capability (registered, enabled, schema version supported); L3 identity and ownership; L4 resource permissions (active grant); L5 operation-specific constraints; L6 risk classification (Tier 0 allows after L1–L5; Tier 1 requires approval); L7 approval validation (bound, unexpired, unrevoked, exact fingerprint); L8 execution-time revalidation of L1–L7 immediately before dispatch.
  - A later layer never overrides an earlier DENY (tested). If the policy service or any lookup fails, the decision is DENY. A `policy_decisions` row is written for each decision affecting a consequential operation, and if that insert fails the operation is not dispatched.
  - Unit tests cover every layer, a disabled tool with a valid approval (L2 rejects), an expired approval (L7 rejects), and a stale approval at dispatch (L8 rejects). Non-author security review recorded.
- **Todo List**:
  - [ ] Implement the 8 layers and typed decision (P3-09).
  - [ ] Implement fail-closed behaviour and the audit-persistence gate.
  - [ ] Unit tests and security review.
- **Relevant Context**:
  - Roadmap Step 9; tracker P3-09
  - Specs: 03.23.3–03.23.5, 03.23.9
- **Status**: `[ ] pending`

---

### Sub-Task 4: Risk classification, PC-06 and tool registry hardening (Steps 10, 11)
- **Intent**: Every tool has an explicit risk tier and complete registry entry before any bridge code is written, and the team answers which operations run automatically.
- **Expected Outcomes**:
  - Risk tiers: `search_files` Tier 0; `create_file` and `launch_application` Tier 1. Tier naming reconciled between 03.11 / ADR-011 (Tiers 0–3) and Product Vision 1.4 (five tiers) in an ADR.
  - PC-06 ADR: which actions run automatically and which need approval (suggestion: `search_files` automatic; `launch_application` always approval; `create_file` approval rule chosen by the team), with a revisit condition. A model-supplied risk tier in arguments is ignored; the registered tier is used.
  - Registry entries. `create_file`: `schema_version` 1, input `directory_id, relative_path, content, if_exists`, output relative path and size and created time, permission `files.create`, retry safe only if the bridge reports the operation was not executed, verification `check_file_exists_at_expected_path`. `launch_application`: input `app_id` and optional bounded arguments, output `launched`, optional process identifier and `started_at`, permission `apps.launch`, retry not safe, verification `verify_process_started` (D-46), enabled only after D-45 is settled on the real bridge.
  - Startup validation rejects a malformed definition or unsupported schema version and disables the tool instead of falling back to unrestricted execution. A security test shows the model cannot register a tool or change a risk tier.
- **Todo List**:
  - [ ] Risk tiers, tier-naming ADR and PC-06 ADR (P3-10).
  - [ ] `create_file` and `launch_application` registry entries and startup validation (P3-11).
  - [ ] Tests for escalation, registration and startup validation.
- **Relevant Context**:
  - Roadmap Steps 10, 11; tracker P3-10, P3-11
  - Specs: 03.23.5, 03.31.05, 03.31.06, 03.31.10–03.31.13, 03.36
- **Status**: `[ ] pending`

---

### Sub-Task 5: Approval lifecycle, dispatch integration and prompt-injection tests (Steps 12–14; D-40, D-41, D-42, D-50)
- **Intent**: Approvals are persisted, atomic, bound to the exact operation and safe against the races in 04.18.06. The policy engine runs again immediately before dispatch.
- **Expected Outcomes**:
  - ADRs D-40 (expiry duration), D-41 (task owner is the only approver in the MVP), D-42 (states) and D-50 (fingerprint over tool name, schema version, canonicalized arguments, target device, resource scope, policy version) as Provisional.
  - Approval service: creates a PENDING approval and moves the step to WAITING_FOR_APPROVAL. Routes `GET /v1/approvals`, `GET /v1/approvals/{approval_id}`, `POST /v1/approvals/{approval_id}/approve`, `POST /v1/approvals/{approval_id}/reject`. Decisions are atomic (conditional update on status and expiry, affected-row count checked). Expiry sweep and restart-time expiry. Invalidation when any fingerprint field changes, and when a user or device is revoked. Another user's attempt returns a not-found-style denial.
  - Pre-dispatch L8 call in the Phase 2 dispatch pipeline before persisting operation intent. Fingerprint mismatch marks the approval INVALIDATED, blocks dispatch and audits it. Policy unavailable means no dispatch. Dispatch audit rows include policy decision ID, approval ID, risk tier and the L8 pass.
  - Adversarial suite: prompt-injection documents (reveal credentials, search outside the approved directory, claim admin rights, "ignore previous rules"); bypass attempts (replayed approval, changed device after approval, changed `max_results`, model-supplied risk tier, revoked credential, non-allowlisted app). Markers such as `adversarial` and `security_regression` run in CI. Acceptance criterion: zero unauthorized side effects. A mutation check shows a deliberately weakened layer fails at least one test.
  - PostgreSQL tests for each 04.18.06 rule: concurrent approvals (one wins), expired approval (update affects 0 rows), revoked user's approval invalidated, cancelled task's approval cannot dispatch. Non-author security review.
- **Todo List**:
  - [ ] Approval ADRs and service (P3-12).
  - [ ] Approval routes, atomic decisions, expiry, invalidation and revocation handling.
  - [ ] Pre-dispatch L8 revalidation and fingerprint check wired into the pipeline (P3-13).
  - [ ] Adversarial and policy-bypass tests with CI marker (P3-14).
- **Relevant Context**:
  - Roadmap Steps 12–14; tracker P3-12, P3-13, P3-14
  - Specs: 04.18.04–04.18.07, 03.23.7, 03.23.8, 03.30.03, 03.30.07, 03.18.7
- **Status**: `[ ] pending`

---

### Sub-Task 6: CLI for approvals, clarification and watch (Step 15)
- **Intent**: The user can inspect pending approvals, see the exact operation and decide, without the CLI being the security boundary.
- **Expected Outcomes**:
  - `nexus approvals`, `nexus approve <approval-id>` and `nexus reject <approval-id>`. The approve flow fetches the detail from the backend (never from the CLI's memory or an untrusted model response) and displays operation and intended effect, target device, exact destination, consequence and reversibility, reason for approval, expiry and what happens if no action is taken, then asks "Approve this exact operation? [y/N]".
  - Clarification flow only if Sub-Task 1 added it: a clarification request bound to the task and step, with a response command (name is a suggestion). A clarification response never grants permissions.
  - Human-readable and stable JSON output (`--output json`, per D-35 and D-75). `nexus task --watch` shows when a task is awaiting approval or clarification with an actionable message.
  - Tests with a fake backend: pending approval shown; expiry shown; correct request sent for approve and reject; Ctrl-C at the prompt does not approve; watch shows the actionable message.
- **Todo List**:
  - [ ] Approval commands (P3-15).
  - [ ] Clarification flow if added.
  - [ ] Watch message and tests.
- **Relevant Context**:
  - Roadmap Step 15; tracker P3-15
  - Specs: 04.18.03–04.18.05, 04.18.07, 04.18.11, 03.16
- **Status**: `[ ] pending`

---

### Sub-Task 7: Bridge journal hardening and `create_file` (Steps 16–18; D-43, D-44, D-47)
- **Intent**: The bridge journal is reliable enough for tools whose uncertain outcomes cannot be blindly retried, and `create_file` never silently overwrites.
- **Expected Outcomes**:
  - D-47 finalized from the Phase 2 Provisional D-29 after validation on real Windows hardware: durability across restart, locking under concurrent operations, cleanup under retention, recovery from a partial write. Journal entries for `create_file` hold operation ID, fingerprint, tool and schema version, target device, directory ID, relative path (never absolute), status, attempt metadata, known result reference, timestamps and reconciliation state, and never file content. `launch_application` entries hold the app ID and verification outcome only. Retention values and revisit condition recorded. On restart, unresolved `create_file` entries are reported as uncertain to the backend, which reconciles before any retry.
  - Reconciliation and verification: after SUCCEEDED the backend queries the bridge journal and confirms file existence at the relative path and size or hash. A lost response triggers `GET /v1/bridge/operations/{id}`: record with file created confirms; record with file not created allows retry per D-43; no record after dispatch means UNCERTAIN, shown to the user and never retried blindly. `if_exists=reject` with an existing destination returns `DESTINATION_ALREADY_EXISTS`, a definite rejection and not an uncertain outcome. The destination is revalidated at execution time.
  - Bridge `create_file`: D-43 (creation strategy) and D-44 (content size limit) settled after a spike on the Windows test PCs. Phase 2's eight-step path validation applied to the destination (no UNC, no device namespaces, no traversal, no junctions, resolved-path prefix check). Existence check as close to the write as possible, with the remaining TOCTOU window documented. Size check before any write. The bridge rejects an operation whose path or directory differs from the envelope. Audit log never contains content.
  - Windows tests on at least two PCs extending the Phase 2 security tests: traversal into the workspace parent, sibling-prefix confusion, junction in the destination, ADS syntax in the filename, content above the limit. Non-author security review.
- **Todo List**:
  - [ ] Journal hardening with D-47 ADR (P3-16).
  - [ ] `create_file` reconciliation and verification (P3-17).
  - [ ] `create_file` bridge implementation with D-43, D-44 ADRs (P3-18).
  - [ ] Windows tests on two PCs.
- **Relevant Context**:
  - Roadmap Steps 16–18; tracker P3-16, P3-17, P3-18
  - Specs: 03.30.05, 03.30.06, 03.30.10, 03.30.11, 03.30.14, 03.31.06, 03.32, 03.19.3
  - Native Windows, not WSL.
- **Status**: `[ ] pending`

---

### Sub-Task 8: `launch_application` (Step 19; D-45, D-46)
- **Intent**: The bridge launches only allowlisted applications, verifies the launch, and never executes arbitrary commands.
- **Expected Outcomes**:
  - D-45 (initial allowlist and locally configured executables) and D-46 (confirm-launch-only versus verify-started, and the verification method) recorded Provisional. If the team judges `launch_application` too risky without UI automation, it is deferred with a justification in the entry list.
  - The bridge resolves `app_id` from its local application mapping. An `app_id` not in the allowlist returns `APPLICATION_NOT_ALLOWLISTED`. The backend cannot supply an executable path and shell interpretation is prohibited. A session check reports when interactive launch is unavailable. The bridge does not run as administrator.
  - Verification after launch (bounded wait, configurable timeout). A SUCCEEDED outcome means the process was launched and the verification passed. It does not mean work inside the application completed, and the output schema states that. Retry is not safe; an uncertain first attempt stays UNCERTAIN until the user reconciles. The audit log has the app ID, outcome and verification evidence only.
  - Windows tests: non-allowlisted app, arbitrary path in arguments rejected, valid allowlisted app launched and verified, second delivery of the same operation ID returns the known outcome, UNCERTAIN when verification times out.
- **Todo List**:
  - [ ] ADRs D-45 and D-46.
  - [ ] Allowlist enforcement, session check, launch and verification (P3-19).
  - [ ] Windows tests.
- **Relevant Context**:
  - Roadmap Step 19; tracker P3-19
  - Specs: 03.36 (Application Execution Strategy), 04.20.05
  - Native Windows, not WSL.
- **Status**: `[ ] pending`

---

### Sub-Task 9: Fault injection, cancellation, disconnection and revocation (Steps 20–22; D-48, D-49, D-54, PC-07)
- **Intent**: Recovery for Tier 1 tools never blindly repeats an uncertain side effect, cancellation never claims a cancel that did not happen, and the disconnect behaviour question is answered.
- **Expected Outcomes**:
  - Phase 2's failure matrix extended into `docs/testing/p3-failure-matrix.md` (path suggested), with each 03.30.13 scenario marked for `create_file` and `launch_application`. New rows: destination already exists; write executed but response lost (UNCERTAIN, reconcile, file found means confirmed, not found means UNCERTAIN continues); bridge crashes after the side effect but before recording it (journal has no record, UNCERTAIN, no second file); cancellation racing with a pending approval; approval expiring while WAITING_FOR_APPROVAL; approval arriving after cancellation. Tests assert real filesystem and application state, not only HTTP status. A mutation check on the `create_file` UNCERTAIN path fails at least one test.
  - D-48 settled (for example a cancel-requested timestamp on the task row versus a separate record). A cancel on an in-flight Tier 1 operation: record the request, dispatch nothing new, wait for the outcome, reconcile, then CANCELLED if safe or INTERRUPTED if UNCERTAIN. CANCELLED is never set while an uncertain side effect may still be running. The CLI says cancellation is requested, not complete. A completed side effect is never reversed (the file is kept). Tests: cancel in WAITING_FOR_APPROVAL (approval INVALIDATED); cancel with a dispatched `create_file`; in-flight create finishes (CANCELLED, file kept); in-flight create uncertain (INTERRUPTED).
  - D-49 (how long before a dispatched operation becomes UNCERTAIN on disconnect, derived from the D-28 lease heartbeat) and D-54 (maximum revocation propagation delay) settled. PC-07 ADR: stop dispatching to the offline device, detect the in-flight operation, do not assume failure, mark UNCERTAIN after the threshold, reconcile on reconnect, revalidate authorization before any retry. A disconnected device is not assumed to have received a revocation. Reconnect: the bridge re-authenticates, reports its journal and the backend reconciles before new work. Tests cover disconnect mid-dispatch, reconnect reconciliation, revocation recorded during disconnect, and respecting an in-flight outcome.
- **Todo List**:
  - [ ] Extend the failure matrix and fault-injection tests (P3-20).
  - [ ] Full cancellation semantics with D-48 ADR (P3-21).
  - [ ] D-49, D-54, PC-07 ADRs and disconnection tests (P3-22).
- **Relevant Context**:
  - Roadmap Steps 20–22; tracker P3-20, P3-21, P3-22
  - Specs: 03.30.13, 04.11.11, 03.15.06, 03.15.08, 04.11.08, 04.20.08, 03.30.11
- **Status**: `[ ] pending`

---

### Sub-Task 10: Permission, configuration and observability CLI (Steps 23, 24; D-51, D-52, D-53, D-55)
- **Intent**: Every developer can inspect and revoke what NEXUS may do on their PC, and any task including Tier 1 operations can be traced end to end.
- **Expected Outcomes**:
  - CLI commands, scoped to the authenticated user's own devices: `nexus config show` (non-secret effective configuration only), `nexus permissions list` and `show <id>`, `nexus permissions revoke <id>` (identity validated, revocation persisted, pending approvals INVALIDATED), `nexus directories list` and `validate <id>` (bridge must be online), `nexus apps list`. A user cannot change another user's configuration by supplying their ID.
  - D-52 configuration versioning: security-sensitive changes bump `configuration_versions`; the bridge reports its effective version on heartbeat; the backend checks compatibility at dispatch. D-55 recorded: in Phase 3 policy changes only via code PR plus ADR, with no runtime UI, and the long-term question stays open. Startup validation extended to all Phase 3 settings (`create_file` workspace directory, `launch_application` allowlist) with actionable failures. Include an approval signing key only if the team decided so in Sub-Task 1.
  - Observability: structured log fields (`timestamp, level, service, event_name, request_id, task_id, operation_id, attempt_id, device_id, error_code, duration_ms`) with no file content, absolute paths or credentials. D-53: `GET /health/live`, `GET /health/ready`, and an authenticated `GET /v1/diagnostics` for authorized operators. `nexus diagnostics` shows CLI and backend versions, DB readiness, bridge last-seen per device, pending uncertain operations and tasks needing recovery, and never prints environment variables, credentials or filesystem listings. The "no secrets in logs" test is extended to cover credentials, absolute path prefixes and `create_file` content fragments. Lightweight counters without high-cardinality labels are optional and Provisional.
  - Tests: another user's ID rejected; revocation blocks the next dispatch; `config show` omits credentials; bridge start fails clearly when a mapping is missing; a failed `create_file` is traceable by `operation_id`; health endpoints respond within a bounded time.
- **Todo List**:
  - [ ] Permission and configuration CLI, versioning and startup validation (P3-23).
  - [ ] Structured logging, health endpoints, `nexus diagnostics` and D-53 (P3-24).
- **Relevant Context**:
  - Roadmap Steps 23, 24; tracker P3-23, P3-24
  - Specs: 04.20.07, 04.20.08, 03.20.05, 03.19.03, 03.19.05, 03.19.08
- **Status**: `[ ] pending`

---

### Sub-Task 11: Acceptance matrix, release evidence and Gate 3 review (Steps 25–27)
- **Intent**: Prove every Gate 3 item on PostgreSQL and Windows, record the evidence honestly, and hand off to Phase 4.
- **Expected Outcomes**:
  - 15 acceptance scenarios with evidence in `docs/testing/p3-acceptance.md`: approve then `create_file` succeeds (SUCCEEDED); approval expires before dispatch (EXPIRED, not dispatched); approval rejected; fingerprint change between approval and dispatch (INVALIDATED); `create_file` to an existing destination (`DESTINATION_ALREADY_EXISTS`); `create_file` response lost (UNCERTAIN, reconciled); allowlisted launch verified; non-allowlisted launch refused; prompt-injection document cannot expand scope; cancel after `create_file` dispatch; device disconnect after dispatch; permission revocation blocks a queued operation; `search_files` still works; policy engine unavailable blocks dispatch; approval by a non-owner denied. The primary end-to-end scenario runs on at least two Windows PCs over the LAN. A mutation check on approval expiry fails the expiry scenario.
  - Release evidence report `docs/releases/p3-evidence.md`: commit, migration and configuration versions, automated results, Windows results for both tools, approval-flow results, failure-matrix results, known defects, unresolved decisions, untested scenarios. Clean-setup reproduction by a developer who did not write the instructions. Troubleshooting guide extended with Phase 3 error codes. Milestone sign-off checklist per Roadmap Step 26.
  - Non-author security review with the Phase 2 checklist extended: no client-supplied authority fields in approval bodies; fingerprint verified before every dispatch; no silent overwrite; no arbitrary executables; prompt-injection tests pass; policy fails closed; audit persistence gates consequential actions; revocation blocks new dispatch and in-flight work follows the protocol; no secrets in logs, approval records or diagnostics. Critical and high defects fixed first.
  - Gate 3 checklist from the tracker satisfied, including zero unauthorized side effects, PC-06 and PC-07 ADRs, D-40 to D-55 recorded, and no critical or high defect open. Tracker updated (including MVP checklist items 6, 8, 9, 10, 11 only with test evidence). Hand-off pairing and retrospective held.
  - Phase 4 entry list: model benchmark and environment, model adapter contract, multi-step plan validation (the planner may now use `create_file` and `launch_application`), memory schema, retrieval design, grounding rules, prompt-injection evaluation set building on the Phase 3 fixtures, AI safety integration with the policy engine, model-runtime performance baseline.
- **Todo List**:
  - [ ] Complete the acceptance matrix and run the end-to-end scenario on two PCs (P3-25).
  - [ ] Evidence report, clean-setup reproduction and milestone sign-off (P3-26).
  - [ ] Security review, Gate 3 review, tracker update, Phase 4 entry list, hand-off and retrospective (P3-27).
- **Relevant Context**:
  - Roadmap Steps 25–27 and §5; tracker P3-25 … P3-27 and Gate 3 exit criteria
  - Specs: 03.23.11, 03.23.14, 04.18.16, 03.31.16, 04.28.05
- **Status**: `[ ] pending`
