## 03.38.1 Purpose

NEXUS is a terminal-first computer companion. Its interface must make it easy to express a goal, understand what the system intends to do, monitor progress, respond to approval requests and inspect the outcome.

The interface must not hide important uncertainty behind conversational confidence. A friendly response is useful, but the persisted task state and verified execution evidence are the source of truth.

This section defines the user-facing interaction model across the CLI, backend task lifecycle, approvals, context and errors.

The design should support two complementary interaction styles:

- Natural-language requests: users describe the outcome they want.

- Explicit commands: users inspect devices, tasks, approvals, history, memory and diagnostics.

Natural language is the entry point for computer assistance, not a replacement for precise administrative controls.

## 03.38.2 Core UX principles

1. Make the next action obvious. The user should know whether NEXUS is working, waiting, blocked or finished.

2. Distinguish acceptance from completion. Receiving a task ID means the request was recorded, not that the work is finished.

3. Expose consequential actions before execution. Approval requests show the exact operation and target.

4. Be honest about uncertainty. An unknown outcome must not be presented as success or failure without evidence.

5. Keep user control available. Users can inspect tasks, cancel work, review memory and understand permissions.

6. Prefer useful details over noisy logs. Show the current step, important events and actionable errors; provide detailed diagnostics separately.

7. Keep terminal automation scriptable. Machine-readable output must be stable and free of decorative output on standard output.

8. Do not make security depend on interface wording. Approval prompts and displayed task details support—not replace—backend and bridge enforcement.

## 03.38.3 Primary interaction flow

A typical task should follow a predictable sequence.

1. Request

The user describes the desired result and target computer.

2. Acceptance

NEXUS validates the request and persists it, returning a task ID.

3. Plan or clarification

NEXUS builds a bounded plan, validates it, or asks a focused question.

4. Execute or wait

Authorized steps run; consequential actions wait for required approval.

5. Verified result

NEXUS reports completion, failure, cancellation, partial success or uncertainty.

A clarification request may occur before a valid plan exists. An approval request may occur after a plan has been validated. These are different conditions and should not be displayed as if they were the same task state.

## 03.38.4 CLI command design

The command names below are proposed and should be aligned with the API contract from Section 03.16 before implementation.

| **Command** | **Purpose** |
| --- | --- |
| nexus login | Authenticate the user |
| nexus logout | End the current session |
| nexus devices | List devices the user is authorized to access |
| nexus run | Submit a natural-language task |
| nexus task <task-id> | Inspect a task's current state |
| nexus task <task-id> --watch | Follow task progress |
| nexus task <task-id> --steps | Inspect step-level execution |
| nexus task <task-id> --result | Display the stored result |
| nexus cancel <task-id> | Request task cancellation |
| nexus approve <task-id> <approval-id> | Submit an approval decision |
| nexus reject <task-id> <approval-id> | Reject an approval request |
| nexus history | List authorized task history |
| nexus memory list | List authorized memories |
| nexus memory show <memory-id> | Inspect a memory |
| nexus memory delete <memory-id> | Request memory deletion |
| nexus status | Show service, device and task-system status |
| nexus diagnostics | Run bounded, privacy-safe diagnostics |

These commands should have documented argument rules, exit codes and error behavior. The examples are a proposed interface, not evidence that these commands already exist.

### Command-line behavior rules

- Commands that operate on a task must verify ownership and authorization.

- A user's default device may be supported as a convenience, but NEXUS must display the resolved target and must never silently switch devices.

- --watch controls the local display only; stopping it does not cancel the task.

- cancel requests cancellation. The user must inspect the task state to establish whether cancellation actually completed.

- Approval commands must reference the specific pending approval and remain subject to backend validation.

- Memory inspection and deletion must apply the same ownership rules as memory retrieval.

- Unknown commands and invalid arguments should produce a useful error and usage guidance.

- Standard output should contain the requested result; progress and diagnostics should go to standard error where appropriate.

## 03.38.5 Natural-language request handling

The run command should support natural-language goals without making users learn the internal tool registry.

An illustrative command:

nexus run "Find the latest design document and summarize it" \

--device my-windows-pc

