## 03.24.1 Purpose

NEXUS has three developers working across the backend and task execution, Windows integration, and AI/context components. Those components must agree on their interfaces before being implemented independently.

This section defines how components exchange requests, structured results, state changes and errors without becoming tightly coupled to each other's internal implementation.

The goal is to prevent integration failures such as:

- The AI planner returns a structure the orchestrator cannot interpret.

- The backend authorizes an operation but the bridge expects a different request format.

- The bridge reports a timeout while the backend incorrectly records a definitive failure.

- One component changes a field name or status value and silently breaks another component.

- Two workers dispatch the same task step concurrently.

- A model or tool adapter leaks implementation-specific exceptions into the public API.

This section establishes proposed contract shapes and rules, not a final OpenAPI specification or production-ready code.

## 03.24.2 Contract design principles

1. Explicit schemas: requests and responses have documented fields and types.

2. Stable identifiers: tasks, steps, devices, operations and approvals have distinct identifiers.

3. Versioned boundaries: externally consumed contracts declare a version where compatibility matters.

4. Typed errors: expected failures have stable codes; unexpected exceptions do not leak implementation details.

5. No implicit authority: a valid payload is not automatically an authorized operation.

6. Durable state is authoritative: task status comes from persisted backend state, not a CLI cache or model response.

7. External side effects remain uncertain until verified: transport success is not proof that a computer operation succeeded.

8. Backward compatibility: compatible fields can be added deliberately; incompatible changes require a versioned migration plan.

9. Bounded payloads: requests, results, logs and retrieved context have defined size limits.

10. Testable independently: every component can be tested against a contract without requiring the entire NEXUS system.

## 03.24.3 Component boundaries

These are logical boundaries. They do not require every box to be a separate process or microservice. The initial backend remains a modular monolith unless measurements justify a different deployment.

## 03.24.4 Shared identifier and data conventions

The following identifiers serve different purposes and must not be interchangeable.

| **Identifier** | **Purpose** |
| --- | --- |
| user_id | Identifies the account requesting or owning an operation |
| device_id | Identifies a registered Windows computer |
| task_id | Identifies a durable user request and its execution lifecycle |
| step_id | Identifies one logical operation within a task |
| operation_id | Identifies the intended external operation across delivery retries |
| attempt_id | Identifies one attempt to deliver or execute that operation |
| approval_id | Identifies a decision request for an operation |
| request_id | Correlates an API request with its response and diagnostics |
| event_id | Identifies a persisted or delivered event |
| policy_version | Identifies the policy version used for a decision |

Proposed conventions

- IDs are opaque to clients; clients must not infer ownership or permissions from their format.

- Timestamps use UTC in ISO 8601 format.

- Durations use milliseconds where represented numerically.

- Task and operation states use documented enumerated values, not arbitrary model-generated strings.

- Optional fields must have defined semantics. Missing, null, empty and unknown values must not be treated as interchangeable.

- Request and result payloads must be bounded.

- Internal Python exceptions must be mapped to documented application errors at the appropriate boundary.

The precise ID format, such as UUIDs, and the serialization library remain implementation choices. The important requirement is consistent behavior across components.

## 03.24.5 Contract A — CLI to FastAPI

The CLI communicates with the backend through the versioned /v1 API defined in Section 03.16.

### Task submission

Proposed request:

{

"client_request_id": "client-generated-id",

"target_device_id": "registered-device-id",

"request": "Find the project design document"

}

Proposed response:

{

"task_id": "server-generated-task-id",

"status": "queued",

"request_id": "api-request-id"

}

The values above are illustrative placeholders, not a finalized schema.

### Contract requirements

- The caller must be authenticated.

- The backend derives the task owner from authenticated identity, never from an untrusted user_id in the request.

- The target device must be explicitly supplied or resolved through a configured default that the CLI displays clearly.

- The backend verifies that the caller is authorized to use that device.

- Duplicate submission with the same user's client_request_id and equivalent payload returns the existing task rather than creating a duplicate.

