## 2.1 Functional modules

NEXUS will be divided into the following functional areas.

FR-01

User and device management

Identify users, register Windows devices, authenticate requests and enforce ownership.

FR-02

Terminal interface

Accept requests, display progress, collect approvals and present results.

FR-03

Request understanding and planning

Interpret intent, identify missing information, produce structured plans and select supported tools.

FR-04

Windows tool execution

Perform permitted file, document and application operations on the intended computer.

FR-05

Task orchestration

Track steps, dependencies, progress, cancellation, timeouts, retries and recovery.

FR-06

Approval and policy engine

Apply risk tiers, enforce permissions and obtain approval for sensitive actions.

FR-07

Context and memory

Store, retrieve, inspect, update and delete user-controlled context.

FR-08

History and audit

Record task outcomes, execution events, approvals and diagnostic information.

FR-09

Reliability and operations

Handle disconnections, service failures, configuration errors and resource limits.

## 2.2 Core user journeys

These journeys define the expected end-to-end behavior before we specify individual APIs or database tables.

### Journey A — Complete a computer task

1. User submits a request. Example: “Find the latest project design document and summarize it.”

2. NEXUS establishes context. It identifies the user, intended device, available permissions and relevant conversation context.

3. NEXUS plans the work. It creates a structured plan using supported operations, identifying any missing information.

4. Policy validation occurs. Every proposed operation is checked against the user's permissions, device scope and risk policy.

5. The task executes. The Windows bridge performs permitted operations and returns structured results.

6. Results are verified. NEXUS checks the returned evidence and records whether the task succeeded, partially succeeded or failed.

7. The user receives the outcome. NEXUS presents the summary, source file and any relevant warnings. Task history is persisted.

Acceptance criteria

- A task cannot execute a tool operation that fails authorization.

- The intended Windows device is explicitly identified.

- A failure is not reported as success.

- The user can inspect the final result and task history.

- If a required detail is ambiguous, NEXUS asks a targeted question rather than inventing it.

### Journey B — Perform an action requiring approval

1. The user requests an operation that could overwrite an existing file.

2. NEXUS prepares the exact proposed operation, including the target path and intended change.

3. The policy engine determines that confirmation is required.

4. NEXUS displays the proposed action and waits for an explicit decision.

5. If approved, the system revalidates authorization and executes the approved operation.

6. If rejected or expired, the action is not performed.

7. The decision and execution outcome are recorded.

Important rule: Approval must apply to the specific operation shown to the user. It must not authorize a different path or silently expanded set of operations.

### Journey C — Resume after a computer disconnects

1. A task is running on a registered Windows device.

2. The device becomes unreachable.

3. NEXUS marks the task or step as interrupted or awaiting recovery, according to the defined state model.

4. The system checks whether the operation is safe to resume.

5. A read-only operation may be retried within its configured limits. A write operation must not be blindly repeated if its previous outcome is uncertain.

6. The user sees an accurate status and can retry, cancel or inspect the task where supported.

Acceptance criteria: No interrupted task is automatically marked successful without evidence. Recovery behavior must be defined separately for each operation class.

### Journey D — Use memory across sessions

1. A user asks NEXUS to remember a project preference.

2. NEXUS explains what information will be saved when appropriate and stores it under the correct user.

3. During a later session, a relevant request triggers memory retrieval.

4. NEXUS uses the retrieved context only within the applicable user's permissions.

5. The user can inspect, correct and delete the stored memory.

Acceptance criteria: One user's private memory cannot be retrieved by another user through the API, terminal interface, model context or task execution.

## 2.3 Detailed requirement catalogue

The following are initial normative requirements proposed for the MVP.

Priority: P0 = required for MVP; P1 = important if time permits; P2 = future enhancement.

### FR-01 — Identity and device management

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-01.1 | NEXUS must authenticate users before accessing protected functionality. | P0 |
| FR-01.2 | Each Windows bridge must have a distinct registered device identity. | P0 |
| FR-01.3 | Each task must identify its owner and intended execution device. | P0 |
| FR-01.4 | The backend must reject cross-user access to tasks, memories, approvals and private device records. | P0 |
| FR-01.5 | A user must be able to revoke a device's access. | P0 |

### FR-02 — Terminal interface

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-02.1 | Users must be able to submit natural-language requests. | P0 |
| FR-02.2 | The interface must display task identifiers and meaningful progress states. | P0 |
| FR-02.3 | The interface must support approval, rejection and cancellation where applicable. | P0 |
| FR-02.4 | The interface must display final results and actionable errors. | P0 |
| FR-02.5 | Users must be able to inspect previous tasks. | P0 |

