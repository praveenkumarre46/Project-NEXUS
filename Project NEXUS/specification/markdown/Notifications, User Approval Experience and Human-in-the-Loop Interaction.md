## 04.18.01 Purpose

NEXUS needs a reliable way to involve users when a task requires a decision, encounters a problem or finishes executing.

The interaction system must answer five questions:

1. What happened? The current, persisted task state.

2. What needs my attention? Approval, clarification, recovery or another action.

3. What exactly am I approving? The specific operation, destination and consequences.

4. What happens if I do nothing? Whether the task waits, expires or remains interrupted.

5. How do I know my decision took effect? The recorded decision and subsequent task state.

The initial interface remains terminal-first. NEXUS should not require a web dashboard, desktop notification service or mobile application to complete the core workflow.

Core principle: notifications communicate state; they do not grant permissions. An approval must be validated by the backend and execution boundary regardless of how the user received or submitted it.

## 04.18.02 Interaction categories

NEXUS should distinguish notifications by the action they require.

Approval required

A particular operation cannot proceed until an authorized user approves it. The task remains in the relevant waiting state.

Clarification required

NEXUS lacks information needed to create a valid plan, such as which document or target device the user intends.

Blocked or recovery required

A device is unavailable, a dependency failed, an operation has an uncertain outcome or a safe recovery decision is needed.

Completion or failure

The task has reached a recorded outcome. The CLI reports the outcome and provides access to its steps, results and artifacts.

These categories are not all separate task states. A notification is a user-facing representation of an underlying task, approval or recovery condition.

## 04.18.03 Notification delivery strategy

### MVP decision proposal

Use the CLI and persisted backend state as the authoritative notification channel.

- Display an immediate response after a task is accepted.

- Show approval or clarification requirements when they arise.

- Allow the user to inspect waiting tasks with a command.

- Provide optional task watching through polling.

- Make notifications retrievable after the CLI exits or the backend restarts.

- Do not depend on a continuously open terminal to preserve notifications.

Proposed commands:

nexus tasks

nexus task <task-id>

nexus task <task-id> --watch

nexus approvals

nexus approve <approval-id>

nexus reject <approval-id>

nexus cancel <task-id>

These are illustrative command names; they must be aligned with the CLI contract already defined in Section 03.16 before implementation.

### Delivery versus state

The backend's persisted records are authoritative. A notification being printed does not prove the user received it, and a notification being missed does not remove the underlying approval requirement.

For example, if an approval becomes pending while the user's terminal is closed, the approval must still be visible when the user returns and inspects pending tasks.

The initial implementation does not need a separate notification broker. Persisted task and approval records can support CLI polling. A separate delivery service should be considered only if a concrete need emerges.

## 04.18.04 Approval request contract

An approval request must describe one exact proposed operation. Generic prompts such as “NEXUS wants permission to continue” are insufficient for consequential actions.

A logical approval record should contain:

| **Field** | **Purpose** |
| --- | --- |
| approval_id | Unique identifier for the decision request |
| task_id and step_id | Identify the operation requiring approval |
| requester_user_id | Identifies the task owner or requesting user |
| target_device_id | Identifies the computer where the operation would run |
| tool_name and tool_schema_version | Identify the registered operation |
| operation_fingerprint | Binds approval to the normalized operation |
| risk_tier | Records the policy-computed risk classification |
| reason | Explains why approval is required |
| created_at and expires_at | Define the approval's validity window |
| decision and decided_at | Record the user's decision |
| policy_version | Supports validation against the applicable policy |

These are logical fields, not a finalized database schema. The backend must derive the authoritative user, device, risk and policy information rather than trusting values supplied by the CLI or model.

### What the user must see

Before deciding, the user should be able to inspect:

- The task and intended outcome.

- The exact action to be performed.

- The target device.

- The logical resource scope and relevant destination.

- The filename or other important arguments, where applicable.

- Whether existing data could be changed.

- Why approval is required.

- When the request expires.

- What will happen if the user approves, rejects or takes no action.

The displayed details must describe the actual operation fingerprinted by the backend. The CLI must not reconstruct approval details from an outdated plan or an untrusted model response.

