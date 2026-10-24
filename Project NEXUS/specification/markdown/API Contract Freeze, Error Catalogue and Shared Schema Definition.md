## 04.08.01 Purpose

The three developers will implement different parts of NEXUS, but those parts must agree on the exact shape and meaning of the data they exchange.

For example, the backend cannot safely interpret a bridge response if one developer uses success, another uses completed, and a third treats a timeout as a failure that can always be retried.

This section establishes the rules for freezing shared contracts before implementation expands.

Objective: every component must agree on identifiers, required fields, valid states, error meanings, authorization boundaries, version compatibility and failure behavior.

The contract freeze applies to the first vertical slice. It does not mean that every future NEXUS API or tool must be designed now.

## 04.08.02 Contract ownership

| **Contract** | **Accountable owner** | **Required reviewer** |
| --- | --- | --- |
| Public API and task lifecycle | Developer 1 | Developers 2 and 3 |
| Bridge protocol and local tool execution | Developer 2 | Developers 1 and 3 |
| Planner proposal and context interfaces | Developer 3 | Developers 1 and 2 |
| Shared error catalogue and identifiers | Developer 1 coordinates | All three developers |
| Security and recovery invariants | Shared responsibility | All three developers |

The accountable owner maintains the contract, examples and tests. Other developers must approve changes that affect their consumers.

A contract must not be changed unilaterally after another component has implemented against it.

## 04.08.03 Contract layers

NEXUS should maintain distinct contracts for distinct boundaries.

1. Public API

CLI ↔ FastAPI

Authentication, requests, task status, approvals, results and errors.

2. Internal application

Services ↔ orchestrator and policy

Validated domain objects, state transitions and authorization decisions.

3. Planner

AI or deterministic planner → backend

Structured proposals and clarification results; never authoritative permission decisions.

4. Bridge protocol

Backend ↔ Windows bridge

Device identity, operation envelope, deadlines, responses and protocol compatibility.

5. Tool contract

Registry ↔ tool implementation

Arguments, results, resource limits, risk metadata, retries and verification.

These layers may share schema definitions where appropriate, but they should not collapse into one giant schema. In particular, a planner proposal is not a bridge command, and a bridge response is not itself proof that the overall task succeeded.

## 04.08.04 Identifier and timestamp conventions

The initial contract should define these identifiers consistently:

| **Identifier** | **Meaning** |
| --- | --- |
| user_id | Authenticated user identity |
| device_id | Registered target computer |
| task_id | Durable task |
| step_id | Logical operation within a task |
| operation_id | Stable identity of one logical external operation |
| attempt_id | One execution attempt |
| request_id | Correlation identifier for a request |
| client_request_id | Client-generated key for duplicate task-submission protection |
| approval_id | Approval record for a specific operation |
| policy_version | Policy version used for a decision |

Rules:

- Identifiers are opaque to consumers; they must not encode permissions.

- The authenticated identity determines task ownership.

- A client-generated request ID is not an authentication credential.

- An operation ID is not proof of authorization.

- Timestamps use UTC in ISO 8601 format.

- Missing, null, empty and default values must have documented, distinct meanings where relevant.

- IDs used for correlation must remain consistent across retries of the same logical operation.

The exact ID format—UUID or another suitable opaque identifier—is still an implementation decision.

## 04.08.05 Public task API schemas

The following examples establish the intended contract semantics. They are proposed examples, not final Pydantic models or a generated OpenAPI specification.

### A. Task submission request

{

"client_request_id": "client-generated-unique-id",

"target_device_id": "registered-device-id",

"request": "Find files containing the word design"

}

Required fields:

- client_request_id: enables duplicate-submission detection.

- target_device_id: explicit destination device.

- request: user-requested task description.

The backend must derive user_id from the authenticated session. It must not accept a client-supplied owner as authoritative.

### B. Task acceptance response

{

"task_id": "task-id",

"status": "QUEUED",

"request_id": "request-correlation-id",

"created_at": "2026-10-22T12:00:00Z"

}

The response means the task has been durably accepted. It does not mean execution has started or completed.

