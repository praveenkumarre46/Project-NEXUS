## 04.06.01 Purpose

The first vertical slice is the smallest complete workflow that proves the core NEXUS architecture works across the CLI, backend, database and a real Windows computer.

Instead of building all backend modules, AI planning, memory and automation tools independently, the team will deliver one end-to-end capability:

A user submits a file-search request in the terminal, NEXUS persists a task, routes it to the explicitly selected Windows device, searches only an approved directory, records the result and displays it to the user.

This milestone uses a deterministic plan. It does not require a live AI model, document summarization, unrestricted shell commands or graphical desktop automation.

### Success criteria

- The task has a durable ID and persisted status.

- The authenticated user owns the task.

- The selected device is authenticated and authorized.

- The backend and bridge validate the operation independently.

- File access remains inside a configured directory scope.

- Duplicate requests do not create duplicate tasks.

- Failures and disconnections are represented honestly.

- The CLI displays the recorded outcome rather than assuming success.

## 04.06.02 Scope boundary

Included in this slice

Authentication, device selection, task creation, PostgreSQL persistence, deterministic planning, policy validation, bridge communication, scoped file search, task history and basic recovery tests.

Excluded from this slice

Live AI planning, semantic memory retrieval, document summarization, file creation, application launching, GUI automation, broad multi-step plans and unrestricted command execution.

The first slice is not the entire MVP. It is the integration foundation on which the remaining features will depend.

## 04.06.03 End-to-end execution flow

### 1

CLI

Submit request, target device and client request ID

### 2

FastAPI

Authenticate user and validate request

### 3

PostgreSQL

Persist task and enforce idempotency

### 4

Task orchestrator

Claim task and prepare a registered search operation

### 5

Policy engine

Validate ownership, device, tool and directory scope

### 6

Windows bridge

Authenticate request and validate local restrictions

### 7

Filesystem tool

Search only the configured test directory

### 8

PostgreSQL

Persist step outcome and final task status

### 9

CLI

Display task ID, result summary and any error

This is the logical flow. The actual bridge transport remains a decision to validate; outbound polling is the current provisional preference. The flow must preserve the same authorization and recovery rules regardless of transport.

## 04.06.04 Request and operation contracts

The first slice needs only a small number of contracts, but each must be explicit before the three developers work in parallel.

### A. Task submission

Illustrative request:

{

"client_request_id": "client-generated-unique-id",

"target_device_id": "registered-device-id",

"request": "Find files containing the word design"

}

The authenticated user identity must come from the authentication context, not from a client-supplied user_id.

The backend must validate:

- client_request_id is present and conforms to the agreed format.

- target_device_id refers to a registered device the user is permitted to target.

- request is non-empty and within the documented length limit.

- The requested operation maps to a supported capability.

- The request cannot override security policy through natural-language instructions.

The request above is an example, not the final API schema.

### B. Deterministic planner output

For the first slice, a simple deterministic request handler can map an explicitly supported file-search request to a search_files operation. It should not pretend to understand arbitrary natural-language requests.

The resulting operation must contain:

- Registered tool name and schema version.

- Target device ID.

- Logical directory ID.

- Search query.

- Result and execution limits.

- Expected result structure.

The backend—not the planner—assigns authoritative task, step and operation identifiers and determines the required permissions.

### C. Bridge operation

The bridge request must identify the intended operation and device, carry validated arguments, and include a deadline or timeout policy.

The bridge must reject unknown tools, invalid arguments, unsupported protocol versions and out-of-scope directories. It returns a structured result or a typed error. It must not accept a generic command string to execute.

## 04.06.05 Task persistence and idempotency

The first implementation must persist a task before reporting successful acceptance.

Proposed minimum records:

| **Record** | **Purpose** |
| --- | --- |
| tasks | Owner, target device, request ID, status and timestamps |
| task_steps | Search operation, status, operation ID and outcome |
| task_step_attempts | Dispatch attempts and their recorded outcomes |
| audit_events | Security-relevant events and decisions |

The exact schema remains governed by the database design and migrations.

### Duplicate submission behavior

1. The CLI submits a request with a client-generated request ID.

2. The backend checks the unique key scoped to the authenticated user.

3. If the same ID and same normalized request are submitted again, return the existing task.

4. If the same ID is reused with a different request or target device, return a stable conflict error.

5. Concurrent duplicate submissions must be handled by database constraints and transactions, not just an application-level check.

A timeout from the API does not prove that the request was rejected. The CLI should be able to retry with the same request ID or retrieve the existing task.

### Completion behavior

The task may be marked SUCCEEDED only after the search operation has a valid, correlated result and the backend has successfully persisted the outcome. If the bridge might have executed the operation but the result cannot be established, the system must preserve uncertainty and invoke the recovery rules from Section 03.30.

## 04.06.06 Windows file-search boundaries

The bridge must use a logical directory identifier rather than trusting a path supplied by the model or client.

Example configuration:

Logical directory: nexus_test_documents

Local directory:   configured by the Windows device owner

Allowed operation: search_files

The actual local path is intentionally unspecified here; each developer configures their own test directory.

The initial search tool should:

- Search only the configured directory.

