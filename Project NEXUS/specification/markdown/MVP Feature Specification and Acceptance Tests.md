## 03.26.1 Purpose

## Section 03.25 established the delivery roadmap. This section defines what the NEXUS MVP must actually deliver and how the team will prove that each feature works.

A feature is not accepted simply because its main workflow succeeds once. It must also meet its security, persistence, error-handling and recovery requirements.

This specification uses three labels:

- Required: a capability or safety property that the MVP must satisfy.

- Proposed: a concrete implementation or scope choice that the team should review.

- Open: a decision that needs evidence or an explicit team agreement before implementation.

The acceptance tests below are illustrative test specifications. The team should convert them into automated tests and record their results during development.

## 03.26.2 MVP feature inventory

| **ID** | **Feature** | **Priority** | **Acceptance evidence** |
| --- | --- | --- | --- |
| MVP-01 | User authentication and isolation | P0 | Unauthorized and cross-user access tests pass |
| MVP-02 | Device registration and ownership | P0 | Each user operates only authorized devices |
| MVP-03 | Terminal CLI | P0 | Users submit tasks and inspect status and results |
| MVP-04 | Durable task lifecycle | P0 | State transitions survive backend restarts |
| MVP-05 | Restricted Windows bridge | P0 | Only registered, authorized tools can execute |
| MVP-06 | File search and document reading | P0 | Scoped filesystem tests pass |
| MVP-07 | Safe file creation | P0 | No unintended overwrite or out-of-scope write |
| MVP-08 | Policy and human approval | P0 | Prohibited and unapproved operations never dispatch |
| MVP-09 | Operation deduplication and recovery | P0 | Uncertain effects are reconciled before unsafe retry |
| MVP-10 | Task history and audit | P0 | Authorized history and required audit records persist |
| MVP-11 | Local AI planning | P1 | Structured plans pass a defined evaluation set |
| MVP-12 | User-controlled memory and retrieval | P1 | Save, retrieve, correct and delete workflows pass |
| MVP-13 | Multi-device LAN deployment | P0 | All three developers use their own registered computers |
| MVP-14 | Diagnostics and backup recovery | P0 | Failures are diagnosable and restoration is tested |

P0 identifies the minimum safe product foundation. P1 identifies AI and personalization capabilities that are central to NEXUS's product vision but can be developed after the core execution and enforcement contracts are stable. A release intended to demonstrate the complete NEXUS vision must still include both useful AI planning and context/memory.

## 03.26.3 MVP-01 — Authentication and user isolation

Goal: identify the user making each request and ensure that private resources remain isolated.

### Required behavior

- Authenticate users through the agreed authentication mechanism.

- Derive user identity from authenticated credentials, not request-body claims.

- Protect task, memory, device and approval endpoints.

- Reject expired, invalid or revoked credentials.

- Return consistent errors without exposing internal authentication details.

- Ensure one user cannot access another user's private tasks or memory by guessing an identifier.

### Acceptance tests

Valid user credentials permit authorized access.

Missing or invalid credentials are rejected.

User A cannot retrieve User B's task using its task ID.

User A cannot read or modify User B's private memory.

Changing a request-body user_id cannot impersonate another user.

Revoked credentials cannot authorize new requests.

0 of 6 test cases marked as verified. This is a local checklist, not a test runner.

Failure condition: any unauthorized cross-user read or write is a release blocker.

Open: the final authentication mechanism, token lifetimes, refresh strategy and account-provisioning workflow.

## 03.26.4 MVP-02 — Device registration and ownership

Goal: ensure that an operation executes on the intended Windows computer.

### Required behavior

- Each Windows bridge has a distinct registered device identity.

- Device authentication uses a credential or equivalent trusted mechanism, not the device ID alone.

- The backend verifies that the requesting user is authorized to use the target device.

- A task identifies its target device explicitly, or uses a configured default shown to the user.

- Revoked or unregistered devices cannot accept new authorized operations.

- If the target device is offline, NEXUS reports the unavailability; it does not silently redirect the task.

