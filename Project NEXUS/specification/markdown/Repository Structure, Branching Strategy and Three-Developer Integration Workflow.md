## 04.04.01 Purpose

NEXUS has three developers working on tightly connected components: backend execution, Windows integration, and AI/context. The main engineering risk is not simply that individual components fail. It is that the components evolve incompatible interfaces and only discover the mismatch near the end of the 10–12-week schedule.

This section defines how the team will:

- Organize the repository around the approved architecture.

- Establish shared contracts before parallel development.

- Manage branches, pull requests and code reviews.

- Run automated checks consistently.

- Integrate Windows, WSL 2, PostgreSQL and local inference.

- Keep all three developers working against the same tested contracts.

The guiding principle is parallel implementation behind agreed interfaces, followed by continuous integration into one working system.

## 04.04.02 Repository structure

The repository should reflect the logical architecture already defined in Section 03.08. The following is the proposed structure, not a claim that every file needs to exist on day one.

nexus/

├── apps/

│   ├── api/                  # FastAPI application and routes

│   ├── cli/                  # Terminal interface

│   └── windows_bridge/       # Native Windows process

│

├── nexus_core/

│   ├── domain/               # Framework-independent domain types

│   ├── services/             # Application use cases

│   ├── execution/            # Task state, orchestration, recovery

│   ├── tools/                # Registry, schemas, tool policies

│   ├── ai/                   # Planner and context assembly

│   ├── memory/               # Memory lifecycle and retrieval

│   ├── security/             # Authorization and policy enforcement

│   ├── infrastructure/

│   │   ├── database/

│   │   ├── model_adapters/

│   │   └── bridge_transport/

│   └── observability/        # Structured logging and diagnostics

│

├── migrations/               # Database schema migrations

├── contracts/

│   ├── api/

│   ├── bridge/

│   ├── tools/

│   └── events/

│

├── tests/

│   ├── unit/

│   ├── integration/

│   ├── contract/

│   ├── security/

│   ├── reliability/

│   └── end_to_end/

│

├── deploy/

│   ├── docker-compose.yml

│   └── config/

├── scripts/

├── docs/

│   ├── architecture/

│   ├── decisions/

│   ├── testing/

│   └── operations/

│

├── .env.example

├── .gitignore

├── pyproject.toml

└── README.md

### Structure rules

1. nexus_core/domain/ contains domain rules and types without depending on FastAPI, a model runtime or database session APIs.

2. apps/api/ translates HTTP requests into application-service calls. It must not independently implement task authorization or execution logic.

3. apps/windows_bridge/ is packaged and run as a native Windows-side process.

4. nexus_core/ai/ generates proposals; it does not become an alternate execution or permission layer.

5. contracts/ contains reviewed interface definitions and examples used by multiple components.

6. migrations/ contains version-controlled database changes. Developers must not rely on undocumented manual schema modifications.

7. tests/ separates fast deterministic tests from tests requiring PostgreSQL, Windows or a real model.

8. docs/decisions/ stores the architecture decision records from Section 04.01.

Avoid creating empty abstractions for hypothetical future services. Add modules when there is a defined responsibility and a concrete consumer.

## 04.04.03 Branching and pull-request strategy

For a three-developer project with a 10–12-week timeline, use a lightweight branching strategy. Long-lived branches increase integration risk because changes to shared contracts, database migrations and task-state logic quickly become interdependent.

### Proposed branch model

- main — the latest integrated, tested and releasable version.

- feat/<short-name> — a focused feature.

- fix/<short-name> — a defect correction.

- docs/<short-name> — a documentation-only change.

- test/<short-name> — a focused test addition or improvement.

Examples:

feat/task-state-machine

feat/windows-file-search

feat/local-model-adapter

fix/duplicate-task-submission

docs/bridge-protocol

Use short-lived branches and merge through pull requests. Do not let each developer maintain a separate long-lived integration branch.

### Pull-request rules