- Enforce maximum depth, result count and execution duration.

- Avoid following directory links or junctions by default.

- Return bounded metadata, not entire file contents.

- Use stable, documented error codes.

- Avoid returning sensitive absolute paths unless the result contract requires them.

- Support cancellation where practical, while reporting if an operation has already completed.

Search results are not permanent permissions. If a later feature reads a returned file, the bridge must revalidate that file against the active scope.

### Required negative tests

- Search using an unregistered directory ID.

- Attempt directory traversal.

- Attempt to escape through a link or junction.

- Target another device.

- Send an unknown tool name.

- Send malformed or excessive arguments.

- Revoke the bridge credential and retry.

- Disconnect the bridge while the task is pending.

- Lose the bridge response after dispatch and verify that NEXUS does not report fabricated success.

## 04.06.07 Implementation order and team dependencies

Implement the slice in the following order. Do not have all three developers independently invent their own interfaces.

1. Freeze the minimum contracts

2. Agree on the task request/response, task and step states, search_files arguments and result, error codes, device identity and operation envelope.

3. Gate: backend and bridge developers approve the same contract examples and tests.

4. Implement persistence and task acceptance

5. Create the migration, enforce request idempotency, add task lookup and implement legal state transitions.

6. Gate: duplicate requests, conflicting IDs and concurrent submissions behave correctly against PostgreSQL.

7. Implement the deterministic operation path

8. Map the supported search request to a registered tool proposal. Validate its schema, device and permissions before dispatch.

9. Gate: unsupported requests and invalid operations are rejected without contacting the bridge.

10. Implement the Windows bridge search tool

11. Add device authentication, local directory configuration, argument validation, bounded search and structured responses.

12. Gate: Windows-specific path and authorization tests pass.

13. Integrate orchestration and recovery

14. Persist intent before dispatch, correlate the response with the operation, record the outcome and handle timeouts and disconnections.

15. Gate: interrupted operations are not blindly replayed and uncertain outcomes remain visible.

16. Complete CLI and end-to-end tests

17. Display task IDs, progress, results and errors. Test the workflow with at least two developers' Windows computers, then run the three-user integration scenario.

18. Gate: the full workflow passes from a clean setup with documented results.

### Responsibility split

| **Developer** | **Primary deliverables** |
| --- | --- |
| Developer 1 — backend | Task API, PostgreSQL schema, idempotency, state transitions, orchestration and recovery |
| Developer 2 — Windows integration | Bridge identity, transport integration, scoped file search, Windows path security and local result reporting |
| Developer 3 — AI/context | Deterministic planner interface, tool proposal schema, capability descriptions and fixtures for later model integration |

All three must review the shared contracts. Developer 3 can prepare the planner interface without introducing a live model dependency into this milestone.

## 04.06.08 Acceptance-test matrix

| **Scenario** | **Expected result** |
| --- | --- |
| Valid scoped search | Task succeeds with bounded results |
| Same request ID and payload | Existing task returned; no duplicate task |
| Same request ID, changed payload | Conflict; no second task |
| Unauthenticated submission | Rejected; no accepted task |
| Unauthorized device | Denied before dispatch |
| Unknown tool | Rejected by backend validation |
| Invalid local directory scope | Rejected by bridge |
| Bridge offline before dispatch | No false success; task remains recoverable |
| Response lost after dispatch | Outcome reconciled or marked uncertain |
| Backend restarts with pending task | State restored and recovery logic applied |
| Two workers claim the same task | At most one valid active claim |
| One user requests another user's task | Access denied |
| Search returns excessive matches | Results are bounded |
| Model runtime unavailable | This deterministic slice still works |
| PostgreSQL unavailable | No false claim of durable acceptance |

Tests involving concurrency and transaction behavior must use PostgreSQL. Filesystem security tests must run on Windows, because Linux-only path tests do not adequately cover Windows path semantics.

## 04.06.09 Observability requirements

Every run should be traceable using a correlation chain:

request_id → task_id → step_id → operation_id → attempt_id

Persist or log the following as appropriate:

- Task and operation state transitions.

- Target device and tool identity.

- Dispatch and response timestamps.

- Attempt count and timeout classification.

- Stable error codes.

- Result summaries and verification evidence.

- Recovery decisions.

Do not log passwords, bridge credentials, full document contents or unnecessary private paths. Logs alone are not the authoritative task history; persisted task and step records remain the source of truth.

## 04.06.10 Milestone exit criteria

The first vertical slice is complete when:

- The task API and database migration work on a clean setup.

- Request idempotency is enforced under concurrent submission.

- The deterministic planner produces only a registered search operation.

- Backend authorization and bridge-side validation both work.

- Windows file search remains within its configured scope.

- The CLI displays persisted task status and actual results.

- Duplicate delivery, disconnection and lost-response scenarios have tests.

- Recovery never blindly repeats an uncertain operation.

- Cross-user and cross-device authorization tests pass.

- The workflow runs across the intended LAN topology.

- Setup, execution and troubleshooting instructions are reproducible.

- No critical or high-severity security defect remains open.

A successful happy-path demonstration alone does not satisfy this milestone. The recovery and negative tests are part of the deliverable.
