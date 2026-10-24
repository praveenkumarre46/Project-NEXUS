## 03.29.1 Purpose

NEXUS must represent task progress precisely enough that the CLI, API, scheduler, AI planner, Windows bridge and recovery logic all agree on what has happened.

Consider this scenario:

1. A user asks NEXUS to create a file.

2. The backend records the task and sends the operation to the Windows bridge.

3. Windows creates the file successfully.

4. The bridge's response is lost before the backend records the result.

5. The backend restarts.

At this point, the file may exist even though the database does not record success. Marking the task as failed and repeating the operation could create a duplicate or overwrite data.

The task state machine must preserve the distinction between what NEXUS knows, what it has requested and what may have happened externally.

This section defines:

- Legal task and step states.

- Allowed state transitions.

- Which component is permitted to make each transition.

- Required persistence and validation.

- Handling for cancellation, approval, timeouts, retries and recovery.

- Invariants that automated tests must enforce.

The state machine is a proposed formalization of the earlier architecture sections. Exact enum names and schema representations can change during implementation, but the behavioral invariants must remain intact.

## 03.29.02 State-machine design principles

1. Persist before dispatch. Record execution intent before sending an operation that may cause an external side effect.

2. Never infer success from submission. Dispatching an operation does not prove it executed.

3. Unknown is a valid outcome. When evidence is insufficient, preserve uncertainty rather than inventing success or failure.

4. Enforce transitions centrally. Application services validate state changes; API handlers, AI output and bridge messages must not update arbitrary states directly.

5. Use transactions for state changes. Concurrent updates must not silently overwrite one another.

6. Separate task state from step state. A task may contain several operations with different outcomes.

7. Make recovery explicit. Restarting a process must not automatically replay every unfinished operation.

8. Keep policy independent. A legal state transition does not itself authorize an operation.

## 03.29.03 Task lifecycle

The task represents the overall request submitted by a user.

### QUEUED

Accepted and durably recorded; awaiting scheduling

### RUNNING

Planning, validating or executing eligible work

#### WAITINGFORAPPROVAL

Human decision required

#### INTERRUPTED

Recovery or reconciliation required

Return to execution only when the required checks pass

#### Terminal task states

SUCCEEDED

FAILED

CANCELLED

This is a conceptual overview. The transition table below is authoritative for the proposed initial behavior.

### State definitions

| **State** | **Meaning** |
| --- | --- |
| QUEUED | The task has been accepted and persisted but has not started active processing. |
| RUNNING | The task is undergoing planning, validation, execution or verification. |
| WAITING_FOR_APPROVAL | At least one required approval blocks further consequential execution. |
| INTERRUPTED | Progress cannot safely continue until recovery, dependency restoration or outcome reconciliation occurs. |
| SUCCEEDED | All required work completed and the defined success conditions were verified. |
| FAILED | The task cannot complete successfully under the current attempt or defined recovery policy. |
| CANCELLED | Cancellation has been confirmed, and no further task work will be dispatched. |

SUCCEEDED, FAILED and CANCELLED are terminal for a particular task ID. A new attempt that constitutes a new user request should use a new task ID and retain any relevant linkage to the original task.

A task with partial success can be FAILED while its result records which steps succeeded and which failed or remain uncertain. Do not add PARTIALLY_SUCCEEDED as a state unless a concrete API or operational need demonstrates that it improves the lifecycle model.

## 03.29.04 Legal task transitions

The following table defines the proposed permitted transitions.

