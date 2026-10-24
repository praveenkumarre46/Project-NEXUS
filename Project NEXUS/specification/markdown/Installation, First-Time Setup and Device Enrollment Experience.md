## 04.21.01 Purpose

NEXUS must be installable and usable by all three developers without requiring each person to reverse-engineer the setup process.

This section defines the path from a clean development environment to a verified working installation, including:

- Development prerequisites.

- Repository setup and dependency installation.

- PostgreSQL initialization and database migrations.

- FastAPI startup and health checks.

- Local AI runtime configuration.

- Native Windows bridge installation.

- User authentication and device enrollment.

- Initial permission configuration.

- End-to-end validation and troubleshooting.

Core principle: a successful installation means the system has passed a reproducible verification process—not merely that its processes started.

The setup must preserve the existing architecture: Windows 11 is the user's operating system, Ubuntu on WSL 2 is the primary backend development environment, and the Windows bridge executes approved local operations on each user's computer.

## 04.21.02 Supported installation topology

The initial deployment uses a designated team computer for the shared backend and local AI inference, subject to the hardware and compatibility assessment from Sections 04.02 and 04.03.

Designated team computer

FastAPI · PostgreSQL · Local AI runtime

Authenticated LAN communication

PC 1

CLI + Windows bridge

PC 2

CLI + Windows bridge

PC 3

CLI + Windows bridge

This is the target topology, not proof that the selected host or network is already ready.

### Deployment requirements

- Each developer uses their own authenticated NEXUS account.

- Each Windows bridge has its own device identity and credentials.

- Each bridge executes operations only on its registered computer.

- PostgreSQL is accessible only to authorized backend components.

- The model runtime is not exposed unnecessarily to the LAN.

- The backend must not be exposed to the public internet for the MVP.

- If the host is unavailable, clients must report the outage accurately; tasks must not silently move to another device or host.

## 04.21.03 Prerequisites

The team should maintain a versioned prerequisites document that records tested versions rather than relying on unpinned, moving dependencies.

| **Component** | **Requirement** |
| --- | --- |
| Operating system | Windows 11 on each user computer |
| Linux environment | Ubuntu under WSL 2 for backend development |
| Python | A project-pinned version supported by the selected dependencies |
| PostgreSQL | A documented, tested version |
| Git | Repository cloning and collaboration |
| Container tooling | Docker Desktop or another validated PostgreSQL deployment method, if selected |
| FastAPI environment | Project-managed Python dependencies |
| Windows bridge | Native Windows-compatible Python environment and dependencies |
| Local AI runtime | Version and model selected after hardware evaluation |
| Network | Reliable private LAN connectivity between clients and host |
| Storage | Sufficient capacity for the repository, database, model files, logs and backups |

Docker Compose remains a candidate for reproducible backend and database startup. The final choice should be recorded in the repository's deployment documentation.

The Windows bridge must be tested separately from the WSL backend. A Python package that works in Ubuntu must not be assumed to work identically in native Windows.

## 04.21.04 First-time setup sequence

The installation should follow a fixed order so developers can identify exactly which layer failed.

Step 1 — Obtain the repository

Clone the approved repository, check out the documented branch and confirm the working tree is clean before setup.

Step 2 — Install dependencies

Create the project-managed Python environment, install pinned dependencies and validate required tools.

Step 3 — Initialize PostgreSQL

Configure the database, apply versioned migrations and verify connectivity using the application's database role.

Step 4 — Start the backend

Validate configuration, start FastAPI and verify liveness, readiness and authenticated API behavior.

Step 5 — Validate the AI runtime

Load the selected local model, run the structured-output benchmark and verify the chosen GPU or CPU execution mode.

Step 6 — Install the Windows bridge

Configure the backend address, protect the device credential and run the bridge under the intended Windows user.

Step 7 — Enroll and authorize the device

Authenticate, register the bridge, verify device ownership and configure the initial directory and application permissions.

Step 8 — Run the smoke test

