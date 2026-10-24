## 03.19.1 Purpose

NEXUS operates across several independently failing components: the CLI, FastAPI backend, PostgreSQL, AI runtime and Windows bridge on each user's computer. When a task fails, the team must be able to determine what happened, where it happened, why it happened and whether any computer operation actually took effect.

Observability must support four goals:

1. Debugging: identify the source of errors without guessing.

2. Reliability: detect stuck tasks, disconnected devices and failed dependencies.

3. Security: identify unauthorized attempts and policy violations.

4. Performance: measure API latency, model inference time, database delays and Windows operation duration.

A successful health check does not prove that every task can complete. Likewise, an HTTP success response does not prove that an external Windows action succeeded.

## 03.19.2 Observability architecture

## 03.19.3 Logging standards

All backend and bridge logs should use structured fields rather than relying exclusively on free-form messages.

### Required fields

| **Field** | **Purpose** |
| --- | --- |
| timestamp | When the event occurred, preferably UTC |
| level | DEBUG, INFO, WARNING, ERROR or CRITICAL |
| service | API, orchestrator, model adapter, CLI or Windows bridge |
| event_name | Stable machine-readable event identifier |
| request_id | Correlates an incoming API request with its response |
| task_id | Identifies the task, when applicable |
| step_id / operation_id | Identifies the individual operation, when applicable |
| device_id | Identifies the registered device, when applicable |
| duration_ms | Measures elapsed time where relevant |
| error_code | Stable application-defined error identifier, when applicable |

Additional fields may include a worker identifier, attempt number, bridge protocol version, dependency name and outcome.

Not every event needs every field. For example, a startup event may have no task ID.

### Example log event

{

"timestamp": "2026-10-22T12:30:00Z",

"level": "WARNING",

"service": "orchestrator",

"event_name": "operation_outcome_uncertain",

"request_id": "req-example",

"task_id": "task-example",

"operation_id": "op-example",

"device_id": "device-example",

"error_code": "BRIDGE_RESPONSE_TIMEOUT",

"duration_ms": 15000

}

This is an illustrative event format, not a final logging schema or evidence of an actual NEXUS execution.

Rules:

- Use stable event names and error codes so logs can be searched reliably.

- Record state transitions explicitly.

- Include exception details in restricted diagnostic logs where appropriate, but never return raw stack traces to ordinary CLI users.

- Use structured logging with bounded field lengths.

- Do not log full authorization headers, passwords, access tokens, refresh tokens, bridge credentials or other secrets.

- Avoid logging full prompts, document contents, extracted text or private memory by default.

- Sanitize user-controlled strings to prevent log injection.

- Keep timestamps consistent across components; record both event time and elapsed duration when useful.

## 03.19.04 Task and operation tracing

Every accepted task needs a stable task ID. Every operation needs a stable operation ID, and each attempt should be distinguishable from the logical operation itself.

A typical trace should allow the team to reconstruct this sequence:

1. Request accepted: authenticated user submits a request; backend records the task.

2. Planning: the model proposes a plan; the backend validates the plan.

3. Authorization: policy determines whether an operation is permitted or requires approval.

4. Dispatch: the orchestrator records intent and sends the operation to the target device.

5. Execution: the bridge validates and executes the registered tool.

6. Result handling: backend records the response, verification outcome or uncertainty.

7. Completion: final task state and user-visible result are persisted.

A single task can have many steps and attempts. Correlation identifiers must preserve these relationships without treating each retry as a new logical operation.

### Key distinction

- Task history explains what happened to the user's task.

- Audit events record security-relevant decisions and actions.

- Application logs explain implementation and runtime behavior.

- Metrics quantify system behavior over time.

These are related, but they are not interchangeable. A log file should not be the only durable record of a consequential operation.

## 03.19.05 Health checks and readiness

NEXUS should distinguish process liveness from service readiness.

