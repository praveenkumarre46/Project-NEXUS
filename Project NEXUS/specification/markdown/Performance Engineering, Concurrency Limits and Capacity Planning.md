## 03.27.1 Purpose

This section defines how NEXUS will measure, manage and improve performance without sacrificing authorization, task reliability or data safety.

NEXUS has several distinct performance paths:

- Backend: FastAPI request handling, PostgreSQL queries and task coordination.

- AI: Local model loading, inference, planning and context retrieval.

- Windows bridge: Network communication, filesystem operations and application launching.

- End-to-end execution: The time between submitting a request and receiving a verified result.

These paths must be measured separately. Otherwise, a slow task might be incorrectly blamed on FastAPI when the actual bottleneck is model inference, database contention or an unavailable Windows device.

### Confirmed constraints

| **Constraint** | **Current position** |
| --- | --- |
| Initial users | 3 developers |
| Memory | 16 GB RAM reported on the designated computer |
| GPU | AMD dedicated GPU; exact model and VRAM unknown |
| Backend | Python, FastAPI and PostgreSQL |
| AI | Local-first, with hybrid capability |
| Execution | Native Windows bridge on each user's computer |
| Deployment | One designated team computer is the provisional shared host |
| Budget | Zero-budget design; no required paid APIs or infrastructure |

These constraints do not yet establish how many tasks can safely run simultaneously or how quickly the local model will respond. We must benchmark the actual machine before fixing those limits.

## 03.27.2 Performance objectives

NEXUS must satisfy five objectives.

1. Responsive API: Users should receive a task ID promptly without waiting for the entire task to finish.

2. Controlled concurrency: Multiple users must be able to submit tasks without overwhelming the model, database or target device.

3. Predictable resource usage: Model inference, context size, database connections and tool outputs must be bounded.

4. Safe degradation: When the model, bridge or database is overloaded or unavailable, NEXUS must report the condition honestly rather than silently losing work.

5. Evidence-based scaling: Architectural changes must be justified by measurements, not assumptions.

An important distinction: task acceptance latency is not task completion latency. The API may accept a task quickly even if model inference takes several seconds or minutes.

## 03.27.3 Measure latency by execution phase

Every task should expose enough timing information to identify its slowest phase.

1. API acceptance

Request validation, authentication, idempotency check and durable task creation.

2. Queue and scheduling

Time waiting for a worker, model slot, device slot or other required resource.

3. AI planning and context

Context retrieval, prompt preparation, inference, structured-output validation and any bounded replanning.

4. Policy and approval

Permission checks, risk classification, approval lookup and pre-dispatch revalidation. Human approval wait is measured separately.

5. Bridge and tool execution

Dispatch delay, network round trip, local validation, filesystem/application operation and result reporting.

6. Persistence and verification

Recording outcomes, updating task state and verifying the required result.

Store timestamps and durations at meaningful boundaries, using a monotonic clock for elapsed durations inside each process. Use UTC timestamps for cross-process event correlation, accounting for possible clock differences between computers.

Do not add all overlapping durations together and assume they equal wall-clock time. For example, parallel context retrieval and other work may overlap.

## 03.27.4 Metrics to collect

| **Area** | **Required measurements** |
| --- | --- |
| API | Request count, error rate, latency percentiles, task acceptance latency |
| Scheduling | Active tasks, queued tasks, queue wait, rejected or deferred work |
| PostgreSQL | Query latency, connection-pool wait, active connections, slow queries, lock waits, deadlocks |
| AI runtime | Model load time, inference latency, tokens generated where available, failures, queue wait |
| Host resources | RAM, CPU utilization, GPU utilization and VRAM where supported, disk space and I/O |
| Windows bridge | Last heartbeat, dispatch delay, tool duration, timeout count and reconnects |
| Reliability | Retries, uncertain outcomes, stale claims, interrupted tasks and recovery duration |
| Memory retrieval | Retrieval latency, result count, context preparation time and retrieval failures |

Use p50, p95 and p99 where there are enough observations to make them meaningful. The p95 is the latency below which 95% of measured requests finish; it helps reveal slow experiences hidden by averages.

Do not use individual task IDs, filenames or user IDs as metric labels. Those belong in appropriately protected logs or traces, not high-cardinality metric dimensions.

## 03.27.5 Proposed performance targets

These are initial engineering targets to validate, not confirmed requirements or guaranteed performance.

