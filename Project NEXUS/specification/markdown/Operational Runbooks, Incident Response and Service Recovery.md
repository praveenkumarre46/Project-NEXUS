## 04.24.01 Purpose

NEXUS must remain diagnosable and recoverable when individual components fail. Because it can execute operations on real Windows computers, operational recovery must preserve security boundaries and distinguish confirmed outcomes from uncertain ones.

This section defines how the three developers should respond to:

- Backend or database outages.

- AI runtime failures and resource exhaustion.

- Windows bridge disconnections.

- Stuck tasks and uncertain external operations.

- Authentication, credential and permission failures.

- Failed deployments and migrations.

- Suspected unauthorized access or security incidents.

- Backup restoration and service recovery.

Core principle: restore service without sacrificing correctness. Getting NEXUS running again is not enough if the system has lost track of what it did on a user's computer.

## 04.24.02 Operational responsibilities

The team should assign a primary incident owner for each incident. Ownership determines who coordinates the response, not who is solely responsible for fixing every component.

| **Area** | **Primary responsibility** | **Supporting responsibility** |
| --- | --- | --- |
| FastAPI, task orchestration and PostgreSQL | Developer 1 | Developer 2 or 3, as relevant |
| Windows bridge and local execution | Developer 2 | Developer 1 for task recovery |
| AI runtime, planning and context retrieval | Developer 3 | Developer 1 for task-state safety |
| Cross-component incidents | Designated incident owner | All affected developers |
| Security incident | Designated incident owner coordinates | All three participate in containment and evidence review |
| Release-related failure | Release owner | Component owners and reviewer |

For the initial team, the incident owner can be assigned manually. A dedicated incident-management platform is not required.

## 04.24.03 Incident severity and response priorities

Severity should reflect user impact, security exposure and the risk of incorrect external side effects—not merely whether a process is down.

SEV-1 — Critical

Security breach or unsafe execution

Examples: unauthorized cross-user access, unauthorized device operation, credential compromise, filesystem scope escape or evidence that prohibited operations executed.

Response: contain immediately, stop affected execution paths, preserve evidence and investigate before resuming.

SEV-2 — High

Major service failure or corrupted task confidence

Examples: PostgreSQL failure affecting accepted tasks, widespread bridge incompatibility, migration failure or multiple uncertain operations.

Response: stop unsafe dispatch, identify affected tasks, restore a trustworthy service state and reconcile external operations.

SEV-3 — Moderate

Limited feature or device degradation

Examples: one bridge is offline, model inference is unavailable, or a supported document parser repeatedly fails.

Response: isolate the affected capability, communicate the limitation and preserve unrelated safe operations.

SEV-4 — Low

Non-blocking defect

Examples: confusing diagnostic output, a non-critical performance regression or a documentation error.

Response: record the issue, assign an owner and fix it through the normal workflow.

These severity levels and example categories are proposed. Response-time commitments should be set after the team agrees on availability expectations.

A suspected security incident should be treated conservatively until the scope is understood. A lower-severity classification must not delay containment of an active unauthorized operation.

## 04.24.04 Standard incident-response lifecycle

1. Detect

Health checks, logs, user reports or task-state anomalies

2. Triage

Determine scope, severity, affected users, devices and tasks

3. Contain

Stop unsafe dispatch, revoke compromised access or isolate a failing component

4. Diagnose

Use task history, audit events, dependency health and operation evidence

5. Recover

Repair, roll back, restore or reconcile as appropriate

6. Verify and close

Run smoke tests, confirm safe task behavior and record follow-up actions

### Mandatory incident rules

1. Do not delete logs or operation records to make a system appear healthy.

2. Do not blindly restart or replay all nonterminal tasks.

3. Do not disable authorization or approval checks to restore functionality faster.

4. Do not assume a timeout means an external operation failed.

5. Do not claim that recovery succeeded until the relevant checks pass.

6. Preserve enough evidence to determine which users, devices and tasks were affected.

7. If the system cannot establish a safe outcome, preserve uncertainty and escalate.

## 04.24.05 Runbook A — Backend unavailable

Symptoms: the CLI cannot connect, the API is not responding, or readiness checks fail.

### Procedure

1. Confirm the backend host is running and reachable.

2. Check the API process and its recent logs.

