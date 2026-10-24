## 04.05.01 Purpose

Before the three developers implement features in parallel, they need a consistent development environment that can be recreated from the repository and its documentation.

NEXUS spans several execution environments:

- Windows 11 for user-facing computer operations.

- Ubuntu on WSL 2 for backend development.

- Python and FastAPI for the API and application services.

- PostgreSQL for durable application state.

- A native Windows process for the bridge.

- A local AI runtime for planning and context processing.

- Git and automated tests for shared development.

These components must not depend on one developer's machine-specific paths, untracked files, manually modified database or undocumented environment variables.

Goal: a new developer should be able to follow the setup instructions, run the backend and test suite, connect a test Windows bridge and understand which optional capabilities require additional setup.

This is a setup specification, not a command-by-command installation tutorial. Exact software versions should be selected and pinned after the host and runtime decisions in Sections 04.01–04.03 are resolved.

## 04.05.02 Standard development environments

Use separate environments for Linux-side development and Windows-specific execution.

### Ubuntu on WSL 2

Backend development environment

- Python virtual environment and project dependencies.

- FastAPI application and application services.

- Database migrations and backend tests.

- Git operations and development scripts.

### PostgreSQL

Application persistence

- Local or containerized development database.

- Separate test database.

- Version-controlled schema migrations.

### Windows 11

Native computer integration

- Windows bridge and local tool implementations.

- Filesystem security and path handling tests.

- Application-launch tests and bridge diagnostics.

- Windows-side credential storage if selected.

### Optional local AI runtime

Inference and planning evaluation

- Installed and tested independently.

- Fixed model/runtime versions for reproducible evaluation.

- Not required for deterministic backend unit tests.

### Environment rules

1. Run Windows-specific bridge code in the intended Windows environment rather than assuming Linux path and process semantics are equivalent.

2. Use a documented Python version and dependency lock or equivalent reproducible dependency specification.

3. Keep development and test databases separate.

4. Keep the model runtime optional for tests that do not require inference.

5. Do not expose PostgreSQL to the LAN merely to simplify development.

6. Do not assume that WSL 2 networking, filesystem mounts or GPU access behave identically on every developer's computer.

## 04.05.03 Software prerequisites and version policy

The team should maintain one approved version matrix in the repository.

| **Dependency** | **Required decision** | **Validation** |
| --- | --- | --- |
| Windows | Supported Windows 11 configuration | Bridge and filesystem tests |
| WSL 2 / Ubuntu | Supported distribution and configuration | Backend setup and network checks |
| Python | One supported version for backend and CLI | Clean environment installation |
| PostgreSQL | One supported major version | Migrations, transactions and locking tests |
| FastAPI and related packages | Pinned compatible versions | API and integration tests |
| SQLAlchemy and Alembic | Candidate persistence and migration stack | Fresh install and upgrade tests |
| Git | Supported version | Clone, branch and clean-checkout workflow |
| Docker / Docker Compose | Optional or standard deployment method | Repeatable service startup |
| AI runtime and model | Selected versions after benchmarking | Hardware compatibility and model evaluation |

Do not allow each developer to independently upgrade core dependencies. Dependency changes should be reviewed, tested and committed.

### Dependency management rules

- Declare direct dependencies in the project configuration.

- Commit the lock file if the chosen dependency manager supports one.

- Avoid unpinned production dependencies.

- Separate runtime dependencies from development and test dependencies.

- Document any native Windows-specific dependencies separately.

- Record the tested Python and PostgreSQL versions in the setup guide.

- Upgrade dependencies deliberately, not as an incidental fix for an unrelated issue.

Docker Compose is a candidate for reproducible PostgreSQL and backend services. The team should confirm whether it is the standard development path or an optional convenience before writing the final onboarding commands.

## 04.05.04 Repository bootstrap procedure

The repository should provide a single, documented onboarding sequence.

1. Obtain the repository

2. Clone the shared Git repository into the documented WSL filesystem location. Confirm that the working tree is clean before setup.

3. Create the Python environment

