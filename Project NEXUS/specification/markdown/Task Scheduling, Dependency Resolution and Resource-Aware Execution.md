## 04.12.01 Purpose

## Section 04.11 defined how workers claim tasks safely. This section defines which eligible work should run next, which steps must wait, and when concurrent execution is safe.

NEXUS must coordinate three developers using shared backend resources while executing operations on different Windows computers. A task may contain several dependent steps, require AI inference, wait for an approval or be blocked because its target computer is offline.

The scheduler must therefore balance:

- Correct dependency ordering.

- User and device authorization.

- Fairness between users.

- Availability of workers, model capacity and target devices.

- Cancellation, deadlines and recovery.

- Bounded resource consumption.

Recommended initial approach: use a simple PostgreSQL-backed scheduler with dependency-aware eligibility checks, round-robin selection among eligible users and conservative concurrency limits. Do not add a separate scheduling service or message broker until measurements demonstrate a need.

## 04.12.02 Scheduling concepts

NEXUS should keep four concepts separate.

Eligibility

Is the task authorized, approved where necessary, and ready according to its dependencies and state?

Dependency resolution

Which steps can run now, and which must wait for earlier results?

Resource admission

Is the required worker, device, model slot or other resource available?

Fair scheduling

Among eligible work, whose task should receive the next available capacity?

These checks must not be collapsed into one queue-order calculation. For example, a task at the front of a queue may still be waiting for approval or targeting an offline device. It should not block unrelated eligible work.

## 04.12.03 Dependency graph and execution readiness

A multi-step task should be represented as a directed acyclic graph (DAG) when its dependencies are known. A DAG expresses ordering requirements without forcing every step to run sequentially.

Consider this illustrative request:

Find two approved project documents, read them and produce a comparison file.

A valid execution plan might look like this:

Step A — Search documents

Identify permitted source files

Step B — Read file 1

Depends on A

Step C — Read file 2

Depends on A

Step D — Compare and prepare output

Depends on B and C completing successfully

Steps B and C may run concurrently if the target device, resource limits, permissions and tool contracts allow it. Step D cannot start until the required outputs from both reads are available.

The diagram is an example of dependency behavior, not a commitment to a particular document-processing implementation.

### Dependency rules

- A step is eligible only when all required dependencies have succeeded.

- A dependency failure blocks dependent steps unless a documented alternative exists.

- A rejected or expired approval must not be treated as successful completion.

- An uncertain step is not a successful prerequisite.

- Cycles must be rejected during plan validation.

- Optional steps must be explicitly identified and must not silently become required.

- A completed step must not be repeated just because an unrelated branch failed.

- A revised plan must preserve already verified results where they remain valid.

The scheduler determines readiness from persisted state, not from a model's claim that a prerequisite has finished.

## 04.12.04 Dependency resolution algorithm

For each task, the scheduler should maintain enough structured information to determine which steps are ready without asking the model to reconstruct execution state repeatedly.

### Proposed readiness algorithm

1. Load a candidate task and its persisted steps.

2. Exclude terminal tasks, cancelled tasks and tasks that are not eligible to progress.

3. Check task ownership, target-device status and current authorization.

4. For each pending step, inspect its dependency records.

5. Mark a step ready only if every required dependency has a verified successful outcome.

6. Check whether the step requires approval, planning, model inference or a Windows bridge.

7. Check the relevant resource limits.

8. Select a fair candidate and atomically claim it.

9. Revalidate the relevant conditions before dispatch.

10. Persist the transition and continue scheduling when capacity becomes available.

The implementation may calculate readiness dynamically from persisted step states or maintain a derived readiness field for efficient queries. If readiness is cached or persisted, the team must ensure it cannot become the authority when dependencies change.

### Readiness examples

| **Step condition** | **Scheduling behavior** |
| --- | --- |
| All dependencies succeeded | May become eligible |
| A required dependency is running | Wait |
| A required dependency failed | Block or follow an explicitly defined recovery path |
| A required dependency is uncertain | Wait for reconciliation |
| Approval is pending | Wait without occupying an execution slot |
| Target device is offline | Defer device-bound execution |
| Resource capacity is full | Remain eligible but wait for capacity |
| Task is cancelled | Do not dispatch new work |

