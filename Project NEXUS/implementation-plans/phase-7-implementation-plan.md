# Phase 7 (Hardening and Release Candidate) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-7-hardening-and-release.md`](../roadmap/phase-7-hardening-and-release.md) (Steps 0–21) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2h (P7-00 … P7-21). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal (Gate 6): a release candidate that all three developers jointly sign off, backed by actual evidence for the full acceptance suite (Workflows A–F), the security acceptance matrix, backup and restore rehearsal, a CI/CD pipeline, packaging and upgrade procedures, reproducible installation, reliability experiments, and measured performance and model quality on the real hardware. Gate 6 requires repeatable evidence; a demonstration without repeatable tests does not count (04.28.05). No developer can independently declare the system release-ready (03.40.9).

Prerequisite: Gate 5 must be fully evidenced. Any Gate 5 item not resolved becomes a Phase 7 blocker. This phase hardens, verifies, documents and signs off; it adds no new tool types or workflows. A scope change must be recorded as a decision and reviewed by all three developers. A failed security invariant cannot be reclassified as optional merely to complete the release (03.40.11).

Decisions settled here: D-95 to D-104. Owners are assigned by the team; every security-sensitive check involves a reviewer other than its primary author (03.39.12, 03.40.9). Suggested primary areas: backend/persistence developer for backup and performance, bridge developer for filesystem and Windows checks, AI/context developer for prompt injection and model quality.

Excluded from Phase 7: new tool types or user workflows, cloud deployment, shared project memory, OCR and spreadsheet processing, tamper-evident audit storage, automated scaling.

Honest-status points to confirm in Sub-Task 1:
- Two different "gate" vocabularies exist. Project Gates 1–6 are the milestone gates. The CI pipeline has five gates labelled A–E (04.22.4). Always say "CI Gate A" or "Gate 6" to avoid confusion.
- Two different checklists exist: the 25-item MVP release evidence checklist (03.40.10) and the 21-item release sign-off checklist (04.28.10), plus 10 release-blocking conditions (03.40.11). All three are completed with cited evidence.
- The Roadmap mapping table mentions a "10 item" backup rehearsal, but its Step 11 lists 8 exercises (04.25.10). Read 04.25.10 and cover every required exercise, not only the eight listed.
- D-97 and D-98 (RPO and RTO) are derived from measured restore time and database size, not aspirational numbers. D-95 and D-96 (CI platform and Windows runner) stay Open or Blocked if a zero-budget option does not exist; GitHub Actions is not assumed.
- Risk-tier naming (Tiers 0–3 vs five tiers), D-23, D-24, D-25 and D-75 remain governed by their own ADRs. If any is still Open at release, it is listed as an unresolved decision in the evidence report rather than silently settled.
- The AMD GPU result must come from the actual designated host, not from another developer's environment (04.22.9). A documented CPU fallback is acceptable only if D-68 was settled.
- The document count discrepancy (finding R1: 66 expected vs 65 present) is raised before sign-off, because the missing specification may add release requirements.
- Documents the Roadmap did not read and which may add Phase 7 requirements: Operational Runbooks, Incident Response and Service Recovery; Privacy, Data Retention and User Data Export. They are read before Steps 13, 17 and 20.

---

## Sub-Tasks