Every pull request should include:

- The problem being solved.

- The relevant requirement or architecture decision.

- The interface or database changes, if any.

- Tests added or updated.

- Security and failure-handling implications.

- Configuration or migration changes.

- Known limitations.

A pull request that changes a shared contract must identify affected consumers. For example, changing a bridge response field requires checking the backend dispatcher, bridge implementation, contract tests and recovery handling.

### Merge requirements

The proposed baseline is:

1. The change is small enough to review.

2. Automated checks pass.

3. At least one other developer reviews the change.

4. Security-sensitive changes receive appropriate cross-review.

5. Contract and migration changes are backward-compatible where required, or coordinated with their consumers.

6. The branch is integrated with the current main without unresolved conflicts.

A passing test suite is necessary but not sufficient if the change violates an architecture decision or creates an untested side-effect failure.

## 04.04.04 Shared contracts before parallel implementation

Before the three developers build their components independently, agree on the minimum interfaces they will share.

Task and state contract

Developer 1

Task identifiers, state names, legal transitions, error representation and operation correlation.

Bridge protocol and tool contracts

Developer 2 + Developer 1

Authenticated request envelope, tool schemas, result statuses, timeouts and duplicate-delivery behavior.

Planning contract

Developer 3 + Developer 1

Structured plan format, clarification response, dependency references and validation failures.

Memory and context contract

Developer 3

Memory ownership, provenance, retrieval response and deletion behavior.

Authentication and authorization contract

Developer 1 + Developer 2

User identity, device identity, target-device ownership, approval binding and local bridge enforcement.

### Contract approval process

For each contract:

1. Write the proposed request and response schemas.

2. Document required and optional fields.

3. Define validation and failure behavior.

4. Define version compatibility rules.

5. Add representative valid and invalid examples.

6. Write contract tests.

7. Have the producer and consumer owners review the interface.

8. Freeze the initial version for the first integration milestone.

“Freeze” does not mean the interface can never change. It means changes require an explicit review of compatibility and affected components.

### Important ownership rule

The developer who owns a component owns its implementation, but not unilateral control over a cross-component contract.

For example, Developer 3 can propose a change to the plan format, but Developer 1 must verify its effect on validation and orchestration, and Developer 2 must verify whether it affects the bridge protocol or tool arguments.

## 04.04.05 Continuous integration and quality gates

The team should automate repeatable checks as early as possible. The exact CI platform is an implementation decision; the required checks should not depend on a particular vendor.

### Proposed pipeline

The pipeline should separate checks by cost and environment.

| **Test layer** | **Typical trigger** | **Dependency** |
| --- | --- | --- |
| Formatting and static analysis | Every pull request | Python environment |
| Unit tests | Every pull request | No live model; external systems mocked |
| Contract tests | Every relevant pull request | Shared schemas and deterministic fixtures |
| PostgreSQL integration tests | Every backend or persistence change | Test database |
| Security regression tests | Every relevant change, with full suite regularly | Controlled fixtures and test identities |
| Windows bridge tests | Bridge changes and integration builds | Windows test environment |
| Real-model evaluation | Model/planner changes and release candidates | Selected runtime and model |
| Full end-to-end suite | Integration checkpoints and release candidates | Integrated backend, database and Windows bridge |

A test should not silently skip a required assertion because an external dependency is unavailable. If a test requires a real model or Windows host, the pipeline should report that the test was not run and reserve it for the appropriate environment.

## 04.04.06 Coding standards and implementation boundaries

The team should agree on a small set of rules before the codebase grows.

### Python standards

- Use a shared Python version and dependency configuration.

- Use type hints on public interfaces and important domain contracts.

- Validate external inputs at application boundaries.

- Use typed, stable error codes rather than relying on exception text.

- Keep functions and modules focused on one responsibility.

- Use asynchronous I/O where it is beneficial, without assuming that CPU-heavy work becomes non-blocking merely by using async def.

