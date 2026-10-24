## 04.07.01 Purpose

## Section 04.06 defined the first end-to-end workflow. This section converts it into concrete work items that three developers can implement in parallel without inventing incompatible interfaces.

The milestone is still limited to authenticated task submission, durable task tracking and scoped Windows file search. The objective is to prove the shared architecture before introducing live AI planning or additional computer-control capabilities.

### Planning rules

1. Freeze shared contracts before parallel implementation.

2. Assign one primary owner to each work item.

3. Keep database migrations and API changes reviewable.

4. Require tests with each feature, not after integration.

5. Integrate working code continuously instead of waiting for all branches to finish.

6. Do not mark a task complete because its code exists; its acceptance tests must pass.

## 04.07.02 Work breakdown structure

The work is divided into six work packages.

WP-01

Shared contracts and repository foundation

Owner: All developers

Exit gate: Agreed schemas, errors and interface tests

WP-02

Task API and PostgreSQL persistence

Owner: Developer 1

Exit gate: Durable task creation and duplicate protection

WP-03

Windows bridge and scoped search

Owner: Developer 2

Exit gate: Authenticated, bounded Windows file search

WP-04

Deterministic planner and tool proposals

Owner: Developer 3

Exit gate: Valid search proposals; invalid plans rejected

WP-05

Orchestration, integration and recovery

Owner: Developer 1, with all-team review

Exit gate: End-to-end workflow and failure handling

WP-06

CLI, multi-user validation and release evidence

Owner: Shared

Exit gate: Clean setup and acceptance matrix pass

The work packages are a planning structure, not six independent projects. WP-05 depends on the contracts and working components from WP-02 through WP-04.

## 04.07.03 WP-01 — Shared contracts and repository foundation

Owner: all three developers. Coordinator: Developer 1.

Agree on the following artifacts before implementation branches diverge:

| **Artifact** | **Required contents** |
| --- | --- |
| Task API contract | Request, response, status, ownership and duplicate-request behavior |
| Task lifecycle contract | Legal states, transitions and terminal outcomes |
| Tool contract | search_files input/output schema, limits and errors |
| Bridge contract | Device identity, operation envelope, response and timeout behavior |
| Error catalogue | Stable machine-readable codes and user-facing meanings |
| Test fixtures | Valid requests, invalid arguments, authorization failures and failure scenarios |

### Work items

- WP01-01: Create the initial repository structure and development instructions.

- WP01-02: Agree on request IDs, task IDs, step IDs and operation IDs.

- WP01-03: Define the initial task and step state transitions.

- WP01-04: Define the search_files contract and protocol version.

- WP01-05: Add shared contract fixtures and validation tests.

- WP01-06: Agree on configuration names and test-environment isolation.

Acceptance: all three developers can validate the same contract fixtures without relying on undocumented assumptions.

Do not freeze implementation details such as bridge transport, exact dependency versions or database field types until the corresponding architecture decisions have been resolved.

## 04.07.04 WP-02 — Task API and PostgreSQL persistence

Owner: Developer 1

### Deliverables

| **Work item** | **Implementation responsibility** | **Acceptance condition** |
| --- | --- | --- |
| WP02-01 | Database connection and migration setup | Fresh PostgreSQL database migrates successfully |
| WP02-02 | Task and step persistence models | Required ownership, status and ID constraints exist |
| WP02-03 | Task submission endpoint | Valid request creates a durable task |
| WP02-04 | Idempotency handling | Duplicate submissions behave according to the contract |
| WP02-05 | Task status and step queries | Authorized users can inspect their own tasks |
| WP02-06 | State transition service | Invalid transitions are rejected |
| WP02-07 | Persistence integration tests | Concurrency and constraints are tested against PostgreSQL |

### Implementation boundaries

Developer 1 owns the authoritative task state and database transactions. The API layer should call application services rather than updating task records directly.

The first API endpoints are expected to include:

- POST /v1/tasks

- GET /v1/tasks/{task_id}

- GET /v1/tasks/{task_id}/steps

These are proposed endpoints from the earlier API specification. Their schemas should be finalized in WP-01.

### Required failure tests

- PostgreSQL is unavailable during submission.

- Two requests with the same idempotency key arrive concurrently.

- The same key is reused with a different target device.

- A user attempts to read another user's task.

- A stale worker attempts to update a task after losing its claim.

- A task transition violates the agreed state machine.

Exit gate: task creation, retrieval, ownership checks and state transitions work independently of the Windows bridge and AI runtime.