### Sub-Task 1: Learning blocks, gap analysis and ADR stubs (Steps 0–4)
- **Intent**: The team shares one definition of "release-ready" and records which release evidence already exists from earlier phases and which is new.
- **Expected Outcomes**:
  - Release-readiness learning: the 10 architectural invariants, 6 end-to-end workflows, 10 reliability experiments, 12 security-acceptance items and the 25-item checklist. A gap document (suggested `docs/releases/p7-gap.md`) has a row per release-evidence item with status `evidenced from Phase 6 / in progress / not started`.
  - CI/CD learning: the five CI gates, three compatibility boundaries (API to CLI, backend to bridge, planner to tool registry), and the deterministic-testing policy (a test whose dependency is unavailable is reported as not run, never as passed). D-95 and D-96 stubs recorded, even as Open or Blocked.
  - Backup learning: database backup vs complete recovery, RPO, RTO, and that a successful backup command is not proof of restorability. D-97, D-98, D-99 stubs recorded with an honest view of what the team can support.
  - Packaging learning: five version dimensions (backend, CLI, bridge, database schema, AI runtime and model), five upgrade classes A–E, fail-closed handling of unknown or security-sensitive incompatible versions. D-100, D-101, D-102 stubs recorded.
  - Threat-model learning: a document (suggested `docs/security/threat-model-review.md`) lists each of the 12 security-acceptance items with evidence source, the phase that introduced it, and whether Phase 7 re-verification is needed. The 10 release blockers are reviewed.
  - Tracker updated with the Gate 5 carry-overs and the stub ADR statuses.
- **Todo List**:
  - [ ] Release readiness and gap document (P7-00).
  - [ ] CI/CD concepts; D-95, D-96 stubs (P7-01).
  - [ ] Backup, RPO and RTO; D-97, D-98, D-99 stubs (P7-02).
  - [ ] Packaging and upgrade classes; D-100, D-101, D-102 stubs (P7-03).
  - [ ] Threat-model review document (P7-04).
- **Relevant Context**:
  - Roadmap Steps 0–4 and §5; tracker P7-00 … P7-04
  - Specs: 03.40.1–2, 03.40.11, 04.28.01–05, 04.22.2–8, 03.21.4–6, 04.25.2–4, 04.23.3–5, 03.39.1–5, 03.39.9
- **Status**: `[ ] pending`

---

### Sub-Task 2: End-to-end acceptance workflows A–F (Steps 5–6)
- **Intent**: Prove the six required workflows on the integrated environment with three users and three devices, each with a written acceptance record.
- **Expected Outcomes**:
  - Workflow A (search and summarize a document): the summary is based on the document actually read, the source stays within the user's authorized scope, and the result is never shown as successful unless processing and verification succeeded.
  - Workflow B (create a file safely): policy evaluates, approval is awaited if required, the bridge validates directory, relative path, destination and content limits, no silent overwrite occurs, and the CLI reports destination and outcome accurately.
  - Workflow C (recover from an uncertain operation): a lost response leaves the step `UNCERTAIN`, reconnection reconciles using operation identity and bridge records, and the outcome is reported without an unverified success claim or unsafe duplicate.
  - Workflow D (approval and cancellation): waiting for required approval; an unauthorized user cannot approve; approval for one operation does not cover changed arguments; rejection prevents dispatch; an expired approval does not authorize; cancellation stops future steps; an in-flight side effect is reconciled before cancellation is claimed; a cancelled task cannot be revived by late approval or replanning.
  - Workflow E (three-user isolation): three live accounts and three running bridges; each user sees only their own tasks, memory, approvals and devices; changing an identifier does not cross users; concurrent model requests do not mix context; a disconnection affects only the relevant task and device; fair scheduling prevents monopolization.
  - Workflow F (memory and context lifecycle): explicit save of a non-sensitive preference with correct owner and provenance, scoped retrieval, correction, deletion from active retrieval and caches, separate retention for history and audit, and honest description of backup-retention limits.
  - Records in `docs/releases/` for A–C and D–F with inputs, expected and observed outcomes. No workflow is marked passed unless its acceptance condition is met.
- **Todo List**:
  - [ ] Run workflows A, B and C and record results (P7-05).
  - [ ] Run workflows D, E and F (three PCs for E) and record results (P7-06).
- **Relevant Context**:
  - Roadmap Steps 5–6; tracker P7-05, P7-06
  - Specs: 03.40.3, 03.40.5
- **Status**: `[ ] pending`

---