- Define explicit timeouts for network calls and external processes.

- Avoid hidden global state for users, devices, task ownership and permissions.

- Keep secrets and machine-specific paths out of source code.

The exact formatter, linter, type checker and test libraries should be selected once and documented in the repository. Consistency matters more than adopting a large collection of tools.

### Dependency direction

The following dependency direction is proposed:

- Domain types → independent of application frameworks.

- Application services → use domain rules and defined interfaces.

- Infrastructure → implements database, model and bridge interfaces.

- API and CLI → call application services or documented APIs.

- AI planner → produces proposals that application services validate.

- Windows bridge → executes registered local tools after its own validation.

Do not allow the CLI to bypass the backend and write directly to PostgreSQL. Do not let the planner call arbitrary Windows functions. Do not let API route handlers implement a second, competing task state machine.

## 04.04.07 Database migration workflow

Database changes require particular care because the task state, operation identity and recovery model depend on consistent persisted data.

Every schema change should follow this process:

1. Define the requirement and the affected records.

2. Update the data model and migration.

3. Identify constraints, indexes and ownership rules affected.

4. Test the migration against a clean PostgreSQL database.

5. Test the upgrade path from the previous supported schema.

6. Test affected queries and concurrency behavior.

7. Review how the application behaves if migration fails.

8. Merge the migration with the corresponding code change.

9. Document any operational migration or recovery requirement.

### Migration rules

- Never rely on manually changing the shared development database without a corresponding migration.

- Avoid two developers independently editing the same migration.

- Do not assume a database rollback reverses a Windows filesystem operation.

- Test migrations using PostgreSQL, not only an in-memory database.

- Keep schema version and application version compatibility documented.

- Back up required data before a potentially destructive deployment migration.

Developer 1 owns the migration workflow, but the other developers must review changes affecting memory, bridge operation records or tool execution.

## 04.04.08 Development, test and integration environments

NEXUS requires more than one environment because not every test should operate on a real Windows computer or invoke a real AI model.

### 1. Local development

Purpose: fast individual progress

Developers run the components they own, using mock interfaces or isolated dependencies when practical.

### 2. Automated integration environment

Purpose: reproducible backend correctness

Use a dedicated PostgreSQL test database, deterministic model fixtures, isolated test directories and test identities. Never run destructive tests against shared user data.

### 3. Native Windows integration environment

Purpose: validate actual Windows behavior

Test path handling, local bridge authentication, filesystem operations, application launching and recovery on Windows.

### 4. Shared team integration environment

Purpose: validate the complete system

Run the shared backend, PostgreSQL, selected local model and registered Windows bridges with separate test users and controlled permissions.

### Environment isolation rules

- Automated tests must never use the production or shared team database by default.

- Filesystem tests must use designated temporary directories.

- Test credentials must be distinct from real user credentials.

- Model tests must use fixed, documented inputs.

- A failed integration test must not leave a real user's task or files modified.

- Environment variables and secrets must not be copied into logs or test artifacts.

- The shared host must not silently become a developer's personal test environment for destructive operations.

## 04.04.09 Team integration workflow

Use the following loop throughout the project:

1. Plan: identify the requirement, dependency and acceptance test.

2. Contract: agree on the interface if another component consumes the change.

3. Implement: work on a focused branch.

4. Test locally: run the relevant unit and contract tests.

5. Review: obtain a second developer's review.

6. Integrate: merge into the current shared branch.

7. Verify: run the tests appropriate to the integrated environment.

8. Document: update contracts, decisions and known limitations.

9. Demonstrate: show the behavior using the actual supported workflow.

The team should integrate frequently. Waiting until a feature is “fully finished” before connecting it to the rest of NEXUS makes interface mismatches and architectural mistakes more expensive to correct.

### Daily coordination

A short daily engineering sync should answer:

- What contract or component changed?

- What is blocked?

- What has merged and passed integration tests?