3. Check configuration and whether the intended API address or network binding changed.

4. Check PostgreSQL connectivity and migration compatibility.

5. Check whether a recent deployment or configuration update preceded the failure.

6. Determine whether accepted tasks remain safely persisted.

7. Restart or roll back only after identifying the likely failure and its recovery implications.

8. Verify authenticated API access, task retrieval and device connectivity.

9. Reconcile tasks that were in flight before service restoration.

### Safety requirements

- If PostgreSQL is unavailable, the backend must not claim durable task acceptance.

- If the API is reachable but the database schema is incompatible, normal task execution must remain blocked.

- If the backend restarts after dispatching an operation, it must recover from persisted state and reconcile external effects.

- A restarted process must not automatically treat every expired worker claim as proof that an external operation never happened.

Recovery acceptance: authenticated API operations work, persisted tasks are accessible, required dependencies are healthy and uncertain operations remain correctly classified.

## 04.24.06 Runbook B — PostgreSQL failure or data inconsistency

Symptoms: connection failures, lock contention, failed transactions, migration errors or inconsistencies between task state and operation history.

### Procedure

1. Stop new task dispatch if authoritative state cannot be safely read or written.

2. Determine whether the problem is connectivity, capacity, locking, schema incompatibility or suspected data corruption.

3. Preserve database diagnostics and relevant task/operation identifiers.

4. Avoid repeated destructive repair attempts.

5. Recover database availability or follow the verified restore procedure.

6. Validate constraints, migration state and important relationships.

7. Reconcile tasks that were dispatched before the failure.

8. Run persistence, authorization and end-to-end smoke tests.

9. Resume dispatch only after database consistency and required service behavior are verified.

### Critical data invariants

- Task ownership must remain intact.

- Task and step states must not contradict their persisted history without a diagnosable recovery explanation.

- Operation identities and attempt records must remain consistent.

- Revoked device credentials must not be silently reinstated.

- Approval records must not be reconstructed as approved merely because an operation appears to have started.

- Restoring the database does not establish what happened on a disconnected Windows computer.

If corruption is suspected, prioritize evidence preservation and a verified recovery path over quick manual edits.

## 04.24.07 Runbook C — AI runtime unavailable or resource-exhausted

Symptoms: inference timeouts, failed model loading, invalid output, GPU or RAM pressure, or a model queue that is not progressing.

### Procedure

1. Check whether the failure affects the runtime, the model artifact, resource availability or the application adapter.

2. Check CPU, RAM, GPU/VRAM and inference latency.

3. Inspect bounded diagnostic metadata and model error codes.

4. Stop or reduce new inference work if resource limits are exceeded.

5. Preserve accepted task state.

6. Restart or restore the previously validated runtime configuration if appropriate.

7. Run a simple inference test followed by the structured-planning evaluation.

8. Resume AI-dependent work only when the runtime is healthy and the evaluation requirements pass.

### Safety requirements

- Model failure must not bypass policy validation.

- Invalid or truncated model output must not dispatch a tool.

- AI-dependent tasks must not be marked successful when the required inference did not occur.

- CPU fallback may be used only if the fallback was configured and validated.

- Unrelated deterministic operations may continue only if the product explicitly supports that degraded mode and its dependencies are healthy.

Recovery acceptance: the selected runtime passes its smoke test, resource usage is within configured limits and invalid-output handling remains active.

## 04.24.08 Runbook D — Windows bridge disconnected or unresponsive

Symptoms: a device appears offline, operations time out, or the backend stops receiving bridge results.

### Procedure

1. Identify the device and affected tasks.

2. Check the bridge process, network connectivity, authentication and protocol compatibility.

3. Stop new dispatch to the unavailable device.

4. Preserve the original target device; do not reroute tasks to another computer.

5. Identify operations that were dispatched but whose outcomes were not confirmed.

6. When the bridge reconnects, authenticate it and verify its current capabilities.

7. Reconcile unresolved operations using the operation journal and available Windows-side evidence.

8. Revalidate current permissions, approval and policy before any new dispatch.

9. Resume eligible tasks only after their state is understood.

### Safety requirements

- A heartbeat is evidence of recent communication, not proof that every tool works.

- A timeout is not proof that an operation failed.

- Reconnection is not permission to replay all outstanding operations.