### Acceptance tests

| **Test** | **Expected result** |
| --- | --- |
| User submits a task to their registered device | Task targets that device |
| User submits a task to another user's device without permission | Denied |
| Bridge presents invalid credentials | Rejected |
| Target device disconnects | Task waits or enters a documented recovery state |
| Device is revoked before dispatch | New dispatch is blocked |
| Device reconnects after interruption | Reauthentication and reconciliation occur before unsafe resumption |

Open: device registration bootstrap, credential rotation and whether any device sharing will be supported in the MVP. The provisional policy is owner-only device access.

## 03.26.5 MVP-03 — Terminal-first user experience

Goal: make the core product usable without requiring a web dashboard.

### Proposed command set

| **Command** | **Purpose** |
| --- | --- |
| nexus login | Authenticate |
| nexus logout | End the local authenticated session |
| nexus devices | List devices the user may access |
| nexus run | Submit a request |
| nexus task <id> | Inspect task status |
| nexus task <id> --watch | Follow task progress |
| nexus task <id> --steps | Inspect step outcomes |
| nexus task <id> --result | View the final result |
| nexus cancel <id> | Request cancellation |
| nexus approve <approval-id> | Submit an approval decision |
| nexus reject <approval-id> | Reject an approval request |
| nexus history | Browse authorized task history |
| nexus memory list | List the user's saved memories |

The exact command syntax is proposed and can be adjusted after the first CLI prototype.

### Required behavior

- Task submission returns a durable task ID.

- Status output distinguishes queued, running, waiting for approval, interrupted, succeeded, failed and cancelled states.

- A task with partial or uncertain results must not be presented as an unqualified success.

- Approval output identifies the target device and proposed operation.

- Stopping --watch stops monitoring, not the underlying task.

- Machine-readable output, if supported, must not be mixed with banners or unrelated text on standard output.

- CLI errors use stable exit codes or another documented machine-readable error convention.

### Acceptance tests

1. Submit a task and retrieve it using the returned ID.

2. Disconnect the CLI while a task runs; verify that the backend continues to manage the task.

3. Submit an invalid command; receive a useful error.

4. Request another user's task; receive an authorization error.

5. Watch a disconnected device's task; receive accurate status rather than a false completion.

6. Request JSON output; verify that it conforms to the documented output schema.

Exit criterion: a developer can complete and inspect a supported task using only the terminal.

## 03.26.6 MVP-04 — Durable task lifecycle

Goal: provide reliable task state and progress across concurrency, cancellation and restarts.

### Required behavior

- Persist a task before acknowledging durable acceptance.

- Enforce legal state transitions.

- Persist individual steps and operation attempts.

- Prevent multiple workers from simultaneously owning the same step.

- Distinguish task state from step outcome and overall partial success.

- Handle cancellation as a request whose result must be confirmed.

- Recover nonterminal tasks after restart without blindly re-executing uncertain operations.

- Preserve enough history to explain what happened.

### Acceptance tests

| **Scenario** | **Expected result** |
| --- | --- |
| Same task request is submitted twice with the same idempotency key and payload | Existing task is returned |
| Same key is reused with a different payload | Documented conflict |
| Two workers attempt to claim the same work | At most one valid owner |
| Backend restarts while a task is queued | Task remains recoverable |
| Backend restarts after external dispatch | Operation is reconciled before an unsafe retry |
| Cancellation arrives during execution | Cancellation request is persisted; final outcome is determined accurately |
| A task has both completed and failed steps | Results report partial success or uncertainty accurately |

Release blocker: a stale worker must not overwrite a newer worker's authoritative state or trigger an unguarded duplicate side effect.

Open: exact task and step state enumerations, claim/lease duration, concurrency limits and recovery implementation. These must be settled in the state-machine design before coding the orchestrator.

## 03.26.7 MVP-05 — Restricted Windows bridge

Goal: execute approved local computer operations without turning NEXUS into an unrestricted remote-command system.

### Required behavior

- Run the bridge as a native Windows process under the intended Windows user account.