| **Current state** | **Event or condition** | **Next state** | **Required behavior** |
| --- | --- | --- | --- |
| None | Valid task accepted | QUEUED | Persist task and idempotency key atomically |
| QUEUED | Scheduler claims task | RUNNING | Establish a valid worker claim |
| QUEUED | Cancellation confirmed before dispatch | CANCELLED | Ensure no work was dispatched |
| QUEUED | Required approval is identified | WAITING_FOR_APPROVAL | Persist the approval requirement |
| RUNNING | Required approval blocks progress | WAITING_FOR_APPROVAL | Persist approval request and block further affected execution |
| RUNNING | Outcome or dependency requires recovery | INTERRUPTED | Persist recovery reason and unresolved operations |
| RUNNING | All required work is verified | SUCCEEDED | Persist final result and terminal transition |
| RUNNING | Unrecoverable task failure established | FAILED | Persist error and any partial results |
| RUNNING | Cancellation fully confirmed | CANCELLED | Stop future dispatch and reconcile in-flight work |
| WAITING_FOR_APPROVAL | Valid approval and revalidation succeed | RUNNING | Recheck task state, permissions, expiry and operation fingerprint |
| WAITING_FOR_APPROVAL | Rejection or expiry makes continuation impossible | FAILED | Record reason; no affected operation is dispatched |
| WAITING_FOR_APPROVAL | Task cancelled safely | CANCELLED | Reject later approvals for that task |
| WAITING_FOR_APPROVAL | Required state or operation outcome is uncertain | INTERRUPTED | Reconcile before proceeding |
| INTERRUPTED | Recovery conditions satisfied | QUEUED or RUNNING | Resume only after safe recovery and revalidation |
| INTERRUPTED | Recovery establishes irrecoverable failure | FAILED | Record evidence and preserve partial results |
| INTERRUPTED | Cancellation confirmed and side effects reconciled | CANCELLED | Preserve completed external effects in the result |

Important: some events do not have a single automatic outcome. For example, an expired approval may cause a task to fail, return to a clarification state if that state is added later, or wait for a newly requested approval. The initial implementation should choose one documented policy. It must never dispatch the expired operation.

### Forbidden transitions

The initial state machine must reject, among others:

- SUCCEEDED → RUNNING

- FAILED → RUNNING

- CANCELLED → QUEUED

- WAITING_FOR_APPROVAL → SUCCEEDED without executing and verifying the required work

- INTERRUPTED → SUCCEEDED without reconciling unresolved operations

- Any state → SUCCEEDED solely because a model or bridge claimed success without the required validation

- Any state → CANCELLED while an external side effect may still be running and has not been safely reconciled

A rejected transition should produce a stable internal error, record enough diagnostic context to investigate, and leave the existing valid state unchanged.

## 03.29.05 Task-step lifecycle

A task contains individual steps. Step state must reflect execution at the operation level, not simply mirror the task state.

Proposed states:

| **State** | **Meaning** |
| --- | --- |
| PENDING | Defined but dependencies are not yet satisfied. |
| READY | Dependencies are satisfied and the step is eligible for processing. |
| WAITING_FOR_APPROVAL | The step requires an approval before dispatch. |
| DISPATCHED | Execution intent is persisted and the request has been sent or is in the dispatch process. |
| RUNNING | The bridge or relevant executor has confirmed that execution has started. |
| SUCCEEDED | The operation's required success conditions have been verified. |
| FAILED | Failure is established and the step cannot continue under its current execution attempt. |
| REJECTED | Policy or local validation rejected the operation before execution. |
| UNCERTAIN | Available evidence cannot establish whether the external effect occurred. |
| CANCELLED | The step was safely cancelled and no unresolved effect remains. |

DISPATCHED and RUNNING are intentionally distinct. A request may have been sent but not yet acknowledged as executing. A timeout in either state does not prove that nothing happened.

### Proposed step transitions

#### Normal execution

Happy path

PENDING

READY

DISPATCHED

RUNNING

SUCCEEDED

#### Approval path

READY

WAITING_FOR_APPROVAL

READY

The return to READY is allowed only after approval is valid and all execution checks are repeated.

#### Uncertain outcome path

DISPATCHED

UNCERTAIN

Reconcile

Reconciliation determines whether the operation succeeded, failed, or remains uncertain. An unsafe retry is not an automatic transition.

The diagram illustrates the main paths, not every legal transition. The implementation must maintain an explicit transition map for all supported events.

## 03.29.06 Which component may change task state?

State ownership must be explicit. Otherwise, individual modules will gradually implement conflicting lifecycle rules.

| **Component** | **Responsibility** | **Must not do** |
| --- | --- | --- |
| API layer | Accept requests, authenticate callers and expose task operations | Directly assign arbitrary lifecycle states |
| Task service | Validate and persist permitted task transitions | Assume a requested transition is automatically legal |
| Scheduler | Select eligible work and coordinate claims | Bypass authorization or approval |
| AI planner | Propose plans and request clarification | Mark tasks or operations successful |
| Policy engine | Return allow, deny, approval-required or defer decisions | Execute tools or change task state without the application workflow |
| Windows bridge | Execute registered tools and report local outcomes | Mark the overall task successful |
| Recovery service | Reconcile interrupted work and propose safe resumption | Replay all expired or unfinished operations blindly |
| Persistence layer | Enforce transactions, constraints and durable records | Decide business policy independently |