4. Use the documented Python version and project dependency configuration. Do not install project packages into Ubuntu's system Python.

5. Load safe configuration

6. Start from .env.example or the selected configuration template. Supply local secrets through the documented secret mechanism; never copy production credentials from another developer.

7. Start PostgreSQL

8. Use the approved local or containerized setup. Verify that the backend can connect and that the application and test databases are distinct.

9. Apply migrations

10. Run the version-controlled database migrations. Confirm that a clean database reaches the expected schema version without manual SQL changes.

11. Run deterministic tests

12. Execute formatting, static checks, unit tests and contract tests before attempting real model inference or Windows operations.

13. Start the API

14. Start FastAPI using the documented development command. Verify liveness, readiness and authentication behavior.

15. Configure the Windows bridge

16. Register a test device, establish its credentials and configure only a dedicated test directory. Verify that the bridge is associated with the correct device identity.

17. Run the first end-to-end test

18. Execute the restricted file-search workflow against the test directory and verify the task record, bridge result and CLI output.

19. Configure AI separately

20. Install the selected runtime and model only after the basic stack passes. Run the documented inference smoke test and fixed planning evaluation set.

The final repository must contain the exact commands, expected outputs and troubleshooting steps for the chosen configuration. The sequence above establishes the required order, not an assertion that the team's final tools have already been selected.

## 04.05.05 Configuration and secrets

Configuration must separate application-wide defaults from machine-specific details.

### Proposed configuration categories

| **Category** | **Examples** | **Handling** |
| --- | --- | --- |
| Application | Log level, request limits, environment name | Versioned configuration |
| Database | Connection settings, pool limits | Environment-specific configuration and protected credentials |
| Authentication | Signing keys, session settings | Protected secret mechanism |
| AI | Runtime endpoint, model identifier, inference limits | Versioned configuration |
| Windows bridge | Device identity, backend endpoint, local directories | Windows-specific configuration |
| Security policy | Enabled tools, directory scopes, permissions | Controlled configuration with validation |
| Diagnostics | Log level, health-check settings | Safe configuration, no secret exposure |

### Required files and rules

The repository should include:

- .env.example containing placeholders and non-secret defaults.

- .gitignore rules for local secrets, environment files, generated data and test artifacts.

- A configuration reference documenting each supported setting, its type, default, security implications and whether restart is required.

- Separate example configuration for backend and Windows bridge where their settings differ.

- Startup validation for missing or contradictory security-critical settings.

Never commit live credentials, signing keys, private device credentials or real user data. Never use a randomly regenerated signing key on every restart if doing so would invalidate or unpredictably alter session behavior.

Windows directory paths must be configured on the Windows bridge, mapped to logical directory IDs and validated locally. A Linux path in WSL is not automatically a valid Windows path.

## 04.05.06 Database setup and test isolation

The development environment must make it difficult to accidentally run tests against the wrong database.

The proposed setup defines three distinct uses:

- Developer database: personal, disposable development data.

- Automated test database: isolated and safe to reset as part of the test workflow.

- Shared integration database: controlled data for multi-user and end-to-end tests.

The shared integration database must not be used as the default database for destructive automated tests.

### Startup checks

Before migrations or tests run, the tooling should verify:

1. The configured database host and database name.

2. The intended environment.

3. That the target is not a protected shared or production-like database.

4. The current schema version.

5. The availability of the database dependency.

If the environment cannot be established safely, the operation should fail rather than guess.

### Migration acceptance

A developer must be able to:

- Create an empty database.

- Apply all migrations.

- Start the application.

- Run integration tests.

- Upgrade a database from the previously supported schema.

- Diagnose migration failures without manually editing schema state.

PostgreSQL integration tests are especially important for task idempotency, unique constraints, row locking, worker claims and concurrent state transitions. SQLite or an in-memory substitute cannot establish that these behaviors work correctly on PostgreSQL.

## 04.05.07 Windows bridge setup and safety

Each developer needs a native Windows bridge instance associated with their own registered device.

