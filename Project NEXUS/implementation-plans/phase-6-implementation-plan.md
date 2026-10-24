# Phase 6 (Team Integration) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-6-team-integration.md`](../roadmap/phase-6-team-integration.md) (Steps 0–19) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2g (P6-00 … P6-19). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal (Gate 5): all three developers use one NEXUS backend concurrently, each with a private workspace, and no user can reach another user's tasks, memory, devices or results. The LAN deployment is reachable only through the intended network path. Setup, startup, shutdown and recovery are reproducible. Gate 5 requires repeatable tests on the actual three-PC deployment; a demonstration without repeatable tests does not count (04.28.05).

Gate 5 items (04.28.05): three registered users and devices; cross-user and cross-device isolation; concurrent task and shared-resource tests; restart, disconnect and recovery scenarios; reproducible setup for each developer. Phase 5 outputs feed this gate, and any unfinished Phase 5 item must be closed here.

Decisions settled here: D-85 to D-94 (plus PC-02). Carried-over decisions still relevant: D-05 (WSL networking mode, verified in Sub-Task 3), D-28 and D-32 (lease duration, heartbeat and poll interval, confirmed under three-user load), D-60 (inference concurrency, superseded by D-90 where values differ). Owners are assigned by the team (suggested rotation: BE = Dev A, WB = Dev B, AI = Dev C). Every multi-user test needs all three developers present.

Excluded from Phase 6: shared project memory (D-91), public internet exposure or cloud deployment, advanced priority scheduling or a dedicated message broker (unless tests show PostgreSQL is insufficient), device sharing between users (D-87, owner-only for the MVP), tamper-evident audit storage, automated scaling, multi-inference-host setups, full document indexing and automated CI for multi-device hardware tests.

Honest-status points to confirm in Sub-Task 1:
- The authoritative isolation test list is the 15-row table in 03.37.10, and the scheduling test list is the 15-row table in 03.28.12 (plus the 04.12.11 test plan). The Roadmap did not extract these tables, so they must be read row by row before the tests are written.
- D-88 (PostgreSQL row-level security) must not be claimed as database-enforced isolation unless it is configured and tested at the database boundary (03.37.7).
- D-94 is the bridge local persistence decision. It continues the open chain D-29 → D-47 → D-94 (journal storage) and stays Open or Provisional until the three-user disconnect tests give evidence.
- D-86 (TLS) is settled honestly: either TLS is required now, or the trusted-isolated-LAN assumption and the condition for adding TLS are written down.
- The host-compromise limitation (03.37.9) is recorded as a known limitation: logical isolation does not protect users against a fully compromised backend host.
- Device-unavailable and backend-unavailable are shown differently in the CLI. The error code involved is `DEVICE_UNAVAILABLE` from the 15-code catalogue; the task and step states are unchanged (`PARTIALLY_SUCCEEDED` is never added, and `UNCERTAIN` stays a step state).
- The wire casing and envelope field names (D-23, D-24) and error-code reconciliation (D-25) remain governed by their own ADRs; this phase adds no new contract fields without the change process.

---

## Sub-Tasks

### Sub-Task 1: Entry check and learning blocks (Steps 0–5)
- **Intent**: Confirm Phase 5 delivered what Phase 6 needs and give the team one shared model of ownership boundaries, scheduling, LAN networking, disconnection and Gate 5 evidence before multi-user tests are run.
- **Expected Outcomes**:
  - Phase 5 unchecked items copied to the tracker's carried-over items with owner and target phase. Present from Phase 5: CLI vocabulary and `contracts-v0.5`, task event table, artifact schema, task history CLI, `read_document` bridged and tested, D-71 to D-84 ADRs, migrations through Phase 5.
  - Blocking check: all three developers must have working accounts and registered devices before any isolation test can run (blocks P6-09). If migrations through Phase 5 are missing, P6-06 and P6-09 are blocked.
  - Learning blocks with short notes:
    - Four ownership boundaries (user identity, device identity, resource scope, operation authorization) and the eight isolation rules, each marked tested or untested; the host-compromise limitation recorded in a known-limitations document.
    - Scheduling: task eligibility vs resource availability, the 10-step dependency resolution, round-robin skipping, starvation safeguards, and the rule that a task waiting for approval consumes no model slot or worker.
    - Networking: the four network boundaries, WSL 2 NAT vs mirrored modes, the six connectivity checks from a second machine, and why a successful localhost request does not prove LAN reachability.
    - Disconnection: the six-step response to an unavailable device, configuration-change handling, the host failure cascade, and the replacement-host rule (no dispatch of restored work until database, credentials, registrations and active-task recovery are validated).
    - Gate 5: a concrete test for each of the five Gate 5 items, classification of the 15 isolation scenarios and 15 scheduling tests as covered or new, and a measurable minimum fairness result recorded as a metric.
  - Each developer demonstrates the Roadmap "Verify" checks, for example tracing which tasks run next when User A has three queued tasks, User B has one awaiting approval and User C has one eligible task.
