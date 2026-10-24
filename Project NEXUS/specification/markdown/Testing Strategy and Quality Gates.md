## 03.18.1 Purpose

NEXUS must safely execute actions on real Windows computers while maintaining user-specific memory and persistent task history. Testing therefore cannot focus only on whether API endpoints return successful responses.

The test strategy must prove that NEXUS:

- Executes only registered, authorized operations.

- Keeps users, devices, tasks and memories correctly isolated.

- Handles concurrent requests without corrupting task state.

- Recovers safely from crashes, timeouts and device disconnections.

- Does not repeat uncertain operations blindly.

- Remains useful when the local AI model is unavailable or produces invalid plans.

- Can be installed, tested and operated by all three developers.

Core principle: a successful HTTP response is not proof that the requested computer operation completed correctly.

## 03.18.2 Testing principles

1. Test deterministic logic without an AI model. Most business logic, authorization rules, state transitions and failure scenarios must be testable using controlled inputs.

2. Use real PostgreSQL for database correctness tests. SQLite or mocks cannot establish that PostgreSQL locking, constraints and transactions behave correctly.

3. Test the Windows bridge on Windows. Filesystem behavior, path validation and application launching cannot be fully validated inside Ubuntu on WSL 2.

4. Treat safety as a release requirement. Critical authorization or approval failures block release even when functional tests pass.

5. Test failures deliberately. Simulate lost responses, process restarts, expired approvals, stale workers and disconnected devices.

6. Separate model quality from application correctness. A model can suggest a poor plan; the application must still prevent unauthorized execution.

7. Make failures reproducible. Tests should capture inputs, expected behavior and diagnostic identifiers without exposing secrets or unnecessary document contents.

## 03.18.3 Test pyramid

### Unit tests

Many fast tests · Policies, state machines, validation, retries

| **Test level** | **Main purpose** | **Expected execution** |
| --- | --- | --- |
| Unit | Validate isolated business rules | Every change |
| Integration | Validate components working together | Every change or relevant merge |
| Contract | Verify API and bridge interfaces remain compatible | Every change affecting a contract |
| Security | Verify access controls and prohibited operations | Every change affecting security; full suite before release |
| End-to-end | Verify real user journeys | Before merge to release branch and each release |
| Reliability | Verify recovery from faults | Before release and after execution changes |
| Performance | Measure latency, resource usage and concurrency | Baseline early; regression checks and release benchmark |
| Model evaluation | Measure planning quality and unsafe proposals | Model/prompt changes and release evaluation |

These are complementary layers. Passing one does not replace the others.

## 03.18.4 Unit test requirements

Unit tests should be fast, deterministic and independent of live network services.

### A. Authorization and policy engine

Test that:

- A user cannot access another user's task or memory.

- A device cannot execute an operation targeted at another device.

- An unknown tool is rejected.

- A directory identifier outside the permitted scope is rejected.

- A prohibited operation remains prohibited even if the model or user requests it.

- An expired, rejected or mismatched approval does not authorize execution.

- Changing an operation's arguments invalidates the original approval.

- A revoked device cannot start new operations.

### B. Task state machine

Test every legal transition and representative illegal transitions. For example:

- queued → running

- running → waiting_for_approval

- running → succeeded

- running → interrupted

- interrupted → running only after the recovery rules are satisfied

- Terminal states cannot silently return to active execution.

The exact transition table must be finalized before implementation. The examples above are intended to guide that specification.

### C. Idempotency and retry decisions

Test that:

- A duplicate task submission with the same user, request ID and payload returns the existing task.

- Reusing that request ID with a different payload produces a conflict.

- Read-only operations can be retried only within their configured retry policy.

- An uncertain file-creation outcome triggers reconciliation rather than blind repetition.

- A timeout is not automatically interpreted as proof that an operation failed.

### D. Input and output validation

Test malformed task requests, invalid tool arguments, oversized inputs, unexpected response structures, missing fields and unsupported schema versions.

### E. Memory

Test ownership filtering, duplicate handling, update behavior, deletion from active retrieval, conflict handling and exclusion of unauthorized memories from the context supplied to the model.

## 03.18.5 Integration and database testing

Integration tests verify behavior across service boundaries using real dependencies where correctness depends on them.

Required integration coverage:

- FastAPI request validation and authentication.

- Database migrations against a clean PostgreSQL database.

- Task creation and duplicate-submission protection.

- Atomic task/step claiming by competing workers.

- Approval and execution coordination.

- Task history and audit-event persistence.

- Memory creation, retrieval, correction and deletion.

- Device registration, revocation and last-seen status.

