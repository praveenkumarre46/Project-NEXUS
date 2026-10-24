## 04.11.01 Purpose

Once NEXUS accepts tasks from multiple developers, it must coordinate their execution without duplicating work, corrupting task state or exhausting shared resources.

Consider three users submitting tasks at nearly the same time. A worker might claim a task, the backend might restart, and a second worker might attempt to claim the same task. Meanwhile, the original Windows bridge may still be executing the first operation.

NEXUS must prevent a stale worker from changing authoritative state, avoid unsafe duplicate execution and preserve enough information to recover after failures.

Recommended initial approach: use PostgreSQL for durable task coordination, atomic worker claims, bounded leases and generation-based fencing. Do not introduce Redis or a separate message broker unless measured requirements justify the additional infrastructure.

## 04.11.02 Worker architecture

The worker is the backend component responsible for progressing a persisted task through planning, authorization, dispatch, result handling and recovery.

### FastAPI API

Authenticates requests and persists accepted tasks

### PostgreSQL task store

Authoritative task state, steps, claims and operation intent

#### Worker A

Claim, execute and record

#### Worker B

Claim independent eligible work

### Operation dispatcher

Checks policy and sends operations to the authenticated target bridge

The worker may initially run within the backend application process. Its logical responsibilities should remain separate from HTTP request handlers so it can later move into a separate process if load or reliability measurements require that change.

A worker is not a security authority. It must load authoritative task and device data and apply the required authorization and policy checks before dispatch.

## 04.11.03 Separate task eligibility from resource availability

A task should execute only when two independent conditions hold.

Task eligibility answers whether the task is allowed and ready to progress:

- The task is in an eligible state.

- Required dependencies are complete.

- The target device is registered and authorized.

- Required approvals are valid.

- The tool and protocol are supported.

- The task has not been cancelled or otherwise invalidated.

Resource availability answers whether execution capacity is available:

- A worker slot is available.

- The target device can accept work.

- The model runtime has capacity, if needed.

- Database capacity is available.

- The task remains within configured concurrency and resource limits.

A task can be eligible but waiting for a resource. Conversely, an available worker must not execute a task that is unauthorized, awaiting approval or dependent on an unresolved operation.

This distinction is important because queue position alone must never imply permission to execute.

## 04.11.04 Atomic task claims

Two workers must not independently decide that the same task is available based on separate reads.

The claim must be established atomically in PostgreSQL. The implementation can use row locking, conditional updates or another verified PostgreSQL coordination pattern.

### Required claim behavior

1. Find an eligible task.

2. Atomically claim it, ensuring that another worker cannot obtain the same active claim.

3. Record the worker identity, claim generation and lease expiry.

4. Confirm that the claim succeeded.

5. Only then begin the work associated with that claim.

6. Verify claim ownership before committing subsequent authoritative state transitions.

If a worker loses the claim, it must stop making authoritative state changes for that task.

### Illustrative claim record

The following describes logical fields, not a finalized table schema:

| **Field** | **Purpose** |
| --- | --- |
| task_id | Task being claimed |
| worker_id | Current worker identity |
| claim_generation | Monotonically increasing fencing generation |
| claimed_at | Claim timestamp |
| lease_expires_at | Claim expiration timestamp |
| last_heartbeat_at | Last recorded worker progress |
| claim_status | Active, expired or released |

The team must decide whether these fields belong directly in the task table or in a separate claim table. Avoid duplicating authoritative state across both without a clear consistency model.

### Transaction boundaries

The database transaction should cover the claim and its associated state change, not the entire task execution.

Do not keep a PostgreSQL transaction open while waiting for:

- A model to generate a plan.

- A Windows bridge to respond.

- A file operation to complete.

- A human to approve an operation.

Long-running transactions can hold locks, consume connections and delay unrelated users.

## 04.11.05 Leases and fencing stale workers

A lease is a time-bounded claim. It helps NEXUS detect a worker that has stopped making progress, but it does not prove that the worker or its external operation has stopped.

For example, a worker may pause temporarily, lose its database connection and continue executing a delayed request to the Windows bridge after its lease expires.

A second worker must not assume that the old operation is harmless.

### Fencing rule

Each successful new claim should receive a higher claim generation. Authoritative task-state updates must verify that the worker still owns the current generation.

Conceptually:

- Worker A claims task generation 7.

- Worker A stalls and its lease expires.

- Recovery evaluates the task and assigns generation 8 when a new claim is safe.

- Worker A later resumes with generation 7.

- Its stale state updates are rejected.

A fencing token protects backend state only if every relevant state-changing path checks it. It does not automatically stop an external Windows operation already in progress.

### Lease-expiry behavior

When a lease expires, NEXUS should:

1. Mark the claim as stale or eligible for recovery.

2. Inspect the task and operation records.

3. Determine whether the worker had dispatched an external operation.

4. Reconcile any operation that might have executed.

5. Revalidate authorization, device status and approval.

6. Reclaim work only when doing so is safe.