- **Todo List**:
  - [ ] Entry check, carried items and blocking checks (P6-00).
  - [ ] Learning blocks 1–5 and Gate 5 test plan draft (P6-01 to P6-05).
- **Relevant Context**:
  - Roadmap Steps 0–5; tracker P6-00 … P6-05
  - Specs: 03.37.2, 03.37.3, 03.37.9, 03.28.03–06, 04.12.02–05, 03.22.04, 03.22.07–09, 04.12.08, 04.28.05, 03.37.10, 03.28.12, 04.12.11
- **Status**: `[ ] pending`

---

### Sub-Task 2: Database isolation audit and authorization review (Step 6; D-88, D-91)
- **Intent**: Confirm that every user-owned query applies an ownership filter before any multi-user test, and settle the two scope decisions that bound the isolation claims.
- **Expected Outcomes**:
  - D-91 settled: shared project memory is out of Phase 6 scope; isolation tests assume personal memory only (03.37.5).
  - D-88 settled: application-level ownership filters are the primary enforcement. PostgreSQL row-level security is recorded as optional defense-in-depth and claimed only if configured and tested. The ADR states plainly what is and is not enforced at the database level.
  - An authorization audit checklist (suggested `docs/security/authorization-audit.md`) with a line-by-line check of every repository function that returns a list or updates a record, confirming the ownership filter. Background workers take the authoritative owner and target device from persisted task records, never from session state or a previous claim.
  - Connection-pool session behaviour verified: a database session cannot carry a previous user's authorization context (verify whether the pool library resets session state).
  - Mutation tests for missing ownership filters (removing a filter makes a test fail). `contracts-v0.6` tagged after the audit (suggestion). Non-author security review recorded.
- **Todo List**:
  - [ ] Settle D-91 and D-88.
  - [ ] Complete the authorization audit and worker-ownership check.
  - [ ] Verify connection-pool session behaviour; tag `contracts-v0.6` (P6-06).
- **Relevant Context**:
  - Roadmap Step 6; tracker P6-06; risk P6-R3
  - Specs: 03.37.3, 03.37.5, 03.37.7, 03.37.12
- **Status**: `[ ] pending`

---

### Sub-Task 3: LAN deployment, network security and TLS (Steps 7 and 16; D-85, D-86)
- **Intent**: The backend is reachable by the three developers' PCs and only by them; PostgreSQL and the model runtime are never exposed to the LAN; the TLS decision is made honestly.
- **Expected Outcomes**:
  - D-85 settled: the designated host's LAN address by static DHCP reservation, stable local hostname or another reliable option, with what to do when it changes.
  - FastAPI bound to a specific LAN interface (not `0.0.0.0` unless justified), with the bind address and port in deployment configuration, not source code. Port policy table completed from 03.22.04 for FastAPI, PostgreSQL, the model runtime and the bridge: port, bound interface, permitted machines and enforcing firewall rule (suggested `docs/operations/port-policy.md`). No public router port forwarding.
  - WSL 2 networking mode (D-05) confirmed and any portproxy rules recorded. Windows-native firewall steps are flagged.
  - The six connectivity checks run from a second machine and recorded (suggested `docs/operations/connectivity-checks.md`): FastAPI reachable, PostgreSQL not reachable from an ordinary client, model endpoint not exposed, each bridge authenticates and polls, one bridge disconnect/reconnect cycle, and repeat after a host restart. Needs at least two other Windows PCs.
  - D-86 settled with an honest statement: TLS required before Gate 5 if the LAN is shared with untrusted devices or machines can be reached by others; otherwise the trusted-isolated assumption and the condition for adding TLS are documented. An IP address or network location is never treated as authentication.
  - The ten minimum network-security requirements from 03.22.08 checked: API and bridge authentication, authorization on every protected resource, firewall rules, no public forwarding, no direct database access for clients, no shared bridge credential across devices, replay and duplicate protection, bounded request sizes, timeouts and connection limits, safe handling of malformed requests, and redaction of secrets and private content from network diagnostics.
  - Security test from a non-enrolled LAN machine: every sensitive route returns 401 and no data. Each bridge uses its own per-device credential. Non-author security review recorded.
