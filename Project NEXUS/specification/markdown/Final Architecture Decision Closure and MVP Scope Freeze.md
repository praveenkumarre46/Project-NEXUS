## 04.27.01 Purpose

NEXUS now has a detailed functional specification, architecture, security model, execution protocol, testing strategy, deployment approach and recovery plan. The next risk is not a lack of design detail—it is allowing unresolved choices and expanding scope to delay implementation.

This section establishes a controlled baseline for the three-developer team.

It will:

- Separate confirmed requirements from proposed implementation decisions.

- Identify decisions that block implementation.

- Assign an owner and evidence requirement to unresolved choices.

- Freeze the first release's functional scope.

- Define what is explicitly deferred.

- Establish a change-control process.

- Set the conditions for moving from specification to implementation.

Core principle: freeze the scope and interfaces that the team needs to start building, not every implementation detail that can be learned through testing.

## 04.27.02 Decision status definitions

Every important decision should have one of these statuses.

| **Status** | **Meaning** |
| --- | --- |
| Confirmed | Explicitly selected or established by the project requirements |
| Provisional | Recommended baseline that can be changed if evidence contradicts it |
| Open | A decision remains to be made |
| Blocked | Work depends on a missing fact, capability or validation result |
| Deferred | Intentionally excluded from the initial release |

A provisional decision is not a confirmed fact. An open decision should have an owner, a deadline or milestone, and a clear way to resolve it.

## 04.27.03 Confirmed product baseline

The following items are established requirements for NEXUS.

Product and users

NEXUS is a local-first AI computer companion for a three-developer team. It combines useful Windows computer automation with context awareness and user-controlled memory.

Development environment

Windows 11 is the target computer environment. Ubuntu on WSL 2 is the development environment. The selected backend stack is Python, FastAPI and PostgreSQL.

User experience

Terminal-first interaction, durable task IDs, visible progress, explicit approval where required, cancellation, honest results and accessible task history.

Deployment and budget

Initial deployment is intended for the local network. No paid AI API or paid infrastructure is required for the intended baseline.

Security and reliability

User isolation, device identity, registered tools, policy enforcement outside the model, safe retries, recovery of uncertain operations and auditable consequential actions are core requirements.

Team and timeline

Three developers, with a 10–12 week target. A reliable, tested product is more important than forcing the project into ten weeks by cutting essential safety work.

The designated inference host, AMD GPU, balanced planning preference and hybrid retrieval preference are also recorded as user-selected preferences. Actual hardware compatibility, model selection and measured performance still require validation.

## 04.27.04 Architecture decisions proposed for the initial release

The following decisions are recommended as the working baseline. They should be recorded as provisional until the required validation is complete.

| **Decision** | **Recommended baseline** | **Closure evidence** |
| --- | --- | --- |
| Backend architecture | Modular monolith | Dependency rules and integration tests |
| Shared persistence | PostgreSQL | Migration and concurrency tests |
| Database coordination | PostgreSQL-backed worker claims and leases | Duplicate-claim and stale-worker tests |
| Windows execution | Native Windows bridge per computer | Windows integration and security tests |
| Bridge communication | Authenticated outbound polling | Connectivity, replay and revocation tests |
| Tool registration | Version-controlled registry | Schema and compatibility tests |
| Initial tools | Scoped file search, document reading, create-only file creation, allowlisted application launch | Tool-specific tests and safety review |
| AI authority | AI proposes; application code authorizes | Policy-bypass regression tests |
| AI runtime | Local runtime on designated team computer initially | Hardware benchmark and runtime evaluation |
| Memory retrieval | PostgreSQL lexical retrieval first; hybrid semantic retrieval behind an interface | Retrieval quality and privacy evaluation |
| Task recovery | Durable state, operation IDs, reconciliation and uncertainty | Failure-injection tests |
| GUI automation | Deferred beyond the initial safe tool set | Separate feasibility assessment |

These choices intentionally avoid adding a message broker, microservices, a separate vector database or a complex deployment platform before evidence demonstrates a need.

### Decision closure rules

A provisional decision becomes confirmed only when:

1. Its owner has gathered the required evidence.

2. The chosen option satisfies the relevant acceptance criteria.

3. Important alternatives and trade-offs are documented.

4. Affected interfaces and tests are updated.

5. The team records the decision and any remaining limitations.

If a decision fails validation, the team should select a tested alternative rather than quietly weakening the requirement.