## 04.18.05 Approval interaction design

An approval interaction should be explicit and difficult to misinterpret.

## Example: file overwrite request

Illustrative approval screen — not a real pending request.

Proposed operation

Replace an existing report in the approved workspace.

Target

my-windows-pc

Destination

approved_workspace/monthly-report.txt

Consequence

Existing file contents could be replaced.

Reason for approval

The operation may overwrite existing user data.

No operation should execute merely because this screen is displayed. The backend must validate the decision and recheck policy before dispatch.

### Decision behavior

- Approve: records the decision for the exact operation. It does not guarantee that execution will succeed or that the operation remains authorized.

- Reject: records the rejection and prevents dispatch of that operation.

- Expire: prevents dispatch under that approval. The task follows the defined expiration policy.

- Cancel task: stops future eligible work and reconciles any in-flight external operations.

- Inspect: shows the request without changing its state.

A user must not be able to approve an operation by changing its target, arguments or risk-relevant properties after reviewing it.

### Approval expiry

An approval expiration period is still an open decision. The team should choose a default based on expected usage and the consequences of stale consent.

The implementation must support an explicit expiry timestamp even before a default duration is finalized. Once expired, an approval cannot authorize a new dispatch. A renewed request requires a new valid approval and any necessary policy revalidation.

## 04.18.06 Approval state machine and concurrency

Proposed approval states:

- PENDING

- APPROVED

- REJECTED

- EXPIRED

- INVALIDATED

The following rules are required:

1. Only a pending, unexpired approval can receive a decision.

2. A decision is recorded atomically; two concurrent decisions cannot both become authoritative.

3. An approved operation must still pass authorization, capability and policy checks immediately before dispatch.

4. A changed operation invalidates the previous approval.

5. A cancelled task cannot be revived by a late approval.

6. A revoked user or device cannot continue through a stale approval.

7. A duplicate submission of the same decision must return the recorded outcome rather than execute the operation again.

8. A rejection or expiration must never be interpreted as permission to proceed.

### Race-condition example

Suppose an approval is pending while the user cancels the task. At nearly the same time, another request approves the operation.

NEXUS must serialize or otherwise safely coordinate the competing transitions. The authoritative task state and approval state determine whether dispatch remains possible. If cancellation has made the task ineligible, the approval cannot revive it.

Database transactions should protect the decision and related state transitions. The system must not keep a database transaction open while waiting for a person to respond.

## 04.18.07 Clarification requests

Clarification is different from approval. Approval asks whether an authorized operation may proceed; clarification asks what the user actually intends.

Examples:

- Several matching documents exist, and NEXUS cannot determine which one is relevant.

- The user has not specified a target device and no configured default applies.

- The destination is ambiguous.

- The requested file format is unsupported or unspecified in a way that affects the result.

- Two interpretations would lead to materially different actions.

### Clarification rules

- Ask the smallest question that resolves the ambiguity.

- Show enough context for the user to answer accurately.

- Preserve the task ID and previously verified work where possible.

- Do not execute the ambiguous operation while waiting.

- Revalidate the plan after receiving the answer.

- Request fresh approval if the clarified operation changes an approval-bound property.

- Expire or abandon unresolved requests according to an explicit task policy.

A clarification response must not automatically grant permissions. For example, selecting a destination does not grant permission to overwrite files in that destination.

### Example

Task: task-456

Status: WAITING_FOR_CLARIFICATION

I found three matching documents:

1. design-v1.pdf

2. design-v2.pdf

3. design-final.pdf

Which document should I use?

No document has been modified.

The final statement should be displayed only if the recorded execution state supports it.

## 04.18.08 Blocked tasks and recovery decisions

Not every blocked task needs human approval. Some tasks simply need a dependency to become available or an uncertain operation to be reconciled.

NEXUS should distinguish the cause and provide an appropriate next action.

