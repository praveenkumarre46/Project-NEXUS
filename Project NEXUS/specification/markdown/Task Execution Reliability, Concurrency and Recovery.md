## 03.15.1 Objectives

NEXUS must:

- Preserve accepted tasks and their execution history.

- Prevent duplicate task submissions from unintentionally repeating work.

- Coordinate concurrent workers without claiming the same work unsafely.

- Keep user approvals attached to the exact operation they authorize.

- Handle cancellation without falsely claiming an operation stopped.

- Recover from backend, model-runtime and device failures.

- Distinguish definite failure from an uncertain outcome.

- Report partial completion honestly.

- Avoid holding database transactions open while waiting for slow external operations.

Fundamental constraint: PostgreSQL and a Windows computer cannot participate in one ordinary atomic transaction. NEXUS cannot guarantee that an external computer operation executes exactly once in every crash scenario. It must combine durable state, operation identifiers, safe retries and reconciliation.

## 03.15.2 Task lifecycle and state machine

The following is the proposed task-level lifecycle. Individual steps have their own lifecycle, specified below.

### Proposed task states

| **State** | **Meaning** |
| --- | --- |
| queued | Request is accepted and stored but has not started execution |
| running | A worker is coordinating task progress |
| waiting_for_approval | At least one required operation is awaiting a valid user decision |
| interrupted | Execution cannot safely continue without recovery assessment |
| succeeded | All required operations completed and the required outcome was verified |
| failed | The task cannot complete successfully under its current execution plan |
| cancelled | Cancellation is confirmed and no further task operations will be dispatched |

A task with some successful steps and some failed steps needs an explicit outcome classification. For example, the task may be terminal with a partial_success outcome rather than treating partial success as proof that the whole task succeeded.

### State-transition requirements

- Every accepted task must have a durable initial state.

- A transition must be validated against the current state.

- Every successful transition must be persisted before it is reported as durable progress.

- A task must not be marked succeeded solely because the model generated a plan or the bridge accepted a request.

- A task must not be marked cancelled merely because a cancellation request was received.

- Recovery must inspect the state of any operation that may already have affected the user's computer.

- Terminal states must not be reopened casually. If recovery or compensation is required after a terminal state, it should be an explicit, auditable process.

The complete legal transition table will be finalized alongside the database and API contracts.

## 03.15.03 Task steps and operation states

A task is a sequence of logical steps. A step can represent searching files, reading a document, creating a file or launching an application.

The task state alone is insufficient to recover safely. NEXUS must track the state of each step and each attempt to perform that step.

### Proposed step states

| **State** | **Meaning** |
| --- | --- |
| pending | Waiting for dependencies or dispatch |
| ready | Dependencies are satisfied and execution may be considered |
| waiting_for_approval | Required authorization is pending |
| dispatched | The backend sent an operation request |
| running | The bridge reports that the operation is executing, if supported |
| succeeded | The operation result meets the tool's success contract |
| failed | A definite failure has been established |
| rejected | Policy, schema or local validation rejected the operation |
| uncertain | Available evidence cannot establish whether the external effect occurred |
| cancelled | The operation was confirmed not to proceed or was safely stopped |

The exact states may be simplified during implementation, but uncertainty must not be collapsed into ordinary failure.

### Step execution protocol

1. Prepare: validate the proposed tool and its arguments.

2. Authorize: check user, device, permissions and approval requirements.

3. Persist intent: store the operation ID and a durable step state before dispatch.

4. Dispatch: send the request to the explicitly registered target device.

5. Execute: the bridge validates the request again and invokes its registered tool.

6. Record: persist the response, attempt information and outcome.

7. Verify: apply the tool's verification contract to establish what actually happened.

8. Advance: release dependent steps only when their prerequisites are satisfied.

The backend should use short database transactions for preparation, claims and result recording. It should not hold a database transaction open while waiting for a model response, user approval or a Windows operation.

## 03.15.04 Duplicate requests and idempotency

Network failures and impatient retries can cause the same task request to reach the backend more than once.

