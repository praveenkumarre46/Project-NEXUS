## 03.40.1 Purpose

The previous sections define NEXUS's individual components and their responsibilities. This section establishes how those components must work together as one dependable product.

NEXUS is not ready merely because the FastAPI server starts, the model generates plans, PostgreSQL stores records or the Windows bridge can create a file. The integrated system must prove that a real user can submit a request, receive a validated plan, pass authorization, execute the intended operation on the correct computer, recover safely from failures and obtain an accurate result.

This section defines:

- The integrated end-to-end architecture.

- The order in which components should be integrated.

- The system-level acceptance scenarios.

- Release-blocking requirements and evidence.

- Final MVP sign-off responsibilities for the three developers.

The central release principle is demonstrated end-to-end behavior, not isolated component readiness.

## 03.40.2 Integrated architecture

The proposed MVP combines the previously defined components into a modular backend and a separate native Windows bridge on each participating computer.

NEXUS CLI

Request submission · Task inspection · Approval · Results

### Shared FastAPI backend

Identity and policy

Authentication, authorization, approvals

Task orchestration

States, scheduling, cancellation, recovery

AI and context

Planning, retrieval, memory

Tool coordination

Registry, device routing, verification

PostgreSQL

Users, devices, tasks, approvals, memory and audit records

Local AI runtime

Planning and context processing on the designated host

Authenticated bridge communication

Target-specific operations · Correlation IDs · Result reconciliation

Developer A PC

Windows bridge and local tools

Developer B PC

Windows bridge and local tools

Developer C PC

Windows bridge and local tools

Illustrative three-device topology. The actual host, network configuration and number of participating devices must be validated before deployment.

### Architectural invariants

1. PostgreSQL is the authoritative source for persisted task and approval state.

2. The AI model proposes plans but cannot authorize or directly execute them.

3. The backend enforces user identity, ownership, policy and task-state transitions.

4. Each Windows bridge enforces its own device and resource restrictions.

5. An accepted task has a durable identifier.

6. External side effects are verified or explicitly classified as uncertain.

7. No user task silently switches to another device.

8. Private memory and task history remain isolated by user.

9. Model unavailability must not corrupt task records or cause unauthorized fallback execution.

10. Critical security and recovery requirements must pass before release.

## 03.40.3 Required end-to-end workflows

The MVP should be accepted against complete user workflows, not merely individual endpoints.

### Workflow A — Search and summarize a document

1. A user authenticates and selects their registered Windows computer.

2. The user submits a request through the CLI.

3. The backend persists the task and returns a task ID.

4. The planner identifies a permitted document-search and reading workflow.

5. The plan passes schema, capability, scope and policy validation.

6. The bridge searches only the configured directory and returns bounded results.

7. The selected document is read through the approved document-processing pipeline.

8. NEXUS generates a bounded summary using the authorized extracted content.

9. The result is persisted with appropriate source references.

10. The CLI displays the actual task state and summary.

Acceptance condition: the summary is based on the document actually read, the source remains within the user's authorized scope, and the result is not presented as successful unless the required processing and verification succeeded.

### Workflow B — Create a file safely

1. The user requests a new output file.

2. NEXUS resolves the intended target device and approved workspace.

3. The planner proposes a create_file operation.

4. The policy engine validates the operation and determines whether approval is required.

5. If approval is required, execution waits for the correct decision.

6. The backend persists the operation intent and dispatches it through the authenticated bridge.

7. The bridge validates the directory, relative path, destination and content limits.

8. The file is created without silently overwriting an existing destination.

9. The operation result is recorded and verified.

10. The CLI reports the destination and outcome accurately.

Acceptance condition: the operation cannot escape the approved directory, overwrite an existing file without a separately supported and authorized workflow, or claim success without sufficient evidence.

### Workflow C — Recover from an uncertain operation

1. NEXUS dispatches a file-creation operation.

2. The bridge performs the operation, but the response is lost.

3. The backend records that the outcome is uncertain rather than assuming failure.

4. On reconnection, NEXUS reconciles the operation using its identity, bridge records and available evidence.