- Restart recovery for tasks that were active when the backend stopped.

### PostgreSQL concurrency tests

These are particularly important for NEXUS because multiple developers may submit requests at the same time.

The tests must verify that:

1. Two simultaneous submissions using the same idempotency key do not create two tasks.

2. Two workers competing for the same work item cannot both acquire a valid execution claim.

3. A stale worker cannot overwrite the state committed by a newer worker.

4. Concurrent cancellation and approval requests result in a defined, valid state.

5. Database constraints prevent duplicate step numbers and operation identifiers where uniqueness is required.

6. Transaction failures do not leave partially persisted application state.

Use independent database sessions and genuinely concurrent test execution. Merely calling the same function twice sequentially is insufficient.

Important boundary: PostgreSQL can protect NEXUS's own records, but it cannot atomically commit a database transaction and an external Windows filesystem or application operation. Reliability tests must explicitly cover that gap.

## 03.18.6 Windows bridge contract and filesystem tests

The bridge is a security boundary, not just a helper process. It must validate incoming requests independently of the backend's validation.

### Bridge contract tests

- Valid requests using a supported protocol and schema are processed correctly.

- Unsupported protocol versions and unknown tool names are rejected.

- Requests targeting another device are rejected.

- Invalid arguments, expired deadlines and oversized payloads are rejected.

- Duplicate operation IDs do not blindly execute the operation again.

- Revoked or unauthenticated clients cannot issue operations.

- Bridge responses use documented status and error formats.

- Backend timeouts, bridge crashes and lost responses are represented accurately.

- Incompatible API/backend and bridge versions fail safely with a diagnosable error.

### Windows filesystem tests

Use temporary test directories and generated test files, never personal or production documents.

| **Scenario** | **Expected result** |
| --- | --- |
| Search an authorized directory | Only permitted matching files are returned |
| Request a directory outside the configured scope | Rejected |
| Attempt path traversal | Rejected |
| Attempt unauthorized UNC/network path access | Rejected unless explicitly supported and authorized |
| Create a file at a new destination | File created and verified |
| Create a file where one already exists | No silent overwrite |
| Supply malformed or excessive input | Rejected within defined resource limits |
| File is locked, missing or inaccessible | Structured error; no false success |
| Bridge restarts after an operation | Reconciliation follows the operation's retry policy |

Path validation must account for Windows path semantics, including case-insensitive comparisons, junctions/reparse points and races between validation and file access. A simple string-prefix check is not an adequate security boundary.

### Application-launch tests

Test the configured application allowlist, invalid application IDs, executable-path substitution attempts, malformed arguments and launch failures. Verify that a successful process launch is not reported as proof that the entire user-requested workflow completed.

GUI interaction beyond the agreed MVP scope must not be treated as covered merely because application launching works.

## 03.18.7 Security and adversarial testing

Security tests must exercise the complete authorization path: CLI/API, task service, policy engine, orchestrator, bridge and local tool.

Identity and tenant isolation

Attempt to read, update, cancel or approve another user's task; access another user's memory; submit forged device IDs; and use revoked credentials.

Prompt injection and untrusted content

Include instructions in test documents asking the model to reveal secrets, change permissions, read unrelated folders or bypass approval. Confirm that content cannot alter application-enforced policy.

Approval integrity

Replay approvals, modify arguments after approval, target a different device, use expired approvals and race approval against cancellation. All must follow the defined policy.

Execution restrictions

Try unknown tools, shell-like payloads, executable-path injection and arguments designed to escape a permitted directory. Confirm that no unrestricted command execution path exists.

Secrets and private data

Verify that passwords, access tokens, bridge credentials and unnecessary document contents are not exposed in logs, API errors, audit metadata or test artifacts.

Security tests should include both expected-denial tests and expected-allow tests. A system that rejects everything is not secure in a useful operational sense; permitted actions must still work.

## 03.18.8 Reliability, recovery and fault injection

Fault-injection tests deliberately interrupt NEXUS at dangerous boundaries to prove its recovery behavior.

| **Injected failure** | **Required behavior** |
| --- | --- |
| Backend stops before an operation is dispatched | Task remains recoverable; no unrecorded dispatch is assumed |
| Backend stops after dispatch but before recording the result | Operation is reconciled before any unsafe retry |
| Bridge performs a write but its response is lost | Outcome is treated as uncertain until reconciled |
| Device disconnects during execution | No silent rerouting; status reflects interruption or uncertainty |
| Database connection fails | No false success response or untracked state transition |
| Model runtime becomes unavailable | Deterministic operations remain usable where possible; AI-dependent tasks fail or pause honestly |
| Approval expires while a task waits | Operation cannot proceed using the expired approval |
| Cancellation races with dispatch | No new operation is dispatched after cancellation takes effect under the defined rules |
| Worker lease expires while the old worker is still alive | Stale worker cannot commit conflicting state; duplicate external execution is prevented or reconciled |
| Bridge restarts with an operation in progress | Reports known state and follows safe reconciliation rules |