NEXUS must support a client-generated client_request_id for task submission.

Proposed behavior:

- The first valid request creates a task and stores its request identifier.

- Repeating the same identifier for the same user and equivalent request returns the existing task.

- Reusing that identifier for a different request returns a conflict.

- The database enforces uniqueness; an application-level “check then insert” is not sufficient by itself under concurrent requests.

- The client can retrieve the existing task after a network timeout rather than blindly submitting a new one.

Task idempotency does not automatically make each computer operation idempotent. A task may contain several operations, and some operations—such as launching an application—may have different semantics when repeated.

Each operation should have a stable operation_id across retries of that logical operation. The bridge should retain enough information to identify duplicate operations and return a known outcome when possible.

### Retry classification

| **Operation type** | **Proposed retry rule** |
| --- | --- |
| Read-only file search | Retry after a transient failure, subject to limits |
| Read a document | Retry if safe and the file remains within authorized scope |
| Create a new file | Reconcile destination state before retrying |
| Launch an application | Check the known operation outcome before repeating where feasible |
| Unknown or unsupported tool | Do not retry as an alternative command |
| Operation with uncertain external effects | Reconcile first; otherwise preserve uncertainty |

A repeated request with the same operation ID must not silently become a new operation with different arguments. A changed operation requires new validation and, where applicable, fresh approval.

## 03.15.05 Worker coordination and concurrency

The initial architecture is a modular backend with PostgreSQL-backed coordination. A separate message broker is not required unless measured workload or operational requirements justify it.

Multiple workers may try to claim work simultaneously. The database must arbitrate ownership rather than relying on in-memory flags.

### Proposed worker-claim model

Each active claim should identify:

- The task or step being claimed.

- The worker identifier.

- A claim generation or fencing token.

- The claim time and lease expiry.

- The current execution state.

A worker must verify that it still owns the valid claim before committing a result. If a claim expires and another worker takes over, a stale worker must not overwrite the newer worker's task state.

PostgreSQL row locking and atomic updates are candidate implementation mechanisms. The precise query strategy should be selected during the database design and validated with concurrent integration tests.

### Concurrency boundaries

NEXUS must manage concurrency at more than one level:

1. Task-level: multiple tasks may be active at once.

2. Step-level: independent steps may be eligible to run concurrently only if their dependencies and side effects permit it.

3. Device-level: an individual computer may need a limit on simultaneous operations.

4. Model-level: concurrent inference must respect available CPU, memory and GPU resources.

5. Resource-level: conflicting operations against the same file or application may require serialization.

For the MVP, prefer a simple, configurable concurrency limit and conservative execution. Parallelize only when the task model and tool contracts establish that it is safe.

A database lease is not proof that an external Windows operation stopped. If a worker loses its lease while a bridge operation is in progress, the system must reconcile that operation before another worker repeats it.

## 03.15.06 Cancellation semantics

Cancellation is a request to stop further work, not evidence that the work has stopped.

The API should acknowledge the cancellation request separately from reporting the final task state.

### Proposed cancellation behavior

- Queued task: prevent dispatch if execution has not started.

- Running task before dispatch: stop future dispatches once the cancellation request is recorded and observed.

- Waiting for approval: invalidate or close the pending execution path so a late approval cannot restart the cancelled task.

- Bridge operation in progress: request cancellation only if the tool and bridge support it.

- Operation with uncertain outcome: reconcile before deciding whether cancellation can safely be confirmed.

- Already completed operation: preserve the result. Do not imply that cancellation undid an action already performed.

When cancellation is requested, the orchestrator should prevent new step dispatches and determine the status of any in-flight operations. A task becomes cancelled only after the system establishes that the remaining execution has stopped or will not proceed and that the required final-state conditions are satisfied.

Some computer operations may not be safely reversible. NEXUS must not promise that cancelling a task restores the computer to its previous state.

## 03.15.07 Recovery after a backend restart

PostgreSQL is the durable record of accepted tasks, steps, approvals and recorded outcomes. In-memory worker state alone is insufficient.

