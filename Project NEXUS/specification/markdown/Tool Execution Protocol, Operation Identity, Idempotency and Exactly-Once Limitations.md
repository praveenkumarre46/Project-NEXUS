## 03.30.1 Purpose

NEXUS coordinates work across several independent components: the FastAPI backend, PostgreSQL, the AI runtime and a native Windows bridge on each user's computer. These components can fail independently, and network messages can be delayed, duplicated or lost.

This creates a fundamental reliability problem.

Suppose NEXUS asks a Windows bridge to create a file:

1. The backend sends the operation.

2. The bridge creates the file successfully.

3. The bridge sends a success response.

4. The response never reaches the backend.

5. The backend times out.

The backend knows the operation was dispatched, but it does not know whether the file was created.

If it retries blindly, it may duplicate a side effect. If it marks the operation failed, it may report an incorrect result.

NEXUS must treat operation delivery, execution and outcome recording as separate events. This section defines the protocol that makes that distinction explicit.

## 03.30.02 Core concepts and identifiers

NEXUS needs multiple identifiers because a task, a logical operation and an individual attempt are not the same thing.

| **Identifier** | **Meaning** | **Lifetime** |
| --- | --- | --- |
| task_id | One user request to NEXUS | Entire task lifecycle |
| step_id | One planned logical step within the task | Lifetime of that step |
| operation_id | One logical external operation | Stable across retries of the same operation |
| attempt_id | One attempt to deliver or execute an operation | New for each distinct attempt |
| bridge_request_id | Identifies a transport request or message | Depends on the transport protocol |
| device_id | Registered target Windows computer | Device registration lifetime |
| worker_id | Backend worker coordinating execution | Worker process or registration lifetime |

The identifiers must be opaque and unguessable where they cross trust boundaries. An ID is a correlation mechanism, not proof of authorization.

### Example

A user submits one task to create a report and open an approved application afterward.

- One task_id represents the overall request.

- The file creation has one step_id and one stable operation_id.

- If a retry is allowed, it reuses that logical operation identity while receiving a new attempt_id.

- Opening the application is a separate logical operation with its own operation identity.

The exact schema and identifier format remain implementation decisions. The separation of identities is a behavioral requirement.

## 03.30.03 The execution protocol

Each operation should follow a durable protocol.

1. Prepare

Validate the step, tool contract, arguments and dependencies.

2. Authorize

Check identity, device scope, policy and any required approval.

3. Persist intent

Commit the operation identity, arguments reference or snapshot, attempt and dispatch intent.

4. Dispatch

Send the authenticated, device-targeted operation to the bridge.

5. Execute and report

The bridge validates locally, executes the registered tool and returns a structured outcome.

6. Record and verify

Validate the response, persist the result and verify the required postcondition.

The intent must be durably committed before dispatch. Otherwise, the bridge could perform a side effect that the backend has no record of requesting.

The backend must not hold a PostgreSQL transaction open throughout network communication or tool execution. Persist intent in a short transaction, commit it, and then perform the external operation.

A timeout, process crash or lost response between these stages can leave the operation uncertain. Recovery must be designed around that possibility.

## 03.30.04 Operation contract

Every bridge operation must use a versioned, validated contract. The following is an illustrative envelope, not the final API schema.

{

"protocol_version": "1",

"operation_id": "stable-logical-operation-id",

"attempt_id": "unique-attempt-id",

"task_id": "parent-task-id",

"step_id": "logical-step-id",

"target_device_id": "registered-device-id",

"tool_name": "create_file",

"tool_schema_version": "1",

"arguments": {

"directory_id": "approved-workspace",

"relative_path": "report.txt",

"content": "Example report content"

},

"deadline": "2026-10-22T14:00:00Z"

}

The actual operation arguments must follow the registered tool's input schema. Unknown fields, unsupported protocol versions and invalid arguments must be handled according to a documented contract policy; security-sensitive unknown fields must fail closed.

