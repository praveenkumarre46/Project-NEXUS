## 04.28.01 Purpose

This section consolidates the NEXUS specification into an execution plan for three developers over 10–12 weeks.

The objective is to stop planning in isolation and begin building an integrated product that can safely perform useful tasks on each developer's Windows computer while retaining relevant context and personal memory.

The plan must balance four outcomes:

1. Working functionality: users can complete real, supported computer tasks.

2. Reliable execution: tasks survive restarts, disconnections and uncertain outcomes.

3. Useful intelligence: local AI can plan tasks and use relevant context without receiving authority to bypass policy.

4. Team readiness: all three developers can install, run, test and recover the system.

Planning assumption: 12 weeks is the baseline. Ten weeks is an accelerated target only if the integration gates are met early. Essential security, recovery and isolation work must not be cut to meet the shorter timeline.

## 04.28.02 The delivery strategy

Build NEXUS as a sequence of working vertical slices rather than completing every backend feature before testing Windows execution.

Milestone 1 — Establish the foundation

Repository, contracts, PostgreSQL, migrations, authentication and hardware validation

Milestone 2 — First real Windows operation

Durable task → authenticated bridge → scoped file search → persisted result

Milestone 3 — Safe task execution

Policy, approval, file creation, cancellation, idempotency and recovery

Milestone 4 — AI and context

Validated local model, structured planning, memory and retrieval evaluation

Milestone 5 — Integrated team deployment

Three users/devices, isolation, performance tests, backups and installation

Milestone 6 — Release candidate

Failure injection, recovery drills, security review, documentation and sign-off

A deterministic or mocked planner should be used in the early vertical slice. This lets the team validate the task lifecycle, policy and bridge protocol before model quality becomes another source of uncertainty.

## 04.28.03 Twelve-week schedule

| **Week** | **Primary objective** | **Required deliverable** |
| --- | --- | --- |
| 1 | Establish the project | Repository, developer setup, hardware inventory, initial architecture decisions |
| 2 | Freeze shared contracts | Initial API, task states, bridge protocol, error catalogue and database migration workflow |
| 3 | Implement durable backend tasks | Authenticated API, PostgreSQL persistence, task submission and status retrieval |
| 4 | Complete first vertical slice | Windows bridge, authenticated dispatch, scoped file search and end-to-end result |
| 5 | Implement policy and permissions | Tool registry, user/device ownership, directory scopes and approval lifecycle |
| 6 | Implement safe side effects | Create-only file tool, operation deduplication, cancellation and initial recovery tests |
| 7 | Validate local AI feasibility | Runtime/model benchmark on the designated computer, adapter and structured planner |
| 8 | Integrate context and memory | Explicit memory CRUD, scoped retrieval, grounding and injection tests |
| 9 | Complete user-facing workflows | CLI history, results, approvals, diagnostics and supported document processing |
| 10 | Validate team integration | Three users/devices, concurrency, isolation, disconnect and restart tests |
| 11 | Harden the release | Backup restoration, security regression, performance testing and upgrade/recovery rehearsal |
| 12 | Release candidate and sign-off | Clean installation, full acceptance suite, documentation and defect review |

These are target weeks, not guaranteed completion dates. If hardware or model validation takes longer than expected, the team should use a tested CPU fallback or adjust the schedule rather than weakening safety checks.

## 04.28.04 Work allocation for three developers

The team should divide implementation by component ownership while sharing responsibility for contracts, security and end-to-end testing.

### Developer 1 — Backend, persistence and execution

Primary ownership

- FastAPI API and application services.

- PostgreSQL schema, migrations and transaction boundaries.

- Authentication, authorization and user/device ownership.

- Task state machine, worker claims and scheduling.

- Operation identity, idempotency, cancellation and recovery.

- Approval lifecycle, audit records and task results.

- Backup and restore workflow.

### Developer 2 — Windows bridge and computer operations

Primary ownership

- Native Windows bridge and device enrollment.

- Bridge authentication, polling and protocol compatibility.

- Tool registry integration and capability reporting.

- Safe directory mapping and Windows path validation.

- File search, supported document reading and create-only file creation.

- Allowlisted application launching.

- Local operation journal, deduplication and external-effect verification.

### Developer 3 — AI, planning and context

Primary ownership

- Local runtime and model feasibility benchmark.

- Model adapter and structured plan generation.

- Plan validation integration and clarification behavior.

- Context assembly and explicit personal memory.

- Lexical and semantic retrieval behind a stable interface.

- Document summarization and source-grounded responses.

- Model evaluation, prompt-injection tests and quality regression reports.

### Shared responsibilities

All three developers must:

- Review changes to shared contracts.

- Review security-sensitive changes outside their own component.

- Contribute to integration, concurrency and failure-injection tests.

- Participate in clean-install and recovery exercises.

- Update documentation when behavior or configuration changes.

- Demonstrate their component working with the actual integrated system.

Ownership is not a silo. Developer 1 cannot independently redefine the bridge protocol, Developer 2 cannot independently expand tool permissions, and Developer 3 cannot make the model authoritative over execution.

## 04.28.05 Milestone gates

Work advances when the required evidence exists—not merely when the calendar reaches a particular week.

Gate 1 — End of Week 2: Contracts agreed

Required:

- Shared identifiers and task/step states.

- API and bridge message contracts.

- Initial tool schemas and error catalogue.

- Database migration workflow.

- Hardware inventory started and AI validation owner assigned.

If contracts are still changing independently, do not expand parallel implementation.

Gate 2 — End of Week 4: First vertical slice works

Required:

- An authenticated user submits a task.

- The backend persists it and returns a task ID.

- The intended Windows bridge receives an authenticated operation.

- Scoped file search returns a structured result.

- The result and task state are persisted and visible in the CLI.

- Duplicate submission and unauthorized device tests pass.

Gate 3 — End of Week 6: Safe side effects

Required:

- Tool policy and approval enforcement.

- Safe file creation without silent overwrite.

- Operation deduplication and recovery rules.

- Cancellation and disconnection behavior.

- Tests for lost responses and uncertain external outcomes.

Gate 4 — End of Week 8: AI and memory integrated

Required:

- A validated local runtime and selected model, or a documented blocker and tested fallback.

- Structured plans and application-side validation.

- User-scoped memory and context retrieval.

- Prompt-injection and unsupported-action tests.

- Evidence-grounded summaries and honest failure reporting.

Gate 5 — End of Week 10: Team integration

Required:

- Three registered users and devices.

- Cross-user and cross-device isolation.

- Concurrent task and shared-resource tests.

- Restart, disconnect and recovery scenarios.

- Reproducible setup for each developer.

Gate 6 — End of Week 12: Release candidate

Required:

- Full end-to-end acceptance suite.

- No unresolved critical or high-severity security defects.

- Backup restoration and upgrade/recovery rehearsal.

- Measured performance and model quality.

- Installation, operations and troubleshooting documentation.

- Explicit team sign-off.

If a gate fails, the team should identify the blocker, reduce nonessential scope or adjust the schedule. A gate must not be marked complete based on a demonstration that lacks repeatable tests.

## 04.28.06 First two weeks: detailed execution checklist

The first two weeks should produce an environment and a contract that all three developers can use. They should not be spent designing more architecture documents.

### Week 1 — Establish the foundation

### Week 1 checklist

0/8

Create the shared Git repository and agreed directory structure

All three

Establish branching, pull-request review and coding standards

All three

Verify Python, WSL 2, PostgreSQL and test environment setup

Developer 1

Inventory designated host hardware, AMD GPU and available memory

Developer 3

Test LAN connectivity from another Windows computer

Developer 1 + 2

Define the first bridge tool contract and file-search scope

Developer 2 + 1

Define the planner interface and deterministic test fixtures

Developer 3 + 1

Agree on task lifecycle, IDs and stable error format

All three

### Week 2 — Freeze contracts and prove persistence

### Week 2 checklist

0/7

Commit initial API and bridge contract definitions

All three

Create initial PostgreSQL schema and migrations

Developer 1

Implement basic authentication and ownership checks

Developer 1

Implement bridge enrollment and authenticated connectivity prototype

Developer 2

Implement a mock planner that returns a validated structured plan

Developer 3

Add contract tests and a PostgreSQL integration-test environment

All three

Record unresolved runtime, transport and security decisions

All three

These checklists are planning aids; they do not inspect the repository or confirm that any task has been completed.

## 04.28.07 Weekly team workflow

A small team can coordinate with a lightweight process.

### At the start of each week

- Select a small set of measurable deliverables.

- Identify dependencies between developers.

- Agree on any contract changes before implementation begins.

- Define the tests required to demonstrate each deliverable.

- Reserve time for integration rather than allocating every day to isolated coding.

### During the week

- Work on short-lived feature branches.

- Keep pull requests focused.

- Run component tests before requesting review.

- Review contract, permission and persistence changes with affected developers.

- Integrate frequently enough to expose incompatible assumptions early.

- Record blockers and update the decision register.

### At the end of each week

Each developer demonstrates:

1. What works in the integrated environment.

2. Which automated tests pass.

3. Which requirements remain incomplete.