- Is anyone implementing against an outdated schema?

- Has any assumption been discovered to be false?

- What is the next demonstrable end-to-end result?

The purpose is to expose dependencies early, not to create unnecessary status reporting.

## 04.04.10 First vertical-slice milestone

The first integrated milestone should prove one complete, restricted operation from the user's terminal to the intended Windows computer and back.

Do not begin with complex document summarization, semantic memory or broad automation.

### Milestone definition

User request: search a configured directory on the explicitly selected Windows device for files matching a query.

The first vertical slice should include:

1. A user authenticates through the CLI.

2. The CLI submits a request with a target device and unique client request ID.

3. FastAPI authenticates the user and validates device ownership.

4. PostgreSQL stores the task and its initial state.

5. The task orchestrator validates the registered search_files tool and its arguments.

6. The backend dispatches an authenticated, versioned request to the intended Windows bridge.

7. The bridge validates the target, tool, configured directory scope and query limits.

8. The bridge returns a bounded structured result.

9. The backend persists the outcome and updates the task state.

10. The CLI displays the final status and result.

11. Tests demonstrate that duplicate submission, an unauthorized device and a disconnected bridge do not produce unsafe behavior.

### Why this milestone comes first

It exercises the most important architectural boundaries without requiring the local model to be operational. The team can test identity, task persistence, bridge transport, filesystem scope, result recording and CLI behavior using a deterministic request path.

After this passes, the same interfaces can be extended to document reading, AI planning and memory retrieval.

### Vertical-slice exit criteria

- The task can be traced across all participating components using stable IDs.

- The requested device is the device that actually executes the operation.

- Task state remains correct after backend restart.

- Invalid scope and unauthorized access are rejected.

- Duplicate delivery is handled according to the operation contract.

- Disconnection does not result in a false success claim.

- The workflow runs from a clean documented setup.

- Automated tests cover both successful and rejected requests.

## 04.04.11 Proposed ownership and review matrix

| **Area** | **Primary owner** | **Required review** |
| --- | --- | --- |
| API, database and task lifecycle | Developer 1 | Developer 2 or 3 for cross-component contracts |
| Windows bridge and filesystem tools | Developer 2 | Developer 1 for authorization and recovery |
| AI planner, model adapter and memory | Developer 3 | Developer 1 for execution boundaries and persistence |
| Shared contracts | Relevant producer and consumer owners | At least one affected consumer |
| Security-sensitive changes | Change owner | Another developer familiar with the affected boundary |
| Release candidate | All three | Evidence-based sign-off |

Ownership must not create isolated knowledge. Each developer should be able to explain the complete request lifecycle and understand the failure behavior of their dependencies.

## 04.04.12 Definition of done

- Repository structure and dependency rules are agreed.

- Branch naming and pull-request requirements are documented.

- Shared contracts have named owners and review requirements.

- CI covers unit, contract and PostgreSQL integration tests.

- Windows-specific tests have an appropriate execution environment.

- Database migrations are version-controlled and tested.

- Test and shared integration environments are isolated.

- The first vertical-slice workflow has an explicit acceptance test.

- All three developers have reviewed the integration workflow.

- The team can reproduce the documented development setup.

Section exit criterion: the team can develop components in parallel while maintaining compatible interfaces, automated quality gates and a continuously integrated version of NEXUS.

## Next: Section 04.05 — Development Environment Bootstrap and Reproducible Setup

This section will specify how all three developers set up NEXUS consistently, including:

- Git repository initialization and shared Python configuration.

- Ubuntu on WSL 2 and native Windows bridge prerequisites.

- PostgreSQL setup, migrations and isolated test databases.

- Environment variables, secrets and machine-specific configuration.

- Local AI runtime setup without making it a prerequisite for basic backend tests.

- A clean-install verification checklist so a new developer can reproduce the environment without relying on undocumented steps.

The objective is to make the repository usable by all three developers before the team begins parallel feature implementation.
