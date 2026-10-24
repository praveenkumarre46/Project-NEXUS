## 04.19.01 Purpose

NEXUS must be able to explain what happened during a task, not merely display its final status. Users and developers need to investigate failures, understand decisions, identify completed work and safely continue interrupted workflows.

This section defines three related but separate capabilities:

- Task history: what happened during a task, including its steps and results.

- Security audit trail: who initiated or authorized consequential actions and which policy decisions were recorded.

- Execution replay: reconstructing a prior workflow for investigation or running an explicitly requested new attempt without blindly repeating external side effects.

Core principle: history is evidence of recorded events, not permission to repeat them. Replaying a workflow must not silently replay its previous authority.

## 04.19.02 History, audit and logs are different

Task history

Explains the lifecycle of a task: request accepted, steps completed, approval awaited, device disconnected, result verified and task finalized.

Security audit trail

Records significant security-relevant events: authentication, access denials, approval decisions, device revocation and consequential execution decisions.

Operational logs

Help developers diagnose runtime behavior, exceptions, timeouts, performance and dependency failures.

These records may reference the same task or operation IDs, but they have different purposes and access rules.

For example, a failed document read belongs in task history. An unauthorized cross-user access attempt belongs in the security audit trail. A database connection timeout belongs in operational logs and may also produce a task-history event if it affects the task.

Do not use raw application logs as the sole source of task history or security evidence.

## 04.19.03 Task timeline and event model

Each task should have a chronological, inspectable timeline based on persisted events and current authoritative state.

Proposed event categories include:

| **Category** | **Example events** |
| --- | --- |
| Task lifecycle | TASK_ACCEPTED, TASK_STARTED, TASK_COMPLETED |
| Planning | PLAN_CREATED, PLAN_REJECTED, CLARIFICATION_REQUESTED |
| Execution | STEP_READY, OPERATION_DISPATCHED, OPERATION_RESULT_RECORDED |
| Approval | APPROVAL_REQUESTED, APPROVAL_GRANTED, APPROVAL_REJECTED, APPROVAL_EXPIRED |
| Device | DEVICE_UNAVAILABLE, DEVICE_RECONNECTED, DEVICE_REVOKED |
| Recovery | RECOVERY_STARTED, OPERATION_RECONCILED, OUTCOME_REMAINS_UNCERTAIN |
| Artifact | ARTIFACT_CREATED, ARTIFACT_VERIFIED, ARTIFACT_UNAVAILABLE |

These names are illustrative. The team should reconcile them with the event and error contracts already defined in Section 04.08 and Section 03.24.

### Logical event fields

A history event may contain:

- event_id

- task_id

- step_id, where applicable

- operation_id, where applicable

- event_type

- occurred_at

- recorded_at

- actor_type and authorized actor reference

- device_id, where applicable

- correlation_id

- outcome

- Bounded, structured metadata

The distinction between occurred_at and recorded_at matters. A bridge may execute an operation while disconnected and report its outcome later. The system should preserve both timestamps when reliable, rather than pretending the event was received at the same time it occurred.

A timestamp supplied by a bridge is evidence to evaluate, not unquestionable proof. Validate its association with the authenticated device and operation.

## 04.19.04 Recording task history reliably

History must remain useful across backend restarts, device disconnections and failed operations.

### Recording rules

1. Persist task acceptance and its idempotency key before acknowledging durable acceptance.

2. Record important task and step transitions in the same transaction as their authoritative state changes where practical.

3. Record operation intent before dispatching a Windows side effect.

4. Record the bridge's correlated response and the verification outcome separately when they represent different facts.

5. Preserve failures and uncertainty rather than replacing them with a generic failure message.

6. Ensure retries do not create duplicate logical events for the same occurrence.

7. Prevent stale workers from writing authoritative events after losing their claim.

8. Do not allow an ordinary user or model response to fabricate authoritative history entries.

### Transactional consistency

Suppose a task is marked SUCCEEDED, but the application crashes before the corresponding completion event is committed. The history would contradict the task state.

The preferred design is to write the state transition and its corresponding history event in the same PostgreSQL transaction when both belong to the same logical change.

External events, such as Windows bridge responses, require a different process: authenticate and validate the response, persist the received evidence, then apply the valid transition. PostgreSQL cannot atomically commit a Windows file operation.