Tests should inject failures at multiple points in the operation lifecycle, not just simulate a generic service outage.

Release-blocking reliability rule: NEXUS must never report an uncertain external operation as definitely successful or definitely failed without sufficient evidence.

## 03.18.9 AI model and planning evaluation

AI evaluation must be repeatable and separate from live user requests. The test suite should contain a version-controlled evaluation set of representative tasks, including ambiguous requests, unsupported requests, permission-boundary attempts and malicious document instructions.

### Evaluation categories

- Tool selection: Did the planner choose a registered tool appropriate for the request?

- Argument correctness: Are required arguments present and valid?

- Plan quality: Are steps ordered correctly, dependencies represented and verification included where required?

- Clarification: Does NEXUS ask a question when essential information is missing?

- Scope adherence: Does it remain within the user's permissions and the selected device?

- Prompt-injection resistance: Does untrusted content fail to expand access or grant authority?

- Failure honesty: Does it communicate unsupported operations and model failures accurately?

- Context quality: Does hybrid retrieval find relevant information without including another user's private context?

Track both model output quality and downstream safety enforcement. An unsafe proposal that the policy engine blocks is still a planning-quality defect, but it must not become an execution failure.

### Proposed initial model-evaluation metrics

| **Metric** | **Measurement** |
| --- | --- |
| Structured-plan validity | Percentage of outputs matching the required plan schema |
| Tool-selection accuracy | Percentage of evaluation cases selecting an acceptable tool |
| Argument validity | Percentage of tool proposals passing schema and semantic validation |
| Clarification quality | Percentage of ambiguous cases handled according to the expected decision |
| Unauthorized execution | Count of prohibited operations actually executed |
| Retrieval relevance | Relevance of retrieved memories/documents to the evaluation query |
| Planning latency | Median and 95th-percentile response time on the designated host |

The required thresholds for planning quality, latency and retrieval relevance remain open decisions until a baseline is measured on the actual AMD GPU and designated host. Unauthorized execution must have a zero-tolerance release criterion in the tested scenarios.

A fixed, curated evaluation set is necessary so model or prompt changes can be compared against a stable baseline. It should include positive examples as well as adversarial cases.

## 03.18.10 End-to-end acceptance scenarios

These scenarios verify that NEXUS works as a product rather than merely as a collection of components.

### E2E-01 — First-time setup

1. A developer follows the onboarding documentation on a clean supported environment.

2. The developer configures the backend connection and Windows bridge.

3. The database migrations complete successfully.

4. The developer registers their device and authenticates.

5. The developer runs a safe smoke-test task.

Pass condition: the setup is reproducible without undocumented manual fixes, and the task's result is verified.

### E2E-02 — Search and read a permitted document

1. A user requests a search within an authorized directory.

2. NEXUS plans the operation using a registered tool.

3. The policy engine validates the user's scope.

4. The bridge searches and returns bounded results.

5. NEXUS reports the result and records task history.

Pass condition: only authorized content is returned, the correct device executes the task and history reflects the actual outcome.

### E2E-03 — Create a file safely

1. A user requests a new file in an approved workspace.

2. NEXUS presents an approval request if the configured policy requires it.

3. The exact operation and destination are validated.

4. The bridge creates the file without overwriting an existing destination.

5. NEXUS verifies the result.

Pass condition: the file exists with the expected contents, and no unauthorized or unintended overwrite occurs.

### E2E-04 — Multiple developers and devices

1. At least two users authenticate from different clients.

2. Each user submits tasks targeting their own registered device.

3. Both tasks progress concurrently.

4. Each user inspects their own history and memory.

5. Cross-user and cross-device access attempts are rejected.

Pass condition: concurrency works within configured limits and no cross-user data or operation leakage occurs.

### E2E-05 — Interrupted operation

1. Start an operation with an external side effect.

2. Simulate a bridge disconnect or lost response.

3. Restart or reconnect the relevant component.

4. Inspect task and step state.

5. Allow reconciliation before retrying any uncertain operation.

Pass condition: the task does not silently switch devices, duplicate an unsafe action or falsely report completion.

### E2E-06 — AI unavailable

