## 03.28.1 Purpose

## Section 03.27 established that NEXUS needs bounded concurrency, measurable performance and explicit resource limits. This section defines who gets to use those resources, in what order, and what happens when demand exceeds capacity.

NEXUS initially has three developers sharing a designated computer for backend services and local AI inference. One user might submit a simple file search while another submits a multi-step task that requires several model calls. Without scheduling rules, a single long-running task could consume available inference capacity and delay everyone else.

Resource governance must prevent:

- One user monopolizing model inference or task workers.

- Short, interactive tasks being trapped behind long-running work indefinitely.

- Disconnected devices consuming worker slots.

- Repeated retries creating extra load during an outage.

- Unlimited queued tasks exhausting database storage or memory.

- Priority rules accidentally bypassing authorization, approval or safety checks.

Core rule: scheduling decides when an authorized operation may run; it never decides whether that operation is authorized.

## 03.28.2 Scope and constraints

| **Area** | **Initial design** |
| --- | --- |
| Users | Three team members |
| Shared resources | Backend workers, model inference, PostgreSQL connections and host memory |
| Device resources | Each user's Windows bridge and local tools |
| Coordination | PostgreSQL-backed durable task state |
| Scheduler | Simple application-level scheduling in the modular backend |
| Fairness | Per-user limits and fair access to shared resources |
| Priority | Small, explicit set of scheduling classes |
| Additional infrastructure | No Redis or separate message broker initially |
| Safety | Policy and approval checks remain mandatory regardless of priority |

The first version should be deliberately simple. NEXUS does not need a sophisticated distributed scheduler for three users on a local network. It does need deterministic rules that can be tested under concurrency.

## 03.28.3 Separate task scheduling from resource scheduling

NEXUS should distinguish two decisions.

### Level A — Task eligibility

Can this task proceed at all?

- Is the user authenticated and authorized?

- Is the target device registered and permitted?

- Are required approvals valid?

- Are dependencies and task state correct?

- Is the operation permitted by policy?

### Level B — Resource availability

If eligible, can it run now?

- Is a worker available?

- Is a model inference slot available?

- Is the target device available?

- Are database and host resource limits respected?

- Is the task within the user's concurrency allowance?

A task that is waiting for approval is not eligible for execution. A task targeting an offline device must wait or enter a defined recovery state rather than occupy a worker indefinitely. A task denied by policy must never become runnable merely because resources are idle.

## 03.28.4 Proposed scheduling classes

Use a small number of classes based on operational needs, not on which user submits the task.

| **Class** | **Examples** | **Proposed behavior** |
| --- | --- | --- |
| Interactive | Simple search, short read-only request | Prefer lower waiting time |
| Standard | Ordinary multi-step computer task | Normal fair scheduling |
| Background | Large searches, non-urgent bulk context processing | Lower preference when interactive work is waiting |
| Blocked | Waiting for approval, unavailable device or dependency | Not eligible until the blocking condition changes |

These classes are a proposal. A task's class must be derived from controlled application metadata and bounded task characteristics—not from a model's unsupported claim that its task is urgent.

Users should not be able to label every task as interactive to bypass fairness. Any future manual priority override must be explicitly authorized and audited.

### Important distinction: approval waiting

Human approval waiting is not a lower-priority execution task. It is a blocked state. It consumes no model slot or worker while waiting, except for bounded bookkeeping and notification work.

When approval arrives, NEXUS must revalidate the approval, task state and permissions before making the step eligible again.

## 03.28.05 Fairness between users

NEXUS should begin with per-user concurrency limits plus round-robin selection among eligible users.

For example, if Developer A has five tasks waiting and Developers B and C each have one, the scheduler should not automatically run all five of A's tasks first.

A simple selection cycle could look like this:

Illustrative scheduler cycle — not a fixed runtime guarantee

User A

## 1

eligible task

User B

## 1

eligible task

User C

## 1

eligible task

Select one eligible task per user in turn. If a user has no eligible task, skip that user for this cycle. Continue while capacity remains.

This is a starting policy, not a requirement to allocate identical processing time in every situation. A task can consume much more inference time than another task, and users can target different devices.

To make fairness practical:

1. Apply per-user limits to active tasks and outstanding work.

2. Rotate fairly among users with eligible tasks.

3. Avoid allowing a user to occupy every available inference slot with queued work.

4. Recheck eligibility when a task is selected.

5. Record scheduling decisions sufficiently to diagnose unexpected delays.

### Proposed initial per-user policy

- A user may have multiple accepted tasks, subject to a global queue limit.

- A configurable per-user limit controls how many tasks can be active at once.

- Only a bounded number of that user's tasks may occupy shared AI inference capacity concurrently.

- A user with no eligible work does not reserve idle capacity.

- An offline target device does not keep an execution slot indefinitely.

Exact numeric limits remain open until the Section 03.27 benchmark identifies a safe capacity.