The envelope is not trusted simply because it comes from the backend. The bridge must authenticate the caller and validate the target device, tool, arguments, permissions and local filesystem or application restrictions.

### Contract requirements

- The operation_id remains stable across attempts for the same logical operation.

- A new attempt_id identifies each distinct attempt.

- The target device must match the authenticated bridge registration.

- The tool name and schema version must be supported.

- Arguments must be validated against the registered tool contract.

- The deadline must be enforced using a defined clock and timeout policy.

- Credentials, passwords and unrelated private context must not be embedded in operation arguments.

- Retries must not silently change the logical operation's parameters.

If a planned operation changes materially—for example, creating a different file or using a different target directory—it is a new logical operation and requires fresh authorization and, when applicable, approval.

## 03.30.05 Idempotency and deduplication

An operation is idempotent when repeating it has the same intended effect as performing it once. Not all NEXUS tools have this property.

| **Tool or operation** | **Initial retry classification** | **Required behavior** |
| --- | --- | --- |
| search_files | Generally safe to retry | Repeat within scope and resource limits |
| read_document | Generally safe to retry | Repeat if the file is still permitted and available |
| create_file | Not blindly retryable | Check operation history and destination state before retrying |
| launch_application | Not automatically retryable | Reconcile whether the launch occurred; duplicate launches may matter |
| Unknown or newly registered tool | No default retry | Define and test its retry contract before enabling it |

Even a read-only operation can be expensive, observe changed data or expose new information, so retries still require authorization and resource limits.

### Bridge-side deduplication

The bridge should maintain a durable record of operations it has accepted and their known outcomes. For a repeated operation ID:

1. Verify that the incoming operation matches the original logical operation.

2. If a completed outcome is recorded, return the known outcome rather than executing it again.

3. If the operation is still in progress, report that status rather than starting a duplicate.

4. If the previous attempt has an uncertain outcome, initiate reconciliation where supported.

5. If the same operation ID arrives with different parameters or a different target, reject it.

The deduplication record should include the operation identity, a securely computed fingerprint of the relevant request, status and available outcome evidence. It should not need to retain complete private document content indefinitely.

Important limitation: deduplication prevents known duplicate executions. It does not by itself solve the crash window between performing an external side effect and durably recording its result.

## 03.30.06 Exactly-once execution: what NEXUS can and cannot promise

NEXUS must not promise exactly-once execution for arbitrary Windows operations across backend crashes, bridge crashes and network failures.

The backend database and an external Windows filesystem operation do not participate in one shared atomic transaction. A PostgreSQL commit cannot roll back a file that Windows has already created.

Instead, NEXUS should combine:

- Durable operation identity.

- At-least-once delivery where retry is appropriate.

- Deduplication of known duplicate requests.

- Tool-specific idempotency.

- Reconciliation of uncertain outcomes.

- Explicit uncertainty when reliable evidence is unavailable.

These mechanisms can provide strong practical reliability, but they cannot guarantee that every arbitrary external side effect happens exactly once.

### Example: file creation

### Case A — The bridge never received the operation

The backend has reliable evidence that dispatch did not reach the execution boundary.

Retry may be allowed under the operation's retry policy.

### Case B — The file was created, but the response was lost

The backend cannot infer failure from the timeout.

Reconcile the operation record and destination before considering another attempt.

### Case C — The bridge also crashed before recording the outcome

The operation record may not settle whether the side effect happened.

Inspect available evidence. If the result remains ambiguous, preserve UNCERTAIN and do not retry blindly.

### Can atomic file creation help?

Yes, within limits. For create_file, the bridge should use a safe create-if-absent approach where the platform and filesystem support it. The operation must not silently overwrite an existing file.

A unique operation-specific temporary file followed by an atomic rename may be useful for some workflows, but the precise behavior depends on the filesystem, target path and rename semantics. It must be designed and tested rather than assumed to be universally atomic.