- Reusing the identifier with a different payload produces a documented conflict.

- A successful response means the task was durably accepted—not that the operation has completed.

### Task status

The status endpoint should return the persisted task state, timestamps, safe progress information, required user action and an error summary when applicable.

The API must not expose another user's private task data simply because a caller knows a task ID. Every task-related endpoint requires an ownership or explicitly granted access check.

### Cancellation and approval

- A cancellation request records a request to stop; it does not claim that an external operation has stopped.

- An approval endpoint records a decision only after authentication, authorization and operation-binding checks.

- A CLI disconnect or interruption of status polling does not cancel the underlying task.

- A retry of an API request must not create a duplicate task or approval decision.

## 03.24.6 Contract B — AI planner to application services

The AI planner accepts a bounded request and the authorized context prepared by NEXUS. It returns a structured proposal or asks for clarification.

Proposed internal result:

{

"schema_version": 1,

"goal_summary": "Locate the requested project document",

"needs_clarification": false,

"steps": [

{

"step_number": 1,

"tool_name": "search_files",

"arguments": {

"directory_id": "project-documents",

"query": "design"

},

"expected_outcome": "Matching file metadata is returned"

}

]

}

This is a conceptual contract. It is not yet the final schema, and the tool's arguments must match the trusted registry before use.

### Planner responsibilities

- Interpret the user's request.

- Select from the tools and capabilities provided in the planning context.

- Produce structured, bounded proposals.

- Identify missing information when clarification is necessary.

- Describe expected outcomes without claiming they have occurred.

- Return a typed failure when planning cannot proceed.

### Planner restrictions

The planner cannot:

- Authorize its own proposed operations.

- Create or modify registered tools.

- Change permissions, risk classifications or target-device ownership.

- Mark an operation as successfully executed.

- Write directly to authoritative task state.

- Bypass approval requirements by rewriting a request as a different action.

The application services validate the planner's output and decide whether it can proceed. If the model produces malformed output, the backend must reject or retry planning within a bounded policy; it must not attempt to execute the malformed response.

## 03.24.7 Contract C — Orchestrator to policy engine

The orchestrator asks the policy engine to evaluate a proposed operation using trusted identity, device, resource and tool information.

Proposed logical input:

{

"task_id": "task-id",

"step_id": "step-id",

"user_id": "authenticated-user-id",

"target_device_id": "registered-device-id",

"tool_name": "create_file",

"normalized_arguments": {

"directory_id": "approved-workspace",

"filename": "notes.txt"

},

"approval_id": null

}

The policy engine must not trust a supplied user or device identifier merely because it appears in the payload. It must receive or resolve trusted authorization context from the application layer.

Proposed logical result:

{

"decision": "REQUIRE_APPROVAL",

"reason_code": "APPROVAL_REQUIRED",

"policy_version": "active-policy-version",

"required_permissions": [

"workspace.file.create"

]

}

These examples describe the shape of the interaction, not final production values.

### Contract requirements

- Policy decisions use deterministic, testable application logic.

- The decision includes a reason code suitable for audit and diagnosis.

- Hard prohibitions take precedence over approvals.

- The decision must apply to normalized arguments, not a different representation of the operation.

- The result must identify the policy version used.

- The orchestrator re-evaluates security-relevant conditions immediately before dispatch.

- If the policy engine fails or cannot resolve an essential authorization fact, the operation is not dispatched.

The policy engine does not execute tools, and the orchestrator does not independently invent risk classifications.

## 03.24.8 Contract D — Orchestrator to Windows bridge

This is the most security-sensitive integration boundary because it crosses from the shared backend to an individual Windows computer.

The bridge transport is provisionally designed around authenticated outbound polling by each bridge, as discussed in Section 03.22. Whether operations are delivered through polling or a persistent connection is still an open implementation decision. The operation contract should remain independent of that choice.

### Proposed operation envelope