The setup process should cover:

- Installing the documented Windows-side dependencies.

- Loading machine-specific configuration.

- Registering the bridge with the backend.

- Provisioning a unique device credential.

- Mapping logical directory IDs to permitted local directories.

- Configuring approved application IDs, if application launching is enabled.

- Starting the bridge in the intended user context.

- Verifying connectivity and reported capabilities.

- Revoking and replacing the device credential in a controlled test.

### Safe initial configuration

Start with a dedicated test directory containing synthetic files. Do not initially point the bridge at an entire user profile, all drives or shared personal folders.

The bridge must reject:

- Unknown tools and unsupported protocol versions.

- Invalid or revoked device credentials.

- Requests targeting a different device.

- Directory IDs not configured locally.

- Paths that escape the permitted scope.

- File creation that would silently overwrite an existing file.

- Operations exceeding their configured limits.

The backend must not treat a successful bridge connection as proof that every tool is available. Tool capabilities and local directory configuration must be validated separately.

## 04.05.08 Deterministic testing without a live model

A core goal of this setup is that developers can work on NEXUS without waiting for an AI runtime to load or using real inference for every test.

The repository should provide deterministic fixtures for:

- Valid plans.

- Malformed model output.

- Unknown tools.

- Missing or invalid arguments.

- Clarification requests.

- Unauthorized device targets.

- Approval-required operations.

- Model timeouts and unavailability.

- Plans containing malicious or irrelevant document instructions.

A mock planner can return a predetermined proposal so the team can test the task state machine, policy engine and bridge protocol independently.

However, mock tests do not replace the real-model evaluation. Keep two separate claims:

- Deterministic contract tests passed: the application correctly handles known inputs and failures.

- Real-model evaluation passed: the selected runtime and model meet the documented quality and resource criteria.

This distinction prevents a fully mocked test suite from creating a false impression of AI readiness.

## 04.05.09 Clean-install and onboarding acceptance

The setup documentation is complete only when another developer can follow it without relying on undocumented assistance.

### Developer onboarding checklist

### 0/19

### Repository

Fresh clone works from the documented location

Python environment installs from the committed dependency specification

Formatting and unit tests run successfully

### Backend and database

API starts with validated configuration

PostgreSQL connects and migrations succeed

Test database is isolated from shared integration data

Health and readiness checks report the expected state

### Windows integration

Bridge registers with a unique device identity

Bridge authenticates and reports its capabilities

Scoped search works in the dedicated test directory

Unauthorized target and invalid paths are rejected

### AI readiness

Mock planner tests pass without a model

Model runtime setup is documented separately

Real inference smoke test records the runtime and model version

Model failure does not corrupt persisted tasks

### Reproducibility and security

No secrets are required from another developer

No live credentials or local data are committed

A second developer can reproduce the setup

Troubleshooting and cleanup instructions are documented

This checklist records your selections in the current interface; it does not execute setup commands or verify the repository.

## 04.05.10 Ownership and completion criteria

| **Owner** | **Setup responsibility** |
| --- | --- |
| Developer 1 | Python/backend setup, PostgreSQL, migrations, configuration validation and deterministic integration tests |
| Developer 2 | Native Windows bridge setup, device credentials, directory configuration and Windows-specific tests |
| Developer 3 | Model/runtime installation instructions, inference smoke tests and fixed evaluation dataset |
| All three | Clean-install reproduction, secret-safety review and first end-to-end workflow |

### Definition of done

- All three developers can clone and set up the repository independently.

- Core backend tests do not require a live AI model.

- PostgreSQL migrations work on a fresh database.

- Test data and test databases are isolated.

- Each bridge has a unique registered identity.

- Machine-specific directories and secrets are not embedded in source code.

- Model setup and hardware requirements are documented separately.

- The first end-to-end workflow passes on the shared integration environment.

- Setup instructions and troubleshooting steps have been validated by someone other than their author.

Section exit criterion: the team has a reproducible, secure development foundation that supports parallel implementation without depending on undocumented local configuration.