The destination must be revalidated at execution time, and path checks must account for Windows path normalization and filesystem race conditions.

## 03.30.07 Operation fingerprints and immutable requests

For safe deduplication, the bridge and backend need to identify whether two deliveries represent the same logical operation.

A proposed fingerprint can cover:

- Tool name and schema version.

- Canonicalized arguments.

- Target device.

- Resource scope.

- Relevant execution options.

The fingerprint should be calculated from a deterministic representation. Secret values should not be exposed through diagnostic logs merely because they contribute to the fingerprint.

If the operation is already registered under the same operation_id, a fingerprint mismatch must be rejected. It must not silently replace the original operation.

An approval fingerprint and an execution fingerprint serve related but distinct purposes:

- Approval fingerprint: proves that the operation being executed matches the operation that was approved.

- Execution fingerprint: supports request consistency and deduplication across delivery attempts.

Both must be checked against trusted, validated data—not a fingerprint supplied by the AI model.

## 03.30.08 Deadlines, timeouts and retries

A deadline limits how long NEXUS is willing to wait for a stage or operation. It does not prove that the external operation stopped when the deadline passed.

Each tool contract must define:

- Maximum execution duration.

- Dispatch timeout.

- Result-wait timeout.

- Retry eligibility.

- Maximum attempts and total retry budget.

- Backoff behavior for transient failures.

- Reconciliation strategy.

- Final handling if the result remains uncertain.

### Retry rules

1. Retry only if the operation contract permits it.

2. Recheck task cancellation, device status, authorization and approval before dispatch.

3. Preserve the same logical operation ID when retrying the same operation.

4. Assign a new attempt ID for the new attempt.

5. Apply bounded backoff and retry budgets.

6. Reconcile uncertain side effects before another potentially consequential attempt.

7. Record each attempt's outcome independently from the overall logical operation.

The system should distinguish three different timeout conditions:

| **Condition** | **Interpretation** |
| --- | --- |
| Dispatch timeout | The request may or may not have reached the bridge |
| Execution timeout | The operation may still be running or may have completed |
| Result-recording timeout | The side effect may have happened even if its outcome was not durably recorded |

These conditions need not map to the same error code or recovery path.

## 03.30.09 Structured operation outcomes

The bridge should return a structured outcome that distinguishes execution status from certainty.

Proposed outcome fields:

| **Field** | **Purpose** |
| --- | --- |
| operation_id | Logical operation being reported |
| attempt_id | Attempt associated with the response |
| device_id | Authenticated target device |
| protocol_version | Protocol version used |
| status | SUCCEEDED, FAILED, REJECTED, RUNNING or UNCERTAIN |
| error_code | Stable machine-readable error when applicable |
| result_summary | Bounded, non-sensitive description of the result |
| evidence | Permitted verification metadata, where available |
| started_at / finished_at | Execution timing, where known |

This is a proposed contract, not a finalized wire schema.

A response must be authenticated and correlated with the operation before it changes task state. A validly authenticated bridge can still return an error, an incomplete result or an outcome that needs reconciliation.

### Outcome semantics

- SUCCEEDED: the tool reports success, and the backend's required verification conditions are satisfied.

- FAILED: failure is established, with no unresolved external side effect that could make a retry unsafe.

- REJECTED: validation or policy blocked the operation before execution.

- RUNNING: the bridge knows execution is in progress.

- UNCERTAIN: the available evidence cannot establish whether the operation succeeded or failed.

If a tool reports success but required verification cannot be completed, the backend must not automatically mark the overall task successful. It may need to keep the step unresolved or classify it as uncertain, according to the tool contract.

The backend must also distinguish the bridge's reported result from the backend's durable recording of that result. If persistence fails after receiving a response, recovery must use the operation identity and available evidence to reconcile the discrepancy.

## 03.30.10 Verification and reconciliation