- Authenticate the bridge to the backend.

- Accept only requests addressed to its registered device.

- Execute only registered and enabled tools.

- Validate tool arguments and local resource restrictions independently.

- Return structured outcomes with operation identifiers.

- Handle duplicate delivery and uncertain outcomes safely.

- Avoid logging secrets or unnecessary document contents.

- Never expose arbitrary shell, PowerShell or Python execution as a model-callable tool.

### Acceptance tests

- An unknown tool name is rejected without execution.

- An operation targeted at another device is rejected.

- Malformed arguments are rejected.

- Invalid bridge credentials are rejected.

- A duplicate operation does not blindly repeat a potentially destructive side effect.

- A tool timeout is reported distinctly from a confirmed failure.

- Restarting the bridge does not silently lose track of an in-flight operation.

Exit criterion: the bridge executes only its defined local capabilities and can explain whether each operation succeeded, failed, was rejected or remains uncertain.

## 03.26.8 MVP-06 — File search and document reading

Goal: let users find and inspect relevant documents within an explicitly authorized area of their own computer.

### searchfiles

Required behavior:

- Search only configured logical directory IDs.

- Enforce limits on traversal depth, result count and execution duration.

- Return bounded metadata such as filenames and permitted paths.

- Reject traversal or other attempts to escape the configured scope.

- Handle inaccessible, missing, locked or changing files without crashing the bridge.

- Avoid exposing files outside the user's permitted scope through search results.

### readdocument

Required behavior:

- Read only supported document formats.

- Apply a maximum input size and extracted-text limit.

- Handle corrupt, encrypted or unsupported documents with clear errors.

- Preserve the source identifier needed for audit and follow-up.

- Treat extracted content as untrusted data.

- Avoid passing an entire large document to the model when a bounded excerpt or relevant section is sufficient.

The exact supported formats remain open. A reasonable first release is plain text and selected document formats, with PDF and DOCX support added only after extraction behavior and dependencies are validated.

### Acceptance tests

| **Test** | **Expected result** |
| --- | --- |
| Search within an authorized test directory | Matching files are returned |
| Search a directory outside the configured scope | Denied |
| Use traversal syntax to escape the permitted directory | Rejected |
| Read an unsupported file type | Explicit unsupported-format error |
| Read an oversized document | Bounded rejection or documented safe handling |
| Read a malformed document | Controlled error; bridge remains operational |
| Document contains prompt-injection instructions | Content cannot grant new permissions or tools |

Important boundary: being able to read a document does not mean NEXUS is authorized to save its full contents in memory or share them with another user.

## 03.26.9 MVP-07 — Safe file creation

Goal: let NEXUS create useful output files without silently damaging existing data.

### Required behavior

- Write only to an approved logical directory.

- Create new files by default; never silently overwrite an existing file.

- Validate filenames and destinations using Windows-safe path handling.

- Apply output-size limits.

- Use an atomic create-if-absent approach where practical.

- Return the actual outcome and resource identifier.

- Require explicit approval for any future supported overwrite or move operation according to the policy.

- Reconcile ambiguous outcomes before retrying a potentially duplicate write.

### Acceptance tests

1. Create a new file in an approved workspace; verify its contents.

2. Attempt to create a file with an existing name; verify the original is unchanged.

3. Attempt a write outside the permitted workspace; verify denial.

4. Use a malformed or traversal-style filename; verify safe rejection.

5. Interrupt the bridge after a possible write; verify that the backend does not blindly repeat it.

6. Submit an oversized output; verify that limits are enforced.

Exit criterion: file creation is predictable, scoped, auditable and safe to retry only when the tool's state and semantics make retry safe.

## 03.26.10 MVP-08 — Policy enforcement and human approval

Goal: ensure that every operation passes the authorization and risk rules defined in Section 03.23.

### Required behavior

- Unknown tools are denied.

- The model cannot assign permissions or downgrade risk.

- Hard prohibitions cannot be overridden by approval.

- Resource permissions are evaluated independently of tool selection.

