## 04.01.1 Purpose

NEXUS now has a broad architecture specification. The next task is to turn its unresolved questions into explicit engineering decisions before the team commits to detailed implementation.

An open question should not remain buried in prose across dozens of sections. Each important decision needs:

- A clearly stated question.

- The options being considered.

- A recommended direction, if the available evidence supports one.

- The evidence needed to confirm or reject that recommendation.

- An accountable owner.

- A deadline or dependency.

- A record of the final decision and its consequences.

This is especially important for NEXUS because the shared host, AMD GPU, Windows bridge, AI runtime, database and recovery model interact. A premature decision in one area can force unnecessary redesign elsewhere.

Rule: a recommendation is not a confirmed architectural decision until its owner records the evidence and the team accepts the result.

## 04.01.2 Decision statuses

Use four statuses throughout the project.

| **Status** | **Meaning** |
| --- | --- |
| Confirmed | Explicitly agreed or established by reliable evidence |
| Provisional | Recommended for planning, but still requires validation |
| Open | Multiple viable options remain; no final selection |
| Blocked | Cannot be decided responsibly until a dependency or missing fact is resolved |

For example, the team has confirmed a local-first AI preference and a designated inference computer. The exact model and GPU acceleration path remain open because the AMD GPU model and available VRAM have not yet been established.

Do not mark a decision confirmed simply because a developer started implementing one option.

## 04.01.3 Prioritized decision register

The following register identifies the decisions that can materially affect architecture, security, cost or the 10–12-week schedule.

Priority P0 = resolve before dependent implementation; P1 = resolve before feature integration; P2 = resolve when the need is demonstrated.

| **ID** | **Decision** | **Current status** | **Priority** |
| --- | --- | --- | --- |
| ADR-001 | Shared backend host and operating environment | Provisional | P0 |
| ADR-002 | AMD GPU compatibility and AI inference runtime | Open | P0 |
| ADR-003 | Initial local AI model | Open | P0 |
| ADR-004 | Windows bridge communication method | Provisional: polling | P0 |
| ADR-005 | User and device authentication | Open | P0 |
| ADR-006 | Exact initial tool set and supported operations | Provisional | P0 |
| ADR-007 | Database schema and task-state persistence | Provisional architecture | P0 |
| ADR-008 | Worker coordination and concurrency limits | Provisional | P0 |
| ADR-009 | Document formats and extraction libraries | Open | P1 |
| ADR-010 | Memory retrieval implementation | Provisional: PostgreSQL-first hybrid | P1 |
| ADR-011 | Approval expiry and Tier 2 operation policy | Open | P0 |
| ADR-012 | Backup frequency, location and recovery targets | Open | P0 |
| ADR-013 | Network transport security and TLS | Open | P0 |
| ADR-014 | Shared project memory and device sharing | Deferred | P2 |
| ADR-015 | Interactive GUI automation | Deferred | P2 |
| ADR-016 | Measurable performance and model-quality targets | Provisional | P1 |

The register is a planning artifact. Its statuses should be updated only when the relevant evidence is available.

## 04.01.4 ADR-001 — Shared backend host

Question: Which computer will host FastAPI, PostgreSQL and initially the local AI runtime?

### Options

- Option A — Designated team computer: one existing computer hosts the services.

- Option B — Dedicated always-on computer: use a separate machine if available and suitable.

- Option C — Split deployment: run the backend and database on one host and inference on another.

Provisional recommendation: start by evaluating Option A, because it fits the zero-budget constraint and avoids unnecessary deployment complexity. Do not commit until the actual host's availability, memory, storage and network reliability are checked.

### Evidence required

- Confirm the host operating system and whether the computer is available during team working hours.

- Measure available RAM and disk space under ordinary workloads.

- Identify whether other applications compete for GPU, RAM or CPU resources.

- Verify that the host can be reached from two other Windows computers on the LAN.

- Confirm firewall configuration and private service binding.

- Demonstrate backend startup and recovery after a host restart.

Owner: Developer 1, with Developer 3 validating inference requirements.

Decision gate: choose the host before finalizing the deployment configuration and model benchmark environment.

## 04.01.5 ADR-002 — AMD GPU compatibility and inference runtime

Question: Which local inference runtime can reliably use the actual AMD GPU, and is GPU acceleration necessary for the initial release?