- A revoked or incompatible bridge must remain ineligible for new work.

- If the bridge's operation journal is missing or insufficient, preserve uncertainty where the external outcome cannot be established.

Recovery acceptance: the bridge is authenticated, compatibility is confirmed, safe tools pass a read-only test and outstanding operations have been reconciled or explicitly left uncertain.

## 04.24.09 Runbook E — Task stuck, duplicate execution or uncertain outcome

Symptoms: a task remains in RUNNING, a worker lease expires, the same operation appears more than once, or a file may have been created despite a timeout.

This runbook is safety-critical because task records and external Windows side effects cannot be committed in one atomic transaction.

### Procedure

1. Retrieve the task, step, operation and attempt records.

2. Identify the last confirmed transition and whether the operation was dispatched.

3. Determine whether the original worker or bridge may still be executing.

4. Check claim generation, lease status, bridge journal and correlated responses.

5. Inspect available external evidence using the tool's documented verification method.

6. Classify the outcome as confirmed success, confirmed failure or unresolved.

7. Retry only if the tool contract permits it and the previous effect has been reconciled sufficiently.

8. Record the recovery decision and any remaining uncertainty.

9. Verify that dependent steps are blocked or released according to the confirmed outcome.

### Recovery decision table

| **Evidence** | **Required action** |
| --- | --- |
| Operation was never dispatched and this is reliably established | Resume or dispatch if still authorized |
| Read-only operation failed and is safe to retry | Retry within its configured budget |
| File creation may have succeeded | Reconcile the destination and operation journal before retry |
| Application launch response was lost | Inspect available process and operation evidence before deciding |
| Original worker is stale but external execution may continue | Prevent stale state updates and reconcile external execution |
| Outcome cannot be established | Preserve uncertainty and require further recovery |
| Task was cancelled but a side effect may have occurred | Reconcile the effect; do not pretend cancellation reversed it |

### Prohibited shortcuts

- Manually changing an uncertain task to SUCCEEDED.

- Deleting an operation record to permit another attempt.

- Generating a new operation ID merely to bypass duplicate detection for the same unresolved effect.

- Treating an expired lease as proof that the old worker stopped.

- Replaying every incomplete step after a restart.

Recovery acceptance: each affected operation has a defensible recorded outcome, unsafe retries are prevented, and unresolved uncertainty remains visible.

## 04.24.10 Runbook F — Authentication or device credential failure

Symptoms: login failures, rejected bridge credentials, unexpected session expiration or suspected credential exposure.

### Procedure

1. Identify the affected account, device and authentication boundary.

2. Determine whether the issue is an ordinary configuration error or a possible compromise.

3. If compromise is suspected, revoke the affected credential or session through the authorized mechanism.

4. Prevent new operations using the compromised identity.

5. Check audit events for suspicious authentication, enrollment or operation activity.

6. Rotate or re-provision credentials through the approved workflow.

7. Re-enroll a device only after its identity and ownership are verified.

8. Confirm that revoked credentials remain rejected.

9. Review queued and in-flight operations associated with the affected identity.

10. Document the incident and any required access review.

### Required safeguards

- Do not copy credentials into chat, tickets or diagnostic logs.

- Do not temporarily disable authentication to restore connectivity.

- Do not share one device credential across all three computers.

- Do not reinstate a revoked credential simply because an old backup contains its metadata.

- Revocation prevents future authorized use; it cannot reverse an operation that already happened.

If there is evidence of unauthorized execution, follow the security incident runbook below as well.

## 04.24.11 Runbook G — Failed deployment or migration

Symptoms: the new backend does not start, bridges become incompatible, migrations fail or smoke tests fail after an update.

### Procedure

1. Stop further rollout.

2. Identify the exact release and versions already deployed.

3. Record the failed step, error codes and migration state.

4. Determine whether persistent data or external operations may have changed.

5. Select a recovery strategy: application rollback, forward-fix, compatible mode or verified database restore.

6. Confirm compatibility between the recovery version and current schema.

7. Preserve current security restrictions and credential revocations.

8. Restore service in a controlled sequence.

9. Reconcile in-flight and uncertain operations.

10. Run release smoke tests before reopening normal execution.

11. Record the cause and update the deployment procedure or regression tests.

### Important distinction

An application rollback and a database rollback are different actions. Neither should be assumed to undo Windows-side effects.