When the backend restarts, it should:

1. Load tasks that were not in terminal states.

2. Identify claims that are expired or no longer owned by a live worker.

3. Inspect dispatched or running steps whose outcomes were not durably recorded.

4. Query the target bridge for known operation status when the protocol supports it.

5. Reconcile operation outcomes before deciding whether to retry.

6. Revalidate authorization and approval requirements before resuming work.

7. Mark unrecoverable ambiguity as interrupted or uncertain and report it honestly.

### Recovery scenarios

| **Crash point** | **Recovery action** |
| --- | --- |
| Before the task is committed | The task was not durably accepted; a repeated request can safely attempt submission using its request ID |
| After task commit, before execution | Resume from persisted task state after validating eligibility |
| After operation intent is stored, before dispatch | Determine whether dispatch occurred before retrying |
| After dispatch, before bridge response | Query or reconcile the operation; do not assume it failed |
| After bridge execution, before result persistence | Retrieve the recorded bridge outcome if available; otherwise assess the external state |
| After result persistence, before the client receives it | Return the persisted result on subsequent status queries |
| While awaiting approval | Restore the pending approval state and apply its expiry and authorization rules |

The hardest case is a write operation that succeeded on Windows, followed by a backend crash before its result was saved. A restarted backend must not blindly repeat that write.

## 03.15.08 Recovery after a Windows device disconnects

Each task has an explicit target device. An offline device must not cause NEXUS to silently execute the task on the designated inference host or another teammate's computer.

When the target bridge disconnects:

- Stop dispatching new operations to that device.

- Preserve all recorded step outcomes.

- Detect whether an operation was in flight.

- Distinguish a known failure from a lost response.

- Resume only when the device reconnects and the operation is safe to continue.

- Revalidate the device's registration and authorization.

- Require recovery or user input if the external outcome cannot be established.

A heartbeat indicates recent communication, not proof that every tool is available or that the computer is in a state suitable for an operation.

## 03.15.09 Approval, expiry and cancellation races

Approval can race with cancellation, task recovery or a change in the requested operation.

The backend must define one authoritative ordering for competing state changes. It must not let an approval request and a cancellation request independently authorize execution.

Required rules:

- Approval is bound to the specific task, step, user, device, tool, normalized arguments, risk decision and expiry.

- If the operation or relevant parameters change, the previous approval no longer applies.

- Approval expiry must be checked when execution is about to proceed, not only when the approval is created.

- A late approval must not restart a terminal or cancelled task.

- If cancellation wins the state transition, pending operations must not be dispatched.

- Concurrent decisions must be serialized or resolved using a defined transactional rule.

- Authorization must be rechecked immediately before dispatch.

The approval expiry duration remains a configuration decision. It should be defined before implementation rather than embedded as an undocumented constant.

## 03.15.10 Partial success and compensation

Some tasks consist of several independent actions. If a task has five steps and the fourth fails, the first three may already have changed the user's computer.

NEXUS must distinguish:

- Complete success: all required steps succeeded and the requested outcome was verified.

- Partial success: some steps succeeded, but the full requested outcome was not achieved.

- Failure without known side effects: execution failed and no relevant external change is known to have occurred.

- Uncertain outcome: evidence is insufficient to establish what happened.

- Cancellation after partial execution: further execution stopped, but completed actions remain recorded.

The task result should identify completed, failed, skipped and uncertain steps.

### Compensation policy

Compensation means performing a separate action intended to reverse or mitigate an earlier action. It is not the same as rolling back a database transaction.

For the MVP:

- Do not automatically compensate arbitrary computer operations.

- A compensating operation must be explicitly defined, authorized and safe for that tool.

- Do not delete or overwrite data as an assumed way to recover.

- If a safe compensation is unavailable, report the partial outcome and offer a supported next step.

- Preserve an audit trail of the original action and any compensation.

## 03.15.11 Timeouts and retry budgets

Every external operation should have a documented timeout policy. A timeout must not automatically be interpreted as proof that the operation failed.