Submit a permitted read-only task, verify its execution and result, then confirm that unauthorized cross-user and cross-device access is denied.

Each step should produce a clear pass/fail result and a stable error code. A later step must not conceal a failure in an earlier prerequisite.

## 04.21.05 Repository and Python environment setup

The repository should provide one documented path for installing dependencies and running checks.

### Required repository assets

- README.md with the supported setup path.

- pyproject.toml and a committed dependency lock file, or another documented reproducible dependency mechanism.

- .env.example containing placeholders only.

- Database migrations.

- Backend, CLI and bridge startup instructions.

- A configuration validation command.

- Unit, integration and contract test instructions.

- A troubleshooting guide.

- A documented Windows bridge installation process.

### Environment isolation

Use a project-specific Python environment rather than installing application dependencies globally.

The exact Python version, dependency manager and lock-file format remain open until the team selects and validates them. Once chosen, all three developers should use the same supported versions.

The Windows bridge should have its own native Windows environment. Do not assume that a WSL virtual environment, Linux executable or Linux filesystem path is usable by the Windows bridge.

### Installation acceptance criteria

- A clean checkout can install the documented dependencies.

- Dependency versions are reproducible.

- Missing prerequisites produce actionable errors.

- Secrets are not required to be committed to the repository.

- Tests can run without requiring a live AI model for every unit test.

- The installation instructions have been verified by a team member other than the original author.

## 04.21.06 PostgreSQL initialization and migrations

Database setup must be repeatable and must not depend on manual schema changes that are absent from the repository.

### Setup workflow

1. Start the selected PostgreSQL deployment.

2. Create or provision the application database and a least-privilege application role.

3. Configure the backend's database connection through protected configuration.

4. Apply the committed migration sequence.

5. Verify the schema version and database connectivity.

6. Run a basic persistence test.

7. Confirm that the backend cannot accidentally use the production or shared team database during integration tests.

Alembic with SQLAlchemy remains the proposed migration approach.

### Rules

- A clean database must be buildable from migrations.

- Existing supported environments must be upgradeable through the documented migration path.

- Schema changes require reviewed migrations.

- Migration failure must stop deployment from being reported as ready.

- A migration rollback must not be assumed to reverse external Windows side effects.

- Test databases must be isolated from real user task history, permissions and memory.

- Database credentials must not be exposed in startup logs or diagnostic output.

## 04.21.07 Backend startup and readiness

The backend must distinguish being alive from being ready to accept work.

| **Status** | **Meaning** |
| --- | --- |
| LIVE | Backend process is responsive |
| READY | Required dependencies and configuration permit the supported service operations |
| DEGRADED | Some capabilities are unavailable, but explicitly supported functions remain usable |
| UNAVAILABLE | Required service behavior cannot safely proceed |

These are proposed health classifications; exact endpoint response contracts are to be finalized.

### Startup validation

The backend should validate:

- Required configuration values and secrets.

- Database connectivity and migration compatibility.

- Authentication and device-credential configuration.

- Policy and tool-registry validity.

- Model runtime configuration, where required.

- Resource and payload limits.

- Network bind address and service exposure.

- Required directories for backend-managed data.

The service must not advertise readiness for an operation that depends on an unavailable component.

For example, if the model runtime is down, a simple health request or eligible deterministic operation may still work, provided the system explicitly supports that degraded mode. An AI-dependent task must not be reported as completed when inference never occurred.

## 04.21.08 Local AI runtime installation and validation

The designated host will run the initial inference service, subject to the hardware assessment and model benchmark. The runtime and model have not yet been finalized.

### Required workflow

1. Confirm the host's CPU, available RAM, AMD GPU model and VRAM.

2. Select a runtime compatible with the actual hardware and operating environment.

3. Install a pinned runtime version.

4. Obtain a suitable model with a license compatible with the project.

5. Record the model version or artifact digest and runtime configuration.

6. Run a simple inference smoke test.