The GPU's exact model and VRAM are still unknown. Consequently, the team must not assume that a runtime supporting one AMD configuration will support this machine or the chosen model.

### Options

- GPU-accelerated inference, if the exact hardware and software stack are supported.

- CPU inference as a baseline and fallback.

- A split approach in which the application remains local-first while inference runs on a separately validated host.

### Validation sequence

1. Record the GPU model, dedicated VRAM, driver version, operating system and available system memory.

2. Identify candidate runtime and model combinations compatible with that exact configuration.

3. Run a small, repeatable inference test.

4. Measure cold-start latency, warm inference latency, memory consumption and failures.

5. Test two or three concurrent user requests.

6. Repeat with CPU inference if practical.

7. Record the configuration that produced each measurement.

Do not select the model based only on its parameter count, a benchmark from different hardware or an assumption that CUDA support implies AMD support.

Owner: Developer 3.

Decision gate: select a runtime and fallback strategy before integrating the production planner. Deterministic planning and mock AI should remain available while this work is underway.

## 04.01.6 ADR-003 — Initial AI model and planning quality

Question: Which model can produce sufficiently reliable structured plans within the available hardware and latency budget?

### Candidate evaluation criteria

Evaluate candidate models against the same fixed set of representative NEXUS requests:

- Select the correct registered tool.

- Produce valid arguments for the selected tool.

- Identify dependencies between steps.

- Ask for clarification when the target or intended outcome is ambiguous.

- Respect the supplied device and resource scope.

- Handle unsupported requests honestly.

- Resist instructions embedded in untrusted documents.

- Produce output within the configured context and response limits.

Record both successful and unsuccessful cases. A model that generates fluent explanations but repeatedly produces invalid plans is not suitable merely because it feels conversational.

Provisional recommendation: select the smallest model that passes the required planning-quality checks and fits the measured resource budget. Keep the model provider behind the adapter defined in Section 03.13.

Owner: Developer 3.

Decision gate: agree on a candidate only after the runtime benchmark and fixed evaluation set have been run. Policy enforcement must remain deterministic regardless of the selected model.

## 04.01.7 ADR-004 — Windows bridge communication

Question: How should the shared backend send operations to each Windows bridge?

### Options

| **Option** | **Advantages** | **Trade-offs** |
| --- | --- | --- |
| Outbound polling | Straightforward firewall behavior; bridge initiates connections | Adds polling delay and repeated requests |
| Persistent outbound connection | Lower dispatch latency; fewer repeated polls | Connection lifecycle and reconnect handling are more complex |
| Backend-initiated inbound connection | Direct dispatch model | Requires inbound reachability and more difficult firewall configuration |

Provisional recommendation: start with outbound polling. It matches the current LAN topology and avoids requiring an inbound listener on every developer's computer.

Before implementation, the team must define:

- Bridge authentication and credential rotation.

- How the bridge claims work intended for its registered device.

- How duplicate deliveries are handled.

- How the backend learns that a device is offline.

- Polling interval, request timeout and backoff.

- How revoked devices are prevented from receiving new operations.

- How in-flight operations are reconciled after reconnection.

Owner: Developer 2, with Developer 1 responsible for the backend contract.

Decision gate: settle the transport envelope and failure semantics before implementing bridge polling or persistent connections.

## 04.01.8 ADR-005 — User and device authentication

Question: How will team members authenticate to NEXUS, and how will each Windows bridge authenticate independently?

Two separate decisions are required.

### User authentication

Possible starting approaches include local password-based accounts or an existing identity provider if the team already has one suitable for the deployment.

For a zero-budget local deployment, local accounts are a reasonable candidate, but the team must define password hashing, login rate limits, session lifetime, credential storage, logout, account disabling and recovery.

### Device authentication

Every bridge needs a unique credential or an equivalent authenticated identity mechanism. A device ID alone is not authentication.

The design must support credential revocation, replacement and verification of the intended target device. The bridge must not accept a request simply because it contains a familiar task or device identifier.

Provisional recommendation: use a small, explicit authentication design rather than building a custom identity platform. Keep user credentials and device credentials separate.

Owner: Developer 1 for user authentication; Developer 2 for bridge identity.

Decision gate: authentication and ownership checks must be agreed before enabling real filesystem operations.

## 04.01.9 ADR-006 — Exact initial tool set

