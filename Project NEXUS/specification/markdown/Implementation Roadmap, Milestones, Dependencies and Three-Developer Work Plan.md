## 03.25.1 Purpose

This section translates the NEXUS architecture into an executable plan for a three-developer team working over 10–12 weeks, with zero required paid infrastructure and a local-network deployment target.

The roadmap prioritizes a working, safe end-to-end system over building every subsystem independently and integrating them at the end.

The project has two equally important goals:

1. Product goal: NEXUS can understand useful requests, perform a restricted set of computer tasks on the correct Windows computer, and report reliable results.

2. Engineering goal: the team learns and demonstrates practical backend engineering—database transactions, concurrency, authorization, asynchronous execution, persistence, recovery, testing and performance measurement.

The roadmap is a proposal. The exact schedule depends on developer availability, the designated host's hardware, AMD GPU compatibility, and how difficult native Windows integration proves to be.

## 03.25.2 Delivery strategy

NEXUS should be built vertically: establish the smallest complete workflow, then add capabilities without weakening its safety or reliability.

The first complete workflow should be:

A user submits a request in the CLI → the backend creates a durable task → the planner proposes a supported operation → policy validates it → the correct Windows bridge executes it → the backend records the result → the CLI reports the outcome.

Initially, the workflow should use a deterministic or mocked planner and a safe read-only tool. The local AI runtime can be integrated after the execution, authorization and persistence contracts work independently.

This sequencing avoids making the AI model a prerequisite for testing database correctness, task-state transitions, device routing and failure recovery.

### Scope priorities

P0

Working foundation

Authentication, device identity, PostgreSQL persistence, versioned contracts, task lifecycle, restricted Windows bridge, policy enforcement, audit and automated tests.

P1

Useful AI companion

Local model integration, structured planning, hybrid context retrieval, user-controlled memory, human approval and robust multi-step task reporting.

P2

Post-MVP expansion

Broad GUI automation, complex application workflows, advanced dashboards, multiple inference hosts and sophisticated distributed infrastructure.

The priorities do not mean AI and memory are optional product goals. They mean the team establishes safe execution foundations first, then integrates and evaluates the AI and memory capabilities against the same delivery milestones.

## 03.25.03 Twelve-week delivery roadmap

Baseline proposal: 12 weeks, with a possible 10-week delivery if integration and hardware validation go smoothly.

## W1–2

Foundation

Milestone 1 — Development environment and contracts

- Create repository, development setup and test structure.

- Validate the designated host, network access and AMD GPU/model-runtime options.

- Establish FastAPI, PostgreSQL and migrations.

- Agree on task states, identifiers, API schemas and bridge protocol.

- Implement a minimal authenticated API and health checks.

Exit: all three developers can run the project and pass the baseline integration tests.

## W3–4

Execution

Milestone 2 — First safe computer operation

- Implement durable task submission and status retrieval.

- Implement the task state machine and worker-claim mechanism.

- Register a Windows bridge for each developer's computer.

- Implement search_files in a restricted test directory.

- Add device authentication, authorization and cross-user isolation tests.

- Demonstrate the full CLI-to-bridge-to-CLI workflow.

Exit: a user can search an authorized directory on their own computer and receive a persisted result.

## W5–6

Safety

Milestone 3 — Controlled actions and recovery

- Implement the tool registry and deterministic policy engine.

- Add approval requests and approval-bound operation validation.

- Implement safe document reading and create-only file creation.

- Add cancellation, duplicate submission protection and bounded retries.

- Test bridge disconnection, duplicate delivery and uncertain outcomes.

- Persist task steps, operation attempts and required audit events.

Exit: supported operations obey permissions, and failures do not trigger blind retries.

## W7–8

Intelligence

Milestone 4 — Local AI and context

- Benchmark candidate model/runtime combinations on the designated host.

- Integrate a replaceable model adapter.

- Add structured planning and clarification handling.

- Implement user-scoped memory and hybrid retrieval behind defined interfaces.

- Add prompt-injection tests and validate model outputs against registered tools.

- Measure inference latency, memory use and multi-user contention.

Exit: the AI can propose valid plans for a defined evaluation set without bypassing policy enforcement.

## W9–10

Integration

Milestone 5 — Three-user integrated MVP

- Run the complete system across all three Windows computers.

- Add task history, memory management and useful diagnostics.

- Test concurrent task submissions and database locking behavior.

- Test restarts, host outages and bridge reconnections.

- Add reproducible setup instructions and clean-install testing.

- Fix integration defects before adding more capabilities.

Exit: the three-user MVP passes the agreed functional, security and recovery tests.

## W11–12

Hardening

Milestone 6 — Release candidate

- Run adversarial and failure-injection tests.

- Measure performance with three concurrent users.