- Approval is bound to the exact normalized operation and target device.

- Changed arguments invalidate the prior approval when they affect the approved operation.

- Approval and permission validity are checked immediately before dispatch.

- The bridge enforces its local restrictions even if the backend approves an operation.

- Every required decision is recorded in the audit trail.

### Acceptance tests

Unregistered tool proposal is denied.

Tier 2 operation cannot execute without required approval.

Expired or rejected approval does not permit dispatch.

Changed destination invalidates the previous approval.

Approval cannot override a hard prohibition.

A revoked device is blocked even if an earlier approval exists.

A malicious document cannot approve an operation or expand permissions.

The bridge rejects a locally prohibited operation even after backend approval.

0 of 8 test cases marked as verified. This is a local checklist, not execution evidence.

Release blocker: any tested route that permits an unauthorized operation to execute.

## 03.26.11 MVP-09 — Deduplication, cancellation and recovery

Goal: preserve reliable outcomes when network delivery, the backend or the Windows bridge fails.

### Required behavior

- Deduplicate task submissions using the agreed client request identifier.

- Assign stable operation identifiers to logical external operations.

- Track individual delivery or execution attempts separately.

- Use tool-specific timeout and retry rules.

- Never treat a timeout as proof that a side effect did not happen.

- Reconcile uncertain file creation or other external effects before unsafe retries.

- Persist cancellation requests and stop dispatching future steps when cancellation is accepted.

- Preserve already completed external actions; do not imply that cancellation rolled them back.

- Revalidate current authorization and approval before resuming an operation after interruption.

### Acceptance tests

| **Failure** | **Required behavior** |
| --- | --- |
| Duplicate API submission | No duplicate task |
| Duplicate bridge delivery | No blind repeat of an external side effect |
| Backend crashes before dispatch | Pending operation remains recoverable |
| Backend crashes after dispatch | Reconcile the operation before an unsafe retry |
| Bridge executes but response is lost | Preserve uncertainty until the outcome is verified |
| Device disconnects mid-task | No silent device switching |
| Cancellation races with a new step | Apply state rules and prevent unauthorized future dispatch |
| Approval expires during an interruption | Revalidate; do not automatically reuse an expired approval |

Exit criterion: the team can demonstrate recovery from at least one failure before dispatch, one failure after dispatch and one lost-response scenario involving a possible side effect.

## 03.26.12 MVP-10 — Task history and audit

Goal: allow users and developers to understand task outcomes without exposing unnecessary private data.

### Required behavior

- Persist task and step status changes.

- Record required authorization and approval decisions.

- Associate events with task, operation, device and request identifiers where applicable.

- Restrict history and audit access to authorized users or designated operational roles.

- Record failures with stable error codes.

- Bound stored result payloads.

- Avoid logging credentials, tokens, full private documents or complete prompts by default.

- Distinguish task history, security audit records and diagnostic logs.

### Acceptance tests

- A completed task appears in the correct user's history.

- A task's recorded steps explain its reported outcome.

- An approval decision can be traced to its operation.

- Unauthorized users cannot retrieve private task history.

- A failed operation has enough diagnostic information for investigation without leaking secrets.

- A large tool result is stored or displayed according to the configured limits.

Open: retention duration for task history, audit records, logs and tool results. These categories should not automatically inherit the same retention policy.

## 03.26.13 MVP-11 — Local AI planning

Goal: translate natural-language requests into useful, validated plans without making the model a security authority.

### Required behavior

- Use the replaceable model-provider interface.

- Support a local inference configuration on the designated team computer, subject to hardware validation.

- Produce structured plans that conform to the planner contract.

- Select only registered tools.

- Ask for clarification when a required target, resource or other essential detail is missing.

- Keep planning separate from execution.

- Handle malformed model output and model unavailability gracefully.

- Use bounded context, output size, retries and inference time.

- Keep policy enforcement independent of the model.

- Evaluate planning quality against a fixed set of representative tasks.

### Acceptance tests

1. A request to find a document produces a valid proposal for the registered search tool.