The CLI submits the request and receives a durable task identifier if acceptance succeeds.

Example response:

Request accepted

Task ID: task_abc123

Target: my-windows-pc

Status: QUEUED

Track progress:

nexus task task_abc123 --watch

The identifiers and formatting are illustrative only.

### Request-handling rules

- Do not claim a task was accepted until the backend confirms durable acceptance.

- If the backend is unavailable, report that acceptance could not be confirmed.

- If the request is ambiguous, ask a focused question before taking a consequential action.

- If the requested capability is unsupported, explain the limitation honestly.

- Do not make the user repeat context that is already available and authorized.

- Do not silently convert a vague request into a broader or more consequential operation.

- If the request exceeds configured planning or execution limits, explain the limit and offer a narrower supported approach.

The user should be able to distinguish three outcomes: request not accepted, request accepted but not completed, and task completed with verified results.

## 03.38.6 Plan visibility and informed approval

For straightforward, low-risk operations already covered by the user's permissions, NEXUS should avoid unnecessary interruptions. For consequential operations, the interface must expose enough detail for an informed decision.

A proposed approval display:

### Approval required

Illustrative terminal preview

Task

Create a report in the approved workspace.

Target device

my-windows-pc

Proposed operation

Create a new file named report.txt containing the generated report.

Destination

The resolved approved workspace, with the destination shown clearly enough to identify it.

Existing-file behavior

Do not overwrite an existing file.

Approval details

The precise operation, relevant parameters, consequences and expiry must be visible.

Decision

Approve or reject through the supported CLI.

The real interface must show the actual resolved destination and the exact operation being approved, not generic placeholder wording. It should identify any meaningful irreversible consequences and the approval's expiry.

The approval must be bound to the validated operation, target device, arguments, resource scope and policy requirements. If any material detail changes, NEXUS must revalidate the operation and obtain a new approval when required.

The UI cannot authorize an action merely by displaying an approval prompt. The backend and Windows bridge must independently enforce the relevant rules.

## 03.38.7 Progress and task transparency

Users should not have to inspect server logs to understand the progress of ordinary tasks.

The CLI should show the current task state, current step, completed steps, blocked steps, any required user action and the most recent meaningful event.

Illustrative progress display:

Task: task_abc123

Status: RUNNING

Target: my-windows-pc

Steps:

[done]   Find matching document

[done]   Read document

[active] Generate summary

[pending] Create summary file

Last event:

Summary generation started

The status of a step must come from persisted task records, not from a model-generated progress message.

### Progress display requirements

- Show only progress that the backend can substantiate.

- Do not invent percentage completion when no defensible estimate exists.

- Distinguish waiting for approval from waiting for a device or dependency.

- Distinguish a running operation from a dispatched operation whose execution is not confirmed.

- Show partial success when some steps succeeded and others failed.

- Preserve the ability to inspect individual steps and structured errors.

- Avoid flooding the terminal with repeated polling output.

- Ensure that a terminal disconnect or interrupted --watch command does not change task state.

Polling is the proposed initial approach. Server-sent events or WebSockets can be introduced later if measured latency or usability justifies their complexity.

## 03.38.8 Results, partial success and uncertainty

The final response must accurately describe what happened, including when only part of the requested task was completed.

| **Outcome** | **What NEXUS should communicate** |
| --- | --- |
| Success | The requested outcome was verified, with relevant results or references |
| Failure | What failed, the last confirmed state and a useful next step |
| Partial success | Which steps succeeded, which failed and what remains unresolved |
| Cancellation | Whether cancellation was requested and whether the task reached a confirmed cancelled state |
| Uncertain outcome | What may have happened, what evidence is available and why the result cannot yet be confirmed |
| Unsupported request | Which capability is missing and what narrower supported action may be possible |

For example, if NEXUS reads a document and generates a summary but cannot establish whether the output file was created, it must not report the entire task as successful. It should report the completed work and clearly mark file creation as uncertain.

Results should include, when applicable:

- Task ID and final state.

- Target device.

- Completed, failed, skipped and uncertain steps.

- Output references or approved destination details.

- Stable error code and human-readable explanation.

- Any remaining user action.