1. Stop the model runtime.

2. Submit a request requiring AI planning.

3. Submit a deterministic operation that does not require a model, where the product supports it.

4. Restart the model runtime and verify recovery.

Pass condition: AI-dependent work fails or pauses clearly, while independent functions continue to work where designed.

### E2E-07 — Memory lifecycle

1. Save an explicitly requested memory.

2. Retrieve it in a relevant future task.

3. Update or correct it.

4. Delete it.

5. Verify it is no longer returned by active retrieval.

Pass condition: memory ownership and lifecycle rules hold, and deletion does not unintentionally delete unrelated task history.

## 03.18.11 Performance and capacity testing

NEXUS should be measured on the actual development and deployment hardware, rather than relying on generic benchmark figures.

Test these workloads:

- One user submitting and completing a task.

- Three users submitting tasks concurrently.

- Several tasks waiting for approvals while other tasks execute.

- Concurrent memory searches and task-history queries.

- Slow model inference or a model that temporarily stops responding.

- A bridge that responds slowly or disconnects.

- Large-but-allowed directory searches and supported document reads.

Record:

- API response latency, including median and p95.

- Task queue wait time separately from model-planning and tool-execution time.

- Database query latency and lock contention.

- Model latency, RAM use, GPU utilization and VRAM use where available.

- Bridge operation latency and timeout rates.

- Error rate, retry rate and number of uncertain operations.

- Behavior as concurrent task volume increases.

### Proposed performance targets

The following are candidate targets for discussion, not confirmed requirements or measured capabilities.

| **Area** | **Proposed initial target** |
| --- | --- |
| Basic API reads | p95 under 500 ms under a small controlled test load |
| Task acceptance | p95 under 1 second, excluding long-running work |
| Concurrent use | Three active users without cross-user interference or state corruption |
| Recovery | All injected crash scenarios reach a documented recoverable or terminal state |
| AI-dependent tasks | Establish a measured baseline first; set the target after benchmarking the designated host |

These targets must be validated and adjusted using the real environment. AI inference, filesystem size, network conditions and document extraction can dominate end-to-end latency.

## 03.18.12 Test data and environment strategy

Tests must not depend on private user documents, production credentials or manually prepared undocumented database state.

Required test environments:

- Unit environment: isolated functions, controlled dependencies and fake model responses.

- Integration environment: dedicated PostgreSQL database and controlled service dependencies.

- Windows bridge environment: Windows-side tests against temporary directories and safe test applications.

- End-to-end environment: isolated NEXUS deployment with test accounts and registered test devices.

- Model evaluation environment: fixed evaluation dataset and recorded model/runtime configuration.

Test fixtures should create their own users, devices, tasks, memories and directories, then clean up after completion. Tests must not share mutable state in a way that makes their outcomes depend on execution order.

The team must also define a deterministic way to simulate:

- Model success, malformed output and timeout.

- Bridge success, rejection, timeout and lost response.

- Database failure and transaction conflicts.

- Approval, cancellation and device-revocation races.

For AI-dependent tests, use canned model responses for ordinary CI runs. Run a separate real-model evaluation on the designated inference host.

## 03.18.13 Continuous integration and quality gates

Every pull request should pass a consistent automated pipeline before merge.

### Proposed pull-request pipeline

1. Static checks — formatting, linting, type checks where configured, dependency and secret scanning.

2. Unit tests — domain rules, authorization, state machine, validation, retry decisions and memory logic.

3. Integration tests — PostgreSQL transactions, constraints, migrations and API/service interactions.

4. Contract tests — API schemas, tool schemas, bridge protocol and supported version compatibility.

5. Security regression tests — tenant isolation, policy enforcement, approval integrity and prohibited operations.

6. Build and packaging checks — backend and CLI build; Windows bridge checks on a Windows runner or designated Windows test machine.

A release candidate additionally requires:

- The end-to-end acceptance scenarios to pass.

- The reliability and recovery suite to pass.

- No unresolved critical or high-severity security defect.

- A successful fresh-install and database-migration test.

- A real-model benchmark and evaluation run on the designated host.

- Review of performance regressions, logs and known limitations.

- Updated setup instructions and release notes.

### Coverage policy

Do not use overall line coverage as the only quality metric. High coverage can still miss critical races and unsafe behavior.

Proposed initial coverage goals:

- Aim for at least 80% line coverage across core backend/domain logic.

- Require direct tests for every critical authorization rule and task-state invariant.

- Require negative tests for every high-risk tool and permission boundary.

- Require PostgreSQL-backed tests for concurrency and transactional invariants.