Question: Which Windows operations will NEXUS actually be allowed to execute in its first release?

The architecture has identified four candidates, but the precise schemas and limits remain open.

| **Tool** | **Proposed initial behavior** | **Main unresolved detail** |
| --- | --- | --- |
| search_files | Search a configured directory within defined limits | Search depth, result count, hidden files and time limit |
| read_document | Extract text from supported files | Supported formats, file size and extraction limits |
| create_file | Create a new file in an approved workspace without overwriting | Content limit, safe path rules and verification |
| launch_application | Launch an approved application by logical ID | Application allowlist, arguments and launch verification |

The initial release should not add arbitrary shell execution merely to make the assistant appear more capable. Nor should the team imply that launching an application means NEXUS can perform arbitrary GUI interactions inside it.

For each enabled tool, finalize its input/output schema, risk classification, required permissions, timeout, retry behavior, verification method and bridge implementation version.

Owner: Developer 2, with Developer 1 responsible for policy and registry integration.

Decision gate: enable each tool only after its contract, local enforcement and negative tests are complete.

## 04.01.10 ADR-007 — Database and task-state persistence

Question: Which persistence mechanisms are necessary for reliable task execution without introducing unnecessary infrastructure?

Provisional recommendation: use PostgreSQL as the authoritative store for users, devices, tasks, steps, approvals, memories and audit records. Use schema migrations and real PostgreSQL integration tests.

Before implementation is considered stable, settle:

- Final table relationships and ownership constraints.

- Atomic task submission and duplicate-request handling.

- Atomic worker claims and stale-worker protection.

- Legal task and step transitions.

- Approval/cancellation race behavior.

- Operation-intent persistence before dispatch.

- Handling of external side effects that cannot be rolled back with a database transaction.

- Retention and deletion rules.

A separate message broker is not required by the current architecture. Reconsider one only if measurements or operational requirements justify it.

Owner: Developer 1.

Decision gate: finalize the minimum schema and transition invariants before implementing the full orchestrator.

## 04.01.11 ADR-008 — Worker coordination and concurrency

Question: How many tasks, model requests and operations may run concurrently, and how will work be claimed safely?

Provisional recommendation: begin with conservative limits and PostgreSQL-backed coordination. Do not assume that every resource benefits from unrestricted parallel execution.

The team needs explicit limits for:

- Active tasks per user.

- Queued tasks per user and globally.

- Active worker claims.

- Concurrent inference requests.

- Operations in flight per device.

- Database connection usage.

- Document extraction and model context sizes.

The first load test should simulate three developers using different devices, including overlapping model requests, a slow document read and one disconnected bridge.

Owner: Developer 1 for scheduler and persistence; Developer 3 for inference measurements; Developer 2 for device-side limits.

Decision gate: configure initial values from observed behavior, then record the limits in deployment configuration and tests.

## 04.01.12 ADR-009 — Document formats and extraction

Question: Which file formats must the first release support?

Plain text is the simplest initial format. PDF and DOCX are candidates, but their inclusion should depend on extraction correctness, resource use and dependency compatibility.

The team should test:

- Normal text documents.

- Large files and malformed inputs.

- Documents with tables and unusual layouts.

- Files that contain prompt-injection instructions.

- Unsupported and partially readable files.

- Extraction limits and cancellation behavior.

Scanned-document OCR, spreadsheet semantics and presentation analysis should remain outside the initial scope unless a validated requirement justifies them.

Owner: Developer 3 for extraction and context quality; Developer 2 for authorized Windows file access.

Decision gate: publish a supported-format list and explicit size and processing limits before describing document reading as a supported feature.

## 04.01.13 ADR-010 — Memory retrieval implementation

Question: Should NEXUS use PostgreSQL search alone initially, or add semantic vector retrieval?

Provisional recommendation: start with PostgreSQL-backed lexical retrieval and an abstraction that can combine lexical and semantic results. Add embedding-based retrieval after measuring whether it materially improves the fixed memory evaluation set.

This avoids committing early to a separate vector database and additional operational burden.

The team must decide:

- Which local embedding model, if any, is supported.

- How lexical and semantic candidates are merged and ranked.

- How ownership filters are applied before context is exposed to the model.

- How stale or superseded memories are handled.

- How updates and deletion invalidate indexes and caches.

- How retrieval quality and unauthorized-exposure risk are measured.