The difference between blocked and waiting for capacity matters operationally. A blocked step cannot proceed until a prerequisite or external condition changes. A capacity-limited step may run as soon as a resource becomes available.

## 04.12.05 Fair selection among users

The scheduler should prevent one developer from monopolizing the shared worker pool or local inference runtime.

### Recommended baseline: round-robin selection

For the initial three-user environment:

1. Determine which users have eligible work.

2. Exclude work that is blocked, unauthorized, awaiting approval or targeting an unavailable device.

3. Select the next eligible user in the rotation.

4. Select one eligible step for that user.

5. Apply resource and per-device limits.

6. Claim the step atomically.

7. Advance the rotation after successful scheduling.

If a selected user has no step eligible for a required resource, the scheduler should skip that user for that resource and continue considering others. It must not repeatedly select an impossible operation and starve unrelated work.

### Per-user concurrency

A user may have several accepted tasks, but that should not automatically grant them several simultaneous model slots.

The scheduler should separately track or derive:

- Active tasks per user.

- Active operations per user.

- Active operations per device.

- Active inference requests.

- Tasks waiting for approvals.

- Tasks waiting for an offline device.

The initial limits should be conservative and configurable. Their numerical values should be finalized after the team benchmarks the actual hardware and three-user workload.

### Priority handling

The first release should avoid an elaborate priority system. A simple fair rotation is easier to test and explain.

If priorities are introduced later:

- The application, not the model, controls allowed priority classes.

- A user cannot override authorization or resource limits by declaring urgency.

- Priority must not permit an unsafe operation to bypass approval.

- Aging may be used to reduce starvation.

- Blocked work must not accumulate priority indefinitely in a way that monopolizes capacity once unblocked.

## 04.12.06 Resource-aware scheduling

A step can be logically ready but still unable to execute because a required resource is busy. NEXUS should represent this as a scheduling condition rather than a task failure.

### Resource requirements per step

Each registered tool or execution stage should declare its resource requirements. The scheduler should not infer resource consumption solely from the natural-language request.

| **Resource** | **Example constraint** | **Scheduling response** |
| --- | --- | --- |
| Worker slot | No free worker | Wait for a slot |
| AI inference | Model at configured concurrency limit | Wait for inference capacity |
| Windows bridge | Device already has its permitted active operations | Wait for that device |
| Document parser | Maximum concurrent extractions reached | Defer extraction |
| PostgreSQL | Connection pool at capacity | Apply bounded backpressure |
| Filesystem scope | Conflicting write or resource reservation | Serialize if required by the tool contract |
| Host memory | Resource safety threshold reached | Pause admission or defer suitable work |

A resource being available does not grant authorization. The policy engine and current task state remain authoritative.

### Initial scheduling policy

- Begin with conservative worker and model concurrency.

- Use per-device limits to prevent one bridge from being overwhelmed.

- Avoid holding a worker while waiting for a person or an unavailable device.

- Limit document-processing size and duration before allocating expensive resources.

- Apply bounded queues and explicit capacity responses.

- Record queue wait and resource wait separately from execution duration.

### Resource reservation

Not every step needs a reservation. A read-only file search may need only a worker and a device slot. A model-based planning step may need a model slot but no Windows bridge operation.

If multiple resources are required simultaneously, NEXUS must avoid deadlocks caused by workers holding one resource while waiting indefinitely for another. The initial design should prefer checking availability and acquiring resources in a defined order, with bounded acquisition and release behavior.

Do not build a general-purpose resource reservation framework until the initial tools demonstrate that simpler per-resource limits are insufficient.

## 04.12.07 Parallel execution and serialization

Parallel execution can improve responsiveness, but only when independent steps can safely run at the same time.

### Parallelism allowed when

- Dependencies have completed.

- The operations are independent according to their tool contracts.

- The target device supports the required concurrency.

- Permissions and approvals are valid.

- Resource limits permit the work.

- Concurrent execution does not introduce conflicting external side effects.

### Serialization required when

- One step consumes another step's output.

- Two operations may modify the same destination.

- The target application or tool is not safe for concurrent use.

- The operation contract requires exclusive access.