### Sub-Task 3: Security hardening, acceptance matrix and prompt-injection suite (Steps 7–9)
- **Intent**: Every trust-boundary layer has its security requirements implemented and tested, each security-acceptance item cites an actual test result, and prompt-injection resistance is shown against the integrated system.
- **Expected Outcomes**:
  - Hardening review across five layers with a cross-component reviewer for each (03.39.5): API and application (authentication before access, acting user derived from identity, authorization on every read, mutation and approval, input validation, parameterized queries, rate limits, no internal errors exposed); database (dedicated least-privilege application role, not reachable from LAN clients, constraints, short transactions, separated migration privileges); AI and planning (model output untrusted, registered tools only, policy outside the model, scoped retrieval, retrieved text cannot alter policy); Windows bridge (operation origin, device identity, schema, deadline, local permissions, minimum OS privileges, no generic shell or arbitrary code endpoint); network and deployment (intended interfaces only, private PostgreSQL and model endpoint, no public exposure, host firewalls, TLS per D-86). Each developer signs for their primary area. Findings are recorded in a hardening review document.
  - Security acceptance matrix (suggested `docs/security/security-acceptance-matrix.md`) for the 12 items in 03.39.10: cross-user task and memory isolation; device identity and revocation; approval binding and replay protection; restricted filesystem access; no arbitrary model-generated commands; safe handling of uncertain side effects; prompt-injection resistance; secret-safe diagnostics; private service exposure; backup and restore safety; three-user concurrent operation; clean installation and configuration. Each row has test reference, result and reviewer. Anything that cannot be evidenced is recorded as a blocker.
  - Prompt-injection regression suite of the 8 scenarios in 03.39.7: out-of-scope file request in a document; instruction to reveal another user's memory; retrieved memory contradicting authorization rules; unknown tool proposal; arguments changed after approval; instruction to suppress errors or falsely report success; tool output instructing a different operation; malicious filename or extracted text with shell-like syntax. Each test checks for actual unauthorized side effects, not whether the model's message sounds safe, and runs against the integrated system rather than only a mock planner. Results include inputs, model response and observed system behaviour.
  - Defects found are fixed with regression tests; critical and high defects block sign-off.
- **Todo List**:
  - [ ] Hardening review by layer with cross-component reviewers (P7-07).
  - [ ] Security acceptance matrix for the 12 items (P7-08).
  - [ ] Prompt-injection suite for the 8 scenarios (P7-09).
- **Relevant Context**:
  - Roadmap Steps 7–9; tracker P7-07 … P7-09; risk P7-R3
  - Specs: 03.39.3–7, 03.39.10, 03.39.12, 03.40.9
- **Status**: `[ ] pending`

---

### Sub-Task 4: Backup implementation and restore rehearsal (Steps 10–11; D-97, D-98, D-99)
- **Intent**: Backups exist, are protected outside the designated host, and are proven restorable by at least two developers independently.
- **Expected Outcomes**:
  - The backup workflow from 04.25.5 implemented and automated: verify database availability, create a consistent backup, record time, schema version and application release, verify non-empty output and integrity, transfer to a protected location, verify the protected copy, apply retention, record the outcome without logging secrets, and alert the team if a backup fails or is overdue.
  - D-99 settled (another authorized team machine, encrypted external drive or another zero-budget option) with at least one verified protected copy outside the designated host. D-97 and D-98 settled with values derived from the actual database size and measured restore time.
  - Restore rehearsal on isolated data and test devices, never the live deployment: full restore to an isolated database with migrations, constraints and smoke tests; schema upgrade, backup and restore; task recovery with pending and completed tasks; device revocation after restore; memory-deletion reconciliation; host-loss scenario following the 6-step procedure in 04.25.6; pre-migration backup with a simulated migration failure; and any further exercise required by 04.25.10. At least two developers follow the documented procedure independently (04.25.11).
  - For each exercise: start and end time, backup identifier and recovery point, versions, data restored and known loss, tasks needing reconciliation, smoke-test results, deviations and corrective actions. Results are in a backup-restore rehearsal document; the procedure is updated after any deviation.
- **Todo List**:
  - [ ] Backup implementation, protected copy and D-97, D-98, D-99 (P7-10).
  - [ ] Restore rehearsal exercises with two independent followers (P7-11).