- Require recovery tests for every operation type that can produce an external side effect.

The 80% figure is a proposed team target. The security and correctness requirements are mandatory even if the overall coverage percentage is met.

## 03.18.14 Defect severity and release decisions

The team needs a shared rule for deciding whether a defect blocks a release.

| **Severity** | **Example** | **Release decision** |
| --- | --- | --- |
| Critical | Unauthorized file access, cross-user data exposure, prohibited operation executed | Release blocked |
| High | Unsafe duplicate write, approval bypass, corrupted task state, broken recovery | Release blocked |
| Medium | Major supported workflow fails, but no security boundary is breached | Block if a core MVP journey is affected; otherwise document and decide explicitly |
| Low | Minor CLI usability issue or non-critical diagnostic detail | May release with a recorded issue |

Severity is based on impact, not how easy the defect is to fix. A rare security defect can still be critical.

Every release-blocking defect must have a reproducible test or an explicitly documented reason why automated reproduction is not yet feasible.

## 03.18.15 Team responsibilities

The three developers should own the tests closest to their respective modules, while jointly reviewing cross-component risks.

| **Owner** | **Primary testing responsibility** |
| --- | --- |
| Developer 1 — Backend and execution | Task state machine, PostgreSQL transactions, worker concurrency, cancellation, idempotency and recovery |
| Developer 2 — Windows integration | Bridge contracts, filesystem safety, application allowlist, device disconnects and Windows-specific tests |
| Developer 3 — AI and context | Model evaluation, plan validation, retrieval quality, prompt-injection resistance and memory lifecycle |
| All three | API contract changes, end-to-end journeys, security review, release acceptance and clean setup validation |

These are proposed ownership assignments, consistent with the architecture. They do not mean only one developer is responsible for security: each developer must test the security boundary of their own module.

Every pull request that changes a shared contract must include the relevant contract-test updates or explain why no test change is needed.

## 03.18.16 Definition of done

A feature is not complete merely because its happy path works.

A feature is considered done when:

- Its functional requirements and failure behavior are documented.

- Inputs and outputs are validated.

- Authorization and relevant risk checks are enforced.

- Unit and appropriate integration tests pass.

- Negative tests cover important invalid or unauthorized cases.

- Persistent state changes are tested where applicable.

- Logs and error responses are useful without exposing secrets.

- The behavior has been tested on the relevant operating system or runtime.

- Documentation and example configuration are updated.

- Known limitations and unimplemented requirements are recorded.

For external side effects, the definition of done also includes retry, timeout, cancellation and uncertain-outcome behavior.

## 03.18.17 Open decisions

The following details must be agreed or measured before the testing strategy can be finalized.

| **Decision** | **Current position** |
| --- | --- |
| CI platform | Open; choose a free option compatible with the repository and Windows bridge tests |
| PostgreSQL version | Must be pinned before integration testing |
| Python and dependency versions | Must be pinned for reproducible builds |
| Model evaluation thresholds | Set after baseline measurements on the designated host |
| Performance targets | Proposed targets above require validation |
| Test runner and lint tools | Select during repository setup |
| Windows test execution | Confirm available Windows runner or dedicated test machine |
| Test retention and artifacts | Keep sufficient diagnostics without retaining unnecessary private content |
| Release cadence | Define a repeatable release checklist and ownership |

## 03.18.18 Acceptance checklist

### Readiness review

0 of 15 checked

Core correctness

Unit tests cover task states, policy rules and tool validation.

PostgreSQL tests verify uniqueness, transactions and concurrent claims.

API and bridge contract tests pass.

Security

Cross-user and cross-device access attempts are rejected.

Approval replay, argument changes and expiry are tested.

Untrusted documents cannot grant permissions or bypass the tool allowlist.

No unrestricted model-generated shell execution path exists.

Reliability

Crash and disconnect tests cover external side effects.

Uncertain operations are reconciled before unsafe retries.

Cancellation and approval races have defined outcomes.

Restart recovery preserves accurate task state.

Product readiness

Core end-to-end journeys pass on the real Windows environment.

Three-user concurrency has been tested.

Model evaluation and performance baselines are recorded.

A clean setup, migration and release procedure is reproducible.

Copy checklist

The checklist is a working review aid, not evidence that tests have passed. Check items only when the team has actual test results or documented evidence.

## Section 03.18 exit criterion: the team agrees on the test layers, security gates, reliability scenarios, model evaluation approach and release-blocking defects. Numeric performance and model-quality thresholds may remain provisional until measured, but critical safety properties must be defined before implementing real computer-execution tools.