2. An ambiguous request triggers clarification rather than an invented target.

3. An unknown tool in model output is rejected.

4. Malformed structured output does not reach execution.

5. A model timeout produces a useful error or controlled retry.

6. A malicious document cannot grant the model additional permissions.

7. Concurrent planning requests are measured on the designated host.

8. Replacing the model adapter does not require changing task authorization logic.

Open: exact runtime, model, AMD acceleration path and acceptable latency. These must be decided through benchmarking rather than assumed from the GPU brand.

## 03.26.14 MVP-12 — User-controlled memory and hybrid retrieval

Goal: allow NEXUS to retain useful context across tasks while preserving user ownership and privacy.

### Required behavior

- Support explicit memory creation, listing, retrieval, correction and deletion.

- Scope private memories to their owner.

- Keep task history and memory as separate concepts.

- Apply access filtering before retrieved content is passed to the planner.

- Prefer current, confirmed information over stale or uncertain information.

- Preserve source and timestamp metadata where appropriate.

- Treat retrieved memories as untrusted content for tool authorization.

- Remove deleted memories from active retrieval and associated indexes or caches.

- Avoid automatically saving every conversation or full document.

- Keep memory retrieval bounded.

### Acceptance tests

| **Test** | **Expected result** |
| --- | --- |
| User saves an explicit memory | It is available to the same user according to policy |
| User retrieves a relevant memory | Appropriate context is returned |
| Another user requests that memory | Access denied |
| User corrects a memory | Updated information is used in future retrieval |
| User deletes a memory | It is no longer available through active retrieval |
| Similar but unrelated memories exist | Retrieval is evaluated for relevance, not just similarity |
| A retrieved memory contains malicious instructions | It cannot change tool permissions |

Open: embedding model, lexical/semantic ranking, storage implementation and memory retention. A PostgreSQL-based starting point should be benchmarked before introducing a separate vector database.

## 03.26.15 MVP-13 — Three-device LAN deployment

Goal: demonstrate that all three developers can use one shared backend while retaining control of their own computers.

### Required behavior

- Run the backend and PostgreSQL on the selected host or agreed alternative.

- Connect each developer's CLI and Windows bridge through the configured network.

- Authenticate every client and bridge.

- Keep PostgreSQL inaccessible to ordinary LAN clients.

- Restrict the model endpoint to the required local services.

- Avoid public internet exposure and port forwarding for the MVP.

- Handle host, model and device outages explicitly.

- Document startup, shutdown, recovery and device registration.

- Verify that all three developers can reproduce the setup.

### Acceptance tests

- All three developers authenticate and access their own devices.

- A task targeted at one computer never executes on another.

- One disconnected bridge does not invalidate unrelated users' device identity or task ownership.

- The system recovers correctly after a controlled backend restart.

- An unauthorized LAN client cannot access protected API operations.

- PostgreSQL is not exposed as a general LAN service.

- The deployment can be rebuilt from documented instructions on a clean environment.

Open: final host operating system, networking mode, stable address, TLS requirements for the actual LAN, and AMD runtime support.

## 03.26.16 MVP-14 — Diagnostics, backup and restoration

Goal: make NEXUS supportable when something fails, and recover its persisted state after data loss or host failure.

### Required behavior

- Provide basic service-health checks.

- Report whether the backend, database, AI runtime and target device are available.

- Keep diagnostics separate from unrestricted secret or environment-variable dumps.

- Back up the authoritative database according to an agreed schedule.

- Keep at least one protected backup outside the designated host.

- Test restoring the database and resuming service.

- Reconcile nonterminal operations after restoration rather than assuming every pending task is safe to repeat.

- Document credential and device-registration recovery.

### Acceptance tests

1. Database unavailable: readiness reports degraded or unavailable.

2. Model unavailable: deterministic non-AI operations continue where their dependencies permit.

3. Device unavailable: the task reports the correct target and state.

4. Database restored from backup: schema and required relationships validate.

5. A restored task may have performed an external action before failure: reconciliation happens before unsafe retry.