- **Relevant Context**:
  - Roadmap Steps 10–11; tracker P7-10, P7-11; risk P7-R4
  - Specs: 03.21.3–5, 03.21.12, 04.25.2–6, 04.25.10, 04.25.11
- **Status**: `[ ] pending`

---

### Sub-Task 5: Post-restore safety: uncertain operations, revocation and deletion (Steps 12–13)
- **Intent**: A restore never blindly replays uncertain external operations and never silently reinstates revoked access or deleted memory.
- **Expected Outcomes**:
  - Controlled scenario: the backend records intent to create a file, the bridge creates it, the backend fails before recording success, and the database is restored from an earlier backup showing the operation dispatched but unresolved. Verified rules (04.25.7): non-terminal tasks are not automatically re-run; dispatched operations are treated as potentially uncertain; reconciliation uses operation identity and bridge records; retry only where the tool's recovery contract permits; uncertainty is preserved and reported when evidence is insufficient. Never-violated rules checked: no blind replay of incomplete tasks, no assumption that a same-named file was created by NEXUS, a missing journal is not proof the operation never happened, an old backup cannot bypass current policy, revocation or approval, no success without verification evidence. This depends on the D-94 bridge-persistence outcome from Phase 6; if that ADR is Open or implementation is incomplete, the gap is a release blocker (risk P7-R5).
  - Device revocation test: a device revoked after the backup remains revoked after restoring an older backup. Credential-rotation test: old sessions are not reactivated without re-authentication, and trust is not restored merely for convenience.
  - Memory-deletion test using the 7-step reconciliation from 04.25.9 (restore into a controlled environment, apply retention and deletion reconciliation, reapply authoritative deletion and revocation data, invalidate stale indexes and caches, verify deleted memories are not active, verify user-scoped retrieval before normal access, document any limitation). The backup-retention limitation for deleted memory is stated honestly and immediate erasure from every historical backup is not promised.
  - Evidence documents for uncertain operations after restore and for revocation and deletion after restore; all three developers review as a cross-component check.
- **Todo List**:
  - [ ] Uncertain-operation reconciliation after restore (P7-12).
  - [ ] Revocation, credential and memory-deletion safety after restore (P7-13).
- **Relevant Context**:
  - Roadmap Steps 12–13; tracker P7-12, P7-13; risk P7-R5
  - Specs: 03.21.7, 03.21.9, 03.21.10, 04.25.7–9, 03.39.6
- **Status**: `[ ] pending`

---

### Sub-Task 6: CI/CD pipeline with five gates (Step 14; D-95, D-96)
- **Intent**: Every pull request runs the five CI gates, and a failed required check blocks merging.
- **Expected Outcomes**:
  - CI Gate A (code quality: formatting, linting, static analysis, type checking, dependency and import validation, configuration-example validation); CI Gate B (unit tests for state transitions, authorization and policy, idempotency and retry classification, plan and tool-schema validation, memory scope); CI Gate C (fresh database initialization, migration upgrades, uniqueness and transaction behaviour, API, bridge and tool-schema compatibility, concurrent claim and ownership); CI Gate D (security regression: cross-user and cross-device denial, approval replay and modified-argument rejection, path traversal and unapproved filesystem access, unknown-tool rejection, prompt-injection fixtures, secret leakage); CI Gate E (backend tests on the supported Linux environment, native Windows bridge tests on a Windows runner if D-96 allows, package and startup checks, end-to-end tests on designated integration runs).
  - D-95 (CI platform) and D-96 (Windows runner strategy, including what runs if no runner exists) settled or recorded honestly as Open or Blocked with the missing tests listed. A self-hosted runner on a developer's Windows PC is explored if hosted runners are not free.
  - Deterministic-testing policy applied: a deterministic planner fixture returns valid plans, invalid schemas, unsupported tools, clarification requests, unauthorized arguments, approval-triggering plans, and model timeout or unavailable errors. The real model is evaluated separately in Sub-Task 8.
  - Skipped tests carry a recorded reason. A failed security-sensitive check requires a fix and a regression test, not a manual override. The pipeline has been used for at least one merged pull request in Phase 7, with the run record kept.