- The outcome of an earlier step determines whether the later step is permitted.

For example, two read-only searches may be independent. Two attempts to create the same destination file are not necessarily independent: both might observe an absent file and compete to create it. The file creation primitive must enforce create-only behavior, and the result must be reconciled if execution becomes uncertain.

### Initial policy

Start conservatively:

- Allow parallelism across independent tasks where worker, model and device limits permit.

- Allow parallel read-only steps only after the bridge and tool contracts explicitly support the chosen concurrency.

- Serialize conflicting operations when a conflict can be identified.

- Do not assume that all Windows GUI operations can run concurrently.

- Do not parallelize dependent planning or execution steps merely to reduce elapsed time.

The first implementation does not need a sophisticated global DAG optimizer. It needs correct dependency checks and safe resource limits.

## 04.12.08 Device availability and scheduling

A device-bound task must remain bound to its selected target.

When the target becomes unavailable:

1. Stop new dispatch to that device.

2. Preserve the task and its dependencies.

3. Release any worker or model slot no longer needed.

4. Mark the task or step as waiting, interrupted or requiring recovery according to its current execution state.

5. Reconcile operations that might already have executed.

6. Re-evaluate capability, policy and approval after reconnection.

The scheduler must distinguish a task waiting for a device from a task that is actually executing on it.

A device becoming available does not automatically mean all queued operations should be dispatched at once. The scheduler should apply per-device limits and revalidate each operation individually.

### Configuration changes

If a device's configured directories, enabled tools or capability versions change while tasks are queued, those tasks must be checked again before dispatch. A plan that was valid under an earlier configuration is not automatically valid under the new one.

If the target device is revoked, the scheduler must stop new operations to that device. It must not reroute those operations to another computer without a separately authorized workflow.

## 04.12.09 Scheduling interaction with approval, cancellation and recovery

Scheduling must respect the task state machine and operation-recovery protocol.

### Approval waiting

When a step requires approval:

- Persist the approval request and the exact operation being approved.

- Mark the step as waiting for approval.

- Release worker, model and device capacity that is no longer required.

- Recheck the task, approval, target device and policy when approval is received.

- Return the step to eligibility only if all required conditions remain satisfied.

The scheduler must not reserve an execution slot for the entire time a human takes to respond.

### Cancellation

When cancellation is requested:

- Exclude not-yet-dispatched steps from new scheduling.

- Stop scheduling dependent steps.

- Signal active workers where supported.

- Preserve the results of completed steps.

- Reconcile operations whose external outcome is uncertain.

A task cannot be considered fully cancelled merely because it has been removed from the scheduling queue.

### Recovery after a restart

On startup, the scheduler should:

1. Load nonterminal tasks and outstanding claims.

2. Identify stale claims and operations requiring reconciliation.

3. Recover queued tasks whose state is still valid.

4. Re-evaluate dependencies and resource eligibility.

5. Revalidate device status, permissions and approvals before dispatch.

6. Resume only operations that are safe to continue.

The scheduler must not treat every nonterminal task as ready. In particular, DISPATCHED, RUNNING and UNCERTAIN steps require appropriate recovery checks before any retry.

## 04.12.10 PostgreSQL implementation considerations

The initial scheduler can use PostgreSQL tables and queries rather than a separate broker.

Logical scheduling information may include:

- Task and step states.

- Step dependencies.

- Claim and lease records.

- Target device.

- Owner user.

- Resource class.

- Eligibility timestamps.

- Retry and recovery status.

- Scheduling or fairness metadata, if required.

These are logical fields, not a finalized schema. The existing task, step and claim models should be reused wherever possible rather than creating a second source of truth.

### Query and transaction rules

- Keep scheduling transactions short.

- Claim work atomically.

- Do not hold database locks while waiting for AI, approvals or bridges.

- Use indexes aligned with actual eligibility and claim queries.

- Avoid repeatedly scanning the full task history to find ready steps.

- Revalidate eligibility before external dispatch.

- Reject stale worker updates using claim ownership and generation checks.

- Persist transitions and associated scheduling events consistently.

The team should use actual PostgreSQL integration tests for claim races and dependency updates. In-memory mocks alone cannot establish that concurrent transactions behave correctly.