## 03.28.06 Avoiding starvation

Starvation occurs when an eligible task remains waiting indefinitely because other tasks continually take precedence.

NEXUS should use these safeguards:

- Round-robin fairness: prevent one user from continuously winning task selection.

- Bounded priority: interactive work may receive preference, but background work must still make progress.

- Priority aging: a task that waits for a long time may gradually gain scheduling preference, within a defined maximum.

- Blocked-task exclusion: tasks awaiting approvals or offline devices do not compete for execution slots.

- Bounded work units: large operations should have limits on duration, result size or work performed per step.

- Visible waiting status: expose whether a task is queued, blocked or actively executing.

Priority aging should not allow a prohibited or unauthorized operation to run. It changes scheduling preference only after the task passes all eligibility checks.

For the initial three-user deployment, simple round-robin selection may be sufficient. Implement priority aging only if tests show that the chosen priority classes can starve lower-priority work.

## 03.28.07 Shared resource budgets

NEXUS has several different bottlenecks. A single global concurrency limit cannot manage them all correctly.

| **Resource** | **Governance rule** |
| --- | --- |
| Task workers | Limit active work; never hold a worker while waiting indefinitely for a human |
| AI inference | Use a bounded number of inference slots and a bounded waiting queue |
| PostgreSQL | Use a bounded connection pool; short transactions and atomic claims |
| Per-device execution | Limit concurrent operations based on the target tool and device |
| Host memory | Bound context, model concurrency and tool output; monitor memory pressure |
| Disk storage | Bound task results, logs, history growth and queued work |
| CPU-heavy tools | Apply tool-specific limits so bulk work cannot exhaust host resources |
| Network communication | Use deadlines, payload limits and bounded retries |

### Reserve capacity carefully

It may be useful to reserve a small amount of capacity for API health, task status updates and recovery work, so a busy model does not make NEXUS appear completely unresponsive.

However, do not create arbitrary reserved pools before measuring actual demand. First keep API operations lightweight and model execution separately bounded. Add explicit reservations only if benchmarks demonstrate that normal traffic can starve operational work.

## 03.28.08 Queue admission and overload behavior

The scheduler needs two separate policies:

- Admission control: whether NEXUS accepts a new task into durable storage.

- Dispatch control: whether an accepted task is allowed to start using resources now.

A task may be accepted and queued while all execution slots are busy. Admission must nevertheless stop when the configured queue capacity is reached or the service cannot safely persist new work.

| **Situation** | **Expected behavior** |
| --- | --- |
| Model slot busy, queue has capacity | Accept if normal admission checks pass; report queued status |
| Global queue full | Reject new work with a stable, actionable capacity error |
| Per-user quota reached | Apply the configured quota response; do not bypass it silently |
| Target device offline | Report device unavailable or a clearly defined waiting state |
| Database unavailable | Do not claim a task was durably accepted |
| Model overloaded | Bound waiting; expose queue status and enforce deadlines |
| Task cancelled before dispatch | Prevent new dispatch and persist the cancellation outcome |
| Queue contains expired or invalid work | Re-evaluate state and policy; do not execute stale work blindly |

The API response should distinguish a capacity rejection from a successfully accepted task. A capacity rejection must not be reported as a queued task unless NEXUS actually persisted it.

## 03.28.09 Durable scheduling with PostgreSQL

PostgreSQL remains the source of truth for accepted task state. The scheduler must coordinate competing workers without creating duplicate execution.

The initial design should follow this sequence:

1. Read candidate tasks that are eligible for execution.

2. Select a candidate according to the fairness policy.

3. Atomically claim it using a transaction and appropriate locking or conditional update.

4. Persist the claim owner, lease information and fencing generation.

5. Commit the transaction before performing model inference or external work.

6. Revalidate the task, policy and relevant permissions before dispatch.

7. Persist progress and release or renew the claim according to the defined lifecycle.

A worker must not keep a database transaction open throughout a model call or while waiting for a Windows bridge. Those waits can be long and would unnecessarily retain locks and database connections.

### Claim and lease rules

- Only one valid worker may own a particular claim at a time.

- A lease expiring does not prove that the previous worker stopped.

- A stale worker must not overwrite newer task state.

- Fencing tokens or equivalent generation checks must prevent stale state updates.

- An expired claim involving a possible external side effect requires reconciliation before redispatch.

- Duplicate scheduler decisions must not create duplicate tasks or independent operation identities.

Critical point: an expired worker lease is a coordination event, not permission to repeat a file write or another potentially consequential operation.

### Do we need a separate queue?

Not initially. PostgreSQL-backed scheduling is a reasonable starting point for a three-user, local deployment, provided its contention and recovery behavior pass tests.

A dedicated broker should be considered only when measured workload, scheduling requirements or reliability needs demonstrate that PostgreSQL coordination is no longer adequate.

## 03.28.10 Scheduling and cancellation