- **Todo List**:
  - [ ] Implement CI Gates A–E and the deterministic planner fixture.
  - [ ] Settle D-95 and D-96 (P7-14).
  - [ ] Evidence from a merged PR run showing all gates.
- **Relevant Context**:
  - Roadmap Step 14; tracker P7-14; risk P7-R1
  - Specs: 04.22.2–8, 04.22.14–15, 04.22.17
- **Status**: `[ ] pending`

---

### Sub-Task 7: Packaging, versioning, upgrade, rollback and installation (Steps 15–17; D-100 to D-104)
- **Intent**: Every component has a discoverable version, upgrades and rollbacks are rehearsed, and a non-author can install the system from the written instructions.
- **Expected Outcomes**:
  - D-100 (backend packaging), D-101 (CLI and bridge packaging) and D-102 (version scheme, including what counts as a breaking change per component) settled with the simplest option that installs and upgrades reliably. Backend version exposed through an authenticated or appropriately limited diagnostics endpoint; each bridge reports its version during authenticated communication; tool capability reports include supported tool-schema versions; migrations identify the schema version they establish; the release record captures the passing combination.
  - Compatibility matrix (suggested `docs/operations/compatibility-matrix.md`) with fail-closed rules for unknown or security-sensitive incompatible protocol versions. Mixed-version operation is tested; operations that cannot be proven safe stay disabled. This reuses the existing `protocol_version` and `tool_schema_version` envelope fields and does not rename them (D-24 stays governed by its ADR).
  - First release classified by upgrade class (likely at least C and D). The 6-step upgrade procedure (prepare, validate, protect existing state, deploy, verify, approve or recover) and the bridge upgrade sequence (authenticate, check compatibility, stop accepting new operations, report in-flight operations, reconcile uncertain ones, install preserving credentials and journal, re-authenticate, report version and capabilities, read-only test, re-enable) documented and rehearsed at least once, with one upgrade and one rollback or recovery scenario tested. Rollback limits stated honestly (a created file or launched application cannot be rolled back). D-103 settled.
  - Installation guide, startup and shutdown procedure (based on the Phase 6 D-89 ADR) and incident-response procedure (contain, preserve evidence, assess impact, reconcile operations, restore trust, validate, document) written. Installation covers prerequisites, backend and database setup, CLI, bridge enrollment on each PC, AI runtime and pinned model, configuration without secrets, first-time startup and a smoke test. A developer who did not write the instructions reproduces the install on a clean environment and records deviations. D-104 (bridge distribution and upgrade on three computers) settled.
- **Todo List**:
  - [ ] Settle D-100, D-101, D-102; expose versions; compatibility matrix (P7-15).
  - [ ] Upgrade and rollback procedures and rehearsal; D-103 (P7-16).
  - [ ] Installation, startup and incident documents; non-author validation; D-104 (P7-17).
- **Relevant Context**:
  - Roadmap Steps 15–17; tracker P7-15 … P7-17; risk P7-R4
  - Specs: 04.23.2–6, 04.23.8, 04.23.13, 04.23.16, 03.40.8, 03.39.11, 04.25.11, 04.28.10
- **Status**: `[ ] pending`

---