## 04.27.05 Decisions that must close before implementation is blocked

Not every open question prevents the team from starting. The following distinctions keep implementation moving.

Must close before dependent work

Safety-critical interfaces

- User and device authentication contract.

- Task and step lifecycle rules.

- Bridge operation envelope and response contract.

- Tool schemas and authorization boundaries.

- Operation identity, deduplication and uncertain-outcome behavior.

- Database ownership constraints and migration workflow.

Must validate early

Hardware and deployment feasibility

- Exact AMD GPU model and available VRAM.

- Available RAM and storage headroom.

- Local runtime compatibility.

- Model quality and latency under representative load.

- Connectivity from the other Windows computers to the backend.

Can be finalized during implementation

Evidence-driven details

- Exact polling interval and worker lease duration.

- Initial concurrency limits.

- Document extraction and output-size limits.

- Backup retention and measured RPO/RTO.

- Retrieval ranking parameters.

- Performance thresholds beyond the initial proposed targets.

A detail may be finalized during implementation only if it does not undermine an already agreed safety invariant or force incompatible interfaces on other developers.

## 04.27.06 MVP scope freeze

The first release must deliver a complete, safe vertical workflow—not merely a functioning API or an impressive AI demonstration.

### Included in the initial MVP

### MVP acceptance checklist

0 of 15

Use this as a planning checklist. Checking an item here does not run a test or confirm implementation.

Authenticated users and private user data

Device registration, ownership and revocation

Terminal CLI for requests, status, history, approval and cancellation

Durable task and step lifecycle with duplicate-submission protection

Authenticated native Windows bridge

Registered tool catalogue and independent bridge-side validation

Scoped file search and supported document reading

Safe file creation in an approved workspace without silent overwrite

Allowlisted application launching

Risk-based permissions and operation-bound approvals

Operation journals, bounded retries and uncertain-outcome recovery

Local AI planning with structured-output validation

Explicit user-controlled memory and relevant context retrieval

Three-user integration, logs, diagnostics and protected backups

Installation, upgrade, recovery and testing documentation

These features are included in the full MVP target, although they will not all be implemented in the first development milestone.

### Explicitly excluded from the first release

- Unrestricted shell, PowerShell or Python execution generated by the model.

- Arbitrary mouse and keyboard control across the desktop.

- Unrestricted website navigation or account operations.

- Always-listening voice interaction.

- Shared personal memory by default.

- Automatic execution of consequential operations without required approval.

- Multi-host inference routing.

- A separate message broker or vector database without measured justification.

- A web-based administrative dashboard.

- Paid APIs or services required for core functionality.

An excluded feature can be reconsidered through change control, but it does not enter the MVP merely because it is technically interesting.

## 04.27.07 Minimum acceptable end-to-end workflows

The MVP is not complete until these workflows operate across the integrated system.

### Workflow A — Find and summarize a document

1. A user authenticates through the CLI.

2. The user selects or confirms a registered Windows device.

3. NEXUS persists the task and returns its ID.

4. The planner proposes a bounded plan using registered tools.

5. The backend validates permissions and the plan.

6. The bridge searches an authorized directory and reads supported content.

7. The AI produces a response grounded in retrieved evidence.

8. NEXUS records the result and reports the outcome.

Acceptance requires correct device targeting, bounded processing, source-grounded output and no unauthorized access. If the model or document reader fails, the result must say so.

### Workflow B — Create a file safely

1. The user requests file creation.

2. NEXUS validates the target device and approved workspace.

3. The backend validates the operation and obtains approval if required.

4. It persists the operation intent before dispatch.

5. The bridge independently validates the destination and content.

6. The bridge creates the file without silently overwriting an existing file.

7. NEXUS verifies the outcome and persists the result.

8. The CLI reports the destination and verification status.

Acceptance requires safe path handling, correct authorization and recovery of uncertain outcomes.

### Workflow C — Recover from a lost response

1. The bridge performs a write operation.

2. Its response is lost or the backend fails.

3. NEXUS preserves the operation as unresolved.

4. Recovery checks the operation journal and available external evidence.

5. The system determines the outcome where possible.

6. A retry occurs only if the tool's recovery rules permit it.

Acceptance requires that a successful external write is not blindly repeated.

### Workflow D — Preserve isolation under concurrency

1. All three developers submit tasks.

2. Tasks retain their owners and target devices.