| **Measurement** | **Initial target or approach** |
| --- | --- |
| Read-only API request | p95 under 500 ms |
| Task acceptance | p95 under 1 second, excluding unusually slow external dependencies |
| Concurrent users | 3 users operating simultaneously without cross-user interference or lost tasks |
| Task completion | Establish baselines by task type; agree targets after measuring the actual host |
| Model inference | Benchmark the selected model and runtime before committing to a target |
| Recovery | Measure recovery time and verify correctness; do not trade safety for speed |
| Resource use | Avoid sustained memory pressure, uncontrolled queues or GPU/CPU exhaustion |

The API targets apply to the API operation itself, not to model inference or task completion. A task can take longer than one second and still meet the acceptance target if it is durably recorded and its task ID is returned promptly.

A performance target is only useful if the team defines the workload, test environment and measurement method alongside it.

## 03.27.6 Benchmark plan

Run benchmarks against the actual designated host, using realistic test files and the same deployment configuration planned for the team.

### Benchmark scenarios

Scenario A — Read-only filesystem work

Search a permitted directory containing a representative number of files. Measure bridge response time, search duration, result count and resource usage.

Scenario B — Document reading and planning

Read supported test documents, extract bounded content, retrieve relevant context and generate a structured plan. Measure document extraction separately from inference.

Scenario C — File creation

Create a new file in a designated test workspace. Measure authorization, dispatch, local execution, verification and persistence. Include an existing-file conflict and a lost-response simulation.

Scenario D — AI and memory

Run representative requests with and without relevant stored memories. Measure model queue wait, inference time, retrieval latency, context size and plan validation failures.

Scenario E — Three-user workload

Have all three users submit a mix of tasks, including tasks targeting different Windows devices. Confirm that throughput, latency, isolation and recovery remain acceptable.

Scenario F — Dependency failure

Disconnect a bridge, make the model unavailable, restart the backend and simulate database contention. Confirm bounded waiting, truthful task states and safe recovery.

### How to run each benchmark

1. Record the machine specifications, operating system, runtime and model versions, configuration and test dataset.

2. Run a cold-start test to measure startup and initial model-loading costs.

3. Run warm-up requests, then repeat the workload enough times to obtain useful percentiles.

4. Test one user first, then increase concurrency gradually to three users.

5. Record latency, throughput, errors, resource usage and correctness together.

6. Repeat the test after a change, using the same workload and environment.

7. Keep the results in a version-controlled benchmark report, excluding private document content and secrets.

For local model benchmarks, record whether the runtime is actually using the AMD GPU or falling back to CPU. GPU presence alone does not establish that the selected runtime, model format and hardware combination is accelerated.

## 03.27.7 Concurrency control and backpressure

NEXUS must not allow incoming requests to translate into unlimited concurrent inference, database work or Windows operations.

Use separate limits for separate resources rather than one global concurrency number.

| **Resource** | **Required control** | **Initial approach** |
| --- | --- | --- |
| API requests | Request limits and bounded work per request | Keep task submission lightweight |
| Task workers | Maximum active tasks and bounded backlog | Conservative configurable limit |
| AI inference | Model execution slots and bounded waiting | Begin with one inference at a time until benchmarked |
| PostgreSQL | Connection pool and bounded acquisition wait | Size from actual connections and query patterns |
| Windows bridge | Per-device active-operation limit | Begin conservatively; prevent unsafe overlapping writes |
| Tool execution | Tool-specific timeout, output limit and retry budget | Defined in each tool contract |
| Memory/context | Retrieval count, context budget and output limit | Bound both retrieved records and model input |
| Logs and history | Bounded payloads and retention policy | Store summaries and references instead of unlimited raw output |

The initial inference limit of one is a proposed safe baseline, not a claim that the selected model cannot handle parallel requests. Some model runtimes queue requests internally or support controlled parallelism; NEXUS should benchmark the complete stack before increasing the limit.

### What happens when capacity is exhausted?

NEXUS should make an explicit scheduling decision:

- Accept and queue when durable capacity is available.

- Defer or reject when a configured limit is reached and queueing more work would be unsafe or unbounded.

- Return a clear retryable error when the service cannot safely accept the request.

- Expose queue status so users know their task is waiting rather than running.

- Apply fair-use limits so one user cannot consume all model or execution capacity indefinitely.

A request must not disappear merely because the model is busy. Once accepted, it needs a durable task record and a defined state.

### Prevent database contention

- Use short transactions for task creation, claims, approvals and state transitions.

- Never hold a database transaction open while waiting for model inference, a user approval or a Windows bridge response.

- Use database constraints and atomic claims to prevent duplicate task creation and competing worker claims.

- Prevent stale workers from committing updates after losing their lease or fencing token.