4. What changed in contracts or configuration.

5. Which failures or risks were discovered.

6. What the next deliverable depends on.

Important: code merged into the main branch is not the same as a completed feature. A feature is complete only when it works through its intended interface and passes its acceptance tests.

## 04.28.08 Integration and test requirements

The integrated system must be tested across component boundaries, not just within individual modules.

| **Test level** | **What it proves** |
| --- | --- |
| Unit | Individual logic behaves as intended |
| PostgreSQL integration | Transactions, constraints, uniqueness and claims work against the real database |
| Contract | API, planner, tool and bridge messages remain compatible |
| Windows integration | The native bridge enforces its local permissions and handles real filesystem behavior |
| Security | Ownership, approvals, revocation and tool restrictions cannot be bypassed in tested cases |
| Reliability | Restarts, timeouts, duplicate delivery and uncertain outcomes are handled safely |
| AI evaluation | Planning quality, structured output, grounding and injection resistance meet the agreed criteria |
| End-to-end | The actual CLI, backend, database, AI runtime and Windows bridge work together |
| Deployment and recovery | A clean installation, upgrade and restore can be performed using documented procedures |

The real model should not be required for every unit test. Deterministic fixtures should cover application logic; the selected model should run through its dedicated evaluation suite and integration tests.

## 04.28.09 Performance and capacity acceptance

The specification previously proposed these initial targets:

- API read latency: p95 below 500 ms.

- Task acceptance latency: p95 below 1 second.

- Three concurrent users on the intended deployment topology.

These are provisional targets, not yet demonstrated results.

Before release, the team should measure:

- API latency separately from task completion time.

- Queue wait, model inference and Windows tool execution time.

- CPU, RAM, GPU/VRAM and database resource use.

- Behavior under three concurrent users.

- Degradation when the model is unavailable or the target device disconnects.

- Recovery time for representative interrupted operations.

The team should select final targets based on real measurements and expected use. A model that works for one developer in isolation may not be adequate for three concurrent users on a 16 GB host.

## 04.28.10 Release sign-off checklist

Use this as the final gate before calling the initial NEXUS release ready.

### Release readiness

### 0/21

Only check items after reviewing actual test evidence. This checklist does not run tests or verify the release automatically.

### Product functionality

CLI supports task submission, status, history, approval, cancellation and results.

Scoped file search and supported document reading work.

Create-only file creation and allowlisted application launching work.

Local AI planning and user-controlled memory are integrated.

### Security and privacy

Cross-user task and memory access is denied.

Device authentication, ownership and revocation work.

Unknown tools and unauthorized resource paths are rejected.

Approvals are bound to the exact operation and revalidated before dispatch.

Private content and credentials do not leak into ordinary logs.

### Reliability

Duplicate submissions and operation deliveries are handled safely.

Backend restart and bridge disconnection are tested.

Uncertain external effects are reconciled before unsafe retries.

Cancellation and partial success are reported accurately.

### AI and context

The selected local runtime and model have been evaluated on the actual host.

Invalid plans cannot dispatch tools.

Prompt-injection and unsupported-request tests pass.

Retrieved context is scoped, relevant and appropriately grounded.

### Deployment and operations

All three developers can install and run the system.

The deployment is reachable only through the intended network boundaries.

A protected backup can be restored successfully.

Upgrade, rollback limitations and incident runbooks are documented.

### Release blockers

The following must block release:

- Any unresolved critical or high-severity security defect.

- Cross-user or unauthorized cross-device access.

- A path or tool restriction that can be bypassed in a tested scenario.

- Unsafe replay of a potentially completed external operation.

- Unrecoverable task-state corruption.

- An untested or non-reproducible installation.

- Missing required recovery or backup procedures.

- A local model configuration that has not passed the required safety evaluation.

If a required capability cannot be completed safely within the timeline, the team must explicitly reduce the release scope or delay the release. It must not label an unsafe or unverified capability as complete.

## 04.28.11 Final project sign-off

Before implementation begins, the team should agree on the following:

- The MVP scope and exclusions are accepted.

- Component ownership and cross-review responsibilities are understood.

- The first two weeks' deliverables are assigned.

- Shared contracts have a defined owner and review process.

- Hardware and runtime validation have an early milestone.

- Integration and release gates are understood.

- Safety and recovery requirements are not negotiable scope cuts.

- Remaining decisions have owners and closure criteria.

The final release sign-off should record the release version, test results, unresolved non-blocking defects, known limitations, deployment instructions and approval from the team.

Section exit criterion: the team has a measurable delivery plan, assigned work, explicit integration gates and objective release conditions. The specification is ready to become an implementation baseline.