If persistence fails before the task can be accepted, the API must not return a successful acceptance response.

### C. Task status response

{

"task_id": "task-id",

"target_device_id": "registered-device-id",

"status": "RUNNING",

"created_at": "2026-10-22T12:00:00Z",

"updated_at": "2026-10-22T12:00:02Z",

"steps": [

{

"step_id": "step-id",

"tool_name": "search_files",

"status": "RUNNING"

}

],

"error": null

}

The final schema should distinguish required and optional fields, and define whether embedded steps are complete or only a summary. A dedicated steps endpoint can return detailed step history without making every task-status response excessively large.

### D. Error response

{

"error": {

"code": "DEVICE_UNAVAILABLE",

"message": "The selected device is currently unavailable.",

"request_id": "request-correlation-id",

"retryable": true

}

}

The retryable field is informational. It must not authorize an unsafe retry of an external operation. The client must follow the operation-specific recovery policy.

## 04.08.06 Canonical task and step states

Use one canonical set of state names across persistence, application services and API responses. Any different naming required by a transport must be translated at that boundary.

### Task states

| **State** | **Meaning** |
| --- | --- |
| QUEUED | Durably accepted, waiting for eligible execution |
| RUNNING | Execution is in progress |
| WAITING_FOR_APPROVAL | An operation requires a valid approval |
| INTERRUPTED | Execution was interrupted and recovery is required |
| SUCCEEDED | All required operations have verified outcomes |
| FAILED | The task cannot complete under the defined failure policy |
| CANCELLED | Cancellation is confirmed and unresolved side effects are reconciled |

The last three are terminal states. A terminal task must not silently return to an active state.

### Step states

| **State** | **Meaning** |
| --- | --- |
| PENDING | Recorded but not ready to execute |
| READY | Dependencies and eligibility permit execution |
| WAITING_FOR_APPROVAL | Approval is required |
| DISPATCHED | Request sent to the bridge; execution outcome not yet established |
| RUNNING | Bridge has reported execution in progress |
| SUCCEEDED | Operation completed and the result was validated |
| FAILED | Failure is established under the tool contract |
| REJECTED | Operation was rejected by validation or policy |
| UNCERTAIN | External outcome cannot yet be established |
| CANCELLED | Operation did not execute, or its outcome has been reconciled and cancellation confirmed |

DISPATCHED is not equivalent to RUNNING, and UNCERTAIN is not equivalent to FAILED.

### Contract freeze rules

- The orchestrator owns authoritative state transitions.

- The AI planner cannot set execution status.

- The bridge reports evidence and outcomes, but cannot directly change the backend's task state.

- The API cannot bypass transition validation.

- State changes must be persisted before they are reported as authoritative.

- Invalid transitions return a stable error and leave the persisted state unchanged.

The exact handling of an interrupted task and approval expiry must be documented in the state-machine contract before those paths are implemented.

## 04.08.07 Planner proposal contract

The planner returns a proposal that the application must validate. It does not return an executable authorization decision.

Proposed successful response:

{

"proposal_version": "1",

"outcome": "PROPOSED",

"objective": "Find files matching the requested term",

"target_device_id": "registered-device-id",

"steps": [

{

"step_id": "proposal-step-1",

"tool_name": "search_files",

"tool_schema_version": "1",

"arguments": {

"directory_id": "nexus_test_documents",

"query": "design"

},

"depends_on": []

}

]

}

The example demonstrates structure only. The application should assign authoritative execution IDs and validate the requested target against the persisted task and authenticated user's permissions.

The planner contract must define three outcomes:

- PROPOSED: a structurally valid proposal is available for further validation.

- CLARIFICATION_REQUIRED: the request cannot be safely or correctly planned without additional information.

- UNSUPPORTED: the requested capability is unavailable or outside the supported scope.

The planner must not be able to declare an operation approved, remove an approval requirement, assign itself additional permissions, or assert that an external side effect succeeded.

A proposal with an unknown tool, invalid schema or unauthorized target is rejected even if the model claims that it is safe.