The task service and orchestrator should own lifecycle transitions. Other components communicate events or return typed results to that workflow.

A bridge response is evidence about a local operation. The backend must validate the response's operation ID, task ID, device identity and protocol version before using it to update state.

## 03.29.07 Transition invariants

An invariant is a rule that must remain true regardless of concurrency, failures or restart.

### Identity and ownership

- Every task has exactly one owner and one explicit target device.

- The task's owner is derived from authenticated identity, not from an untrusted request body.

- Only authorized callers may read task status, steps, results or approvals.

- A task cannot silently change target devices.

- A revoked user or device cannot perform new unauthorized operations.

### State correctness

- Only documented transitions are permitted.

- Every accepted transition is persisted before it is reported as durable.

- Terminal states cannot return to active states.

- A task cannot succeed while required steps remain unresolved.

- A task cannot be cancelled while an external effect remains unresolved.

- Partial results remain available even if the overall task fails.

### Execution correctness

- Each logical step has a stable operation ID.

- Every dispatch has a recorded execution intent.

- Duplicate delivery cannot create a new logical operation accidentally.

- An expired worker claim does not establish that its operation stopped.

- Retries follow the tool's retry policy and the known operation outcome.

- A timeout never automatically implies failure or permission to repeat a side effect.

### Approval and authorization

- Approval applies only to the exact operation, target, scope and parameters that were approved.

- Expired, rejected or invalidated approval cannot authorize dispatch.

- Authorization is rechecked immediately before execution.

- A task's priority cannot override policy.

- AI-generated output cannot grant permissions or directly mutate lifecycle state.

These invariants should be enforced in application code and, where suitable, reinforced with PostgreSQL constraints and conditional updates.

## 03.29.08 Atomicity and concurrent transitions

Two workers may attempt to claim the same task. A user may cancel a task just as an approval arrives. A bridge result may arrive while recovery is processing an expired claim.

The state machine must define which operation wins and prevent invalid intermediate states.

### Recommended transaction pattern

1. Start a short database transaction.

2. Read or conditionally update the relevant task and step records.

3. Verify the expected current state and claim generation.

4. Verify that the requested transition is legal.

5. Update state, timestamps and required event records atomically.

6. Commit.

7. Perform external work only after the required intent has been committed.

A conditional update can enforce the expected state:

UPDATE tasks

SET status = 'running',

updated_at = CURRENT_TIMESTAMP

WHERE task_id = :task_id

AND status = 'queued';

This is an illustrative fragment, not a complete claim implementation. A production claim also needs appropriate worker ownership, lease or fencing data, concurrency control and verification that exactly one eligible row was claimed.

The application must not assume that a successful SQL statement means it won the claim unless it checks the affected-row count and all required claim conditions.

### Cancellation versus approval race

If approval and cancellation happen concurrently, NEXUS must use an atomic state check so only a valid transition wins.

- If cancellation is committed first, the approval cannot restart the task.

- If approval is committed first, cancellation must still prevent subsequent dispatch if it is committed before dispatch authorization.

- If the operation has already been dispatched, cancellation must follow the in-flight operation and reconciliation rules.

- If the result is unknown, preserve uncertainty until the operation can be reconciled.

The exact serialization mechanism can be finalized during implementation, but these outcomes must remain true.

## 03.29.09 Cancellation is a lifecycle protocol

A user pressing Ctrl+C in the CLI may only stop waiting for output. It must not automatically be interpreted as a cancellation request unless the CLI explicitly sends one.

NEXUS should distinguish these events:

- WATCH_STOPPED: the client stopped displaying progress.

- CANCEL_REQUESTED: a user requested cancellation.

- CANCEL_ACCEPTED: the backend accepted the request and is processing it.

- CANCELLED: the task has reached a confirmed terminal cancellation state.

Only the last represents a completed cancellation.

### Cancellation procedure

1. Authenticate the caller and authorize access to the task.

2. Persist the cancellation request or equivalent durable cancellation intent.

3. Prevent dispatch of new steps.

4. Signal cooperative cancellation to workers and the bridge where supported.

5. Wait for or reconcile in-flight operations.

6. Preserve completed effects and partial results.

7. Mark the task CANCELLED only when the task is no longer executing and unresolved side effects have been addressed.

If an operation cannot be stopped and its outcome cannot be determined, the task must remain interrupted or otherwise explicitly unresolved. It must not be marked cancelled merely to satisfy a user-interface expectation.