## 04.07.05 WP-03 — Windows bridge and scoped file search

Owner: Developer 2

### Deliverables

| **Work item** | **Implementation responsibility** | **Acceptance condition** |
| --- | --- | --- |
| WP03-01 | Bridge startup and configuration | Bridge loads validated local settings |
| WP03-02 | Device authentication | Invalid or revoked credentials are rejected |
| WP03-03 | Bridge protocol handling | Requests are validated against the shared contract |
| WP03-04 | Tool registry integration | Only registered and enabled tools can execute |
| WP03-05 | search_files implementation | Search stays inside a configured logical directory |
| WP03-06 | Bounded result handling | Depth, duration and result limits are enforced |
| WP03-07 | Operation deduplication and recovery | Duplicate operation IDs are handled safely |
| WP03-08 | Windows security tests | Path traversal and link-related tests run on Windows |

### Implementation boundaries

The bridge owns local filesystem access. It must not trust a path simply because the backend or AI supplied it.

The bridge should accept a logical directory ID such as nexus_test_documents, resolve it through local configuration and validate the operation before accessing the filesystem.

It must not provide a generic shell or PowerShell execution endpoint.

### Required failure tests

- A request targets an unknown directory ID.

- A relative path attempts to escape the configured directory.

- A link or junction points outside the permitted scope.

- The bridge receives an unsupported protocol version.

- A request arrives after device revocation.

- A duplicate operation arrives after a prior successful search.

- The bridge restarts with an operation whose outcome was not recorded.

Exit gate: the Windows bridge can authenticate, execute a bounded search and return a structured result without allowing access outside its configured scope.

## 04.07.06 WP-04 — Deterministic planner and tool proposals

Owner: Developer 3

This work package prepares the boundary between natural-language understanding and tool execution without making the first vertical slice depend on an AI model.

### Deliverables

| **Work item** | **Implementation responsibility** | **Acceptance condition** |
| --- | --- | --- |
| WP04-01 | Planner interface | Application code consumes a documented proposal contract |
| WP04-02 | Deterministic search request handler | Supported requests map to search_files |
| WP04-03 | Structured proposal validation | Malformed proposals are rejected |
| WP04-04 | Capability descriptions | Planner receives only relevant registered capabilities |
| WP04-05 | Context fixture interface | Tests can supply controlled context without a live model |
| WP04-06 | Invalid-plan evaluation fixtures | Unknown tools, invalid arguments and scope-expansion attempts are rejected |

### Implementation boundaries

Developer 3 does not own authorization or task state. The planner may propose a search operation, but the backend must independently validate the tool, arguments, target device, resource scope and policy.

For the initial milestone, use explicit supported request forms or a small deterministic parser. Do not label arbitrary text matching as general natural-language understanding.

The live model adapter, model benchmark and hybrid memory retrieval remain separate deliverables.

Exit gate: the backend receives a valid, structured search proposal—or a clear unsupported/clarification result—and never needs to trust the planner as an authority.

## 04.07.07 WP-05 — Orchestration, integration and recovery

Primary owner: Developer 1. Supporting owners: Developers 2 and 3.

This package joins the components into the actual vertical workflow.

### Deliverables

1. Persist the task before confirming acceptance.

2. Claim eligible work using the agreed concurrency-control mechanism.

3. Obtain a validated search proposal.

4. Validate authorization and policy before dispatch.

5. Persist operation intent before contacting the bridge.

6. Dispatch the operation to the specified registered device.

7. Validate response identity and correlate it with the operation.

8. Persist the result and update task state through legal transitions.

9. Expose task progress and results through the API.

10. Reconcile uncertain operations rather than blindly replaying them.

### Integration checkpoints

1. Checkpoint A — API to database

2. Submit and retrieve a task without executing a Windows operation.

3. Checkpoint B — Bridge contract

4. Send a test operation to the correct bridge and reject an unauthorized target.

5. Checkpoint C — Complete search

6. Submit a request from the CLI and obtain persisted search results from Windows.

7. Checkpoint D — Failure recovery

8. Interrupt dispatch or result delivery and demonstrate safe reconciliation.

9. Checkpoint E — Multi-user isolation

10. Execute concurrent tasks for different users and devices without mixing ownership, context or results.

### Required tests

- Backend restart before dispatch.

- Bridge disconnect after dispatch.

- Lost response after a successful operation.

- Duplicate submission during concurrent requests.

- Two workers competing for the same task.

- Device revocation while a task is queued.