| **Check** | **What it establishes** | **What it does not establish** |
| --- | --- | --- |
| API liveness | Backend process is responsive | Database or AI availability |
| Database health | PostgreSQL connection and a basic query work | All queries perform correctly |
| AI readiness | Configured model runtime is reachable and usable for a bounded check | Every generated plan is correct |
| Device health | A recent bridge heartbeat or status report was received | Every local tool is functioning |
| Task readiness | Required dependencies and execution capacity are available | Every submitted task will succeed |

### Proposed endpoints

- GET /health/live — process liveness.

- GET /health/ready — readiness for the configured backend dependencies.

- An authenticated diagnostics command or endpoint — detailed dependency status for authorized operators.

These are proposed routes; the exact response schema and exposure policy remain to be finalized.

Readiness checks must have bounded timeouts. A health check should not trigger expensive model generation or reveal internal addresses, credentials or infrastructure details to unauthorized clients.

The overall status should distinguish at least:

- Ready

- Degraded

- Unavailable

For example, a model outage might make AI-dependent tasks unavailable while leaving task history and other independent API functions operational.

## 03.19.06 Metrics and performance visibility

Collect metrics that help answer operational questions, not simply as many metrics as possible.

### API and backend

- Request count by route and response class.

- API latency, including median and p95.

- Validation, authentication and authorization failure counts.

- Database errors and connection-pool pressure.

- Worker claims, active tasks and waiting tasks.

- Task duration and time spent in each major stage.

### AI runtime

- Planning latency.

- Model errors and timeouts.

- Invalid structured-plan count.

- Token or context-size information if the runtime exposes it safely.

- CPU, RAM, GPU utilization and VRAM use where measurable.

### Windows bridge

- Last heartbeat age.

- Connection failures and reconnects.

- Operation duration by tool.

- Operation outcomes: succeeded, failed, rejected or uncertain.

- Timeout and retry counts.

- Tool-specific failure rates.

### Reliability and safety

- Number of tasks in recovery states.

- Number and age of unresolved uncertain operations.

- Expired approvals.

- Rejected unauthorized operations.

- Duplicate task submissions detected.

- Failed reconciliation attempts.

Avoid high-cardinality metric labels such as arbitrary request IDs, task IDs or full file paths. Use IDs in logs and traces; aggregate metrics by bounded dimensions such as service, tool type, outcome and error category.

## 03.19.07 Error classification and diagnostics

Errors should be classified consistently across API, orchestrator and bridge.

| **Error category** | **Example** | **Expected response** |
| --- | --- | --- |
| VALIDATION_ERROR | Malformed tool arguments | Reject the operation and identify the invalid field where safe |
| AUTHORIZATION_DENIED | User lacks permission for the target operation | Do not execute; return a safe explanation |
| DEPENDENCY_UNAVAILABLE | PostgreSQL or model runtime unavailable | Report dependency status and whether retry may be appropriate |
| EXECUTION_TIMEOUT | Tool did not respond within its limit | Determine whether the outcome is known or uncertain |
| DEVICE_UNAVAILABLE | Target Windows bridge disconnected | Preserve the task and report the device condition |
| OPERATION_OUTCOME_UNCERTAIN | External action may have occurred, but its result was not confirmed | Reconcile before any unsafe retry |
| INTERNAL_ERROR | Unexpected application failure | Record restricted diagnostics and return a safe error |

Error codes are examples. The final registry should be centralized, documented and stable enough for the CLI and automated tests to depend on.

Each user-visible error should explain:

1. What failed or remains uncertain.

2. Whether any action may already have occurred.

3. Whether the user needs to act.

4. Whether retry is safe, unsafe or pending reconciliation.

Never advise a user to retry an uncertain write merely because the first request timed out.

## 03.19.08 CLI diagnostic experience

The terminal interface should help users diagnose common issues without requiring access to server logs.

Proposed commands:

nexus status

nexus devices

nexus task <task-id>

nexus task <task-id> --steps

nexus task <task-id> --result

nexus diagnostics

These are proposed command names and can be aligned with the final CLI contract.