## 04.08.08 Windows bridge request and response contract

The bridge protocol is a security boundary and requires stricter compatibility rules than ordinary internal data structures.

### Proposed request envelope

{

"protocol_version": "1",

"operation_id": "stable-operation-id",

"attempt_id": "attempt-id",

"task_id": "task-id",

"step_id": "step-id",

"target_device_id": "registered-device-id",

"tool_name": "search_files",

"tool_schema_version": "1",

"arguments": {

"directory_id": "nexus_test_documents",

"query": "design"

},

"deadline": "2026-10-22T12:00:30Z"

}

The bridge must authenticate the caller or validate the request through the selected authenticated transport. It must also verify that the target device matches its own registered identity.

### Proposed response envelope

{

"protocol_version": "1",

"operation_id": "stable-operation-id",

"attempt_id": "attempt-id",

"device_id": "registered-device-id",

"status": "SUCCEEDED",

"result": {

"matches": []

},

"error": null

}

The actual result schema belongs to the search_files tool contract. The empty array here is illustrative, not evidence that a search occurred.

### Required response semantics

- SUCCEEDED: the tool completed and produced a result.

- FAILED: the tool's contract establishes that the operation failed.

- REJECTED: validation, authorization or local policy blocked the operation.

- RUNNING: the operation remains in progress.

- UNCERTAIN: the bridge cannot establish the final outcome.

Every response must be correlated to the requested operation and attempt. Mismatched IDs, target device or unsupported protocol versions must not be accepted as successful execution.

If the bridge executes a side effect but fails to record its result, recovery must reconcile the operation. The protocol cannot promise exactly-once execution for arbitrary Windows operations.

## 04.08.09 Canonical error catalogue

Error codes should describe stable categories of failure, not implementation-specific exception names.

| **Code** | **Meaning** | **Expected handling** |
| --- | --- | --- |
| INVALID_ARGUMENT | Request or tool arguments are invalid | Correct the request; do not dispatch |
| AUTHENTICATION_REQUIRED | Valid authentication is missing | Authenticate again |
| ACCESS_DENIED | User or device lacks required access | Do not retry without an authorized change |
| POLICY_DENIED | Policy prohibits the operation | Do not bypass the policy |
| APPROVAL_REQUIRED | Operation needs explicit approval | Present the exact operation for review |
| APPROVAL_EXPIRED | Required approval is no longer valid | Request a new approval if the task remains eligible |
| DEVICE_UNAVAILABLE | Target device cannot currently be reached | Preserve task state and follow recovery rules |
| DEPENDENCY_UNAVAILABLE | A required service is unavailable | Use bounded retry or controlled failure |
| CONTRACT_VERSION_UNSUPPORTED | Component cannot safely interpret the contract | Block execution and resolve compatibility |
| OPERATION_TIMEOUT | A deadline was exceeded | Determine whether execution may have occurred |
| OPERATION_OUTCOME_UNCERTAIN | Final external outcome cannot be established | Reconcile; never blindly repeat |
| FILE_NOT_FOUND | Requested file is not found within the permitted scope | Report the result accurately |
| FILE_ALREADY_EXISTS | A create-only destination already exists | Do not overwrite |
| FILESYSTEM_SCOPE_DENIED | Filesystem access falls outside configured scope | Reject the operation |
| INTERNAL_ERROR | Unexpected application failure | Record safe diagnostics and a correlation ID |

The catalogue should define which component can emit each code, whether it is terminal, whether a retry is meaningful, and what recovery procedure applies.

Avoid exposing stack traces, SQL details, secrets or sensitive local paths in public error responses.

## 04.08.10 Schema validation and compatibility rules

NEXUS needs a consistent schema-validation approach across the API, planner, bridge and tools. Pydantic is a proposed choice for Python-side validation; the team should confirm it when selecting the dependency baseline.

### Rules for the first release

1. Validate incoming data at each trust boundary.

2. Reject missing required fields and invalid types.

3. Apply explicit length, count and payload-size limits.

4. Reject unknown tool names and unsupported security-sensitive fields.