5. The system decides whether the operation succeeded, failed or remains uncertain.

6. NEXUS does not blindly repeat the external side effect.

7. The CLI reports the confirmed outcome or explains what remains unresolved.

Acceptance condition: a lost response does not lead to an unverified success claim or an unsafe duplicate action.

### Workflow D — Approval and cancellation

The system must demonstrate that:

- A consequential operation waits for the required approval.

- An unauthorized user cannot approve it.

- Approval for one operation cannot authorize materially changed arguments.

- Rejection prevents dispatch.

- Expired approval does not authorize execution.

- Cancellation prevents future eligible steps from being dispatched where possible.

- An in-flight side effect is reconciled before final cancellation is claimed.

- A cancelled task cannot be revived by late approval or automatic replanning.

### Workflow E — Three-user isolation

Three developers use the same backend concurrently, each with a separate account and Windows bridge.

NEXUS must demonstrate that:

- Each developer can submit and inspect their own tasks.

- Each bridge executes only authenticated, authorized operations targeting its registered device.

- One user cannot access another user's task, memory, approval or device by changing an identifier.

- Concurrent model requests do not mix private context.

- Device disconnection affects only the relevant task and device routing.

- Fair scheduling and resource limits prevent one user's workload from monopolizing the system.

### Workflow F — Memory and context

A user explicitly saves a non-sensitive project preference, retrieves it in a later authorized request, corrects it and deletes it.

NEXUS must demonstrate that:

- The memory is stored with the correct owner and provenance.

- Relevant requests can retrieve it without retrieving unrelated memories.

- Another user cannot access it.

- A corrected or superseded memory does not continue to mislead planning.

- Deletion removes it from active retrieval and relevant indexes or caches.

- Task history and audit retention follow their separate policies.

- The product accurately describes any backup-retention limitations.

## 03.40.4 Integration order and dependency gates

Integrate components in a sequence that exposes contract and safety problems early.

Gate 1

Backend and persistence

FastAPI, PostgreSQL, migrations, authentication, ownership and health checks.

Gate 2

Durable task lifecycle

Task IDs, legal transitions, idempotent submission, worker claims and status inspection.

Gate 3

Windows bridge

Device authentication, registered tool contracts, scoped filesystem operations and structured results.

Gate 4

Policy and recovery

Approval, cancellation, operation identity, deduplication, uncertain outcomes and reconciliation.

Gate 5

AI planning

Structured proposals, dependency validation, clarification, bounded planning and model-failure behavior.

Gate 6

Memory and context

Private memory lifecycle, authorized retrieval, provenance and context-isolation tests.

Gate 7

Three-user integration

Concurrent requests, device isolation, scheduling, network behavior and resource measurements.

Gate 8

Release candidate

Security regression tests, failure injection, clean installation, backup restoration and final sign-off.

These gates are integration checkpoints, not eight independent projects. The team should continuously merge tested work and preserve an end-to-end path throughout development.

Important: the first working end-to-end flow should use deterministic planning or a mocked planner. Integrate the real local model after the task lifecycle, policy enforcement and bridge contracts are working. This isolates failures and prevents early AI integration from obscuring backend defects.

## 03.40.5 System acceptance requirements

The release candidate must satisfy the following groups of requirements.

| **Group** | **Required evidence** |
| --- | --- |
| Functional correctness | The supported workflows produce their expected verified outcomes |
| Security | Cross-user and cross-device isolation, approval enforcement, filesystem boundaries and credential handling pass tests |
| Reliability | Restart, disconnection, duplicate requests, cancellation and uncertain side effects are handled correctly |
| AI and context | Fixed evaluation set demonstrates bounded plans, appropriate clarification, scope adherence and honest failure handling |
| Performance | Measurements on the actual designated host, including model latency, resource consumption and three-user concurrency |
| Deployment | Fresh installation, documented configuration, database migration and Windows bridge setup succeed |
| Recovery | A verified backup can be restored and nonterminal tasks reconciled safely |
| Operability | Useful health checks, structured diagnostics, stable errors and actionable task history are available |
| Documentation | Developer onboarding, tool contracts, known limitations, recovery procedures and release instructions are current |