{

"protocol_version": 1,

"operation_id": "stable-operation-id",

"attempt_id": "delivery-attempt-id",

"task_id": "task-id",

"step_id": "step-id",

"target_device_id": "registered-device-id",

"tool_name": "search_files",

"schema_version": 1,

"arguments": {

"directory_id": "project-documents",

"query": "design"

},

"deadline": "2030-01-01T00:00:00Z"

}

The deadline is illustrative. The actual contract must define how expiration is handled and how the bridge checks it.

### Bridge response

The bridge should return a structured outcome with:

- The operation and attempt identifiers.

- The authenticated device identity.

- The execution status.

- A bounded, schema-valid result or error.

- Start and completion timestamps when available.

- A stable error code when execution fails.

- Enough information to distinguish a known result from an uncertain outcome.

### Contract invariants

1. The authenticated bridge identity must match the intended target device.

2. The bridge must reject unknown tools and incompatible schemas.

3. The bridge must validate arguments and local permissions independently.

4. Duplicate delivery of the same operation_id must not blindly repeat a potentially destructive side effect.

5. The bridge must distinguish operation execution from transport delivery.

6. A timeout must not automatically be translated into a definitive failure.

7. The backend must verify that the response matches the operation it dispatched.

8. Neither the bridge nor the backend may treat a client-supplied device ID as authentication.

9. The bridge must not expose a generic shell or arbitrary command endpoint.

### Operation delivery versus execution

These events are different:

- The backend queued an operation.

- The backend delivered an operation.

- The bridge accepted an operation.

- The bridge began execution.

- The operation produced a result.

- The backend durably recorded that result.

For example, if a bridge creates a file but its response is lost, the backend cannot conclude that the file was not created. The orchestrator must reconcile the operation before retrying it.

A stable operation ID helps identify duplicates, but it does not create a universal exactly-once execution guarantee across a database, network and Windows filesystem.

## 03.24.9 Contract E — Persistence and transaction boundaries

PostgreSQL is the authoritative store for task state, approvals, operation records and relevant audit events.

Application services should interact with persistence through defined repositories or equivalent interfaces rather than issuing ad hoc database queries throughout the codebase.

### Proposed persistence responsibilities

| **Operation** | **Required behavior** |
| --- | --- |
| Accept a task | Persist task and idempotency information atomically |
| Claim work | Prevent competing workers from simultaneously owning the same work |
| Request approval | Persist the approval request and associated operation binding |
| Record a decision | Enforce decision validity and prevent conflicting duplicate decisions |
| Dispatch an operation | Persist the intent before external dispatch |
| Record an outcome | Validate operation identity and current ownership of the work |
| Recover after restart | Load nonterminal tasks and reconcile uncertain external effects |
| Write an audit event | Persist the required event under the defined audit durability policy |

### Transaction rules

- Use short transactions for state transitions and claims.

- Do not hold a database transaction open while waiting for a model response or remote Windows operation.

- Enforce uniqueness and ownership invariants with database constraints where appropriate.

- Use transactions to keep related database updates consistent.

- Do not claim that a database rollback reverses an already executed Windows action.

- Prevent stale workers from overwriting newer results using an appropriate claim-generation or fencing mechanism.

The exact repository interfaces, SQLAlchemy session pattern, isolation level and worker-claim implementation remain design decisions. They should be selected and tested against the required concurrency behavior rather than assumed in advance.

## 03.24.10 Contract F — Task lifecycle events

NEXUS needs consistent internal events so that components agree on what happened and when.

Proposed event envelope:

{

"event_id": "event-id",

"event_type": "task.step.dispatched",

"schema_version": 1,

"task_id": "task-id",

"step_id": "step-id",

"operation_id": "operation-id",

"occurred_at": "2030-01-01T00:00:00Z",

"correlation_id": "request-or-workflow-id"

}

This is an illustrative envelope. Event names and payloads will be finalized alongside the state machine.

### Initial event categories

