## 03.36.1 Purpose

This section defines how NEXUS should interact with Windows applications, and where the boundary lies between launching an application and actually completing work inside it.

NEXUS must distinguish three different capabilities:

1. Application launching: opening an approved application.

2. Application-specific operations: performing supported actions through a documented API, command interface or registered integration.

3. Interactive desktop automation: inspecting and manipulating a visible application's interface through controls, keyboard, mouse or accessibility interfaces.

These capabilities are not interchangeable. Successfully opening Notepad does not mean NEXUS has written, saved or verified a document. Similarly, clicking a button does not prove that the intended operation succeeded.

The initial design should prioritize reliable, narrowly scoped tools. Broad GUI automation should be added only when it solves an important use case that cannot be handled adequately by the existing tools.

## 03.36.2 Scope and release recommendation

Initial release — include

- Launch approved applications.

- Search and read permitted files.

- Create new files in an approved workspace.

- Verify operation outcomes and report failures honestly.

Later phase — evaluate

- Read application accessibility trees.

- Interact with specific supported UI controls.

- Enter text and navigate defined workflows.

- Verify visible application state after an action.

Excluded from the initial release

- Unrestricted mouse and keyboard control.

- Arbitrary UI interaction generated from screenshots alone.

- Automatic approval of destructive dialogs.

- Unattended interaction with arbitrary websites or accounts.

- Treating visual appearance as sufficient proof of success.

This is a proposed scope decision, not an already confirmed product requirement. The team should validate whether interactive desktop automation is essential to the 10–12 week MVP. If it is, the supported workflow must be selected explicitly rather than adding generic desktop control without limits.

## 03.36.3 Execution approaches

| **Approach** | **Example** | **Strengths** | **Limitations** |
| --- | --- | --- | --- |
| Filesystem tools | Create a report in an approved folder | Direct, testable and relatively reliable | Cannot perform arbitrary application workflows |
| Application launch | Open a browser or text editor | Simple and useful | Launch does not mean task completion |
| Application API/integration | Use a supported application interface | Structured inputs and outputs; often more reliable than UI interaction | Depends on API availability, authentication and integration work |
| Accessibility/UI controls | Locate a named button and activate it | Can target semantic controls | Control availability and application behavior vary |
| Image-based GUI automation | Inspect a screenshot and click a coordinate | Can handle some interfaces lacking usable accessibility interfaces | Fragile to layout changes, resolution, dialogs and timing |

Recommended priority: direct filesystem or application interfaces first, semantic UI controls second, image-based automation only where justified.

The planner must not choose a more powerful execution method merely because it is easier to generate. Tool selection must be based on registered capabilities, authorization and reliability.

## 03.36.4 Windows desktop session architecture

NEXUS runs its backend in the shared environment, while each user's Windows bridge executes authorized operations on that user's computer. Interactive desktop control introduces an additional constraint: the Windows process must have access to the appropriate interactive desktop session.

A background process running as a service may not have the same desktop access as a process running within the logged-in user's session. Therefore, the existing bridge design must not assume that desktop automation will work simply because filesystem access works.

NEXUS backend

Task planning · Authorization · Orchestration

Authenticated Windows bridge

Tool validation · Local policy · Operation tracking

Filesystem tools

Search, read, create

Interactive UI agent

Optional, session-dependent

The UI agent is a proposed additional component, not an existing confirmed part of NEXUS.

### Proposed session rules

- Run interactive automation within the intended user's Windows session, with the minimum necessary privileges.

- Keep the existing filesystem bridge useful even when no interactive desktop is available.

- Detect whether the required session is available before starting a UI-dependent operation.

- Do not silently switch to another user's session, desktop or device.

- Do not assume that a locked, disconnected or logged-out session supports the same interactions as an active desktop.

- Keep the backend as the authority for task ownership, permissions, approvals and task state.

- Have the Windows-side automation component validate operations independently before acting.

The exact Windows session architecture remains open until the team chooses a GUI automation library and tests it on the target Windows 11 environment.

## 03.36.5 Interactive operation contract

If GUI automation is added, it must use registered operations with explicit contracts—not a general-purpose instruction such as “do whatever is necessary on the desktop.”

A UI operation should define:

- Tool ID and schema version.

- Target device and application identifier.

- Required interactive session conditions.

- Requested UI action and validated parameters.

- Required permissions and risk classification.

- Preconditions and expected UI state.

- Timeout and cancellation behavior.

- Verification method.