7. Run NEXUS's structured-planning evaluation dataset.

8. Test resource usage and latency with representative requests.

9. Test concurrent use by the team.

10. Test behavior when the runtime becomes unavailable.

Ollama remains a candidate, not a confirmed decision. AMD GPU acceleration must be validated for the exact operating system, runtime, driver and model combination; do not assume NVIDIA CUDA compatibility.

### AI setup acceptance criteria

- The selected model loads reliably.

- Structured output is validated before use.

- Invalid model output cannot dispatch an operation.

- Inference timeouts do not corrupt task state.

- The application can report model unavailability honestly.

- CPU fallback is available only if it has been tested and explicitly configured.

- Model and runtime versions are recorded for diagnostics and evaluation.

If GPU compatibility is not ready, development can proceed using a deterministic mock planner and the normal safety pipeline. AI integration should not block work on task persistence, authorization or the Windows bridge.

## 04.21.09 Native Windows bridge installation

The bridge must be installed and run on each computer where NEXUS is allowed to perform local operations.

### Installation requirements

- Run under the intended Windows user account.

- Use a dedicated native Windows Python environment or a packaged executable, based on the team's validated distribution approach.

- Configure the backend endpoint without embedding a hardcoded host address in source code.

- Store device credentials in an appropriate protected location.

- Configure logical directory IDs and local application mappings.

- Start with only the initial registered tools enabled.

- Provide clear logs and a diagnostic command without exposing secrets.

- Avoid administrator privileges unless a specific, justified capability requires them.

The initial tool set remains limited to the registered filesystem and application-launch capabilities defined in Section 03.12.

### Bridge startup sequence

1. Load and validate local configuration.

2. Load the protected device credential.

3. Authenticate to the backend.

4. Confirm the registered device identity and status.

5. Report the supported protocol and tool capabilities.

6. Validate local directory and application mappings.

7. Begin the approved polling or communication workflow.

8. Report readiness only for capabilities that passed validation.

If device authentication fails, the bridge must not accept operations as if it were trusted.

### Windows-specific acceptance tests

- Bridge starts from a clean environment.

- The configured Windows paths resolve correctly.

- A permitted search works in a temporary test directory.

- An out-of-scope directory is rejected.

- An unknown tool is rejected.

- Invalid or revoked credentials are rejected.

- Duplicate operation delivery does not blindly repeat a side effect.

- The bridge reconnects and reconciles outstanding operations after a controlled restart.

## 04.21.10 User authentication and device enrollment

Device enrollment must establish a relationship between an authenticated NEXUS user and a particular Windows bridge.

### Proposed enrollment workflow

1. The user authenticates through the CLI.

2. The user initiates enrollment for the local bridge.

3. The backend verifies that the user is authorized to register a device.

4. A unique device identity and credential are provisioned through a protected workflow.

5. The bridge proves possession of its credential.

6. The backend records device ownership and status.

7. The bridge reports its protocol and supported capabilities.

8. The user reviews the device's effective configuration.

9. The device becomes eligible for work only after required checks pass.

The exact enrollment protocol and credential-provisioning mechanism remain open decisions.

### Enrollment security requirements

- Device IDs alone do not authenticate a bridge.

- Different devices must not share one credential.

- The user must not be able to claim another person's device simply by knowing its ID.

- Credentials must not be printed in logs or terminal output.

- Revoked devices cannot reconnect and resume new work using stale credentials.

- Registration must not automatically grant access to every local directory or application.

- A failed enrollment must leave the device untrusted and ineligible for execution.

### Multi-user acceptance criteria

All three developers should be able to authenticate and enroll their own devices independently.

Testing must confirm that one developer cannot use another developer's task ID, approval ID or device ID to access or control their private resources.

## 04.21.11 Initial permission configuration

The initial setup should request only the permissions required for the first supported workflows.

Recommended onboarding sequence:

1. Select or register the local device.

2. Configure one test directory for read-only search.