## 03.29.10 Approval lifecycle and expiry

An approval record should have its own lifecycle, separate from the task and step states.

Proposed approval decisions:

- PENDING

- APPROVED

- REJECTED

- EXPIRED

- INVALIDATED

Approval is not a reusable permission token. It is a decision bound to a specific operation.

The approval record should include:

- Approval ID and the task/step it applies to.

- Requesting user and authorized decision-maker.

- Target device and tool identity.

- Normalized operation arguments or a securely computed fingerprint.

- Relevant resource scope and policy version.

- Creation, expiry and decision timestamps.

- Decision and audit correlation ID.

### Expiry rules

- Expiry must be checked at decision time and immediately before dispatch.

- A late approval must not revive a cancelled task.

- A change to the tool, arguments, target, resource scope or relevant policy must invalidate the previous approval when it changes what is being authorized.

- Approval must not override a hard prohibition.

- A new approval request must receive a new identity or clearly versioned approval record.

The default approval duration remains an open configuration decision. It must be defined before production use.

## 03.29.11 Recovery after a backend restart

The backend must not treat every nonterminal task as immediately runnable when it restarts.

### Recovery procedure

1. Load durable state. Find tasks and steps that are nonterminal, dispatched, running or associated with expired claims.

2. Classify the interruption. Determine whether work was merely queued, was waiting for approval, was dispatched, or may have produced an external side effect.

3. Reconcile external operations. Use the operation ID, bridge's recorded outcome and available local evidence to establish what happened.

4. Revalidate eligibility. Check current user/device status, permissions, approval expiry, policy and task cancellation state.

5. Choose a safe next state. Requeue work that is safe to retry, resume confirmed incomplete work, fail unrecoverable work, or preserve uncertainty.

6. Persist the recovery result. Record the transition and recovery evidence before continuing execution.

### Recovery examples

| **Last known condition** | **Recovery behavior** |
| --- | --- |
| Task was queued and never claimed | Return to normal scheduling after validation |
| Model planning was interrupted before any operation was dispatched | Retry planning within configured limits |
| Read-only search timed out | Retry if the tool's retry policy permits |
| File creation was dispatched, but response was lost | Reconcile the file and operation record before retrying |
| Approval was pending at shutdown | Keep blocked until a valid decision or expiry policy resolves it |
| Device was offline during dispatch | Preserve the correct interrupted/uncertain status and reconcile on reconnect |
| Task was cancelled before any dispatch | Finalize cancellation after confirming no work started |
| A write may have succeeded, but no reliable evidence remains | Keep the outcome uncertain; require a defined recovery or human intervention path |

A database backup or restore adds another challenge: the restored database may not contain the most recent state of an external Windows operation. Restored tasks therefore require the same reconciliation discipline.

## 03.29.12 State history and event records

The current task row answers, “What is the task's state now?” The event history answers, “How did it reach that state?”

These are different responsibilities.

A task transition event should record fields such as:

| **Field** | **Purpose** |
| --- | --- |
| event_id | Unique event identity |
| task_id | Related task |
| step_id | Related step, if applicable |
| event_type | Transition, cancellation request, approval decision, recovery outcome, etc. |
| from_state | Previous state |
| to_state | New state |
| actor_type | User, scheduler, orchestrator, bridge or recovery process |
| actor_id | Authorized actor or component identity where applicable |
| reason_code | Stable machine-readable explanation |
| correlation_id | Connect related API, worker and bridge activity |
| created_at | UTC timestamp |

The exact event schema is not finalized. The important requirement is that state updates and required transition records are committed atomically, so a crash cannot leave a state change without its corresponding durable event.

Not every diagnostic log entry must be a database event. Keep operational logs, durable lifecycle history and security audit events separate, with appropriate access and retention policies.

Do not put full document contents, passwords, tokens or unrestricted model prompts in lifecycle events.

## 03.29.13 Implementation design

The recommended implementation is a central transition service with explicit transition rules.

Illustrative Python pseudocode:

def transition_task(task, event, context):    # Illustrative pseudocode, not production-ready code.    if task.is_terminal:        raise InvalidTransitionError()    next_state = transition_rules.resolve(        current_state=task.status,        event=event,    )    validate_transition_invariants(        task=task,        next_state=next_state,        context=context,    )    return next_state