Cancellation must be integrated with resource governance.

- A task that has not started should be removed from eligibility when cancellation is accepted.

- A task waiting for approval must not become runnable after cancellation.

- A running task should stop scheduling future steps after cancellation is requested.

- An in-flight bridge operation may not be cancellable.

- A cancelled task must release its scheduler and model reservations once those resources are no longer in use.

- If a dispatched operation's result is unknown, preserve the uncertainty and reconcile it rather than marking it cancelled prematurely.

The scheduler must also account for work that has completed its model call but is still waiting for a device. It should not reserve a scarce inference slot for that task unless a specific implementation need has been measured and justified.

## 03.28.11 Failure handling and backpressure

Resource pressure often accompanies failures. Retrying everything immediately can turn a temporary problem into a larger outage.

NEXUS should:

- Use bounded retries and backoff for eligible transient failures.

- Apply retry budgets by dependency or operation type.

- Avoid repeatedly invoking a failed model runtime while it is unavailable.

- Stop dispatching to a disconnected bridge until its status and recovery conditions permit it.

- Keep queued work durable across backend restarts.

- Bound diagnostic and error payload sizes.

- Expose overload, dependency failure and uncertain operation outcomes as distinct conditions.

- Resume work only after eligibility, authorization and recovery checks succeed.

Any circuit-breaker-style mechanism should be introduced only with clearly defined behavior and tests. It must not convert a dependency failure into an invented success or permanently strand tasks.

## 03.28.12 Acceptance tests

| **Test** | **Acceptance condition** |
| --- | --- |
| One user submits many tasks | Other users still receive fair access to eligible capacity |
| One user repeatedly submits interactive work | Lower-priority work continues to progress under sustained load |
| All model slots are occupied | Additional tasks wait within bounds or receive a clear capacity response |
| Per-user limit is reached | Further work follows the configured quota policy |
| A target device goes offline | Its work does not consume execution slots indefinitely |
| A worker crashes after claiming a task | Claim recovery does not cause duplicate external effects |
| A lease expires while a write may be running | The system reconciles before any unsafe retry |
| A task is cancelled while queued | It is not dispatched afterward |
| A task is cancelled while waiting for approval | Late approval cannot restart it |
| The database becomes unavailable | NEXUS does not claim new work was durably accepted |
| A model call is slow | API status and unrelated eligible work remain responsive within tested limits |
| Queue capacity is reached | The API distinguishes rejected requests from accepted, queued tasks |
| Priority aging is enabled | Long-waiting eligible tasks gain preference without bypassing policy |
| The backend restarts | Queued work is recovered and eligibility is reevaluated |

All tests must include assertions about task state and side effects, not merely response codes or execution time.

## 03.28.13 Implementation priorities

P0

Required for the initial release

- Bounded global and per-user task concurrency.

- Bounded inference concurrency and queue capacity.

- Fair selection among eligible users.

- Durable task claims and stale-worker protection.

- Explicit device availability and cancellation handling.

- Clear overload responses and scheduler metrics.

P1

Add when validated by tests

- Priority aging if starvation is observed.

- More advanced workload classes.

- Dynamic capacity adjustment based on measured resource pressure.

- More detailed scheduling analytics.

P2

Future scale, not an MVP dependency

- Distributed scheduling across multiple inference hosts.

- Dedicated broker-based scheduling.

- Advanced weighted-fair scheduling and automated capacity optimization.

## 03.28.14 Open decisions

| **Decision** | **Status** |
| --- | --- |
| Global active-task limit | To be benchmarked |
| Global queue capacity | To be benchmarked |
| Per-user active-task quota | Proposed; numeric value open |
| Per-user inference quota | Proposed; numeric value open |
| Priority classes | Proposed; requires team agreement |
| Round-robin fairness | Recommended initial policy |
| Priority aging | Conditional on evidence of starvation |
| Device concurrency | Set per tool and measured device behavior |
| Admission behavior at capacity | Reject with a stable error; exact limits open |
| Scheduler implementation | PostgreSQL-backed coordination initially |
| Reserved operational capacity | Only if measurement demonstrates need |

## 03.28.15 Definition of done

## Section 03.28 is ready for implementation when:

- Every accepted task has a durable scheduling state.

- Admission control and dispatch control are clearly separated.

- User fairness and concurrency limits are defined and tested.

- The scheduler cannot bypass authorization, approval or device restrictions.

- Stale workers cannot corrupt task state or trigger unsafe duplicate operations.

- Queue growth and resource consumption are bounded.

- Cancellation, overload, disconnection and restart scenarios have deterministic expected behavior.

- The team can demonstrate fairness with three simultaneous users on the actual deployment setup.

Recommended engineering decision: start with PostgreSQL-backed scheduling, round-robin selection among eligible users, conservative resource limits and bounded queues. Benchmark this design before introducing more sophisticated scheduling infrastructure.