Each registered tool should specify:

- Execution timeout.

- Whether cancellation is supported.

- Whether retry is safe.

- Maximum retry count and any backoff policy.

- Whether the operation supports status lookup or reconciliation.

- What evidence is required to declare success.

The task orchestrator should also have bounded limits for planning, approval waiting, task execution and recovery. Their actual values should be configurable and measured.

Do not use one global timeout for every operation. Searching a directory, extracting a large document and launching an application have different performance characteristics.

## 03.15.12 Observability and diagnostics

A failure must be explainable without exposing private file contents or credentials.

For each task and step, capture relevant operational metadata:

- Task ID, step ID and operation ID.

- User and target device identifiers.

- Worker and attempt identifiers.

- State transitions and timestamps.

- Duration and retry count.

- Machine-readable error code.

- Whether the outcome is known, failed or uncertain.

- Recovery decisions and approval events.

Sensitive request content, document bodies, authentication tokens and secrets should not be included in ordinary logs by default.

Proposed error categories include:

| **Code family** | **Meaning** |
| --- | --- |
| TASK_VALIDATION_* | Request or plan is invalid |
| TASK_AUTHORIZATION_* | User, device or operation is not authorized |
| TASK_CONFLICT_* | Duplicate identifier conflict or incompatible state transition |
| TASK_DEVICE_* | Target device unavailable or rejected the operation |
| TASK_TIMEOUT_* | A bounded operation or wait exceeded its limit |
| TASK_RECOVERY_* | Recovery is required or the outcome remains uncertain |
| TASK_EXECUTION_* | A tool operation failed |

These names are proposed conventions, not finalized API contracts.

## 03.15.13 Testing strategy

Reliability requires tests that deliberately create failures rather than testing only successful requests.

### Required failure-injection tests

Test planning checklist

0 of 12

Submit the same task concurrently with the same client request ID.

Submit the same request ID with different request content.

Attempt to claim one step from multiple workers simultaneously.

Terminate a worker after persisting operation intent but before dispatch.

Disconnect the Windows bridge after it receives an operation.

Allow a file creation to succeed, then simulate loss of its response.

Restart the backend while a task is waiting for approval.

Race a cancellation request against an approval decision.

Expire a worker lease while an external operation is still running.

Verify that a stale worker cannot overwrite a newer worker's result.

Confirm that an uncertain write is reconciled before retry.

Verify that completed steps remain visible after partial failure.

Use a real PostgreSQL test instance for concurrency, locking, uniqueness and transaction behavior. Mocked database tests alone cannot establish that these guarantees hold under actual concurrent access.

Tests involving external operations should use a controlled test directory and harmless test applications, not important user files.

## 03.15.14 Acceptance criteria

## Section 03.15 is ready for implementation when:

- Task and step state transitions have explicit legal-transition rules.

- Duplicate task submission is protected by database-enforced idempotency.

- Workers claim tasks or steps atomically.

- Stale workers cannot overwrite newer state.

- Every external operation has an operation ID and a defined retry policy.

- Uncertain outcomes remain distinguishable from definite failures.

- Cancellation does not claim success before the outcome is established.

- Backend restart recovery is tested at key crash points.

- Device disconnection never triggers silent execution on another computer.

- Approval expiry and cancellation races have defined outcomes.

- Partial success is accurately reported.

- Logs support diagnosis without unnecessarily storing private content.

- Failure-injection and concurrency tests pass.

## 03.15.15 Decisions still open

1. How many tasks and model requests may run concurrently?

2. What should the default per-device operation limit be?

3. Which PostgreSQL worker-claim strategy will be used?

4. How long should worker leases last, and how should they be renewed?

5. Which operations need durable deduplication records on the Windows bridge?

6. What are the default timeouts and retry limits for each initial tool?

7. How long may a task wait for approval before expiring?

8. What is the retention policy for task history, attempts and recovery records?

9. Which operations, if any, have supported compensation behavior?

These values should be decided using the actual workload and hardware, not guessed in advance.