- Retry and reconciliation policy.

- Supported failure and uncertainty outcomes.

For example, an operation to enter text into a designated editor could require that the expected application is active and that the intended editable control is identified. If NEXUS cannot identify the correct control, it should stop and report the problem instead of typing into whichever window happens to have focus.

A tool contract must also distinguish between an attempted interaction and a verified application outcome. A click may be registered by the automation library without the application successfully processing the request.

## 03.36.6 UI automation safety rules

Interactive automation can cause consequences that are difficult to reverse. The following rules are proposed for any future implementation.

1. Application allowlist: operate only in explicitly enabled applications and supported workflows.

2. Window verification: identify the intended application or window before interacting.

3. Control verification: prefer semantic controls and accessibility information over screen coordinates.

4. Focus verification: do not enter text unless the intended target is confirmed.

5. Dialog handling: stop when an unexpected confirmation, permission prompt or destructive dialog appears.

6. Sensitive input: do not extract or expose credentials, tokens or private information unless a specifically authorized feature requires it.

7. Approval binding: approval applies to the precise proposed action and relevant parameters; materially changed actions require revalidation.

8. Bounded interaction: impose time, action-count and resource limits.

9. Failure containment: stop dependent steps when the UI state becomes unknown.

10. Auditability: record the tool, target application, action category, outcome and error without unnecessarily recording screenshots or sensitive content.

A UI action that would delete, overwrite, submit, purchase, send or change important settings must not inherit low risk simply because it is performed through a graphical interface. Risk is determined by the consequence of the action, not the input mechanism.

## 03.36.7 Application state and verification

GUI automation must account for changing application state. Windows may display a dialog, the application may be slow, the window may lose focus, or the user may interact with it while NEXUS is operating.

The proposed execution sequence is:

1. Check the target device and required session.

2. Confirm the intended application and supported workflow.

3. Validate authorization and any required approval.

4. Inspect the relevant application state.

5. Execute one bounded action.

6. Inspect the resulting state.

7. Record evidence and decide whether the next step is safe.

8. Stop, ask the user or reconcile if the resulting state differs from expectations.

Do not assume that a fixed delay guarantees readiness. Prefer observable conditions and bounded waits.

### Handling unexpected state

| **Condition** | **Required behavior** |
| --- | --- |
| Application is not open | Launch it only if that action is allowed, then verify readiness |
| Wrong window has focus | Do not enter text; restore or request confirmation |
| Unexpected dialog appears | Pause and report the dialog; do not automatically accept it |
| UI control cannot be found | Stop the current workflow and report the unsupported or changed state |
| Application becomes unresponsive | Apply a bounded timeout and classify the outcome appropriately |
| User interacts with the same application | Detect interference where feasible; pause if the automation's assumptions are no longer valid |
| Operation times out after a potentially consequential action | Reconcile before retrying |
| Application appears to have accepted an action but final result is unknown | Report uncertainty, not success |

A screenshot may be useful diagnostic evidence, but it can contain private information. Capture, transmit and retain screenshots only when the feature requires it and the applicable privacy rules permit it.

## 03.36.8 User interaction and approval experience

NEXUS is terminal-first, so approval and failure handling must work without requiring a separate graphical dashboard.

An illustrative interaction:

Task: Save a summary in the project workspace

Target device: MY-WINDOWS-PC

Planned action:

Application: Approved text editor

Action: Enter summary and save to a new file

Destination: Approved workspace

Existing-file behavior: Do not overwrite

Approval required: Yes

Approve this exact operation? [y/N]

This example illustrates the experience, not a final CLI contract. The actual approval must be tied to a validated operation fingerprint and checked by the backend and bridge. The terminal display itself is not the security mechanism.

For longer workflows, NEXUS should report:

- Which application it is operating in.

- The current step and its objective.

- Whether it is waiting for approval.

- Whether the operation succeeded, failed or remains uncertain.

- What the user can do next.

The user must be able to cancel a task. Cancellation stops future dispatch where possible, but an action already in progress may require reconciliation before NEXUS can report the task as cancelled.

## 03.36.9 Recovery and idempotency

GUI actions often cannot be safely retried. Clicking a button twice might submit a form twice; pressing a shortcut twice might perform an unintended operation.

Each UI tool therefore needs a tool-specific recovery policy.