If the old application version cannot safely read the migrated schema, a tested forward-fix may be safer than forcing an incompatible rollback.

## 04.24.12 Runbook H — Suspected security incident

Examples: a user accesses another user's memory, a bridge executes an unauthorized operation, a credential is exposed, a document injection causes a policy bypass, or a filesystem boundary is escaped.

### Immediate response

1. Contain: stop affected execution paths, disable the affected tool or revoke the affected credential as appropriate.

2. Preserve evidence: retain relevant task history, audit events, operation journals, deployment metadata and sanitized diagnostics.

3. Identify scope: determine affected users, devices, data, tasks and time window.

4. Prevent recurrence: block the vulnerable path and verify the enforcement layer that failed.

5. Recover trust: rotate credentials or rebuild affected components where warranted.

6. Reconcile side effects: determine what happened on Windows devices; do not assume stopping the backend reversed an operation.

7. Validate the fix: add regression tests and repeat relevant security checks.

8. Resume cautiously: require explicit review before restoring affected capabilities.

9. Document the incident: record impact, evidence, decisions, remediation and follow-up owners.

### Evidence handling

- Restrict access to incident records.

- Do not copy full private documents or credentials into incident notes.

- Record timestamps, correlation IDs and affected resource identifiers.

- Distinguish confirmed facts from hypotheses.

- Preserve evidence before cleanup or restoration where practical.

If NEXUS's host or backend credentials may be compromised, assume that ordinary application-level authorization checks may no longer be sufficient until the host, credentials and affected data are assessed.

## 04.24.13 Service recovery and readiness criteria

A component being online does not automatically mean the entire service is safe to use.

NEXUS should have explicit recovery gates.

| **Gate** | **Required evidence** |
| --- | --- |
| Infrastructure | Required processes and dependencies are healthy |
| Persistence | Database connectivity, schema and critical records are consistent |
| Identity | Authentication works and revoked credentials remain rejected |
| Device execution | Bridges authenticate and report compatible capabilities |
| Task recovery | In-flight operations are reconciled or explicitly marked uncertain |
| Policy | Current permissions, approvals and prohibitions are enforced |
| AI | Required runtime passes health and output-validation checks |
| End-to-end | A permitted smoke test succeeds without violating access boundaries |

### Recovery states

The team should distinguish these operational conditions:

- Recovering: restoration or reconciliation is in progress.

- Degraded: a component or feature is unavailable, but documented safe functions remain usable.

- Ready: all dependencies and checks required for the declared operating mode pass.

- Blocked: execution must not resume because safety, integrity or compatibility cannot be established.

These are proposed operational classifications. They should complement—not replace—the authoritative task and step state machines.

## 04.24.14 Incident communication and handoff

Even with only three developers, incident handoffs should be explicit so two people do not independently perform conflicting recovery actions.

Every incident record should contain:

- Incident identifier and severity.

- Incident owner.

- Start time and detection method.

- Affected service, user, device and task identifiers where known.

- Last confirmed healthy state.

- Observed symptoms and stable error codes.

- Actions taken and their results.

- Current recovery state.

- Unresolved uncertainty and safety restrictions.

- Next action, owner and escalation condition.

- Closure decision and follow-up work.

### Communication rules

- State what is known, what is suspected and what remains unknown.

- Communicate when a service is unavailable or a task result is uncertain.

- Do not claim recovery until verification passes.

- Do not expose passwords, tokens, private document contents or unrelated user data.

- When a task may have partially completed, explain which steps are confirmed and which require reconciliation.

A concise, accurate status is more useful than a confident but unsupported claim that everything is fixed.

## 04.24.15 Operational observability and incident metrics

The observability system from Section 03.19 should make the common runbooks executable without requiring unrestricted debugging access.

### Required signals

- API availability and readiness.

- Database connectivity, transaction failures and lock contention.

- Active tasks, queue wait and state-transition failures.

- Worker claim expiration and stale-worker rejection.

- Bridge connectivity, protocol incompatibility and tool failures.

- AI runtime availability, latency, invalid output and resource pressure.

- Operation timeouts, uncertain outcomes and reconciliation duration.

- Authentication failures, revocations and policy denials.

- Migration failures and release smoke-test results.

### Proposed operational metrics