nexus status should summarize the authenticated user, backend connectivity, relevant dependency health and the availability of the selected device.

nexus diagnostics should produce a safe diagnostic summary, such as:

- CLI version and platform.

- Backend reachability.

- Database readiness as reported by the backend.

- AI runtime readiness.

- Bridge version and last-seen status.

- Relevant error codes and correlation IDs.

- Whether tasks need recovery.

It must not dump environment variables, credentials, private memory, unrestricted filesystem listings or full document contents.

If a diagnostic bundle is implemented, it should use an explicit output location, bounded file size and a preview or clear disclosure of included information before sharing it with teammates.

## 03.19.09 Privacy, access and retention

Observability itself can create a data-exposure risk. NEXUS must collect enough evidence to diagnose behavior without turning logs into a second copy of users' private data.

Required rules:

- Users may view only the task history and diagnostic details they are authorized to access.

- Operator access to other users' diagnostic data must be explicitly defined and audited.

- Logs must not contain authentication secrets or unnecessary document contents.

- Task history and security audit events must have separately defined retention rules.

- Deleting a memory must remove it from active retrieval and relevant caches/indexes; it does not automatically imply deletion of task history or audit records.

- Diagnostic exports must be reviewed for sensitive fields before sharing.

- Backups and exported diagnostics must follow the same access and retention policies as their source data.

- Error messages must not expose internal stack traces, sensitive paths or database details to unauthorized clients.

Open decision: exact retention periods, log storage location, operator privileges and backup retention have not yet been selected.

## 03.19.10 Incident and debugging workflow

When a task fails, the team should follow a consistent procedure instead of immediately modifying code or retrying the operation.

1. Find the task. Retrieve its task ID, current state, steps and timestamps.

2. Establish the last confirmed event. Determine whether failure occurred during planning, authorization, dispatch, execution or result persistence.

3. Check the target device. Verify its registered identity, connectivity and recent bridge status.

4. Inspect the operation outcome. Distinguish known failure from unknown external outcome.

5. Check relevant dependency health. Review database, model runtime, API and bridge diagnostics.

6. Preserve evidence. Record the correlation IDs and sanitized logs needed to reproduce the problem.

7. Choose the recovery action. Retry only when the operation's policy allows it; otherwise reconcile or request human intervention.

8. Add a regression test. For reproducible defects, add a test that prevents the same failure from silently returning.

If a potentially destructive operation has an uncertain outcome, investigation and reconciliation come before retrying.

## 03.19.11 Implementation priority for the 10–12-week MVP

#### P0

Required

Essential diagnostics

Structured logs, stable error codes, task and operation IDs, persisted state transitions, safe health endpoints, bridge last-seen status and accurate uncertain-outcome reporting.

#### P1

Next

Operational visibility

Basic latency metrics, dependency readiness, recovery-state visibility, diagnostic CLI output and model/bridge failure summaries.

#### P2

Optional

Advanced observability

Distributed tracing, dashboards, alerting integrations and centralized log aggregation. Add them only if operational complexity justifies the cost and effort.

The initial deployment should not require paid monitoring services. Local logs, PostgreSQL-backed operational records and lightweight metrics are sufficient to establish a baseline.

## 03.19.12 Acceptance criteria

## Section 03.19 is ready for implementation when the team agrees that:

- Every task can be traced from acceptance to its final or recovery state.

- Every external operation has a stable identifier and distinguishable attempts.

- Logs and errors never expose secrets by default.

- Users cannot access another user's task diagnostics without explicit authorization.

- Health checks distinguish liveness, readiness and degraded operation.

- The CLI can identify common backend, AI and device failures.

- An uncertain external action is visibly marked and cannot be blindly retried.

- The team can investigate a failed task using its identifiers and persisted records.

- Retention and operator-access policies are documented before real users' data is stored.

## Section 03.19 exit criterion: the team can diagnose a failed or uncertain task from its persisted state and sanitized diagnostics without guessing, exposing private data or accidentally repeating an external action.