- Measure connection-pool wait, lock wait and slow queries before changing indexes or increasing pool size.

Increasing database connections blindly can worsen contention and consume more memory. Connection-pool size should be based on measured concurrency and PostgreSQL capacity.

### Protect individual Windows devices

A device is an independent execution resource. A slow or disconnected device must not stall unrelated devices.

Initially, NEXUS should avoid overlapping operations that could conflict on the same file or application state. Read-only work may allow greater concurrency, but only after the tool's safety and resource behavior are defined.

The backend must preserve explicit device targeting. An overloaded or disconnected device must never cause a task to execute on another computer automatically.

## 03.27.8 Memory and model resource budgeting

The designated computer has 16 GB of RAM reported, but NEXUS cannot assume all 16 GB is available to its services. Windows, WSL 2, Docker if used, PostgreSQL, the model runtime and other applications all compete for resources.

The team must measure actual consumption before choosing a model or setting production concurrency limits.

### Required measurements

- System memory pressure and available memory during inference.

- Peak resident memory for the model runtime.

- GPU utilization and VRAM usage, if supported by the selected AMD driver and runtime.

- CPU usage when the GPU is unavailable or not used.

- Model loading time, inference time and behavior under concurrent requests.

- PostgreSQL and FastAPI memory use during the same workload.

- Effects of WSL 2 memory allocation and Docker configuration, if applicable.

### Model selection procedure

1. Identify the exact AMD GPU model and its VRAM capacity.

2. Select candidate local runtimes and model sizes based on documented hardware support.

3. Confirm that the runtime can actually use the GPU in the intended Windows/WSL 2 deployment.

4. Benchmark at least one practical CPU fallback path.

5. Test representative planning prompts, structured tool outputs and context sizes.

6. Run the three-user workload while measuring memory pressure, queue time and latency.

7. Choose the smallest model that meets NEXUS's measured planning-quality and latency requirements, rather than selecting a model by parameter count alone.

Do not assume NVIDIA CUDA compatibility for AMD hardware. GPU acceleration, supported model formats and container support remain environment-specific validation tasks.

### Resource exhaustion behavior

NEXUS must handle:

- Model out-of-memory errors.

- Model process crashes or restarts.

- Excessive context size.

- Inference timeouts.

- Slow or saturated storage.

- PostgreSQL connection exhaustion.

- WSL 2 or host memory pressure.

The response should be bounded and explicit: fail the current planning attempt, queue within configured limits, or return a dependency error as appropriate. A fallback model may be used only if it is configured and its behavior is understood; switching models must not silently change authorization rules or weaken validation.

## 03.27.9 Performance optimization sequence

Optimization must follow evidence, with correctness and security protected throughout.

1. Measure first. Reproduce the slowdown and identify the phase responsible.

2. Check configuration and workload. Confirm model loading, context size, timeouts, connection pools and unnecessary repeated work.

3. Optimize the actual bottleneck. Examples include reducing redundant database queries, improving a measured query plan, limiting retrieved context or avoiding repeated model calls.

4. Re-run correctness and safety tests. Confirm that the change preserves ownership checks, policy validation, idempotency, recovery and result accuracy.

5. Compare before and after. Record the same latency percentiles, throughput, resource consumption and failure rates.

6. Change architecture only when justified. Introduce additional infrastructure when measurements show that the current design cannot meet agreed requirements.

### Architectural changes require evidence

| **Potential change** | **Evidence that could justify it** |
| --- | --- |
| Separate model host | Inference competes with the backend for resources, or the designated host cannot meet agreed latency and reliability requirements |
| Dedicated worker process | In-process execution causes blocking, poor isolation or difficult recovery |
| Redis or a message broker | Durable scheduling needs cannot be met reliably with the current PostgreSQL-based coordination approach |
| Vector database | PostgreSQL-based retrieval fails measured relevance, scale or latency requirements |
| Multiple model workers | The runtime and hardware demonstrate a useful throughput gain without unacceptable resource pressure |
| More complex observability stack | Structured logs and basic metrics no longer provide sufficient operational visibility |

These are possible future changes, not current requirements. NEXUS should start with the planned modular backend, PostgreSQL and a simple durable task-coordination model.

## 03.27.10 Performance and reliability test requirements

The performance suite must test correctness as well as speed.