- Database failure while recording the result.

- Cancellation racing with dispatch.

Exit gate: the end-to-end workflow passes both successful and failure scenarios, with no false completion claims.

## 04.07.08 WP-06 — CLI, multi-user validation and release evidence

Owner: shared; Developer 1 coordinates integration.

### Deliverables

- Task submission command with explicit device targeting.

- Task status and step inspection.

- Result display and stable error messages.

- A documented way to cancel or stop monitoring a task, with those behaviors clearly distinguished.

- JSON output suitable for scripts.

- End-to-end test instructions and recorded results.

- A clean-environment reproduction report.

Illustrative CLI usage:

nexus run "Find files containing design" --device my-windows-pc

nexus task <task-id>

nexus task <task-id> --steps

nexus task <task-id> --result

These commands are examples; final flags and output schemas must match the CLI contract.

The CLI must distinguish between a task being accepted, running, waiting for a device, succeeding, failing and having an uncertain outcome. Stopping --watch must not cancel the underlying task.

### Release evidence

The team should produce a short report containing:

- Commit and migration versions tested.

- Environment and dependency versions.

- Automated test results.

- Windows bridge integration results.

- Multi-user isolation results.

- Known defects and unresolved decisions.

- Any scenarios not tested, including why.

Exit gate: another developer can reproduce the complete workflow from the documented setup and obtain the same expected behavior.

## 04.07.09 Dependency graph and merge order

The team should work in parallel only where interfaces are stable.

### Merge sequence

| **Order** | **Merge target** | **Required checks** |
| --- | --- | --- |
| 1 | Contracts, repository conventions and fixtures | All three developers agree on interfaces |
| 2 | Database models and task API | Migration and PostgreSQL integration tests pass |
| 3 | Bridge protocol and scoped search | Windows bridge contract and security tests pass |
| 4 | Deterministic planner interface | Schema and invalid-plan tests pass |
| 5 | Orchestrator integration | Task lifecycle and recovery tests pass |
| 6 | CLI integration | API contract and CLI tests pass |
| 7 | End-to-end milestone | Complete workflow and failure matrix pass |

This is the preferred merge order, not a requirement that every component be finished before another can begin. Developers can work on separate branches using shared fixtures and mocks, then integrate incrementally.

## 04.07.10 Branch and pull-request rules

Each work item should be small enough to review independently.

Suggested branch names:

feat/task-persistence

feat/windows-file-search

feat/deterministic-planner

test/task-recovery

docs/vertical-slice-setup

Every pull request should include:

- The requirement or work-item ID.

- Files and interfaces changed.

- Tests added and their results.

- Database migration or configuration impact.

- Security, retry and failure implications.

- Compatibility considerations for other developers.

- Known limitations.

Changes to shared contracts require review from both the producer and the consumer. Changes involving authentication, authorization, filesystem boundaries, approval or recovery need an additional security-focused review.

Do not merge code merely because the author reports that it works locally. Required checks must either pass or be explicitly recorded as blocked; missing checks must not be silently treated as successful.

## 04.07.11 Suggested milestone schedule

This schedule is a planning estimate within the broader 10–12 week project, not a commitment based on measured team availability.

| **Period** | **Primary objective** |
| --- | --- |
| Days 1–2 | Agree contracts and repository conventions |
| Days 3–5 | Task API, persistence, bridge skeleton and planner fixtures |
| Days 6–8 | Scoped file search and orchestration integration |
| Days 9–10 | CLI integration, failure tests and first complete demonstration |
| Days 11–12 | Multi-user validation, fixes and reproducibility review |

If the bridge transport, device authentication or task-recovery design is not yet resolved, extend the milestone rather than bypassing those boundaries.

## 04.07.12 Milestone sign-off checklist

### Milestone sign-off

### 0/10

Contracts

Task, step and operation contracts are agreed

Shared fixtures and error codes are committed

Backend

Task acceptance and idempotency tests pass on PostgreSQL

Ownership and legal state transitions are enforced

Windows bridge

Bridge authentication and target-device validation pass

Scoped search and Windows path security tests pass

Integration

Complete CLI-to-Windows workflow succeeds

Lost-response and restart scenarios are reconciled safely

Release readiness

Cross-user and concurrent-worker tests pass

Clean setup and known limitations are documented

This is a manual checklist, not an automated test report.

Milestone completion rule: all mandatory checks pass, known limitations are documented, and the team can demonstrate the workflow on the intended environment. Any critical or high-severity security issue blocks sign-off.