### When to add infrastructure

Consider a separate broker or scheduler service only if measurements show that PostgreSQL-backed scheduling cannot meet throughput, latency, isolation or operational requirements.

Evidence might include persistent queue delays, database contention caused by scheduling queries, or a requirement for independently scalable workers. Introducing a broker before measuring these problems would add deployment and recovery complexity without demonstrated benefit.

## 04.12.11 Scheduling and dependency test plan

| **Test** | **Expected result** |
| --- | --- |
| Step has incomplete dependencies | Step does not execute |
| Required dependency succeeds | Dependent step becomes eligible |
| Required dependency fails | Dependent step is blocked or follows an explicit recovery path |
| Dependency is uncertain | Dependent step waits for reconciliation |
| Dependency graph contains a cycle | Plan is rejected |
| Two independent read steps are ready | They may execute concurrently within configured limits |
| Two conflicting writes are ready | Conflict is serialized or safely rejected |
| One user submits many tasks | Other eligible users receive fair scheduling opportunities |
| Selected user has no eligible work | Scheduler skips that user for the current resource |
| AI capacity is exhausted | Work waits or receives controlled backpressure |
| Target device is offline | Work remains bound to the device without holding an execution slot |
| Device configuration changes | Operation is revalidated before dispatch |
| Approval expires while queued | Operation is not dispatched |
| Task is cancelled while queued | No new step is dispatched |
| Worker crashes after dispatch | Recovery reconciles before an unsafe retry |
| Backend restarts with mixed task states | Each task resumes according to its persisted state and recovery requirements |
| Queue reaches capacity | The documented admission policy is enforced |
| Three users submit tasks concurrently | User and device ownership remain isolated |

Performance tests should measure queue wait time, scheduling latency, fairness, active worker count, resource utilization and the number of blocked or uncertain steps.

## 04.12.12 Work packages and ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Dependency representation and validation | Developer 1 + Developer 3 | Validated DAG and readiness rules |
| Scheduler eligibility and atomic claims | Developer 1 | PostgreSQL-backed candidate selection and claim |
| Resource and device limits | Developer 1 + Developer 2 | Configurable concurrency enforcement |
| Tool concurrency declarations | Developer 2 | Documented tool-level concurrency and conflict rules |
| Planner dependency proposals | Developer 3 | Structured dependencies; no authority to mark them successful |
| Fairness and backpressure | Developer 1 | Bounded scheduling and capacity behavior |
| Failure and concurrency tests | All three | Automated integration and recovery evidence |

Changes to task states, dependencies or claims must be reviewed against Sections 03.29, 04.10 and 04.11. The scheduler must not introduce conflicting lifecycle rules.

## 04.12.13 Recommended initial decisions

| **Decision** | **Recommendation** | **Status** |
| --- | --- | --- |
| Scheduling store | PostgreSQL | Provisional |
| Dependency model | DAG for known step dependencies | Recommended |
| User fairness | Round-robin among eligible users | Proposed baseline |
| Resource limits | Conservative, configurable limits | Required |
| Parallelism | Only for explicitly independent, supported operations | Required safety rule |
| Approval waiting | Release execution capacity while waiting | Recommended |
| Offline devices | Keep tasks bound to their target | Required |
| Scheduling infrastructure | No separate broker initially | Provisional |
| Advanced prioritization | Defer until starvation is demonstrated | Recommended |

## 04.12.14 Definition of done

- Dependencies are persisted and validated.

- Cyclic or invalid dependency graphs are rejected.

- Readiness is derived from authoritative state.

- Workers claim only eligible steps.

- Per-user, per-device and shared-resource limits are enforced.

- Independent work can run concurrently where explicitly supported.

- Conflicting operations are safely serialized or rejected.

- Approval waiting and offline devices do not consume worker capacity indefinitely.

- Cancellation and recovery respect dependency and execution state.

- Fairness and concurrency tests pass with three users.

- Queue latency and resource usage are measurable.

- Scheduling behavior is documented and reproducible.

Section exit criterion: NEXUS can choose the next eligible operation while respecting dependencies, permissions, device availability, shared resource limits and fairness between users.