- Test backup restoration and task reconciliation.

- Validate Windows startup, credentials, firewall rules and LAN-only exposure.

- Review logs for private data and secrets.

- Freeze MVP scope, document known limitations and demonstrate the final workflow.

Exit: release criteria pass, unresolved high-risk defects are addressed, and each teammate can install and use NEXUS independently.

### Ten-week compression rule

A 10-week version is reasonable only if the team meets early exit criteria and avoids scope expansion. Compress documentation and optional enhancements, not security, concurrency testing, integration or recovery work. If AMD inference compatibility is difficult, use a CPU-capable fallback for development while keeping the runtime interface replaceable; do not silently assume GPU acceleration will work.

## 03.25.04 Three-developer work allocation

The team can work in parallel, but only after shared contracts are agreed. The assignments below are proposed ownership areas, not isolated silos.

Developer 1 — Backend, persistence and execution

Primary ownership

- FastAPI application and public API.

- PostgreSQL schema, migrations and transactions.

- Task lifecycle, worker coordination and idempotency.

- Policy integration, cancellation, recovery and audit persistence.

- Backend integration and concurrency tests.

Developer 2 — Windows bridge and local tools

Primary ownership

- Native Windows bridge process.

- Device registration and authenticated bridge protocol.

- Filesystem scope validation and supported document reading.

- Safe file creation and application-launch allowlisting.

- Local operation deduplication, bridge recovery and Windows-specific tests.

Developer 3 — AI runtime, planning and context

Primary ownership

- Local inference benchmarks and model adapter.

- Structured planner and clarification behavior.

- Context assembly and user-scoped memory.

- Hybrid retrieval and model evaluation.

- Prompt-injection, schema-validation and AI failure tests.

### Shared responsibilities

All three developers must review:

- Security-sensitive contracts and authorization behavior.

- Changes to shared schemas and state transitions.

- End-to-end tests and release-blocking defects.

- Backup restoration and uncertain-operation recovery.

- Performance measurements and scope decisions.

A component owner is responsible for implementation and first-line tests, not for unilaterally changing shared contracts.

## 03.25.05 Integration checkpoints

Do not wait until Week 9 to integrate the work.

| **Checkpoint** | **Deadline** | **Demonstration** |
| --- | --- | --- |
| IC-1 | End of Week 2 | All components agree on schemas; baseline API and DB work |
| IC-2 | End of Week 4 | One complete request reaches the correct Windows bridge |
| IC-3 | End of Week 6 | Approval, authorization and recovery rules are enforced |
| IC-4 | End of Week 8 | Model planner uses the same trusted tool contracts |
| IC-5 | End of Week 10 | Three users operate their own registered computers |
| IC-6 | End of Week 12 | Release candidate passes security, reliability and deployment checks |

Each checkpoint should produce a working demonstration, test evidence and a list of known defects. A verbal claim that a feature is implemented does not count as an integration checkpoint.

## 03.25.06 Dependency order

The critical path is the sequence of work that determines the earliest realistic completion date.

The workstreams can overlap, but several dependencies are non-negotiable:

- The bridge and backend need a shared operation contract before either side can reliably integrate.

- The orchestrator needs a defined state machine before implementing concurrency and recovery.

- The policy engine needs stable tool metadata before it can enforce risk classifications.

- The planner needs a trusted tool catalogue and output schema before generating executable proposals.

- Memory retrieval needs ownership and privacy boundaries before retrieved information is included in planning context.

- Release testing needs a stable end-to-end workflow before performance results are meaningful.

The AMD GPU and local-model benchmark is an early validation task, not a reason to delay the entire backend. If the preferred model configuration is unsuitable, the team should preserve the provider interface and test the rest of the product independently.

## 03.25.07 Definition of done

A feature is not done merely because the happy path works on one developer's machine.

Every MVP feature must satisfy the relevant checklist:

- Contract and expected behavior documented.

- Authentication and authorization checks implemented where required.

- Unit tests cover normal and invalid inputs.

- Integration tests cover database or bridge behavior where applicable.

- Errors are mapped to stable error codes.

- Logging excludes credentials and unnecessary private content.

- Failure and retry behavior are documented.

- Relevant security and concurrency tests pass.

- The feature works in the shared development environment.

- Setup or operational documentation is updated.

For operations with external side effects, add tests for duplicate delivery, timeout ambiguity, cancellation and recovery wherever applicable.

## 03.25.08 Scope control

A 10–12 week project can easily expand beyond its delivery capacity. The following changes should be treated as separate scope proposals rather than silently added to the MVP:

- Full visual control of the desktop through arbitrary mouse and keyboard actions.

- Unrestricted PowerShell, shell or Python execution.

- Browser automation across arbitrary websites.