### Event ordering

Timestamps alone may not establish an unambiguous order when events originate on different machines.

NEXUS should use authoritative task/step transitions, operation identifiers and a documented event-ordering strategy. A monotonically increasing per-task sequence number is one option if the team needs deterministic timeline ordering.

Events received late must not overwrite newer task states simply because they arrived through a valid connection.

## 04.19.05 Searchable task history

The CLI should allow users to find past work without manually remembering every task ID.

Proposed commands:

nexus history

nexus history --status failed

nexus history --device my-windows-pc

nexus history --since 7d

nexus task <task-id>

nexus task <task-id> --steps

nexus task <task-id> --result

These are proposed command examples; exact flags and filtering semantics remain subject to the CLI contract.

### Initial search filters

- Task ID.

- Creation or completion time range.

- Task status and outcome.

- Target device.

- Tool or step type, if recorded.

- Error code.

- Whether approval or recovery was required.

Free-text search across full prompts and document contents should not be enabled by default. It creates privacy, retention and indexing implications that are unnecessary for basic task history.

### Authorization and pagination

- Every history query must be scoped to the authenticated user.

- Individual task lookup must repeat the ownership check; an unguessable ID alone is insufficient.

- Results must be paginated and bounded.

- Sorting must be deterministic, including a tie-breaker when timestamps match.

- Device revocation must not accidentally transfer historical ownership.

- Shared-project history requires an explicit sharing model and is outside the initial private-history default.

## 04.19.06 Security audit trail

The audit trail records important security and authorization decisions independently of whether the requested task succeeded.

### Events that should be audited

- User authentication and relevant authentication failures.

- Device registration, revocation and credential rotation.

- Access-denied decisions involving tasks, devices or artifacts.

- Approval requests and decisions.

- Policy decisions for consequential operations.

- Changes to tool enablement or security-sensitive configuration.

- Execution attempts involving consequential operations.

- Recovery decisions for uncertain external effects.

- Administrative actions that affect users, permissions or retention.

Not every ordinary read-only tool invocation necessarily needs the same audit detail as a consequential write. The team should define event coverage according to risk and operational requirements.

### Minimum audit attributes

| **Attribute** | **Purpose** |
| --- | --- |
| Actor | User, device, service or administrative identity |
| Action | What was attempted or decided |
| Target | Task, device, approval or resource reference |
| Outcome | Allowed, denied, approved, rejected, failed or uncertain |
| Timestamp | When the event was recorded |
| Correlation reference | Links related records |
| Policy reference | Identifies the applicable policy version, when relevant |

Audit records should not contain raw credentials, access tokens or unnecessary document content.

### Integrity and trust limitations

A database audit table is useful, but it is not automatically tamper-proof. Someone with sufficient database or host privileges may be able to alter it.

For the initial local-network deployment, use restrictive database permissions, controlled administrative access, backups and reviewable configuration changes. Strong tamper-evident or external audit storage can be considered later if the threat model justifies it.

Important: task history is primarily an operational record; a security audit trail is evidence of security-relevant events. Neither should be presented as cryptographic proof unless such guarantees are explicitly implemented and tested.

## 04.19.07 Execution replay: three distinct modes

NEXUS must distinguish replaying recorded information from executing operations again.

Mode A — Historical inspection

Reconstruct the recorded timeline, plan version, step outcomes and available evidence. No external operations are executed.

MVP

Mode B — Diagnostic replay

Re-run planning or validation against recorded, authorized test fixtures without performing real-world side effects. Useful for reproducing model and validation defects.

Recommended next capability

Mode C — New execution attempt

Create a new task or supported continuation based on a prior task. Revalidate current permissions, device availability, plan, dependencies and approval requirements before executing.

Strict safeguards

Mode A is essential for the MVP. Mode B can be added to the testing workflow. Mode C should not be implemented as a blind “repeat everything” command.

## 04.19.08 Safe retry and replay rules

A previous successful operation is not automatically safe to execute again.

For example:

- Repeating a file search is generally safe, subject to current permissions and resource limits.

- Re-reading a document requires fresh access checks and may produce different content if the source changed.

- Creating a file may fail because the destination already exists.

- Launching an application twice may open duplicate instances.