Never treat lease expiry as proof that an external side effect did not occur.

The lease duration, heartbeat interval and renewal policy should be selected using measured task and network durations, with bounded renewal behavior.

## 04.11.06 Concurrency limits and shared resource protection

NEXUS shares a backend, PostgreSQL database and initially a designated computer for local AI inference. Each resource needs its own concurrency control.

| **Resource** | **Required control** | **Initial approach** |
| --- | --- | --- |
| Task workers | Maximum active claims | Configurable conservative limit |
| Per-user tasks | Prevent one user monopolizing capacity | Per-user active-task limit |
| Per-device execution | Avoid overwhelming a bridge | Bounded active operations |
| AI inference | Limit simultaneous model workloads | Start conservatively; benchmark before increasing |
| PostgreSQL | Avoid connection exhaustion | Bounded connection pool |
| Document processing | Prevent excessive memory and CPU usage | File, duration and concurrency limits |
| Queue | Prevent unbounded backlog | Bounded admission and visible capacity errors |

Exact numerical limits remain open. They should be based on host measurements rather than arbitrary claims about how much the machine can handle.

### Initial resource policy

- A single user's burst of tasks must not indefinitely starve other eligible users.

- Device-specific work must remain bound to its intended device.

- The model runtime should have a configurable concurrency limit.

- Work waiting for a human approval must not occupy an active execution slot indefinitely.

- A task waiting for an offline device should not consume a worker slot while it waits.

- If the durable queue reaches its configured capacity, new submissions must receive a clear response rather than disappearing.

- A task must not be reported as durably accepted if PostgreSQL is unavailable and the task has not been persisted.

A fair scheduler, such as round-robin selection among eligible users, is a reasonable starting proposal. The exact fairness policy should be kept simple until the team has measured real contention.

## 04.11.07 Task dispatch and worker responsibilities

A worker should process one bounded unit of work at a time and persist meaningful progress between stages.

The recommended sequence is:

1. Claim an eligible task or step.

2. Load its authoritative owner, target device and current state.

3. Verify that required dependencies have completed.

4. Obtain a structured plan or the next deterministic operation.

5. Validate the operation against the registry and schema.

6. Recheck authorization and policy.

7. Verify approval if required.

8. Persist operation intent.

9. Dispatch to the intended bridge.

10. Record acknowledgement and subsequent execution evidence.

11. Verify the outcome and persist the result.

12. Release the claim or progress to the next eligible step.

Each stage needs defined error and recovery behavior. A generic exception handler that marks every error as FAILED is not sufficient.

### Worker error classification

| **Condition** | **Expected response** |
| --- | --- |
| Invalid request or plan | Reject the operation; do not dispatch |
| Permission denied | Stop the affected operation and record the decision |
| Approval required | Persist waiting state and release execution capacity |
| Device unavailable before dispatch | Preserve a recoverable task state |
| Timeout after possible dispatch | Reconcile or mark the outcome uncertain |
| Database failure before durable acceptance | Do not claim acceptance |
| Database failure after external execution | Recover using persisted intent and bridge evidence |
| Stale claim | Reject state updates from the stale generation |
| Model unavailable | Preserve task integrity and follow the configured failure policy |

The worker must not hold a database transaction open while performing external operations.

## 04.11.08 Cancellation and worker shutdown

Cancellation is a request to stop further work, not proof that all activity has stopped.

When cancellation is requested, NEXUS should:

- Persist the cancellation request.

- Prevent new steps from being dispatched.

- Signal an active worker where practical.

- Apply the tool's cancellation behavior if supported.

- Reconcile any operation that may already have executed.

- Preserve completed side effects and report partial results.

- Mark the task CANCELLED only when the cancellation conditions are satisfied.

If the operation cannot be interrupted safely, the task may remain in a cancellation-pending or recovery state until its outcome is established. Whether cancellation-pending is represented as a separate persisted state or an explicit cancellation flag remains a design decision.

### Graceful shutdown

When the backend is stopping:

1. Stop accepting new worker claims.

2. Stop dispatching new operations.

3. Allow a bounded period for active work to finish.

4. Persist known outcomes and outstanding recovery information.

5. Leave unresolved external operations recoverable.

6. Close database connections cleanly.

A forced process termination can still occur. Startup recovery must not assume that graceful shutdown completed.

## 04.11.09 Backpressure, admission control and fairness

The system needs two separate limits:

- Admission control: determines whether a new task can be durably accepted.

- Execution scheduling: determines when an accepted task can run.

A task may be accepted and queued while execution capacity is temporarily unavailable, provided queue capacity and persistence are healthy.

If the queue is full, NEXUS should return a stable capacity error. It must not create an in-memory-only task and report it as durable.

### Fair scheduling proposal

For the initial three-user deployment:

1. Exclude tasks that are blocked, cancelled, unauthorized or waiting for approval.

2. Group eligible work by user.

3. Select users fairly, initially using round-robin scheduling.

4. Apply per-user and per-device concurrency limits.