- Multiple distributed AI inference hosts.

- A separate message broker or microservice architecture without demonstrated need.

- Complex multi-user memory sharing.

- An administrative web dashboard.

- Always-listening voice interaction.

- Public internet deployment.

A proposed addition should state its user value, engineering cost, security impact, dependencies and which existing work would be delayed or removed.

Scope rule: if a new feature threatens the core workflow or the security/reliability exit criteria, defer it.

## 03.25.09 Project risks and mitigations

| **Risk** | **Impact** | **Mitigation** |
| --- | --- | --- |
| AMD GPU/runtime incompatibility | Local AI is slower or unavailable | Benchmark early; keep inference replaceable; retain a CPU fallback for development |
| Designated host unavailable | Shared API and inference stop working | Persist state, document recovery and avoid unsafe automatic retries |
| Contract drift across developers | Late integration failures | Shared schemas, fixtures, reviews and frequent integration checkpoints |
| Windows path-security defects | Unauthorized file access or writes | Logical directory IDs, independent bridge checks and adversarial path tests |
| Concurrent task races | Duplicate execution or inconsistent state | PostgreSQL-backed claims, uniqueness constraints, fencing and concurrency tests |
| AI generates invalid plans | Tasks fail or behave unpredictably | Structured output validation, bounded retries and policy enforcement |
| Prompt injection | Model proposes unauthorized actions | Treat retrieved content as untrusted and enforce permissions outside the model |
| Excessive feature scope | MVP misses deadline | Freeze the MVP boundary and require explicit trade-off decisions |
| Inadequate recovery testing | Lost or duplicated side effects | Failure-injection tests and a restore/reconciliation drill |
| Team members cannot reproduce setup | Integration stalls | Pinned dependencies, documented onboarding and clean-install verification |

### Early warning indicators

Review the following at least once per week:

- The end-to-end workflow is broken for more than one checkpoint.

- Shared schemas change without coordinated updates.

- A security-sensitive feature has no negative tests.

- Model integration blocks work that should be testable without a model.

- The team cannot explain the state of an interrupted operation.

- A critical task depends on undocumented machine-specific setup.

- New features are added while high-risk defects remain open.

If any of these occur, stop expanding functionality and resolve the dependency first.

## 03.25.10 Release gates

NEXUS must pass all mandatory release gates before the team uses it for real computer operations beyond its restricted test environment.

Gate 1 — Security

No known critical or high-severity security defects remain open. Cross-user access, cross-device access, unauthorized tool calls and approval bypass tests pass.

Gate 2 — Data integrity and recovery

Task transitions, duplicate submissions, concurrent claims and restart recovery are tested. Uncertain external effects are reconciled rather than blindly repeated.

Gate 3 — Three-device integration

Each developer can authenticate, register their own bridge, execute authorized operations on their own computer and inspect their task history.

Gate 4 — Performance and AI evaluation

The team has measured task acceptance latency, model latency, memory consumption and three-user contention on the actual deployment hardware. Any performance targets are based on the agreed benchmark.

Gate 5 — Deployment and recovery

A clean setup succeeds, database migrations are reproducible, the backup can be restored, device credentials are handled safely and network exposure matches the LAN-only design.

## 03.25.11 Open decisions register

| **ID** | **Decision** | **Required by** |
| --- | --- | --- |
| ROAD-01 | Actual weekly availability of all three developers | Week 1 |
| ROAD-02 | Exact designated-host OS, AMD GPU model and VRAM | Week 1 |
| ROAD-03 | Minimum useful model performance and fallback strategy | Week 2 |
| ROAD-04 | Final MVP list of enabled Windows tools | Week 2 |
| ROAD-05 | Polling frequency and task concurrency limits | Before integration testing |
| ROAD-06 | Exact performance targets and test workload | Week 8 |
| ROAD-07 | Final backup frequency, retention, RPO and RTO | Before release |
| ROAD-08 | Whether the release needs GUI automation | Scope decision; default is defer |
| ROAD-09 | Whether the target is a 10-week or 12-week release | End of Week 2, based on evidence |

## 03.25.12 Section acceptance criteria

- The team agrees on the milestone sequence and ownership.

- The first end-to-end workflow is scheduled before AI integration is complete.

- Each milestone has a demonstrable exit condition.

- Shared contracts are established before parallel component development.

- Weekly integration and risk reviews are scheduled.

- Security, concurrency and recovery tests are release requirements, not optional polish.

- The team has a process for deferring scope.

- The final release gate is based on evidence from the actual deployment environment.

### Section exit criteria

The roadmap is ready for execution when each developer knows their ownership area, dependencies, first deliverable and integration checkpoint—and the team has agreed on the minimum conditions for calling NEXUS a successful MVP.