3. Validate that directory through the bridge.

4. Configure a separate approved workspace for create-only file operations, if that tool is enabled.

5. Optionally register an approved application for launching.

6. Review the effective permission list.

7. Run a permitted operation.

8. Run a negative test to confirm that an unapproved path is denied.

Do not request unrestricted filesystem access as a convenience during setup.

The onboarding experience must make it clear that:

- Registering a directory does not grant access to other directories.

- Registering an application does not permit arbitrary command execution.

- A device registration is not a blanket permission grant.

- The model cannot grant itself permissions.

- A permission can be inspected and revoked later.

## 04.21.12 LAN configuration and connectivity validation

Because the backend runs in WSL 2 or another validated host environment, local development connectivity is not sufficient proof that teammate computers can reach it.

### Required validation

- Identify the intended backend host and API address.

- Confirm that the FastAPI service binds to the intended interface.

- Configure the host firewall for only the required private-network access.

- Verify access from a second physical computer.

- Verify that PostgreSQL is not unnecessarily exposed to the LAN.

- Verify that the model runtime is not unnecessarily exposed to the LAN.

- Confirm that each bridge authenticates to the correct backend.

- Test host restart and address-change behavior.

- Verify that no public port forwarding is required.

WSL 2 commonly uses NAT networking by default, while supported Windows 11 configurations can use mirrored networking. The team should choose based on tests of the actual machine and network rather than assume one configuration is universally correct.

### Connectivity acceptance criteria

A teammate can reach the authenticated API and use their registered device, while direct access to private database or model services remains blocked unless explicitly required by the validated deployment design.

If the host becomes unreachable, clients should report the dependency outage and preserve existing task state. They must not claim a task was accepted unless durable acceptance was confirmed by the backend.

## 04.21.13 End-to-end smoke test

Every fresh installation should pass a documented smoke test before being considered ready for development or team use.

The smoke test must use a designated test directory and must not modify real user documents.

## Installation verification checklist

0 of 10

Backend is ready

Health checks pass and required dependencies are available.

User authentication works

A valid user can log in; invalid credentials are rejected.

Device is enrolled

The backend recognizes the correct bridge identity and status.

Read-only search succeeds

The bridge searches only the configured test directory.

Document reading is bounded

A supported test document is read with expected limits and source references.

File creation is safe

If enabled, a test file is created in the approved workspace without overwriting an existing file.

Task result is persisted

Task history shows the actual step outcomes and verification evidence.

Unauthorized access is denied

An out-of-scope directory or unauthorized device request is rejected.

Recovery behavior works

A controlled interruption produces a truthful status and safe recovery behavior.

Secrets stay protected

Logs and diagnostics do not expose credentials or private content.

Copy checklist

This is a manual checklist, not an automated test runner. Mark an item only after verifying the behavior.

The full smoke test should run at initial setup and after material changes to the bridge protocol, database schema, authentication, tool contracts or deployment configuration.

## 04.21.14 Troubleshooting and diagnostics

Setup errors should identify the failing layer instead of reporting a generic “NEXUS failed” message.

| **Symptom** | **First diagnostic area** |
| --- | --- |
| CLI cannot reach backend | API address, host availability, firewall and WSL networking |
| Backend starts but is not ready | Database, migrations, configuration and required dependencies |
| Database connection fails | Connection settings, database availability and application role |
| AI requests fail | Model runtime readiness, model loading and resource capacity |
| Device enrollment fails | User authorization, device credential and registration status |
| Device appears offline | Bridge process, backend address, network and authentication |
| File search returns access denied | Logical directory mapping, operating-system permissions and policy |
| File creation outcome is uncertain | Operation journal, bridge response and destination reconciliation |
| Different developers see inconsistent behavior | Version drift, configuration differences and capability reports |

### Diagnostic command requirements

A command such as nexus diagnostics should report:

- CLI and bridge versions.

- Backend connectivity and readiness.

- Authenticated device status.