Owner: Developer 3.

Decision gate: deliver user-scoped memory CRUD and deterministic lexical retrieval before introducing more complex semantic infrastructure.

## 04.01.14 ADR-011 — Approval expiry and consequential actions

Question: Which operations require approval, how long does an approval remain valid, and who may authorize it?

The architecture establishes risk tiers and operation-bound approvals, but the exact expiry and Tier 2 policy are unresolved.

Provisional recommendation:

- Read-only operations are allowed only within explicitly granted scopes.

- Limited, reversible operations may run without per-operation approval when the user's configured permissions cover them.

- Consequential operations require explicit approval if the operation is supported at all.

- Prohibited operations cannot be authorized through an approval.

- An approval is invalid if the target, arguments, scope or applicable authorization changes materially.

- Expired or rejected approvals never dispatch the operation.

The team must define the default approval lifetime, who can approve, behavior after policy changes and the initial list of consequential operations.

Owner: Developer 1, with Developer 2 reviewing bridge enforcement.

Decision gate: finalize approval semantics before enabling write operations on real user workspaces.

## 04.01.15 ADR-012 — Backup, retention and recovery objectives

Question: How much data loss and downtime can the initial deployment tolerate?

The previous backup design proposed daily backups as a starting point, but this is not yet an approved recovery objective.

The team must choose:

- Backup frequency.

- Backup destination separate from the main host.

- Encryption and access controls.

- Backup retention period.

- Recovery Point Objective (RPO): acceptable data-loss window.

- Recovery Time Objective (RTO): acceptable restoration time.

- Database and configuration recovery procedure.

- Memory deletion behavior when historical backups contain older copies.

- Handling of revoked devices and uncertain tasks after restoration.

Provisional recommendation: start with a documented PostgreSQL backup and a separate protected copy, then perform a real restore drill. Do not promise a particular RPO or RTO until the team measures it.

Owner: Developer 1.

Decision gate: a verified backup and restoration procedure must exist before the system becomes a shared daily-use tool.

## 04.01.16 ADR-013 — Network transport and TLS

Question: What security is required for traffic between the three developer computers and the shared host?

A private LAN reduces exposure but does not, by itself, prove that all clients or network traffic are trustworthy.

The team must establish:

- Which interfaces the API binds to.

- Which clients can reach the API.

- Whether the network is trusted enough for the selected transport.

- Whether TLS is required for API and bridge communication.

- How credentials are protected in transit.

- Which firewall rules are necessary.

- How unauthorized access to the database and model endpoint is tested.

- How the deployment behaves if the host address changes.

Provisional recommendation: no public internet exposure, no router port forwarding, PostgreSQL accessible only to the backend, and bridge communication authenticated regardless of whether TLS is selected.

Owner: Developer 1 for API deployment; Developer 2 for bridge networking.

Decision gate: demonstrate access from a second computer and verify the intended network boundaries before team rollout.

## 04.01.17 ADR-014 — Shared project memory and device sharing

Question: Should developers share project context or operate on each other's Windows computers?

Provisional recommendation: defer both features in the initial release. Keep personal memory private and devices owner-only until the project has a defined membership and delegation model.

If collaboration becomes necessary, specify:

- Explicit project membership.

- Permitted shared memory and resource types.

- Who may create, edit and delete shared information.

- Whether another user may execute operations on a shared device.

- How revocation affects queued and in-flight tasks.

- How audit records identify the requesting user and executing device.

Owner: Shared decision; Developer 1 leads authorization design.

Decision gate: implement sharing only when a real use case justifies the additional permission model and its tests.

## 04.01.18 ADR-015 — Interactive GUI automation

Question: Does the MVP need to click, type or navigate inside application windows, or is restricted filesystem and application launching sufficient?

The current architecture does not establish general GUI automation as an MVP capability.

Provisional recommendation: defer general GUI automation. First validate the restricted tools and task-recovery model. GUI automation introduces additional complexity involving interactive sessions, window focus, UI changes, user presence and ambiguous results.

If later approved, define a narrow set of supported applications and actions, including their risk classification, evidence of success and cancellation behavior.

Owner: Developer 2.

Decision gate: do not claim support for arbitrary GUI tasks until a separate capability specification and safety evaluation exist.

## 04.01.19 ADR-016 — Performance and model-quality targets