| **Condition** | **User-facing behavior** |
| --- | --- |
| Target device offline | Explain that the task remains bound to the original device |
| Model runtime unavailable | Report that planning or generation cannot continue |
| Approval expired | Explain that the operation was not authorized under the expired approval |
| Required step failed | Show the failure and dependent steps that could not proceed |
| External effect uncertain | Explain what is unknown and that blind retry is unsafe |
| Resource limit reached | Report whether the task is queued, blocked or rejected |
| Permission revoked | Explain that authorization is no longer valid without exposing protected details |

### Recovery decisions

Where possible, NEXUS should offer a safe, specific next action, such as:

- Inspect the task's last confirmed step.

- Check the target device's connection.

- Reconcile an operation before retrying.

- Submit a revised request.

- Cancel remaining work.

- Request new approval for a revised operation.

The system must not treat a generic “continue” action as permission to bypass a failed precondition, retry an uncertain side effect or expand the task's original scope.

## 04.18.09 Notification records, deduplication and delivery guarantees

Notifications should be recoverable, but repeatedly displaying the same event should not cause duplicate operations or confusing prompts.

### Proposed notification record

A logical notification record may include:

- notification_id

- user_id

- task_id, where applicable

- approval_id, where applicable

- event_type

- created_at

- read_at, if read tracking is implemented

- delivery_status, if a separate delivery channel is introduced

The backend's task and approval records remain authoritative. Notification records are delivery and presentation metadata, not an alternative source of task state.

### Deduplication rules

- Repeated polling should not create duplicate approval requests.

- Repeated notification delivery should not execute or approve anything.

- A completed task should not repeatedly appear as actively waiting.

- A notification referring to a resolved approval should show the current decision.

- Stale notifications must lead to a fresh state lookup before a decision is applied.

- Read/unread status must never determine whether an operation is authorized.

For the initial CLI, notification delivery can be reconstructed from persisted task and approval records. A separate notification-event table is optional until read tracking, multiple delivery channels or stronger delivery guarantees justify it.

### Future channels

Desktop notifications, email or other channels may be considered later. If introduced, these channels should alert users that attention is required, then direct them to an authenticated NEXUS interface for the authoritative operation details and decision.

A notification payload alone must never function as an approval token or grant permission to execute an operation.

## 04.18.10 Human-in-the-loop policy

Human involvement should be based on the operation's risk and the permissions already configured, not on how confidently the AI describes the request.

| **Situation** | **Proposed behavior** |
| --- | --- |
| Permitted read-only search | Proceed without per-operation approval when the existing grant covers it |
| Create a new file in an approved workspace | Proceed only within the configured permission and create-only policy |
| Overwrite or move important data | Require approval if that operation is supported at all |
| Access another user's private data | Deny under the initial isolation model |
| Execute an unknown tool | Deny |
| Run arbitrary model-generated shell commands | Prohibited |
| Perform an operation with unresolved authorization | Do not dispatch |
| Continue after an uncertain external side effect | Reconcile before deciding whether retry is safe |

These are proposed defaults aligned with the existing autonomy and security model. They do not add new tool capabilities.

### Avoid approval fatigue

Requiring approval for every harmless operation can make the system frustrating to use. Conversely, asking for approval too rarely can make it unsafe.

NEXUS should therefore:

- Respect configured permissions for low-risk operations.

- Request approval when policy requires it.

- Explain why the request is necessary.

- Avoid repeatedly asking for a decision already recorded for the same unchanged operation.

- Never turn one approval into blanket permission for unrelated future operations.

- Never allow the AI to lower the required risk tier.

An approval is consent for a specific operation under specific conditions, not a permanent grant of authority.

## 04.18.11 Privacy and notification security

Notifications can expose private information when displayed on shared screens, copied into terminal logs or sent to external channels.

Required controls:

- Include only the information necessary to explain the event.

- Do not put passwords, tokens or other secrets into notification text.

- Avoid including full document contents in routine notifications.

- Apply user and task authorization before returning detailed notification records.

- Do not disclose another user's task names, file paths or approval details.

- Avoid placing sensitive arguments in shell command history when possible.

- Ensure logs record decision metadata without unnecessarily copying private content.

- Recheck authorization when a user opens an old notification.

- Do not let an old notification bypass device revocation, approval expiry or policy changes.

The CLI should provide a concise explanation by default, with a separate authenticated inspection command for authorized detail.