| **Metric** | **Why it matters** |
| --- | --- |
| Time to detect | Shows how quickly failures become visible |
| Time to contain | Measures how quickly unsafe execution is stopped |
| Time to restore service | Measures availability recovery |
| Number of uncertain operations | Shows unresolved external-effect risk |
| Recovery success rate | Measures whether documented procedures work |
| Repeat incident rate | Highlights ineffective fixes |
| Mean task-state recovery time | Shows how quickly accepted work becomes understandable again |

These metrics are for learning and reliability improvement. They must not encourage the team to mark uncertain operations as complete merely to improve a dashboard.

## 04.24.16 Backup restoration runbook

Use the dedicated backup policy in Section 03.21; this runbook defines the operational sequence for a restore.

1. Identify why restoration is necessary and define the recovery scope.

2. Stop new writes and task dispatch where required.

3. Select a backup whose integrity and provenance can be verified.

4. Restore into an isolated environment first where practical.

5. Validate schema compatibility, ownership constraints and important records.

6. Restore required configuration and dependencies securely.

7. Reconcile task, approval, credential and device state against current security decisions.

8. Identify tasks whose external effects may have occurred after the backup was taken.

9. Reconcile those effects before any unsafe retry.

10. Run authentication, authorization, persistence and end-to-end smoke tests.

11. Record the recovery point, known data loss and unresolved work.

12. Resume operations only after the recovery owner approves readiness.

### Required restrictions

- A restored database must not silently reinstate revoked devices or permissions.

- Deleted memory must not automatically return to active retrieval simply because a backup contains an older copy.

- A restored task record does not prove that the corresponding Windows operation did or did not happen.

- Recovery must preserve uncertainty where external evidence is insufficient.

The team still needs to define its recovery point objective (RPO) and recovery time objective (RTO); no numeric commitment is established by this specification.

## 04.24.17 Post-incident review and prevention

The purpose of a post-incident review is to prevent recurrence, not to assign blame.

For SEV-1 and SEV-2 incidents, the team should conduct a documented review. Lower-severity incidents should receive a review when they reveal a repeated defect or a meaningful gap in the architecture.

### Review questions

1. What happened, and what evidence establishes the sequence?

2. Which users, devices, tasks or data were affected?

3. Why did existing controls fail to prevent or detect the problem?

4. Was the failure caused by code, configuration, deployment, infrastructure or an incorrect assumption?

5. Did the system report its state and uncertainty accurately?

6. Was recovery possible using the documented runbook?

7. Which tests, alerts or safeguards would have prevented or reduced the impact?

8. What changes are needed in the implementation, architecture or documentation?

Every corrective action should have an owner, priority, acceptance criteria and a corresponding test where applicable.

## 04.24.18 Implementation priorities

P0 — Required foundation

Safe incident response

- Incident severity and ownership.

- Backend, database and bridge recovery runbooks.

- Stuck-task and uncertain-operation recovery.

- Credential revocation and security incident handling.

- Deployment rollback and database restore procedures.

- Readiness gates before execution resumes.

P1 — Operational maturity

Faster diagnosis and consistent recovery

- Structured incident records.

- Recovery and reliability metrics.

- Tested host-loss and restore drills.

- Post-incident reviews and regression tracking.

- Clear incident communication and handoff procedures.

P2 — Future improvements

More advanced operations

- Automated incident correlation.

- Automated alerts and escalation.

- More comprehensive recovery automation.

- Centralized operational dashboards, if justified.

## 04.24.19 Definition of done

- Every major service failure has a documented runbook.

- The team can identify affected tasks and devices from persisted records.

- Backend and database outages do not cause false task acceptance or unsafe replay.

- Bridge disconnection and uncertain external effects are handled safely.

- Authentication failures and suspected compromise have a containment process.

- Failed migrations and deployments have a tested recovery strategy.

- Database restoration includes permission, credential and operation reconciliation.

- Readiness gates prevent unsafe execution after recovery.

- Incident records distinguish facts from hypotheses.

- The team has rehearsed representative failure and recovery scenarios.

- Corrective actions are tracked and important failures have regression tests.

Section exit criterion: the three-developer team can diagnose, contain, recover from and learn from major NEXUS failures without bypassing security controls or falsely claiming that external operations succeeded or were reversed.