6. Diagnostics are collected: credentials and private document contents are not dumped.

7. Clean setup and recovery instructions are followed by a teammate who did not author them.

Open: backup frequency, retention, recovery-point objective (RPO), recovery-time objective (RTO) and whether point-in-time recovery is justified for the MVP.

## 03.26.17 Cross-feature end-to-end acceptance scenarios

Individual feature tests are necessary but insufficient. NEXUS must pass complete workflows that cross component boundaries.

E2E-01 — Search and report

A user submits a request, NEXUS searches an approved directory on the selected device, persists the result and returns it through the CLI.

Pass: correct device, bounded results, durable task history and accurate status.

E2E-02 — Create a file safely

A user requests a new file. NEXUS validates the destination, applies policy, obtains approval if required, creates the file and verifies the outcome.

Pass: correct content, correct location, no silent overwrite and an auditable outcome.

E2E-03 — Approval and policy rejection

The AI proposes a consequential operation. NEXUS presents the exact operation, validates the user's decision and blocks changed or prohibited operations.

Pass: no dispatch without valid authorization.

E2E-04 — Uncertain execution

A bridge performs an operation but its response is lost. The backend restarts and later reconnects to the bridge.

Pass: the outcome is reconciled or remains explicitly uncertain; no blind duplicate side effect.

E2E-05 — Context-aware planning

A user asks a follow-up request that depends on a previously saved, authorized project memory.

Pass: relevant context is retrieved for the same user, irrelevant context is excluded and permissions remain unchanged.

E2E-06 — Three-user isolation

All three developers submit tasks concurrently to their own devices while one device disconnects.

Pass: correct task ownership, no cross-device execution, accurate disconnected-device state and consistent persistence.

## 03.26.18 MVP completion scorecard

Use this scorecard during the Week 10 and Week 12 integration reviews.

## Release readiness

## 0/10

Identity and device isolation

Mandatory release gate

Not tested

CLI and durable task lifecycle

Mandatory release gate

Not tested

Restricted Windows bridge

Mandatory release gate

Not tested

Safe file operations

Mandatory release gate

Not tested

Policy, approval and audit

Mandatory release gate

Not tested

Concurrency and uncertain-outcome recovery

Mandatory release gate

Not tested

Three-device LAN deployment

Mandatory release gate

Not tested

Diagnostics and tested restoration

Mandatory release gate

Not tested

Local AI planning and evaluation

Core product capability

Not tested

User-controlled memory and retrieval

Core product capability

Not tested

This is an interactive planning checklist only. A selected “Pass” records your assessment here; it does not run tests or verify implementation.

Copy scorecard

A release cannot be approved based only on the number of passed items. Every P0 gate must pass, and the team must demonstrate both AI planning and context/memory before claiming the full NEXUS MVP is complete.

## 03.26.19 Open decisions

| **ID** | **Decision** | **Required evidence** |
| --- | --- | --- |
| MVP-OD-01 | Final supported document formats | Extraction and error-handling tests |
| MVP-OD-02 | Final set of Tier 2 operations | Security review and explicit tool contracts |
| MVP-OD-03 | Approval expiry and approver rules | Policy agreement |
| MVP-OD-04 | Model and runtime | Actual-host benchmark |
| MVP-OD-05 | Memory retrieval implementation | Relevance, privacy and performance evaluation |
| MVP-OD-06 | Task and audit retention | Privacy and operational requirements |
| MVP-OD-07 | Backup and recovery objectives | Host-failure recovery drill |
| MVP-OD-08 | Whether GUI automation belongs in the MVP | Scope and risk assessment |

## 03.26.20 Section exit criteria

## Section 03.26 is ready for implementation when:

- The team has reviewed every MVP feature and its acceptance tests.

- The supported tool set and prohibited actions are explicit.

- Test cases are assigned to the appropriate component owners.

- Each feature has a measurable definition of done.

- The end-to-end scenarios are included in the integration plan.

- All remaining decisions have an owner and a deadline.

- Release approval depends on recorded test evidence rather than informal assurances.