Verification is tool-specific. There is no universal check that proves every external operation completed correctly.

| **Operation** | **Possible verification** |
| --- | --- |
| File search | Validate result structure and confirm results remain within authorized scope |
| Document read | Confirm extraction completed within configured limits and returned valid content |
| File creation | Confirm destination exists, is within the allowed workspace and matches expected operation metadata |
| Application launch | Confirm the process or launch result where practical; launching does not prove the user-facing application task is complete |

These are examples of verification approaches, not guarantees. Files can change after verification, processes can exit immediately after launch, and some effects may not expose reliable operation metadata.

### Reconciliation protocol

When the outcome is uncertain:

1. Locate the operation using its stable identity.

2. Check the bridge's durable operation record.

3. Check whether the bridge reports the operation as running.

4. Apply tool-specific external verification where supported.

5. Determine whether the operation is confirmed successful, confirmed failed, still running or unresolved.

6. Persist the reconciliation result and supporting evidence.

7. Retry only if the evidence and retry contract make that safe.

If no reliable evidence can resolve the result, NEXUS must preserve uncertainty and surface it to the user. A human recovery step may be necessary.

## 03.30.11 Bridge persistence and restart behavior

The Windows bridge needs enough local persistence to recognize duplicate operation deliveries and report known outcomes after a process restart.

The initial design should consider a local durable operation journal containing:

- Operation ID and request fingerprint.

- Task and step correlation IDs.

- Target tool and schema version.

- Accepted, running and terminal status.

- Attempt metadata.

- Known result or bounded result reference.

- Timestamps and reconciliation state.

The exact storage technology is open. A small local database is one candidate, but the team must validate durability, locking, permissions, cleanup and recovery behavior before choosing it.

### Bridge startup protocol

After restart, the bridge should:

1. Load and validate its local configuration.

2. Re-establish its authenticated device identity.

3. Report its capabilities and protocol version.

4. Load unresolved local operation records.

5. Report known outcomes and still-running or uncertain operations.

6. Reconcile with the backend before accepting duplicate or conflicting work.

7. Accept new operations only when its security and readiness checks pass.

The bridge must not assume that the backend's view is more current than its local evidence. Conversely, local records must not be trusted as authorization to execute new work.

### Retention of deduplication records

Deduplication records cannot be discarded while a task or retry may still refer to them. The retention policy should consider maximum task lifetime, retry window, recovery window and backup/restore behavior.

Once an operation is safely terminal and outside all retry or recovery windows, its detailed result may be eligible for cleanup under the retention policy. Minimal tombstones or operation identity records may need to remain longer to prevent a delayed duplicate delivery from being executed again.

The retention periods remain open until task lifetime and transport retry limits are finalized.

## 03.30.12 Security and authorization at the execution boundary

The operation protocol is also a security boundary. Correct deduplication does not make an unauthorized operation safe.

Before execution, the backend and bridge must independently enforce the controls applicable to their roles.

Backend checks

- The user owns the task or otherwise has explicit access.

- The target device is registered, active and authorized.

- The tool is registered and enabled.

- Arguments satisfy the approved tool schema.

- The current policy permits execution.

- Required approval is valid, unexpired and bound to the exact operation.

- The task is in a state that allows dispatch.

- Cancellation has not prevented the operation from starting.

Bridge checks

- The request came through the configured authenticated transport.

- The request targets this registered device.

- The protocol and tool schema are supported.

- The operation ID has not been reused with conflicting parameters.

- The tool is locally enabled.

- Filesystem and application restrictions permit the requested operation.

- Deadlines and resource limits are respected.

The bridge must not expose a generic command-execution endpoint to compensate for a missing tool. New tools require an explicit contract, risk classification, permissions, retry policy, verification strategy and tests.

A valid operation ID is not authorization. A valid approval is not permission to bypass a local restriction. A high-priority task is not entitled to bypass any of these checks.