| **Operation type** | **Retry policy** |
| --- | --- |
| Inspect application/window state | Usually safe to retry within limits |
| Read visible text | Usually safe to retry, subject to authorization and privacy |
| Open an approved application | Check existing application state before retrying |
| Enter text into a field | Inspect field contents and focus before retrying |
| Save a new document | Reconcile destination and application state first |
| Submit a form or send a message | Do not repeat blindly; establish whether the first action took effect |
| Delete or overwrite content | Requires explicit policy and appropriate approval; uncertain outcomes require reconciliation |

The bridge should use the operation identity and execution journal described in Section 03.30. Where the application offers no reliable way to establish whether an action occurred, NEXUS must preserve the uncertain state and request user assistance rather than claim exactly-once behavior.

## 03.36.10 Testing strategy

GUI automation requires tests beyond those for ordinary API and filesystem tools.

Unit and contract tests

- Validate UI operation schemas and registered capabilities.

- Reject unknown applications, controls and operation types.

- Check risk classification, authorization and approval binding.

- Verify timeouts, retry policies and structured errors.

Windows integration tests

- Test supported applications on the intended Windows 11 configuration.

- Confirm behavior when applications are closed, slow, unresponsive or missing.

- Test locked and logged-out sessions, session changes and unavailable desktops.

- Verify that the bridge never falls back to unrestricted command execution.

Failure and safety tests

- Window focus changes between validation and action.

- An unexpected dialog appears.

- The user changes the application state during execution.

- A timeout occurs after a potentially consequential action.

- The bridge disconnects after the action but before its result is persisted.

- A malicious document or displayed instruction asks NEXUS to bypass policy.

- The same operation is delivered more than once.

End-to-end acceptance scenarios

1. Launch an approved application and verify that it opened.

2. Detect that the required interactive session is unavailable and stop safely.

3. Refuse to type into an unverified window.

4. Stop when an unexpected destructive confirmation appears.

5. Handle an uncertain save or submission without blindly repeating it.

6. Preserve user/device isolation and the task's audit trail.

7. Complete a supported workflow and verify its actual outcome.

Tests must run on the supported Windows configuration. Mocked UI tests alone are insufficient to establish real desktop reliability.

## 03.36.11 Implementation priorities

| **Priority** | **Scope** |
| --- | --- |
| P0 — Initial release | Approved application launching, existing secure filesystem tools, structured results, clear unsupported-action errors |
| P1 — Controlled UI automation | One or two narrowly selected application workflows, session detection, semantic control targeting, bounded execution and verification |
| P2 — Broader desktop automation | Additional applications, more complex workflows, improved visual interpretation and advanced recovery |

The exact P1 workflows must be selected based on user value and technical feasibility. Do not add broad screenshot-driven automation merely to make NEXUS appear more capable.

### Proposed ownership

- Developer 1: orchestration, operation lifecycle, cancellation, approval and recovery.

- Developer 2: Windows bridge, session integration, application launching and any approved UI automation adapter.

- Developer 3: planning support for UI tools, capability descriptions, action selection and evaluation.

All three developers should review authorization, session boundaries and failure behavior before a UI tool is enabled.

## 03.36.12 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| GUI automation in the 10–12 week release | Not confirmed; recommend keeping broad GUI control out of P0 |
| Initial UI automation library | Open; evaluate against actual Windows 11 requirements |
| Supported applications | Open; select specific use cases |
| Accessibility-based versus image-based interaction | Prefer semantic controls where practical |
| Interactive session behavior | Must be validated on the target machines |
| Screenshot retention | No retention by default unless an approved feature requires it |
| User interference detection | Required where feasible; exact mechanism open |
| GUI operation limits | Define per tool after prototyping |
| Consequential UI actions | Explicit policy and approval; some actions may remain unsupported |

## 03.36.13 Definition of done

- The team distinguishes application launching, application integrations and interactive GUI automation.

- The initial release scope is explicitly approved.

- GUI automation, if included, runs only within a supported and validated Windows session.

- Each UI operation has a registered contract, authorization rules and risk classification.

- Window and control identity are checked before consequential interaction.

- Unexpected dialogs and unverified states cause safe pauses.

- Timeouts, cancellation and uncertain outcomes are handled without blind retries.

- No model-generated arbitrary shell or unrestricted desktop-control endpoint exists.

- Privacy-aware diagnostics and Windows integration tests are included.

- The team demonstrates at least one complete supported workflow with verified results, if GUI automation is included.

Section exit criterion: NEXUS has an explicit, testable boundary between supported computer operations and interactive desktop control. The system must never confuse an attempted UI action with a verified result.