- **Todo List**:
  - [ ] Settle D-85; bind address, port policy and firewall (P6-07).
  - [ ] Connectivity checks from a second machine and WSL mode confirmation (P6-07).
  - [ ] Settle D-86; security checklist and non-enrolled-machine test (P6-16).
- **Relevant Context**:
  - Roadmap Steps 7 and 16; tracker P6-07, P6-16; risk P6-R1
  - Specs: 03.22.04, 03.22.07, 03.22.08, 03.22.11
- **Status**: `[ ] pending`

---

### Sub-Task 4: Three-user enrollment, startup procedure and PC-02 (Step 8; D-87, D-89)
- **Intent**: All three developers have registered accounts and devices, the startup and shutdown procedures are documented and tested, and the deployment placement question is closed.
- **Expected Outcomes**:
  - D-87 settled: owner-only device access for the MVP; other users cannot target a device unless a sharing feature is designed and tested.
  - D-89 settled: the 8-step startup sequence (PostgreSQL ready, migrations applied, FastAPI health, model runtime readiness if AI is required, bridges started or connected, bridge identity and health verified, tasks left active at shutdown reconciled, normal dispatch enabled after checks pass) and the 6-step shutdown sequence from 03.22.10 recorded in a startup/shutdown document and followed end to end by a non-author with no errors.
  - Three user accounts created and one Windows bridge enrolled per developer using the Phase 1 procedure. Each bridge authenticates and polls. Device ownership is attributed correctly.
  - PC-02 answered: actual placement of backend, PostgreSQL and model runtime recorded with confirmed hardware, address and service locations in the host-readiness document, and the tracker question closed.
  - Device ownership boundary test: a task submitted from Dev B's credentials targeting Dev A's device is rejected with an authorization failure.
- **Todo List**:
  - [ ] Settle D-87 and D-89; write the startup and shutdown procedure.
  - [ ] Enroll all three accounts and devices.
  - [ ] Answer PC-02; run the device-ownership test (P6-08).
- **Relevant Context**:
  - Roadmap Step 8; tracker P6-08
  - Specs: 03.22.06, 03.22.10, 03.37.4
- **Status**: `[ ] pending`

---

### Sub-Task 5: Cross-user isolation tests (Step 9)
- **Intent**: Prove that tasks, memory, history and devices are private to their owner using three real accounts on the actual deployment.
- **Expected Outcomes**:
  - The 15 scenarios in 03.37.10 read row by row. For each: what is tested, the input, the expected outcome, and whether an existing test covers it or a new one is needed. All 15 implemented or confirmed, plus the positive cases (a user can still reach their own tasks, memory, devices and authorized resources).
  - Minimum negative cases: User B reading User A's task by ID gets not-found; cancelling or approving User A's operation is an authorization failure; targeting User A's device is an authorization failure; reading User A's memory is not-found; updating it is an authorization failure; User B's history and `nexus history` return only User B's tasks; User B's context assembly never includes User A's memories.
  - Concurrent context test: overlapping tasks from User A and User B each receive context scoped to their own memories only (03.37.6).
  - Revocation test: disabling User B's account with a queued task blocks that task and rejects new requests; re-enabling recovers.
  - Report records each scenario's result; zero cross-user exposure is required. All three developers review.
- **Todo List**:
  - [ ] Read the 03.37.10 table and classify coverage.
  - [ ] Implement missing tests and run all 15 plus positive cases.
  - [ ] Run the concurrent context and revocation tests (P6-09).
- **Relevant Context**:
  - Roadmap Step 9; tracker P6-09 (all three PCs required)
  - Specs: 03.37.3, 03.37.4, 03.37.6, 03.37.8, 03.37.10
- **Status**: `[ ] pending`

---