A component passing its unit tests does not establish that the integrated system meets these requirements. The release evidence must come from the appropriate unit, integration, contract, security and end-to-end tests.

## 03.40.6 Performance and reliability acceptance

The performance targets proposed in Section 03.27 remain provisional until measured on the actual deployment hardware.

The release candidate should record:

- API response latency, including p50 and p95.

- Task-acceptance latency.

- Queue wait and task execution time by operation type.

- Model latency, failure rate and concurrency behavior.

- CPU, available RAM, GPU and VRAM utilization where measurable.

- Database query latency, pool pressure and lock contention.

- Windows bridge response times, timeouts and disconnect behavior.

- Retry counts, uncertain outcomes and recovery durations.

The initial validation target is three concurrent developers. This is a starting workload, not a claim that the architecture has been proven to scale beyond it.

### Required reliability experiments

Run controlled tests for:

1. Backend restart with queued tasks.

2. Backend restart while a bridge operation is in flight.

3. Database interruption and recovery.

4. Model runtime unavailable during planning.

5. Device disconnection during execution.

6. Duplicate task submission.

7. Concurrent attempts to claim the same work.

8. Approval expiry or revocation before dispatch.

9. Lost bridge response after an external side effect.

10. Restoration from backup with nonterminal tasks present.

For each experiment, record the initial state, injected failure, expected behavior, observed behavior and regression test. If the actual outcome cannot be established, the system must preserve uncertainty instead of fabricating a clean recovery.

## 03.40.7 AI acceptance and model-readiness gate

Because NEXUS is local-first and uses a designated computer with an AMD GPU, model selection must be based on observed compatibility and performance—not a model's published hardware requirements alone.

Before release, the team should demonstrate:

- The selected runtime starts reliably on the chosen host.

- The model produces plans conforming to the documented structured contract.

- Invalid plans are rejected by deterministic validation.

- Unknown tools and unauthorized operations cannot be executed.

- Clarification works for materially ambiguous requests.

- Prompt-injection tests do not result in unauthorized side effects.

- Memory and document context remain correctly scoped.

- Model failure does not corrupt task state.

- Three concurrent users can use the service within the agreed resource and latency limits.

- A CPU fallback is available if the team elects to support it and it meets the required operational behavior.

The exact model, inference runtime, context window and hardware-acceleration path remain open until benchmark results are available.

AI quality should be measured using a fixed evaluation set covering plan validity, tool selection, argument correctness, dependency handling, clarification, context relevance, scope adherence and failure honesty. A model upgrade requires regression evaluation before deployment.

## 03.40.8 Release management and version compatibility

The initial deployment should use a controlled release process rather than having every developer manually modify the shared host.

A release candidate should identify:

- Application version and source revision.

- Database schema and migration version.

- Bridge protocol version.

- Tool definitions and schema versions.

- AI runtime and model version.

- Security policy version.

- Configuration version or documented configuration revision.

- Test results and known limitations.

### Proposed release sequence

1. Freeze the candidate's interfaces and configuration.

2. Run automated unit, integration, contract and security tests.

3. Apply database migrations in a controlled environment.

4. Run end-to-end tests against the actual Windows bridge.

5. Test restart, recovery and backup restoration.

6. Benchmark the selected AI runtime and three-user workload.

7. Review critical and high-severity findings.

8. Prepare a reproducible installation and rollback or recovery procedure.

9. Obtain sign-off from the responsible developers.

10. Deploy to the team and monitor the initial operational period.

Database rollback is not automatically safe after application data or external Windows operations have changed. Prefer tested forward fixes where appropriate, and reconcile external side effects before restoring older task state.

The initial release should also document which API, bridge and tool versions are compatible. Unknown or security-sensitive incompatible protocol versions must fail closed.

## 03.40.9 Three-developer release responsibilities

Each developer owns their implementation area, but no developer can independently declare the whole system release-ready.