| **Category** | **Example events** |
| --- | --- |
| Task lifecycle | Task accepted, started, completed, failed |
| Step lifecycle | Step prepared, dispatched, succeeded, failed, uncertain |
| Approval | Approval requested, approved, rejected, expired |
| Device | Device connected, disconnected, revoked |
| Recovery | Reconciliation started, outcome confirmed, recovery blocked |
| Policy | Operation allowed, denied or held for approval |
| System | Model unavailable, database unavailable, worker restarted |

### Event-handling rules

- Events describe facts; they do not independently grant permissions.

- State-changing events must be checked against legal task and step transitions.

- Duplicate event delivery must be handled safely where retries are possible.

- Event ordering must not be assumed across independent components unless the implementation explicitly guarantees it.

- Timestamps alone are not sufficient to establish ordering in every concurrent scenario.

- Private document contents, credentials and unrestricted prompts should not be included in event payloads by default.

For the initial modular monolith, internal service calls and durable database records may be sufficient. A separate message broker is not required merely to implement an event vocabulary.

If the system later needs reliable asynchronous event publication, a transactional outbox is a candidate solution so database changes and event publication can be reconciled without pretending they are one atomic operation.

## 03.24.11 Standard error contract

Every boundary must return errors that the receiving component can interpret consistently.

Proposed public API error:

{

"error": {

"code": "DEVICE_UNAVAILABLE",

"message": "The selected computer is currently unavailable.",

"retryable": true

},

"request_id": "request-id"

}

The message is user-facing. The error code is the stable machine-readable contract. The example does not guarantee that retrying immediately is safe; retry safety depends on the operation and its current execution state.

### Proposed error categories

| **Category** | **Example code** | **Handling** |
| --- | --- | --- |
| Invalid request | INVALID_ARGUMENT | Correct the request; do not retry unchanged |
| Authentication failure | AUTHENTICATION_REQUIRED | Reauthenticate |
| Authorization failure | ACCESS_DENIED | Do not retry without a legitimate permission change |
| Policy restriction | POLICY_DENIED | Explain the restriction safely |
| Approval required | APPROVAL_REQUIRED | Wait for the appropriate decision |
| Device unavailable | DEVICE_UNAVAILABLE | Wait for reconnection; preserve task state |
| Dependency failure | DEPENDENCY_UNAVAILABLE | Apply bounded retry rules where safe |
| Operation timeout | OPERATION_TIMEOUT | Determine whether the external effect occurred |
| Uncertain outcome | OPERATION_OUTCOME_UNCERTAIN | Reconcile before any unsafe retry |
| Contract mismatch | CONTRACT_VERSION_UNSUPPORTED | Block incompatible execution |
| Internal failure | INTERNAL_ERROR | Return a correlation ID; keep implementation details in protected diagnostics |

A single global retryable boolean is not enough to authorize retries of external operations. The orchestrator must combine the error category with the tool's declared retry policy, operation history and known execution state.

## 03.24.12 Contract versioning and compatibility

NEXUS has several interfaces that evolve at different rates. API compatibility and bridge compatibility must therefore be handled separately.

### Proposed rules

- The public API uses the existing /v1 version prefix.

- Bridge messages include a protocol version.

- Tool arguments and results use a tool-specific schema version.

- Internal events use an event schema version where persisted or exchanged across independently deployed components.

- Compatible changes should preserve existing semantics.

- Renaming or removing required fields, changing state meanings, or weakening security behavior requires a controlled migration.

- An unknown security-sensitive field or version must not be interpreted permissively.

- Backend and bridge compatibility must be checked before dispatch.

- Schema migrations must not silently reinterpret old pending operations as safe to execute.

During a rolling update, a bridge that cannot understand an operation must reject it safely. NEXUS should not downgrade security checks simply to maintain compatibility.

Open decision: whether the first release needs simultaneous support for multiple bridge protocol versions. For a small, controlled three-developer deployment, one active version may be sufficient, provided upgrades and recovery are documented.

## 03.24.13 Contract testing and integration ownership

Every contract should have tests that verify both valid behavior and rejection behavior.

Schema and validation tests

Verify required fields, types, bounds, unknown-field policy, malformed JSON and incompatible versions.