5. Select an eligible task for the chosen user.

6. Revalidate eligibility before dispatch.

This avoids a user who submits many tasks monopolizing the shared model or worker pool.

Priority classes and priority aging can be added later if real workloads demonstrate starvation. User-provided urgency must not bypass security checks, capacity limits or approval requirements.

## 04.11.10 Worker observability

Each worker should emit structured events that allow the team to reconstruct what happened without logging sensitive content.

Useful fields include:

- task_id, step_id and operation_id

- worker_id and claim generation

- device_id

- Current task and step state

- Claim acquisition and expiry timestamps

- Dispatch, acknowledgement and result timestamps

- Retry and recovery classification

- Stable error code

- Execution duration

Useful metrics include:

- Active workers and active claims.

- Queue length and queue wait time.

- Claim conflicts and expired leases.

- Task execution duration by tool.

- Device-unavailable duration.

- Model queue wait and inference duration.

- Database pool utilization and lock waits.

- Uncertain operations and recovery duration.

- Tasks rejected by admission control.

Do not use task IDs, user IDs or filesystem paths as unrestricted metric labels. Keep high-cardinality details in appropriately protected logs or persisted task records.

## 04.11.11 Required concurrency and recovery tests

These tests are release requirements, not optional load-testing extras.

| **Test scenario** | **Expected outcome** |
| --- | --- |
| Two workers claim the same task concurrently | Only one obtains the valid active claim |
| Worker loses its lease | Stale worker cannot update authoritative state |
| Old worker resumes after a newer claim | Fencing checks reject stale updates |
| Lease expires after external dispatch | Operation is reconciled before unsafe retry |
| Three users submit concurrent tasks | Ownership remains isolated and scheduling stays bounded |
| One user submits a burst of tasks | Other eligible users continue to receive execution opportunities |
| Model capacity is exhausted | Work waits within configured limits or receives a controlled capacity response |
| Target device is offline | No silent rerouting or worker slot held indefinitely |
| Database becomes unavailable | No false durable acceptance; recovery follows persisted evidence |
| Backend restarts with queued tasks | Eligible work can resume safely |
| Backend restarts with an uncertain operation | Recovery reconciles rather than blindly replaying |
| Cancellation races with dispatch | No new dispatch after cancellation is observed; in-flight work is reconciled |
| Approval expires before dispatch | Operation is not executed |
| Queue reaches capacity | New work is handled using the documented admission policy |

Use PostgreSQL integration tests for claims, transactions and concurrency. Use controlled failure injection for worker crashes, network interruptions and delayed bridge responses.

## 04.11.12 Implementation work packages

| **Work item** | **Owner** | **Completion condition** |
| --- | --- | --- |
| Atomic task claims | Developer 1 | Concurrent claim test passes |
| Claim generation and lease model | Developer 1 | Stale worker updates are rejected |
| Dispatch coordination | Developer 1 + Developer 2 | Operation intent is persisted before dispatch |
| Bridge status and reconciliation | Developer 2 | Uncertain operations can be inspected after reconnect |
| Planner integration | Developer 3 | Planner output cannot bypass worker or policy checks |
| Concurrency configuration | Developer 1 | Limits are configurable, validated and observable |
| Fair scheduling | Developer 1 | Three-user test demonstrates bounded contention |
| Failure-injection suite | All three | Crash, lease-expiry and lost-response tests pass |

The team should implement the minimum safe claim and recovery model before adding sophisticated scheduling features.

## 04.11.13 Recommended initial decisions

| **Decision** | **Recommendation** | **Status** |
| --- | --- | --- |
| Durable task coordination | PostgreSQL | Provisional |
| Worker deployment | Begin inside the modular backend process | Provisional |
| Claim strategy | Atomic PostgreSQL claim with row locking or conditional updates | Required behavior; exact implementation to validate |
| Stale-worker protection | Claim generation/fencing token | Recommended |
| Lease expiry | Trigger reconciliation, not automatic replay | Required safety invariant |
| Queue infrastructure | No separate broker initially | Provisional |
| Resource limits | Configurable conservative defaults | Required |
| Fairness | Round-robin among eligible users | Proposed baseline |
| AI concurrency | Start conservatively and benchmark | Provisional |
| Queue-full behavior | Explicit capacity error; never silently lose accepted tasks | Required behavior |

## 04.11.14 Definition of done

- Workers atomically claim eligible work.

- Task eligibility is separate from resource availability.

- Leases and stale-worker protection are implemented.

- No long database transaction spans external operations.

- Queue and concurrency limits are enforced.

- Per-user and per-device isolation is maintained.

- Cancellation and shutdown preserve recoverable state.

- Lease expiry never implies that an external side effect did not occur.

- Failure-injection and PostgreSQL concurrency tests pass.

- Worker behavior is observable without exposing private data.

- The three-user integration workload has measured results.

Section exit criterion: NEXUS can schedule concurrent tasks using durable coordination while preventing duplicate claims, stale state updates and unsafe retries.