## 04.18.12 Testing strategy

| **Test** | **Expected behavior** |
| --- | --- |
| Pending approval after CLI exits | Request remains available on the next inspection |
| Approval with changed arguments | Original approval is invalidated or rejected |
| Two simultaneous decisions | Only one authoritative transition is recorded |
| Approval after expiry | No dispatch occurs |
| Approval after cancellation | Task is not revived |
| Device revoked while approval is pending | Dispatch is blocked |
| Duplicate approval command | Recorded decision is returned without duplicate execution |
| Repeated polling | No duplicate logical notifications or approvals |
| Clarification response changes destination | Plan is revalidated; new approval required if applicable |
| User requests another user's approval | Access denied |
| Device disconnects during execution | In-flight outcome follows reconciliation rules |
| Notification channel is unavailable | Persisted task and approval states remain inspectable |
| Model produces a misleading approval explanation | Authoritative operation details and policy remain unchanged |
| Approval service or policy is unavailable | Consequential dispatch fails closed |
| Task has a partial result | Notification accurately reports the partial outcome |
| User stops watching a task | Task execution is unaffected unless separately cancelled |

The tests should cover API and database concurrency, CLI behavior, device disconnection and restart recovery. Security-critical tests must verify actual dispatch behavior, not merely that the interface displays a warning.

## 04.18.13 Work packages and ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Approval lifecycle and atomic decisions | Developer 1 | Persisted approval state machine |
| CLI interaction and task inspection | Developer 1 | Consistent commands and status display |
| Device-side dispatch enforcement | Developer 2 | Bridge rejects unauthorized or stale operations |
| Clarification and plan revision | Developer 3 | Structured clarification and validated revised plans |
| Notification wording and outcome summaries | Developer 3 | Accurate, concise user-facing explanations |
| Race-condition and security testing | All three | Approval, cancellation, revocation and retry tests |

Shared contracts must be agreed before parallel implementation. In particular, the approval record, operation fingerprint, task-state transitions and bridge dispatch protocol must use consistent semantics.

## 04.18.14 Implementation priorities

P0 — Required foundation

Safe, reliable decisions

- Persisted approval requests and decisions.

- Exact-operation approval binding.

- Expiration, rejection and cancellation handling.

- CLI task and approval inspection.

- Atomic decisions and pre-dispatch revalidation.

- Honest blocked, partial and uncertain status reporting.

P1 — Better interaction

Clear and recoverable user experience

- Structured clarification requests.

- Notification deduplication and read tracking if needed.

- More useful recovery guidance.

- Improved task watching and result notifications.

- Privacy and usability testing.

P2 — Future channels

Optional notification delivery

- Native Windows desktop notifications.

- Additional delivery channels.

- Richer interactive terminal interface.

- Notification preferences and delivery analytics.

## 04.18.15 Open decisions

| **Decision** | **What must be established** |
| --- | --- |
| Approval expiry duration | Expected task duration and risk of stale consent |
| Who may approve | Initial owner-only rule and any future delegated roles |
| Clarification timeout | Behavior for tasks awaiting user input |
| Notification persistence | Whether task records alone are sufficient for the MVP |
| Task watching interval | Responsiveness versus API and database load |
| Approval invalidation | Behavior after policy, permissions or tool definitions change |
| Desktop notifications | Whether they add enough value to justify the additional integration |
| Audit retention | How long approval and notification decision metadata remains available |

## 04.18.16 Definition of done

- Users can inspect pending approvals after reconnecting or restarting the CLI.

- Approval screens identify the exact operation, target and relevant consequences.

- Approvals are bound to normalized operations and cannot be reused after material changes.

- Expiration, rejection, cancellation and revocation prevent unauthorized dispatch.

- Concurrent approval decisions cannot create conflicting authoritative states.

- Clarification is distinct from authorization.

- Notifications reflect persisted task and approval state.

- Missing notification delivery does not lose task state.

- Notification records and details are access-controlled.

- Security and failure-injection tests pass.

Section exit criterion: users can understand and control NEXUS's consequential actions through a reliable, recoverable terminal workflow without weakening authorization or task-state guarantees.