| **Owner** | **Primary release evidence** |
| --- | --- |
| Developer 1 — Backend and execution | Task-state correctness, PostgreSQL integrity, authorization, scheduling, concurrency, cancellation and recovery |
| Developer 2 — Windows integration | Device authentication, filesystem safety, tool contracts, local execution, Windows compatibility and operation reconciliation |
| Developer 3 — AI and context | Model/runtime benchmark, structured planning, context isolation, memory lifecycle, prompt-injection evaluation and planning quality |
| All three | End-to-end acceptance, cross-component contract review, security review, clean setup, backup/restore and final sign-off |

### Integration responsibilities

- Shared contracts must be reviewed before parallel implementation depends on them.

- Every cross-component change must include appropriate contract tests.

- Each developer must test their component against the integrated environment, not just a local mock.

- Security-sensitive changes require review beyond the change's primary author.

- A release blocker must have a documented resolution; it cannot be waived merely because the planned delivery date is approaching.

## 03.40.10 MVP release checklist

Use this checklist to track release evidence. It is a planning checklist, not a test runner or an automatic certification.

### NEXUS release evidence

### 0/25

### Core product

Authenticated CLI and durable task IDs

Structured planning and tool validation

Task status, results and history

Supported Windows filesystem operations

Useful errors and diagnostics

### Security and privacy

Cross-user and cross-device isolation

Approval enforcement and revocation

Filesystem scope and no-overwrite safeguards

Secret-safe logs and private service endpoints

Memory authorization and deletion behavior

### Reliability

Idempotent task submission

Operation deduplication and uncertainty handling

Cancellation and restart recovery

Three-user concurrency and bounded queues

Verified backup and restore

### AI and context

Local model/runtime compatibility verified

Fixed planning evaluation set passes agreed thresholds

Prompt-injection regression tests pass

Memory and document context remain isolated

Graceful model-unavailable behavior

### Deployment and documentation

Clean installation succeeds from documented instructions

Migrations and configuration validated

Windows bridge setup and revocation documented

Host recovery and incident procedures documented

Known limitations and release version recorded

Only mark an item complete after reviewing its evidence. These selections are not connected to your repository, CI pipeline or test environment.

## 03.40.11 Release-blocking conditions

NEXUS must not be declared ready for shared team use if any of these conditions remains unresolved:

- A user can access another user's private task or memory without authorization.

- A device can execute an unauthenticated or unauthorized operation.

- A model-generated request can bypass tool restrictions or policy.

- An approval can be reused for a materially different operation.

- Filesystem access can escape the configured scope.

- An uncertain side effect is blindly retried when it may duplicate a consequential operation.

- Task state can be corrupted by concurrent workers or recovery.

- Critical or high-severity security defects remain unresolved.

- The team cannot reproduce installation or safely recover the system.

- The actual model/runtime configuration has not been tested sufficiently for the agreed workload.

A missing optional feature can be documented as a limitation. A failed security invariant cannot be reclassified as optional merely to complete the release.

## 03.40.12 Definition of done

- The full system architecture is implemented and documented consistently.

- All required end-to-end workflows pass on the integrated environment.

- Three developers can use separate accounts and Windows bridges concurrently.

- AI planning, policy enforcement, tool execution and result verification remain separate responsibilities.

- Security, concurrency and failure-injection tests provide reproducible evidence.

- Model/runtime performance is measured on the actual designated host.

- Backup restoration and interrupted-operation reconciliation have been demonstrated.

- The deployment can be reproduced from the written instructions.

- Release-blocking defects are resolved.

- The three developers review and approve the release evidence.

Section exit criterion: the team can demonstrate that NEXUS completes supported tasks safely and reliably on the correct Windows computer, preserves user isolation, recovers honestly from failures and can be installed and operated without undocumented manual intervention.

## Architecture status after Section 03.40

Sections 03.01–03.40 now establish the proposed system architecture, including planning, execution, memory, security, deployment, user experience and release acceptance.

The next logical phase is to close the highest-impact open decisions before creating detailed implementation specifications. In particular, the team needs to validate the actual host hardware and AMD GPU compatibility, choose the local AI runtime and model, finalize bridge communication and authentication, and settle the first release's exact supported tools.