- Protocol and tool compatibility.

- Configuration validation results.

- Dependency health and stable error codes.

- Relevant resource and timing information.

It must not dump environment variables, credentials, complete model prompts or unrestricted filesystem listings.

## 04.21.15 Updates, shutdown and reinstallation

The setup process must also account for routine maintenance.

### Updates

- Pull a reviewed version of the repository.

- Review dependency and configuration changes.

- Apply migrations through the documented procedure.

- Verify bridge/backend protocol compatibility.

- Run the relevant tests and smoke test.

- Preserve recoverable state and backups before consequential changes.

### Shutdown

- Stop accepting new work when a controlled shutdown begins.

- Stop claiming additional tasks.

- Allow a bounded drain of work where appropriate.

- Persist the latest confirmed task and operation states.

- Mark unresolved external outcomes for reconciliation.

- Shut down services without claiming that in-flight Windows operations were automatically rolled back.

### Reinstallation

Reinstalling the CLI or bridge must not silently create a new device identity that is treated as an already trusted device. The team needs a documented re-registration process for credential loss, device replacement and revoked devices.

Database restoration and host replacement must follow the backup and recovery procedures in Section 03.21.

## 04.21.16 Work packages and ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Repository setup and backend startup | Developer 1 | Reproducible API and database setup |
| Database initialization and migrations | Developer 1 | Repeatable schema creation and upgrade path |
| Native Windows bridge installation | Developer 2 | Documented bridge setup and diagnostics |
| Device enrollment and local permissions | Developer 2 + Developer 1 | Secure registration and initial configuration |
| AI runtime installation and evaluation | Developer 3 | Tested model/runtime configuration |
| End-to-end smoke tests | All three | Verified clean-install workflow |
| Setup documentation and release checks | All three | Reproducible onboarding guide |

Each developer should independently complete the installation once. The original setup author should not be the only person capable of running the system.

## 04.21.17 Implementation priorities

P0 — Required foundation

Reproducible installation

- Versioned prerequisites and dependency setup.

- PostgreSQL initialization and migrations.

- Backend health and configuration checks.

- Native Windows bridge installation.

- Authenticated device enrollment.

- Initial permission configuration.

- End-to-end smoke test.

P1 — Team readiness

Operational consistency

- Automated setup validation.

- Improved diagnostics and troubleshooting.

- Repeatable update and reinstallation procedures.

- Multi-device integration checks.

- Model/runtime resource benchmarks.

P2 — Future improvements

Simplified distribution

- Packaged Windows bridge installer.

- Optional bridge startup integration.

- Automated environment bootstrap.

- Guided onboarding interface.

## 04.21.18 Open decisions

- Which Python version and dependency manager will be pinned?

- Will PostgreSQL run through Docker Compose or a directly installed service?

- Which host OS and network configuration will be used for the shared deployment?

- Which local AI runtime and model will pass the hardware benchmark?

- How will bridge credentials be provisioned and rotated?

- Will the bridge be distributed as Python source or a packaged executable?

- Which directories and applications will be enabled in the initial smoke test?

- What backup must exist before migrations or upgrades?

- Which setup checks will be automated in CI, and which require native Windows integration testing?

## 04.21.19 Definition of done

- A new developer can follow the documented setup from a clean checkout.

- Dependencies and supported versions are reproducible.

- PostgreSQL can be initialized and upgraded using committed migrations.

- Backend readiness accurately reflects required dependency health.

- The selected AI runtime passes its documented evaluation.

- Each Windows bridge has a unique authenticated device identity.

- Directory and application permissions are explicitly configured.

- The end-to-end smoke test passes on all three developer computers.

- Unauthorized cross-user and cross-device operations are rejected.

- Setup, troubleshooting, update and recovery instructions are documented.

- No critical or high-severity setup-related security defects remain.

Section exit criterion: all three developers can install, enroll, validate and troubleshoot NEXUS using a common documented process without weakening device isolation or security controls.