| **Test** | **Expected result** |
| --- | --- |
| Repeated identical task submissions | Duplicate requests do not create duplicate tasks |
| Three users submitting concurrently | Correct ownership and target-device enforcement; no lost accepted tasks |
| Several requests waiting for inference | Bounded queue and visible waiting status |
| One bridge becomes unavailable | Other devices remain usable; no silent rerouting |
| Model runtime crashes during planning | Task state remains recoverable and error is diagnosable |
| Database lock contention | Bounded waits and no invalid state transitions |
| Slow document extraction | Tool limits and deadlines are respected |
| File creation succeeds but response is lost | Outcome is reconciled before a potentially unsafe retry |
| Host approaches memory limits | Work is limited or rejected safely rather than accepted without bound |
| Load decreases after a spike | Queued tasks drain and resource usage recovers |

Run performance tests in an isolated environment with test accounts, test directories and synthetic or approved test documents. Do not stress-test real user files or enable unrestricted tools merely to simulate load.

Performance tests must not bypass authentication, policy checks, audit requirements or bridge validation to obtain faster numbers.

## 03.27.11 Operational limits and configuration

All resource limits should be configurable, validated at startup and documented. The team should avoid hardcoding values throughout the codebase.

Proposed configuration categories:

performance:

max_active_tasks: TBD

max_queued_tasks: TBD

max_concurrent_inference: 1

max_active_operations_per_device: TBD

database_pool_size: TBD

request_timeout: TBD

tool_timeouts: defined per tool

max_context_size: TBD

max_tool_output_size: TBD

This is an illustrative configuration shape, not a finalized schema. Exact names, units, defaults and validation rules must be decided before implementation. The initial inference limit of one is a proposal; other TBD values require measurements.

Operational rules:

- Limits must be enforced by the backend, not only by the CLI.

- Per-user and per-device limits must be applied consistently.

- Queue limits must prevent unlimited growth during model or device outages.

- Timeouts must distinguish an operation that definitely failed from one whose outcome is uncertain.

- Reducing a concurrency limit must not invalidate work already executing.

- Configuration changes must not bypass policy or retroactively authorize operations.

- Metrics and logs must make saturation and rejected work visible without exposing private content.

## 03.27.12 Team ownership

| **Developer** | **Primary responsibility** |
| --- | --- |
| Developer 1 — Backend | API latency, task scheduling, PostgreSQL performance, worker claims, concurrency correctness and recovery |
| Developer 2 — Windows integration | Bridge latency, per-device concurrency, filesystem performance, operation timeouts and local resource use |
| Developer 3 — AI and context | Model benchmarks, inference capacity, context budgets, retrieval latency and planning quality |
| All three | Three-user load tests, bottleneck review, security regression testing and release sign-off |

Performance ownership does not mean isolated testing. The final benchmark must cover the complete system, because a locally fast component can still be part of a slow end-to-end workflow.

## 03.27.13 Acceptance criteria

## Section 03.27 is ready for implementation when the team agrees on the measurement and capacity policy below.

- API acceptance latency is measured separately from task completion.

- Task timing can be broken down by scheduling, AI, policy, bridge, tool execution and persistence.

- The designated host's exact CPU, RAM availability, GPU and VRAM are documented.

- AMD GPU acceleration is verified or a CPU fallback is benchmarked.

- Three-user workloads are reproducible.

- Model, database, task and per-device concurrency limits are explicit.

- Queues and tool outputs are bounded.

- Overloaded services return honest, actionable states or errors.

- Database contention and stale worker behavior are tested.

- Disconnected devices and uncertain external side effects are handled safely.

- Baseline and post-optimization results are recorded.

- Performance changes do not weaken authorization, auditability or recovery.

- Release targets are agreed based on measured results rather than assumed hardware performance.

## 03.27.14 Open decisions

These are the remaining decisions. They should not be treated as finalized implementation facts.

| **Decision** | **Current position** |
| --- | --- |
| Exact performance targets | Initial API targets proposed; validate through benchmarks |
| Maximum active tasks | Open |
| Maximum queued tasks | Open |
| Model inference concurrency | One proposed as the initial baseline |
| Database pool size | Set after query and concurrency testing |
| GPU runtime and model | Open pending AMD hardware validation |
| CPU fallback | Benchmark before final selection |
| Per-device operation limits | Conservative baseline; exact limits open |
| Memory and context budgets | Set after measuring the selected model |
| Separate model host | Only if measurements justify it |
| Additional queue infrastructure | Not planned unless evidence requires it |

## Section exit criterion

The goal is not to make every NEXUS task instantaneous. It is to make performance measurable, bounded, predictable and safe for three users sharing limited hardware.

Once this section is agreed, the team should be able to answer three questions with evidence:

1. Where does a slow task spend its time?

2. How much simultaneous work can the actual host support without compromising reliability?

3. What should NEXUS do when that capacity is exhausted?