Authorization and security tests

Verify user and device isolation, revoked credentials, approval binding, invalid tool names and locally prohibited paths.

Reliability tests

Verify duplicate submissions, duplicate operation delivery, lost responses, stale workers, cancellation races and restart recovery.

End-to-end integration tests

Verify the complete flow from CLI request through planning, authorization, bridge execution, persisted result and CLI reporting.

### Proposed ownership

| **Developer** | **Primary contract responsibility** |
| --- | --- |
| Developer 1 — backend and execution | Public API, task lifecycle, persistence, policy integration, error mapping and recovery |
| Developer 2 — Windows integration | Bridge protocol, local tool schemas, authentication, local enforcement and execution outcomes |
| Developer 3 — AI and context | Planner schema, context inputs, structured outputs, clarification behavior and model failure handling |
| All three | Contract review, cross-component tests, security review and end-to-end acceptance |

These assignments are a proposal based on the existing team structure. Every developer must understand the security and lifecycle invariants even when another developer owns the implementation.

### Parallel development rule

Before implementation starts, the team should agree on a small contract package containing:

1. Shared identifier definitions.

2. Task and step state enumerations.

3. Planner input and output schemas.

4. Tool registry and operation envelope.

5. Bridge response and error formats.

6. Approval decision semantics.

7. Versioning and compatibility rules.

8. Representative valid and invalid test fixtures.

Each component can then use mocks or contract fixtures while the other components are developed independently.

## 03.24.14 MVP priorities

- P0 — required: task submission and status contracts, planner schema, tool invocation envelope, policy decision interface, approval semantics, bridge request/result schema, stable error codes and contract tests.

- P1 — required as reliability matures: richer lifecycle events, compatibility negotiation, durable event publication if needed, more detailed reconciliation contracts.

- P2 — future: external message broker, multiple independently deployed protocol versions, distributed tracing and more advanced event-driven workflows.

The design should not introduce a message broker, microservices or a complex event platform solely because those patterns are used in larger systems. Add them only when an identified requirement justifies the operational cost.

## 03.24.15 Open decisions register

| **ID** | **Decision** | **Proposed starting point** |
| --- | --- | --- |
| INT-01 | Shared schema technology | Evaluate Pydantic models for Python boundaries |
| INT-02 | Bridge communication | Keep polling as the provisional transport; finalize the protocol independently |
| INT-03 | Internal events | Start with explicit service calls and persisted state |
| INT-04 | Durable event publication | Add a transactional outbox if reliable asynchronous publication becomes necessary |
| INT-05 | ID format | Select one consistent opaque identifier strategy |
| INT-06 | Unknown fields | Define strictness separately for public API, bridge messages and forward-compatible metadata |
| INT-07 | Protocol upgrades | Document compatibility and recovery before enabling mixed versions |
| INT-08 | Payload limits | Establish explicit limits for requests, tool results and error details |
| INT-09 | Error contract | Finalize error codes and map them consistently at every boundary |
| INT-10 | API contract generation | Decide how the OpenAPI specification and shared test fixtures are maintained |

These choices should be resolved before their respective interfaces are implemented. None requires selecting a distributed architecture in advance.

## 03.24.16 Acceptance criteria

- The CLI and backend agree on task submission, status, approval, cancellation and error contracts.

- The planner returns validated structured proposals rather than executable commands.

- The policy engine's decision contract separates authorization from planning.

- The bridge contract identifies the target device and distinguishes operation identity from attempt identity.

- Duplicate delivery and uncertain external outcomes have documented handling.

- Persistence rules prevent duplicate task creation and unsafe concurrent execution.

- State transitions and internal events use documented meanings.

- Incompatible contracts fail safely.

- Each component has independent contract tests and shared test fixtures.

- The team can execute an end-to-end test using all three developers' components without ad hoc field-name or status conversions.

### Section exit criteria

## Section 03.24 is ready to move forward when the three developers agree on the interface contracts and can develop their components independently against the same schemas and test fixtures.