- Relevant timestamps and verification evidence.

Large outputs should be bounded and retrievable through a dedicated result command. NEXUS should avoid placing entire document contents into terminal history or logs unnecessarily.

## 03.38.9 Conversation context and task continuity

NEXUS needs enough context to support follow-up requests without confusing previous work with the current task.

Consider this interaction:

1. User: “Find the latest design document.”

2. NEXUS: Returns two matching candidates.

3. User: “Use the second one and summarize it.”

4. NEXUS: Resolves “the second one” against the previous authorized result and continues, if the reference remains valid.

The system must not assume that every short follow-up refers to the most recent task. If multiple plausible references exist, it should ask for clarification.

### Proposed context-resolution order

1. Current explicit user instruction.

2. Explicit references to a task, device, document or other resource.

3. Relevant state from the active interaction.

4. Authorized, relevant task history.

5. Relevant personal or project memory.

6. Clarification if ambiguity remains material.

This is a proposed resolution order, not an authorization hierarchy. No context source overrides access controls, hard prohibitions or current policy.

Additional requirements:

- Task state is read from the backend's persisted records.

- A document reference must be revalidated before a new read or write operation.

- Memory is used only when relevant and authorized.

- Old approvals are not inherited by a new or materially changed operation.

- A follow-up request does not automatically authorize repeating a consequential action.

- The user must be able to explicitly name a task when continuity is ambiguous.

## 03.38.10 Error messages and recovery guidance

Errors should explain the immediate problem without leaking secrets, private data or internal stack traces.

A useful error message has three parts:

1. What happened: a concise, accurate description.

2. What it means: whether the task is blocked, failed or uncertain.

3. What the user can do: a safe, specific next step where one exists.

Illustrative examples:

DEVICE_UNAVAILABLE

The target computer is offline.

The task has not been redirected to another device. Check the Windows bridge and reconnect the original computer before retrying.

APPROVAL_REQUIRED

This operation is waiting for your approval.

Inspect the proposed operation and approve or reject it using the associated task and approval identifiers.

OPERATION_OUTCOME_UNCERTAIN

The operation may have completed, but NEXUS could not verify the result.

The system will reconcile the operation before attempting an unsafe retry. Do not assume that the requested change did not occur.

The examples illustrate the desired tone and structure; the precise wording and recovery instructions must match the implemented behavior.

Machine-readable error codes should remain stable even if human-readable messages change. Detailed diagnostics may be available through an authorized command, but ordinary error output should not reveal database credentials, authentication tokens, private prompts, unrestricted paths or internal exception details.

## 03.38.11 Interactive and machine-readable output

NEXUS should support both interactive human use and scripts that consume its results.

### Human-readable mode

The default mode should display concise status information, helpful explanations, approval prompts and readable results. Color and terminal formatting may improve readability, but the CLI must still function in terminals that do not support them.

### Machine-readable mode

A proposed option is --output json for commands that return structured data.

Requirements:

- Standard output contains valid JSON without banners, progress bars or unrelated text.

- Diagnostics and progress go to standard error where appropriate.

- Output schemas are documented and versioned.

- Timestamps use a consistent UTC representation.

- IDs and status enums remain stable within the documented contract.

- Sensitive fields are omitted or redacted according to authorization and output policy.

- Exit codes distinguish successful retrieval, validation errors, authorization failures and operational failures where practical.

Example result shape:

{

"task_id": "task_abc123",

"status": "SUCCEEDED",

"outcome": "success",

"target_device_id": "registered-device-id",

"result": {

"summary_file_created": true

},

"error": null

}

This is illustrative, not the final API schema. A real result must be generated from persisted, verified execution records. The CLI must not synthesize success based on the AI's narrative.

## 03.38.12 Accessibility, usability and operational safety

Although NEXUS is terminal-first, the interface must be practical for different terminals, shell environments and user preferences.

Proposed requirements:

- Support ordinary keyboard-driven workflows.

- Do not require color to distinguish success, failure, approval or uncertainty.

- Use concise default output and provide detailed inspection commands.

- Avoid requiring users to remember opaque identifiers when a safe task-listing command can help them select the correct item.