5. Do not silently reinterpret an unknown enum value or protocol version.

6. Keep optional fields and their defaults documented.

7. Return stable error codes instead of leaking framework-specific validation output.

8. Keep the same example payloads in the contract documentation and automated tests.

Not every future additive field must require a new major version. However, any change that alters authorization, operation identity, result meaning, retry safety or state transitions requires explicit compatibility review.

## 04.08.11 Versioning policy

NEXUS has several independently versioned boundaries.

| **Boundary** | **Proposed versioning rule** |
| --- | --- |
| Public API | /v1 route prefix |
| Bridge protocol | Explicit protocol_version |
| Tool schema | Per-tool tool_schema_version |
| Planner proposal | Explicit proposal schema version |
| Persisted task events | Versioned if durable event schemas are introduced |
| Database schema | Ordered migrations with a recorded schema revision |

Version numbers are not interchangeable. For example, a bridge protocol update does not automatically mean that every tool schema must change.

### Compatibility requirements

- Components must advertise or establish the versions they support.

- Unsupported security-sensitive versions fail closed.

- A tool schema change must consider queued and in-flight tasks created under the previous schema.

- Rolling back application code must not reinterpret an already-dispatched operation using different arguments.

- Contract changes require updated fixtures and compatibility tests.

- Version removal requires a documented migration or deprecation plan.

For the first vertical slice, avoid elaborate version-negotiation machinery. Explicit versions and a clear fail-closed rule are sufficient until a real compatibility need emerges.

## 04.08.12 Contract test requirements

Contract tests are shared executable evidence that components agree on the same behavior.

Public API

Valid and invalid task requests

Duplicate request and payload conflict

Authentication and ownership enforcement

Stable error response structure

Task lifecycle

Valid state transitions

Invalid transition rejection

Terminal-state protection

Persisted state after restart

Planner

Valid proposal parsing

Unknown tool rejection

Malformed argument rejection

Clarification and unsupported outcomes

Windows bridge

Request and response schema validation

Operation and attempt correlation

Unknown protocol and tool rejection

Timeout and uncertain-outcome behavior

Cross-component integration

One shared happy-path fixture

One authorization-denial fixture

One disconnected-device fixture

One lost-response/reconciliation fixture

A contract test should run without a live AI model. The bridge's Windows-specific behavior must additionally be tested on Windows rather than inferred from Linux test results.

## 04.08.13 Contract freeze procedure

The initial contracts are considered frozen when the following steps are complete:

1. Draft: each owner publishes schemas, examples, error behavior and unresolved decisions.

2. Consumer review: the developers implementing dependent components verify that the contract is sufficient.

3. Test fixtures: valid, invalid and failure-case examples are committed.

4. Security review: ownership, device targeting, operation identity, approval and retry semantics are checked.

5. Baseline approval: the team records the accepted contract version in the repository.

6. Controlled changes: later modifications include migration impact, affected consumers, tests and backward-compatibility notes.

Freeze means that the team has a reliable starting contract, not that future changes are forbidden.

### Open decisions before implementation

- Exact identifier format.

- Pydantic model organization and strictness settings.

- Bridge transport and authentication mechanism.

- Exact tool-result and error payload schemas.

- Approval-expiry and interruption semantics.

- Unknown-field behavior for each boundary.

- API payload limits and pagination defaults.

- How long older bridge and tool schemas must remain supported.

These decisions should be resolved by the responsible developer with evidence from the architecture, security and integration requirements—not guessed independently.

## 04.08.14 Definition of done

- API, planner, bridge and tool contracts are documented separately.

- Canonical identifiers and task/step states are agreed.

- Request, response and error examples are committed.

- Ownership and authorization rules are reflected in the contracts.

- Operation timeouts and uncertain outcomes have explicit semantics.

- Version compatibility and rejection behavior are documented.

- Shared fixtures and contract tests run in CI.

- All three developers have reviewed the interfaces they consume.

- Unresolved decisions have an owner and closure plan.

Section exit criterion: the team can implement the first vertical slice without inventing incompatible schemas or relying on implicit behavior between components.