### Sub-Task 6: Concurrent scheduling, resource limits, fairness and performance (Steps 10, 11, 14, 15; D-90, D-92, D-93)
- **Intent**: Three users submitting overlapping work receive fair access to shared resources, limits hold under real load, and the scheduler design is judged from measurements.
- **Expected Outcomes**:
  - Three-user concurrent submission: each task gets a unique ID, persists under the correct owner, appears only in its owner's history and is dispatched only to its target device.
  - Round-robin fairness: User A submits 5 tasks, B and C one each; the recorded selection order shows B and C are not consistently dequeued last. Blocked-task exclusion: a task waiting for approval consumes no worker or model slot and does not delay other users. Per-user active-task limit holds, with further submissions queued, not rejected outright. A cross-owner device submission is rejected at authorization. Inference requests are queued fairly when all three users request AI planning together, respecting the inference concurrency limit.
  - Queue admission: at configured capacity the backend returns a capacity rejection that the CLI communicates clearly. Per-device operation limits hold even if several users target one device. Under overload, bounded retries with backoff are observed and a busy model runtime is not hammered.
  - D-90 settled from the three-user benchmark: confirmed values for per-user active tasks, per-device operations and inference concurrency, superseding D-60 where they differ. D-28 and D-32 confirmed under load with no unexpected lease expiry.
  - Fairness and starvation: User A continuously submitting while User B submits one task shows a bounded wait for User B; background work makes progress without starving interactive tasks; approval-waiting tasks consume no scheduling cycles; the CLI shows `QUEUED` while a task waits for capacity. The 15 scheduling tests in 03.28.12 (and the 04.12.11 plan) are read and covered. D-92 recorded as "deferred, round-robin sufficient" if starvation tests pass, otherwise priority aging is implemented without allowing any prohibited or unauthorized operation to run.
  - Performance under three-user load (suggested `docs/operations/p6-benchmark.md`): API read p95, task acceptance p95, queue wait by user, model inference time, bridge operation time, DB query time, CPU, RAM and GPU/VRAM, with multi-step tasks. Results compared with the provisional targets in 04.28.09 (API read p95 under 500 ms, task acceptance p95 under 1 s); shortfalls documented with reasons. D-93 recorded: PostgreSQL sufficient for the three-user deployment, or a broker to be investigated before Phase 7.
  - A minimum fairness metric (for example, no eligible task waits more than N cycles while capacity is available) is recorded as a number, not a qualitative judgement.
- **Todo List**:
  - [ ] Concurrent submission and round-robin validation (P6-10).
  - [ ] Resource limits under load; settle D-90 (P6-11).
  - [ ] Fairness and starvation tests; settle D-92 (P6-14).
  - [ ] Three-user performance benchmark; settle D-93 (P6-15).
- **Relevant Context**:
  - Roadmap Steps 10, 11, 14, 15; tracker P6-10, P6-11, P6-14, P6-15; risks P6-R2, P6-R5
  - Specs: 03.28.04–09, 03.28.11, 03.28.12, 04.12.05, 04.12.06, 04.12.11, 03.37.6, 04.28.09
- **Status**: `[ ] pending`

---

### Sub-Task 7: Backend restart and bridge disconnect under concurrent load (Steps 12–13; D-94)
- **Intent**: A backend restart or one developer's bridge disconnecting never corrupts any user's task state, never produces a false success and never affects other users.
- **Expected Outcomes**:
  - Backend restart test: all three developers have tasks `RUNNING` or `DISPATCHED`; the backend is forced to restart (simulate a crash where possible). Startup recovery loads non-terminal tasks and claims, identifies stale claims and operations needing reconciliation, recovers still-valid queued tasks, re-evaluates dependencies and eligibility, revalidates device status, permissions and approvals before dispatch, and resumes only safe operations. Results: queued tasks are re-queued and dispatched; dispatched tasks are reconciled before any retry; no false `SUCCEEDED`; the task timeline shows the restart; all three users can resume. The replacement-host rule from 03.22.09 is documented.
  - D-94 evaluated: whether the Phase 3 bridge journal (D-47) is sufficient for three-user concurrency or an additional local persistence layer is needed, addressing the case where a Windows action succeeds but the backend never receives the response. It is recorded as Provisional or Open as evidence dictates.
  - Disconnect test: Developer A's bridge drops while User A has a dispatched task; User B and C tasks continue; User A's step becomes `UNCERTAIN` after the D-49 threshold; no new dispatch to the disconnected device.
  - Reconnect test: the backend re-evaluates the recovered operation from the bridge journal; completed work becomes `SUCCEEDED`; an unknown outcome stays `UNCERTAIN` and is never fabricated as success or failure.
  - Revocation during concurrent use: a queued task is not dispatched to the revoked device; an in-flight operation is reconciled; other users are unaffected. The CLI `--watch` shows `DEVICE_UNAVAILABLE` for a device problem and a distinct message for backend unavailability. Native Windows steps are flagged.