Production implementation must additionally perform the transition within an appropriate transaction, verify expected database state and worker generation, persist the transition event, and handle concurrent updates.

### Recommended module responsibilities

- domain/state_machine.py: state definitions, legal transitions and pure transition rules.

- services/task_service.py: authenticated task operations and lifecycle coordination.

- execution/orchestrator.py: plans and sequences work, invoking the transition service.

- execution/recovery.py: identifies unresolved work and coordinates safe reconciliation.

- execution/claims.py: worker ownership, leases and fencing.

- services/approval_service.py: approval creation, decisions, expiry and invalidation.

- infrastructure/database/: transactions, repositories, constraints and migrations.

These names align with the proposed project structure; final filenames may change as the team establishes contracts.

The domain transition rules should be testable without a live model, a real Windows device or PostgreSQL. Separate integration tests must then verify that transactions and concurrent claims preserve the same rules in the real database.

## 03.29.14 Required automated tests

### State-machine unit tests

- Every documented transition is accepted under its required conditions.

- Every forbidden transition is rejected.

- Terminal states cannot return to active states.

- A task cannot succeed while required steps are unresolved.

- An uncertain step cannot be treated as a confirmed failure without evidence.

- A denied operation cannot be dispatched.

### PostgreSQL integration tests

- Two workers cannot successfully claim the same eligible task concurrently.

- A stale worker cannot overwrite a newer transition.

- Task state and transition history are committed atomically.

- Concurrent cancellation and approval cannot violate the state machine.

- Duplicate client request IDs do not create duplicate tasks.

- A transaction rollback leaves no partially committed lifecycle transition.

### Recovery and fault-injection tests

- Backend crash immediately before dispatch.

- Backend crash after dispatch but before result persistence.

- Bridge response lost after successful file creation.

- Worker lease expires while the operation may still be running.

- Device reconnects with an unresolved operation.

- Database restore returns an older task state.

- Approval expires during an execution delay.

- Cancellation arrives while an external operation is in flight.

- Recovery itself crashes before committing its result.

For every scenario, tests must assert both the final state and the external side effects. A test that merely expects 200 OK is insufficient.

## 03.29.15 Implementation priorities

P0

Required before real computer operations

- Explicit task and step state enums.

- Centralized transition validation.

- Durable state changes and transition history.

- Atomic task claims and stale-worker protection.

- Separate handling of failed and uncertain outcomes.

- Cancellation and approval race handling.

- Recovery tests for external side effects.

P1

Reliability improvements

- More detailed recovery classifications.

- Automated reconciliation of known operation types.

- Transition diagnostics and recovery metrics.

- Additional invariants checked against persisted records.

P2

Future extensions

- More advanced workflow compensation.

- Explicit pause/resume workflows if user requirements justify them.

- Richer lifecycle visualization and operational analysis.

## 03.29.16 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| Exact state enum names | Proposed in this section |
| Whether to add a separate CANCEL_REQUESTED task state | Not required if cancellation intent is modeled separately and consistently |
| Approval expiry default | Open |
| Whether expired approval fails or requests a new approval | Must be defined before implementation |
| Recovery retry limits | Tool-specific; exact values open |
| Bridge reconciliation capabilities | Must be established per tool |
| Event-history retention | Open |
| How long to retain uncertain tasks | Open |
| Compensation for partial success | No automatic compensation by default |
| Transition schema and database constraints | Finalize alongside SQLAlchemy models and migrations |

One particularly important distinction: CANCEL_REQUESTED can be represented as a separate durable cancellation field or event rather than a primary task state. Either approach is acceptable if concurrent cancellation, execution and recovery have unambiguous behavior.

## 03.29.17 Definition of done

## Section 03.29 is ready for implementation when:

- The task and step state definitions are agreed.

- Every supported state transition has a documented trigger and validation rule.

- Forbidden transitions are rejected.

- Only the designated application workflow can commit lifecycle transitions.

- Task claims and state updates are safe under concurrent workers.

- Approval, cancellation and execution races have deterministic outcomes.

- Recovery distinguishes confirmed success, confirmed failure and uncertainty.

- No restart path blindly replays unresolved external operations.

- State history is durable, auditable and appropriately bounded.

- Automated tests cover transitions, concurrency, crashes and external side effects.

Recommended engineering decision: implement the state machine before adding broad computer automation. It is the foundation that allows NEXUS to coordinate multiple users and Windows devices without losing track of what actually happened.