- Repeating a form submission or other consequential action could create duplicate external effects.

### Required replay workflow

1. Load the original task and verify that the requesting user can access it.

2. Create a new task or explicitly supported continuation; preserve the original task's history.

3. Identify completed, failed, skipped and uncertain steps.

4. Check whether previously observed resources or documents have changed.

5. Rebuild the plan using the current tool registry and capabilities.

6. Revalidate user permissions, device identity, policy and dependencies.

7. Request new approval where required.

8. Generate new operation identities for genuinely new operations.

9. Reuse an existing operation identity only when reconciling or safely retrying the same logical operation under its defined protocol.

10. Execute through the normal orchestrator and bridge safeguards.

11. Record the new attempt and its relationship to the original task.

A replay must not inherit old approval decisions, revoked credentials or previously granted access.

### Original task versus new task

The original task should remain an immutable historical reference for its recorded outcomes, although authorized corrections or annotations may be supported.

A new execution attempt should have its own task ID and result. It may reference the original task through a field such as replay_of_task_id or parent_task_id. The exact schema remains open.

This makes it possible to compare attempts without rewriting history to imply that the original task succeeded.

## 04.19.09 Plan snapshots and execution provenance

To investigate a failure, NEXUS needs enough information to reconstruct what it intended to do.

A logical plan snapshot may record:

- Plan ID and revision.

- Tool names and schema versions.

- Step dependencies and normalized arguments, subject to privacy controls.

- Target device and relevant capability version.

- Policy version and authorization outcome.

- Model/runtime identifier and relevant configuration version.

- References to the context and evidence used.

- Creation timestamp and validation outcome.

The system should not automatically store full model prompts, full document text or every retrieved memory. Prefer references, bounded metadata and redacted snapshots when they provide sufficient diagnostic value.

### Reproducibility limitations

A saved plan does not guarantee that re-running the plan will produce the same result. The environment, source files, model version, tool versions and permissions may have changed.

For diagnostic replay, record the relevant versions and use fixed fixtures when possible. For live execution, explicitly revalidate the current environment instead of pretending it is identical to the original.

Model-generated plans are proposals, not authoritative execution records. The persisted, validated plan and actual operation events are the evidence to inspect.

## 04.19.10 Retention, deletion and privacy

Task history, audit events and operational logs require separate retention policies.

| **Data category** | **Retention considerations** |
| --- | --- |
| Task history | User value, storage volume and support needs |
| Security audit events | Security investigations, accountability and applicable obligations |
| Operational logs | Debugging value, volume and sensitivity |
| Plan snapshots | Reproducibility versus exposure of request details |
| Operation journal | Duplicate prevention and safe recovery windows |
| Artifact metadata | Whether the referenced file still exists and who may access it |
| Backups | Recovery requirements and the possibility of retaining deleted records |

### Deletion rules

- Deleting a memory does not automatically delete task history.

- Deleting a task's visible history must not silently remove evidence needed for a currently unresolved external operation.

- Expiring operational logs must not erase the only record needed to reconcile an uncertain side effect.

- Retention-required audit records should not be altered merely because a user deletes a task from their visible history.

- Backup restoration must not silently reactivate revoked access or deleted content in active retrieval.

The team must define what users can delete, what gets deactivated, what remains in audit records and how long backups may retain older copies.

Avoid promising that information has been completely erased when it may remain in backups, external logs or other retained copies.

## 04.19.11 Proposed API and CLI integration

The existing API should be extended only where history requires new capabilities.

Proposed endpoints:

| **Endpoint** | **Purpose** |
| --- | --- |
| GET /v1/tasks | Paginated task history |
| GET /v1/tasks/{task_id} | Task state and summary |
| GET /v1/tasks/{task_id}/steps | Step timeline |
| GET /v1/tasks/{task_id}/result | Final result and artifact references |
| GET /v1/tasks/{task_id}/events | Detailed task-event history, if separate event retrieval is needed |
| GET /v1/audit-events | Authorized audit queries, if a separate audit interface is required |

These are proposed routes, not final API contracts. Audit access should not automatically be granted to ordinary users merely because they can view their task history.

### Example CLI output

Task: task-789

Outcome: FAILED

Timeline:

10:30:02  Task accepted

10:30:03  Plan validated