Question: What measurements define acceptable performance and planning quality for the first release?

The previously proposed API targets—such as p95 read latency below 500 ms and task acceptance below one second—are hypotheses to validate, not confirmed service-level objectives.

The team must establish separate targets for:

- API responsiveness.

- Task acceptance and queue delay.

- Model planning latency.

- Document extraction time.

- Supported tool execution time.

- Three-user concurrency.

- Model plan validity and task completion quality.

- Recovery time after device or backend failure.

- Resource consumption on the designated host.

Provisional recommendation: establish a reproducible baseline first, then set targets that fit the actual hardware and supported workload. Keep API latency separate from model latency and end-to-end task duration.

Owner: Developer 1 for API and execution metrics; Developer 3 for model quality and inference performance; Developer 2 for Windows operation timing.

Decision gate: performance targets and model evaluation thresholds must be documented before the final release candidate.

## 04.01.20 Decision closure schedule

The decision process should run alongside development rather than becoming a separate phase that delays all implementation.

| **Timing** | **Decisions to close** | **Required output** |
| --- | --- | --- |
| Week 1 | Host, GPU/runtime investigation, authentication direction, initial tool scope | Host assessment, hardware inventory, draft contracts |
| Week 2 | Bridge transport, database baseline, task-state rules, network boundaries | Reviewed architecture decisions and integration contracts |
| Weeks 3–4 | Worker coordination, filesystem restrictions, initial tool schemas | Tested task-to-bridge vertical slice |
| Weeks 5–6 | Approval policy, retry/recovery rules, document formats | Safe execution and recovery evidence |
| Weeks 7–8 | Model selection, planning thresholds, memory retrieval | Benchmark results and evaluation report |
| Weeks 9–10 | Performance limits, retention, operational recovery | Three-user integration and restore evidence |
| Weeks 11–12 | Remaining release-critical decisions and accepted limitations | Final release record and sign-off |

This schedule follows the existing 12-week roadmap. If the team compresses the schedule to 10 weeks, it must close dependencies earlier; security, recovery and integration gates must not be removed to compensate.

## 04.01.21 Architecture Decision Record template

Use one record per significant decision. The following is the proposed template for the repository.

# ADR-XXX: <Decision title>

- Status: Proposed

- Date: YYYY-MM-DD

- Owner: <Developer>

- Related sections: <Section IDs>

## Context

What problem or unresolved question requires this decision?

## Requirements and constraints

- Confirmed requirements:

- Technical constraints:

- Security constraints:

- Budget and schedule constraints:

## Options considered

1. Option A:

2. Option B:

3. Option C, if relevant:

## Decision

What was selected, and what evidence supports it?

## Consequences

- Benefits:

- Trade-offs:

- Security implications:

- Operational implications:

- Migration or compatibility implications:

## Validation evidence

- Tests:

- Benchmarks:

- Hardware/runtime details:

- Reviewers:

## Revisit conditions

What evidence or requirement change would justify reopening this decision?

The record should explain why an option was selected, not just name the technology. For example, “use polling” is less useful than documenting the measured dispatch delay, firewall behavior and recovery semantics that justified polling.

## 04.01.22 Definition of done

- Every P0 decision has an owner and a defined validation method.

- Confirmed decisions are separated from provisional recommendations.

- Hardware and runtime assumptions have been tested on the designated host.

- Authentication, bridge transport, database persistence and task-state contracts are agreed.

- The initial tool set and approval rules are explicit.

- Recovery, retention and network security decisions are recorded.

- Deferred features have a documented scope boundary.

- Significant decisions are stored as version-controlled ADRs.

- Changes to a decision identify affected components, tests and documentation.

- The team knows which unresolved decisions block implementation and which can remain open safely.

Section exit criterion: every architecture-critical uncertainty has a responsible owner, a concrete evidence-gathering plan and an explicit status. Developers can begin dependent work without accidentally treating assumptions as confirmed requirements.

## Recommended immediate action

Do not attempt to close all 16 decisions at once. Start with the three decisions that most strongly influence the deployment and AI architecture:

1. Identify the designated host and exact AMD GPU model.

2. Validate a local inference runtime on that hardware.

3. Confirm the initial Windows bridge communication and authentication design.

The first two determine whether the preferred local AI configuration is feasible. The third determines how the backend can safely reach each developer's computer.