### FR-03 — Request understanding and planning

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-03.1 | NEXUS must convert supported requests into structured plans. | P0 |
| FR-03.2 | Plans must reference only registered tool operations. | P0 |
| FR-03.3 | The system must ask for clarification when an essential target or instruction is ambiguous. | P0 |
| FR-03.4 | The model must not grant itself permissions or override policy decisions. | P0 |
| FR-03.5 | Unsupported requests must receive an honest explanation instead of fabricated results. | P0 |

### FR-04 — Windows tool execution

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-04.1 | NEXUS must search only configured, permitted directories. | P0 |
| FR-04.2 | NEXUS must read supported document formats and report parsing failures. | P0 |
| FR-04.3 | NEXUS must create files only within permitted locations and under the applicable approval policy. | P0 |
| FR-04.4 | NEXUS must launch only explicitly supported applications. | P0 |
| FR-04.5 | Every tool must validate inputs, enforce limits and return a structured result. | P0 |
| FR-04.6 | The bridge must reject arbitrary shell commands and unregistered operations. | P0 |

### FR-05 — Task orchestration

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-05.1 | Each accepted task must have a durable identifier and persisted state. | P0 |
| FR-05.2 | Tasks must expose progress at the appropriate step granularity. | P0 |
| FR-05.3 | Task execution must enforce configured concurrency limits. | P0 |
| FR-05.4 | Supported tasks must be cancellable, with documented cancellation semantics. | P0 |
| FR-05.5 | Retries must respect operation safety and configured limits. | P0 |
| FR-05.6 | Recovery must distinguish confirmed outcomes from uncertain outcomes. | P0 |

### FR-06 — Approval and policy

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-06.1 | Every registered tool must declare its permitted operation class and required permissions. | P0 |
| FR-06.2 | Operations requiring approval must pause before execution. | P0 |
| FR-06.3 | Approval must be bound to the proposed operation and its parameters. | P0 |
| FR-06.4 | Rejected or expired approvals must not authorize execution. | P0 |
| FR-06.5 | Policy must be enforced server-side and at the trusted execution boundary. | P0 |

### FR-07 — Context and memory

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-07.1 | Memory must be associated with its owning user. | P0 |
| FR-07.2 | Users must be able to inspect and delete saved memories. | P0 |
| FR-07.3 | Retrieved memories must be relevant to the current request and permitted for that user. | P0 |
| FR-07.4 | NEXUS must distinguish stored facts from model-generated assumptions. | P0 |
| FR-07.5 | Memory retrieval must have configurable limits and diagnostic visibility. | P1 |

### FR-08 — History and audit

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-08.1 | The system must persist task state transitions and final outcomes. | P0 |
| FR-08.2 | Approval decisions and consequential tool operations must be auditable. | P0 |
| FR-08.3 | Logs must not expose credentials or unnecessarily duplicate private document contents. | P0 |
| FR-08.4 | Users must be able to retrieve their own task history. | P0 |

### FR-09 — Reliability and operations

| **ID** | **Requirement** | **Priority** |
| --- | --- | --- |
| FR-09.1 | Timeouts must be enforced for model and bridge operations. | P0 |
| FR-09.2 | Network disconnections must not cause false-success responses. | P0 |
| FR-09.3 | Invalid requests and unexpected failures must produce diagnosable errors. | P0 |
| FR-09.4 | Service startup, migrations and configuration must be documented and reproducible. | P0 |
| FR-09.5 | Core user workflows must be testable without requiring a live AI model for every test. | P0 |

These identifiers establish traceability. Their detailed schemas, exact error codes and measurable thresholds belong in later sections.

## 2.4 Non-functional requirements

Functional requirements describe what NEXUS does. Non-functional requirements specify the quality constraints under which it must operate.

| **Category** | **Proposed requirement** |
| --- | --- |
| Security | Enforce authentication, per-user authorization and explicit device boundaries. |
| Reliability | Persist task transitions and handle partial failure without claiming unsupported success. |
| Performance | Measure API, database, model and Windows-tool latency separately. Set numeric targets after establishing a baseline. |
| Concurrency | Concurrent tasks must not corrupt task state or bypass authorization. |
| Maintainability | Keep model adapters, policy evaluation, execution, persistence and platform tools in separate modules. |
| Testability | Support deterministic tests with mocked model and bridge responses. |
| Privacy | Minimize collected data and isolate user memory, task content and device metadata. |
| Portability | Support development inside Ubuntu on WSL 2 and execution against Windows 11 bridges. |
| Cost | No required paid API or infrastructure dependency for the MVP. |

## 2.5 Cross-cutting behavior rules

These rules apply to every functional module:

1. Never trust model output as authority. Validate all proposed tool calls.

2. Never report unverified success. Use evidence from the actual operation.

3. Never silently cross a user or device boundary.

4. Never blindly retry an operation whose previous outcome is uncertain.

5. Never let approval for one action authorize a different action.

6. Never fabricate unavailable context or pretend an unsupported tool ran.

7. Record enough operational detail to debug failures without logging unnecessary sensitive content.