10:30:04  Operation dispatched

10:30:14  Device response timed out

10:30:15  Recovery required

Last confirmed state:

Operation dispatched; final external outcome unknown.

Recommended action:

Inspect operation evidence before retrying.

This is illustrative. A real timeline must use recorded events and the actual persisted state, not fabricated timestamps or guessed causes.

## 04.19.12 Testing strategy

| **Test** | **Expected behavior** |
| --- | --- |
| Backend restarts during a task | Recorded history survives restart |
| State transition and event write fail together | No contradictory committed state |
| Bridge response arrives late | Event is correlated and does not overwrite newer state incorrectly |
| Concurrent history requests | Results remain properly scoped and consistently ordered |
| User guesses another task ID | Access is denied |
| Duplicate bridge response | No duplicate logical execution or misleading history |
| Replay of a read-only task | New attempt uses current authorization and records its own result |
| Replay of a file-creation task | Existing file is reconciled; no blind overwrite or duplicate |
| Old approval exists | New execution cannot inherit it automatically |
| Source document has changed | New attempt records the current source version |
| Audit write fails | Behavior follows the defined security policy; consequential actions must not proceed without required audit evidence |
| Log retention runs | Required task recovery and audit records remain available under their own policies |
| Deleted memory exists in backup | Restoration does not silently reintroduce it into active retrieval |
| Model version changes | Diagnostic comparison records the relevant version difference |
| Concurrent decisions or stale workers | History reflects only authoritative state transitions |

Tests should use a real PostgreSQL instance for transaction and concurrency behavior. External operations should be simulated in isolated test environments unless a specific Windows integration test requires a controlled real operation.

## 04.19.13 Work packages and ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Task timeline and event persistence | Developer 1 | Consistent, durable task history |
| Audit event design and access control | Developer 1 | Authorized, structured security records |
| Bridge event correlation | Developer 2 | Authenticated, operation-correlated device evidence |
| Diagnostic replay and model evaluation | Developer 3 | Reproducible planning and validation tests |
| Safe retry and execution replay | Developer 1 + Developer 2 | Recovery without blind side-effect repetition |
| Plan snapshots and provenance | Developer 3 + Developer 1 | Versioned plans and traceable context references |
| Retention and privacy tests | All three | Verified access, deletion and retention behavior |

## 04.19.14 Implementation priorities

P0 — Required foundation

Durable and trustworthy history

- Persisted task and step timeline.

- Correlated operation evidence.

- User-scoped history access.

- Security audit events for important decisions.

- Recovery-compatible event recording.

- Privacy-safe operational logs.

P1 — Investigation and replay

Diagnosable failures

- Searchable history filters.

- Versioned plan snapshots.

- Diagnostic replay using controlled fixtures.

- Safe new attempts based on previous tasks.

- Retention and deletion behavior.

P2 — Advanced operations

Stronger auditability

- Tamper-evident audit storage if justified.

- Advanced timeline visualization.

- Automated incident investigation.

- Cross-system trace correlation.

## 04.19.15 Open decisions

- Should task events be stored in a dedicated task_events table or alongside existing audit structures?

- Which event types require atomic persistence with state transitions?

- Is a per-task sequence number necessary for deterministic timeline ordering?

- Which history fields may contain sensitive request or argument data?

- How long should task history, security audit records and operation journals be retained?

- Which diagnostic replay capabilities belong in the 10–12 week MVP?

- Should users be able to start a new task directly from a previous failed task?

- What level of tamper evidence is appropriate for the initial local-network deployment?

## 04.19.16 Definition of done

- Task timelines survive backend restarts.

- Task history, audit records and operational logs have distinct purposes and access controls.

- State transitions and corresponding events cannot silently contradict each other.

- Late and duplicate bridge responses are handled safely.

- History queries enforce user ownership and bounded pagination.

- Replay distinguishes historical inspection, diagnostic replay and new execution.

- New execution attempts revalidate permissions and do not inherit old approvals.

- Uncertain external effects are reconciled before unsafe retries.

- Retention and deletion rules are documented and tested.

- Concurrency, security and recovery tests pass.

Section exit criterion: developers and users can reconstruct what happened during a task, investigate failures using reliable evidence and initiate a new attempt without confusing recorded history with current authorization.