## 03.30.13 Required fault-injection tests

These tests should be automated wherever practical and run against isolated test directories and test devices.

| **Failure injected** | **Required result** |
| --- | --- |
| Duplicate operation delivery | Known operation is returned or reconciled; no accidental duplicate side effect |
| Same operation ID, different arguments | Request is rejected |
| Backend crashes before dispatch | Operation remains recoverable; no false success |
| Backend crashes after dispatch | Recovery reconciles before an unsafe retry |
| Bridge executes a write but loses its response | Outcome is reconciled or remains explicitly uncertain |
| Bridge crashes after the side effect but before recording it | No blind retry; inspect evidence and preserve uncertainty if unresolved |
| Bridge receives an expired request | Enforce the documented deadline policy and do not bypass authorization |
| Approval expires before retry | No dispatch without a valid current authorization |
| Device credential is revoked | New unauthorized execution is denied |
| Old duplicate message arrives after completion | Deduplication prevents unintended re-execution |
| Result persistence fails | Backend does not invent a terminal outcome; recovery uses operation identity |
| Bridge returns a mismatched operation ID | Response is rejected and the discrepancy is recorded |
| Local file already exists | Create-only behavior does not silently overwrite it |
| Backend restores an older database backup | Potential external effects are reconciled before resuming |

Tests must verify the actual filesystem or application side effect, not just the backend status code. A test that returns an error while creating a duplicate file is still a failure.

## 03.30.14 Implementation priorities

P0

Required before real external operations

- Stable logical operation IDs and distinct attempt IDs.

- Durable execution intent before dispatch.

- Authenticated, versioned bridge contract.

- Duplicate-request detection and conflict rejection.

- Tool-specific retry and verification rules.

- Explicit uncertain outcomes.

- Recovery after backend and bridge crashes.

- Safe create-only file behavior.

P1

Reliability improvements

- Durable bridge operation journal.

- Automated reconciliation for supported tools.

- Deduplication retention and cleanup.

- More complete execution evidence and diagnostics.

P2

Future extensions

- More advanced operation recovery across multiple hosts.

- Tool-specific compensation workflows where they are demonstrably safe.

- Stronger reconciliation for complex interactive applications.

## 03.30.15 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| Operation and attempt ID formats | Open |
| Bridge transport and delivery guarantees | Polling is the provisional preference; final protocol open |
| Local bridge journal technology | Open |
| Operation-record retention | Open |
| Maximum retry window | Open |
| Tool-specific timeout defaults | Open |
| File-creation verification | Must be specified and tested |
| Atomic file-creation strategy | Platform and filesystem dependent |
| Reconciliation evidence | Defined separately for each tool |
| Handling permanently uncertain operations | Preserve uncertainty; escalation workflow open |
| Response and result size limits | Define per tool |
| Protocol and tool-schema version policy | Versioned contracts required; exact rules open |

## 03.30.16 Definition of done

## Section 03.30 is ready for implementation when:

- Task, step, operation and attempt identities are distinct.

- Every operation has a defined input contract and execution policy.

- Execution intent is durably recorded before dispatch.

- Duplicate deliveries and conflicting reuse of operation IDs are handled safely.

- Tool retry rules distinguish safe retries from uncertain side effects.

- Backend and bridge restart behavior is documented and tested.

- Required verification and reconciliation are defined for every MVP tool.

- The bridge persists enough evidence to recognize known duplicate operations.

- Authorization is revalidated at execution boundaries.

- The team explicitly documents that exactly-once execution cannot be guaranteed for arbitrary external side effects.

- Fault-injection tests verify both durable state and real side effects.

Recommended engineering decision: use stable operation IDs, distinct attempt IDs, durable intent, bridge-side deduplication, tool-specific verification and explicit uncertainty. Do not claim exactly-once execution; make retries safe where possible and make unresolved outcomes visible everywhere else.