### Sub-Task 8: Reliability experiments, performance and model-quality measurements (Steps 18–19)
- **Intent**: Ten failure experiments and real-hardware measurements show the system behaves honestly under failure and meets the agreed AI and performance acceptance evidence.
- **Expected Outcomes**:
  - The 10 reliability experiments from 03.40.6, each with initial state, injected failure, expected and observed behaviour and a regression test: backend restart with queued tasks; restart with an operation in flight; database interruption and recovery; model runtime unavailable during planning; device disconnection during execution; duplicate task submission; concurrent attempts to claim the same work; approval expiry or revocation before dispatch; lost bridge response after an external side effect (also covered in Sub-Task 5); restoration from backup with non-terminal tasks present (also covered in Sub-Tasks 4 and 5). Where the outcome cannot be established, uncertainty is preserved instead of a clean recovery being fabricated.
  - Performance measurements on the actual hardware: API latency p50 and p95, task acceptance p95, queue wait and execution time by operation type, model latency and failure rate, CPU, RAM, GPU and VRAM, database query latency, pool pressure and lock contention, bridge response times, retry counts, uncertain outcomes and recovery durations, three-user behaviour, degradation when the model or a device is unavailable. Provisional targets (API read p95 under 500 ms, task acceptance p95 under 1 s) are met, or the measured value, reason and team decision are recorded.
  - AI acceptance evidence (03.40.7): the runtime starts reliably; plans meet the structured contract; invalid plans are rejected; unknown tools and unauthorized operations cannot run; clarification works for ambiguous requests; prompt-injection tests cause no unauthorized side effects; memory and document context stay scoped; model failure does not corrupt task state; three concurrent users stay within D-90 limits; AMD GPU compatibility is demonstrated on the selected machine or the CPU fallback is documented. The fixed evaluation set is run against the D-67 thresholds, and hard safety gates are not offset by a better average.
  - Records in the reliability experiments, performance measurements and AI acceptance evidence documents.
- **Todo List**:
  - [ ] Run and record the 10 reliability experiments (P7-18).
  - [ ] Performance and model-quality measurements on the designated host (P7-19).
- **Relevant Context**:
  - Roadmap Steps 18–19; tracker P7-18, P7-19; risk P7-R2
  - Specs: 03.40.2, 03.40.6, 03.40.7, 04.28.9, 04.22.9
- **Status**: `[ ] pending`

---

### Sub-Task 9: Release candidate preparation and Gate 6 sign-off (Steps 20–21)
- **Intent**: Complete every checklist with cited evidence, resolve all release blockers and record explicit sign-off from all three developers.
- **Expected Outcomes**:
  - Release candidate identified: release version, source revision, schema and migration version, bridge protocol version, tool definitions and schema versions, AI runtime and model versions, security policy and configuration versions, test results and known limitations.
  - 25-item MVP evidence checklist (03.40.10: core product, security and privacy, reliability, AI and context, deployment and documentation, five each) and the 21-item sign-off checklist (04.28.10: product functionality 4, security and privacy 5, reliability 4, AI and context 4, deployment and operations 4) completed with actual evidence, not planned evidence. All 10 release-blocking conditions resolved, or scope explicitly reduced with all three developers' agreement.
  - Release evidence report `docs/releases/p7-evidence.md`: component versions, test results and evidence references, accepted limitations (including the single-host point of failure and the host-compromise limitation), unresolved non-blocking items, D-95 to D-104 statuses, known risks. Any Open or Provisional decision is listed honestly.
  - Joint review: each developer presents their component's evidence. The Gate 6 criteria and the Definition of Done in 03.40.12 are reviewed. If the gate fails, the blocker is identified and nonessential scope is reduced or the schedule adjusted; the gate is not marked complete without repeatable tests.
  - Each developer records sign-off in `docs/releases/p7-signoff.md` naming release version and date, what they verified, accepted non-blocking limitations and their decision. Every cited evidence document exists and is non-empty. The tracker is updated with all P7 rows, D-95 to D-104, risks and MVP checklist items, only with test evidence.
- **Todo List**:
  - [ ] Identify the release candidate and complete the 25-item and 21-item checklists (P7-20).
  - [ ] Check release blockers and write the evidence report (P7-20).
  - [ ] Joint Gate 6 review and three-developer sign-off (P7-21).
- **Relevant Context**:
  - Roadmap Steps 20–21 and §7; tracker P7-20, P7-21 and Gate 6 exit criteria
  - Specs: 03.40.8–12, 04.28.5, 04.28.10, 04.28.11
- **Status**: `[ ] pending`