3. Workers claim work without duplicate execution.

4. Permissions and policy are revalidated before dispatch.

5. One user cannot read another user's tasks or memory.

6. Device disconnection does not cause silent rerouting.

Acceptance requires correct authorization and safe concurrency, not just successful responses under load.

### Workflow E — Use and delete personal memory

1. A user explicitly saves a memory.

2. NEXUS stores its provenance and ownership.

3. A relevant later request retrieves it only for the authorized user.

4. The user inspects or corrects it.

5. The user deletes it.

6. Subsequent retrieval excludes the deleted memory and relevant indexes or caches are invalidated.

Acceptance requires owner-scoped retrieval and correct deletion behavior.

## 04.27.08 Architecture freeze and change control

Freezing scope does not mean freezing the architecture permanently. It means changes must be justified, reviewed and integrated deliberately.

### A change request must identify

- The requirement or defect motivating the change.

- The current decision and proposed replacement.

- The impact on API, bridge, tool schemas and database.

- Security, concurrency and recovery implications.

- Required migration and compatibility work.

- Test changes and acceptance criteria.

- Impact on the 10–12 week delivery target.

- Whether an existing MVP feature must be removed to accommodate the change.

### Change approval rules

- Security and correctness requirements cannot be removed merely to save time.

- A new feature requires an explicit scope trade-off.

- Shared contract changes require review by affected consumers.

- Database migrations require migration and recovery tests.

- Model changes require relevant evaluation.

- The decision register and implementation plan must be updated.

### Scope-expansion warning signs

The team should stop and review scope if it begins:

- Adding a new infrastructure service before measuring the need.

- Supporting a second automation approach before the first is reliable.

- Expanding tool permissions without tests.

- Changing contracts independently across components.

- Building a dashboard while core task recovery remains incomplete.

- Adding model features before the structured planner passes its safety tests.

The goal is a useful, reliable product—not the maximum number of features.

## 04.27.09 Decision register closure tracker

Use the following tracker to ensure that the specification's remaining open decisions are assigned and resolved. This is a proposed starting register; the team must fill in actual owners and evidence.

### Decision closure tracker

Planning aid only. These statuses are not automatically synchronized with project files or actual implementation.

All

Open

Provisional

Host hardware and network

Owner: Dev 1

Closure gate: Before deployment integration

Open

AMD runtime and model

Owner: Dev 3

Closure gate: Early model milestone

Open

Authentication and device credentials

Owner: Dev 1 + Dev 2

Closure gate: Before bridge integration

Open

Bridge polling and operation protocol

Owner: Dev 2 + Dev 1

Closure gate: Before end-to-end dispatch

Provisional

Tool schemas and limits

Owner: All three

Closure gate: Before tool implementation

Provisional

Document formats and resource limits

Owner: Dev 2 + Dev 3

Closure gate: Before document workflow

Open

Memory retrieval implementation

Owner: Dev 3

Closure gate: Before memory integration

Provisional

Backup retention and RPO/RTO

Owner: Dev 1 + all

Closure gate: Before release candidate

Open

Performance and concurrency limits

Owner: Dev 1 + Dev 3

Closure gate: After benchmark

Provisional

Installation and upgrade workflow

Owner: All three

Closure gate: Before team release

Open

### Exit criteria for architecture decisions

Before the team declares the architecture baseline frozen:

- Every safety-critical open decision has a resolution or a documented implementation blocker.

- Each provisional decision has an owner and a validation method.

- Hardware and model feasibility are tested on the actual designated computer.

- Shared contracts are versioned and agreed upon.

- Deferred features are recorded outside the MVP.

- No unresolved decision silently grants broader authority to the AI or bridge.

## 04.27.10 Definition of done

- Confirmed requirements are separated from provisional choices.

- Architecture-critical decisions have owners and closure criteria.

- MVP scope and exclusions are explicit.

- Five minimum end-to-end workflows are defined.

- Contract and security invariants remain unchanged.

- Scope changes require documented review.

- All three developers agree on module ownership and integration responsibilities.

- The implementation plan fits the intended 10–12 week window, with evidence-based adjustments where necessary.

- No critical dependency is treated as available without validation.

- The team is ready to begin the first vertical implementation slice.

Section exit criterion: NEXUS has a stable implementation baseline. Remaining unknowns are assigned work, not reasons to continue expanding the specification indefinitely.