- Clearly distinguish a task ID from an approval ID, device ID or memory ID.

- Do not echo secrets or sensitive input into terminal history unnecessarily.

- Require explicit confirmation for destructive local CLI actions where applicable.

- Never interpret terminal display text as a substitute for server-side authorization.

- Keep help text, examples and error messages aligned with actual implemented behavior.

A command that changes permissions, revokes a device or deletes memory should explain the effect and apply the defined authorization and confirmation rules. For non-interactive scripts, confirmation requirements must have explicit behavior rather than silently defaulting to approval.

## 03.38.13 Testing and acceptance criteria

### CLI tests

- Valid and invalid command arguments.

- Authentication expiry and denied access.

- Correct exit codes and stable error responses.

- Valid JSON output with no terminal decorations on standard output.

- Interrupted watch session without task cancellation.

- Cancellation request followed by status verification.

- Approval for an incorrect or expired operation is rejected.

### User-experience tests

- A newly accepted task returns an identifier and clear status.

- A clarification request identifies the missing information.

- An approval displays the exact operation and target.

- Progress matches persisted backend state.

- Partial success is reported accurately.

- Uncertain outcomes are never presented as confirmed success.

- Unsupported operations receive honest explanations.

- Follow-up references resolve correctly or trigger clarification.

### Multi-user tests

- Task, memory and device results respect authorization.

- A user cannot act on another user's task through CLI commands.

- Context from concurrent requests remains isolated.

- Machine-readable results do not expose unauthorized fields.

### Proposed usability evaluation

Use a small, repeatable set of real tasks with all three developers. Observe whether users can:

- Submit a task and find its current status.

- Understand why a task is blocked.

- Make an informed approval decision.

- Identify a partial or uncertain result.

- Recover from a common failure without needing to inspect server logs.

The team should record observed confusion and errors rather than assuming that technically correct output is automatically usable.

## 03.38.14 Implementation priorities

| **Priority** | **Scope** |
| --- | --- |
| P0 — Initial release | Request submission, task IDs, status inspection, progress, approval/rejection, cancellation requests, history, stable errors and truthful results |
| P1 — Better interaction | Context-aware follow-ups, richer progress reporting, improved result inspection and consistent JSON output |
| P2 — Advanced UX | Optional interactive terminal interface, richer task visualization, configurable notifications and advanced workflow navigation |

The initial release must include task transparency and the essential approval/cancellation workflow. These are safety and reliability requirements, not cosmetic improvements.

### Proposed ownership

- Developer 1: CLI/API contract, task status, progress, errors and result consistency.

- Developer 2: device selection, device diagnostics and accurate reporting of Windows-side outcomes.

- Developer 3: clarification behavior, context resolution, model-generated explanations and evaluation of response accuracy.

- All developers: test real end-to-end workflows and ensure the displayed status agrees with persisted execution evidence.

## 03.38.15 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| Default CLI output | Human-readable |
| Structured output | JSON mode proposed |
| Progress updates | Polling initially |
| Approval interaction | Explicit CLI commands, bound to exact operation |
| Device selection | Explicit target or clearly displayed configured default |
| Follow-up context | Resolve from authorized active context; clarify ambiguity |
| Terminal color and formatting | Optional; never required for meaning |
| Notification system | Not required for initial release |
| Interactive terminal UI | Deferred unless user testing demonstrates a need |
| Error-code and exit-code catalog | Finalize with API and CLI contracts |

## 03.38.16 Definition of done

- The terminal workflow from request to verified result is documented.

- Accepted tasks return durable identifiers and accurate statuses.

- Clarification, approval, cancellation and uncertainty have distinct behaviors.

- Progress and final results reflect persisted task and step records.

- The CLI supports the essential task, device, history and memory operations.

- Machine-readable output is stable and scriptable.

- Error messages are actionable without exposing sensitive information.

- Follow-up requests use authorized context and handle ambiguity safely.

- All three developers can complete representative tasks and diagnose common failures.

- End-to-end tests verify that the user-facing result matches the actual execution outcome.

Section exit criterion: a user can understand what NEXUS is doing, what it needs from them, what actually happened and what to do next—without relying on unsupported claims from the AI model.