- **Todo List**:
  - [ ] Backend restart test with all three users (P6-12).
  - [ ] Settle D-94; disconnect, reconnect and revocation tests (P6-13).
- **Relevant Context**:
  - Roadmap Steps 12–13; tracker P6-12, P6-13; risk P6-R4
  - Specs: 04.12.08, 04.12.09, 03.22.09, 03.22.10, 03.37.8
- **Status**: `[ ] pending`

---

### Sub-Task 8: Reproducible setup, Gate 5 acceptance, evidence and hand-off (Steps 17–19)
- **Intent**: Each developer can reproduce the deployment without help, every Gate 5 item has repeatable evidence on the actual three-PC deployment, and the hand-off to Phase 7 is honest.
- **Expected Outcomes**:
  - The setup guide updated with three-user enrollment, startup and shutdown sequence, connectivity checks, firewall rules, model runtime setup and device registration. Each developer who did not write the instructions sets up from a clean clone using the guide alone and can install dependencies, start PostgreSQL, run migrations, start FastAPI, install and start the bridge, register the device, and submit, watch and inspect a task. LAN reachability is verified from each PC. The 9 reproducible-deployment acceptance items in 03.22.13 are checked. Failures observed are added to the troubleshooting guide.
  - 15 acceptance scenarios (suggested `docs/testing/p6-acceptance.md`) run with all three PCs simultaneously: three simultaneous submissions without contamination; User B cannot read User A's history; User B cannot target User A's device; A's bridge disconnects (A's task becomes `UNCERTAIN`, B and C continue); backend restart with all three busy and no false `SUCCEEDED`; revoked account's queued task blocked; queue flooding by A still schedules B; simultaneous AI planning respects the D-90 limit; concurrent context shows no memory leakage; Developer C reproduces setup from a clean clone; PostgreSQL and the model runtime are unreachable from a non-enrolled machine and sensitive routes return 401; device revoked mid-dispatch is reconciled, not retried blindly; an approval-waiting task does not block other users or consume slots; startup from scratch after host reboot follows the documented order with passing health checks; three-user performance is measured against the documented targets. The 03.37.10 and 03.28.12 lists are confirmed as covered.
  - Non-author security review: cross-user access denied in every tested scenario; device ownership enforced; authorization audit complete; no sensitive route reachable from a non-enrolled machine; D-86 documented honestly; no shared bridge credential; no private content or credentials in ordinary logs. Critical and high defects fixed first.
  - Gate 5 checklist from the tracker satisfied, including D-85 to D-94 recorded with honest statuses (Open and Provisional entries stay that way where evidence is incomplete), PC-02 answered, and no critical or high defect open.
  - Release evidence report `docs/releases/p6-evidence.md`: deployment configuration, authorization audit, isolation, concurrency, restart and disconnect results, performance measurements, network security status, decision statuses, known limitations (including the single-host point of failure and the host-compromise limitation), unresolved decisions and untested scenarios. Tracker updated, including MVP checklist item 14 only with test evidence. Hand-off pairing held.
  - Phase 7 entry list: full acceptance suite, backup and restore rehearsal, security regression testing, performance regression testing, hardening review (rate limits, error handling, input validation), installation and upgrade documentation, release candidate sign-off. Any Gate 5 item not fully resolved becomes a Phase 7 blocker.
- **Todo List**:
  - [ ] Reproducible clean-install validation by each developer (P6-17).
  - [ ] Gate 5 acceptance matrix on all three PCs (P6-18).
  - [ ] Security review, Gate 5 review, evidence report, tracker update and Phase 7 hand-off (P6-19).
- **Relevant Context**:
  - Roadmap Steps 17–19 and §5; tracker P6-17 … P6-19 and Gate 5 exit criteria; risks P6-R6, P6-R7
  - Specs: 03.22.13, 04.28.04, 04.28.05, 03.37.10, 03.28.12, 04.12.11
- **Status**: `[ ] pending`
