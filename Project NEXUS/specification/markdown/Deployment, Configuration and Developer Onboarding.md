## 03.17.1 Deployment objectives

NEXUS must support:

- Development in Ubuntu on WSL 2.

- Execution of computer operations through a native Windows bridge on each user's computer.

- One designated team computer for initial shared AI inference.

- A shared FastAPI backend and PostgreSQL database, with the final host placement subject to hardware and connectivity validation.

- Local-network access restricted to authorized users and registered devices.

- Reproducible setup with documented dependencies and configuration.

- Safe startup, shutdown, restart and database migration procedures.

- A zero-budget baseline that does not require a paid AI API or cloud service.

Deployment principle: the development environment and the computer-execution environment are separate concerns. Ubuntu/WSL 2 is the team's development environment; the Windows bridge runs on the Windows side so it can interact with that user's Windows filesystem and permitted applications.

## 03.17.2 Proposed deployment topology

Designated team computer

This is the provisional topology, not a guarantee that one computer can support all workloads. The designated host must be tested with the backend, database and chosen model under simultaneous use.

If that host cannot provide acceptable performance, the model runtime may be moved to another suitable computer without changing the user-facing task API. The backend and database placement should remain a separate decision.

## 03.17.03 Process and service boundaries

The initial deployment has four logical runtime responsibilities:

| **Component** | **Proposed location** | **Responsibility** |
| --- | --- | --- |
| FastAPI backend | Designated host | Authentication, task orchestration, policy and API |
| PostgreSQL | Designated host | Durable tasks, users, devices, approvals, memories and audit records |
| Model runtime | Designated host initially | Local inference, subject to compatibility and performance testing |
| Windows bridge | Each participating Windows computer | Restricted local computer operations |

The CLI runs where the developer chooses to work. It communicates with the backend over the authorized network connection.

PostgreSQL should not be exposed directly to teammate computers. The bridge should not expose an unrestricted inbound shell service. The model runtime should not be reachable by arbitrary LAN clients.

## 03.17.04 Development environment

The proposed baseline is:

- Windows 11 on each developer's computer.

- Ubuntu on WSL 2 for backend development and project tooling.

- A supported Python version agreed upon and pinned by the team.

- FastAPI for the HTTP application.

- PostgreSQL for durable application data.

- A migration tool, with Alembic as a candidate.

- Git and a shared repository for source control.

- Docker Compose as a candidate for reproducible local backend/database setup.

- A native Windows Python environment for the Windows bridge.

The exact versions should be selected together and recorded in repository configuration. We should not allow developers to independently install different major versions of Python, PostgreSQL drivers or key libraries.

### Important environment boundary

The bridge should be tested in a native Windows environment, not assumed to behave identically when launched from WSL. Filesystem paths, application launching, Windows credentials and interactive desktop behavior may differ between the environments.

Likewise, Windows path strings should not be interpreted using Linux filesystem rules in the bridge.

## 03.17.05 Repository and configuration layout

The previously proposed application structure remains the source of truth for logical modules. Deployment files and configuration should be organized so that secrets and machine-specific paths are not committed to Git.

A proposed layout:

nexus/

├── apps/

│   ├── api/

│   ├── cli/

│   └── windows_bridge/

├── nexus_core/

├── migrations/

├── tests/

├── deploy/

│   ├── docker-compose.yml

│   └── config/

├── scripts/

├── docs/

├── .env.example

├── .gitignore

├── pyproject.toml

└── README.md

This is an organizational proposal; it does not require every directory to exist before its module is implemented.

### Configuration categories

| **Category** | **Examples** | **Handling** |
| --- | --- | --- |
| Backend | Bind address, log level, request limits | Environment/configuration |
| Database | Connection settings | Secret-bearing configuration |
| Model | Provider, endpoint, model identifier, context limit | Configuration with validated defaults |
| Device | Device identifier, bridge connection settings | Device-local configuration |
| Filesystem | Logical directory IDs mapped to allowed Windows paths | Local bridge configuration |
| Security | Signing keys, credentials, token lifetimes | Protected secret storage |
| Diagnostics | Log level, metrics settings | Configuration with privacy-safe defaults |

The repository should contain a template with placeholders and non-secret examples, never real credentials or production-like tokens.

Machine-specific directory paths should be configured on each bridge rather than assumed to be identical across teammates' computers.

## 03.17.06 Secrets and credentials

Secrets must be handled separately from ordinary configuration.

The system may need database credentials, API signing keys, user session credentials and per-device bridge credentials. These serve different purposes and must not be reused as one shared secret.

Required rules:

- Never commit real secrets to the repository.

- Keep .env files and other local secret files excluded from Git.

- Restrict file permissions for secret-bearing configuration.

- Use distinct credentials for each registered device so one device can be revoked without rotating every other device's identity.

- Do not place secrets in CLI arguments, URLs, ordinary logs or model prompts.

- Prefer an appropriate protected credential store on Windows for bridge credentials.

- Provide a documented process for rotating credentials and revoking a compromised device.

- Use separate development credentials and production-like credentials if environments are separated.

For local development, a secret supplied through an environment variable may be adequate for some services, but it should not be treated as a universal secret-management solution. The final approach depends on how each service is launched.

## 03.17.07 Startup and shutdown sequence

The system must have a documented startup order and a predictable health check.

1. Start PostgreSQL

Verify connection and database availability

2. Apply reviewed migrations

Confirm schema version and migration success

3. Start the FastAPI backend

Check configuration, database access and recovery state

4. Verify the model runtime

Confirm provider availability and model readiness

5. Start each Windows bridge

Authenticate, register/verify identity and report capabilities

6. Run health checks

Verify backend, database, inference and target-device connectivity

The exact process order may be adjusted for the selected model runtime, but the backend must distinguish a service being reachable from it being ready to perform its intended work.

### Health reporting

Health checks should distinguish:

- Backend health: API process is running and able to serve requests.

- Database health: required database operations can succeed.

- AI health: the configured inference provider is available.

- Device health: the bridge has recently authenticated and reported its state.

- Task readiness: the services required for a particular task are available.

A database being healthy does not mean AI inference is available. Likewise, an online bridge does not mean its file-search or application-launch tools are enabled.

### Shutdown

Shutdown should stop new work where appropriate, allow bounded cleanup, and preserve durable task state. If a process stops during an external operation, the next startup must invoke the recovery behavior defined in Section 03.15 rather than assume the operation failed.

## 03.17.08 Database migrations and data safety

Database schema changes must be versioned and reproducible.

Proposed rules:

1. Use committed migration files for every schema change.

2. Test migrations against a fresh database.

3. Test upgrade paths from the previous supported schema version.

4. Do not rely on manual production database edits.

5. Do not run concurrent migrations independently from multiple application instances.

6. Back up important development data before destructive migrations.

7. Document how to restore a backup and verify the restored database.

8. Ensure application startup reports an incompatible schema clearly.

A development reset command, if provided, must be clearly distinguished from ordinary startup and require deliberate use. It must not delete a teammate's shared task history or memory by accident.

The retention and backup policy remains open; a backup should not be described as a permanent deletion mechanism, and deleted memories must be handled according to the agreed retention policy.

## 03.17.09 Local-network access and firewall

The designated host will be reachable by other team computers, so network exposure must be deliberate.

Required safeguards:

- Bind the backend to an address reachable by the intended team clients, not automatically to every interface without review.

- Allow inbound access only from the intended private network or approved clients, using host firewall rules.

- Keep PostgreSQL on a backend-only interface or internal container network.

- Restrict the model runtime endpoint to the services that need it.

- Authenticate every bridge connection and bind it to a registered device identity.

- Do not configure public port forwarding.

- Document the ports each service needs and why.

- Test behavior when a client is on a different network or the host firewall blocks access.

WSL 2 networking can differ between machines and configurations. The team must validate actual connectivity from each Windows client to the backend running in WSL 2. Do not assume that a service reachable from Ubuntu is automatically reachable by other LAN devices.

If a VPN, guest Wi-Fi or network isolation prevents teammate access, document the limitation rather than bypassing the firewall with broad, permanent exposure.

## 03.17.10 Docker Compose and service isolation

Docker Compose is a proposed way to make the shared backend and PostgreSQL reproducible. It is not a requirement that every component run in a container.

A possible initial arrangement:

- PostgreSQL runs in a container with a persistent volume.

- FastAPI runs either in a container or in the WSL 2 Python environment, depending on development convenience.

- The model runtime runs in whichever environment provides reliable support for the selected AMD GPU.

- The Windows bridge runs natively on Windows.

GPU compatibility is the deciding factor for the model runtime. Do not assume that putting the model inside Docker automatically provides AMD GPU acceleration. Verify the selected runtime's actual support for the host operating system, GPU model and driver stack.

Compose configuration should use environment variables or configuration files for credentials, health checks where supported, explicit volume definitions and documented service dependencies. A container being started does not guarantee that its service is ready.

## 03.17.11 Developer onboarding workflow

Each developer should be able to follow the same onboarding sequence.

1. Prepare the machine: install or verify Windows 11, WSL 2, Ubuntu, Git and the required development tools.

2. Clone the repository: use the documented branch and verify the expected project structure.

3. Configure the environment: create local configuration from the template, set required secrets securely, and configure the local Windows bridge directories.

4. Install dependencies: use the pinned project dependency configuration.

5. Start the backend dependencies: start PostgreSQL and any required supporting services.

6. Apply migrations: initialize the schema using the documented migration command.

7. Start or connect to the backend: verify health and authenticate.

8. Register the device: establish a unique device identity and confirm that revocation and authorization work.

9. Run automated tests: run unit, integration and contract suites as documented.

10. Run a safe smoke test: perform a read-only operation against a designated test directory and confirm the result and audit record.

The README must include the actual commands once they have been validated. Avoid publishing speculative commands before the team has selected dependency versions, service topology and configuration names.

### Onboarding acceptance test

A developer who has not configured NEXUS before should be able to:

- Start the documented services.

- Authenticate with their own account.

- Register their own Windows computer.

- Run the safe smoke test on that computer.

- See their task history and result.

- Verify that another user's private task and memory are inaccessible.

- Stop and restart their local bridge without corrupting task history.

- Diagnose a deliberately unavailable backend using the documented health checks.

Record setup failures and missing instructions during the test; these are product issues, not merely onboarding inconveniences.

## 03.17.12 Developer workflows and shared responsibility

A three-person team needs clear boundaries without creating silos.

| **Area** | **Primary responsibility** | **Required collaboration** |
| --- | --- | --- |
| Backend and execution | API, PostgreSQL, migrations, task lifecycle and recovery | Review authorization and concurrency changes |
| Windows bridge | Device registration, local tool execution, filesystem and application integration | Agree on bridge contracts and security rules |
| AI and context | Model provider, planning, retrieval and memory integration | Agree on schemas, resource limits and policy boundaries |
| Shared integration | Deployment, contract tests, end-to-end tests and documentation | All three developers contribute |

This is a proposed ownership model, not a restriction on who may modify a component. Each developer should understand the cross-component contracts well enough to diagnose an end-to-end failure.

Before parallel implementation begins, agree on the API schemas, bridge protocol, task-state values, tool contracts and error structure. These interfaces are more important than matching directory names perfectly.

## 03.17.13 Deployment observability and maintenance

NEXUS should provide enough information to diagnose common failures without requiring direct database inspection for every issue.

The documented maintenance workflow should cover:

- Backend and model-runtime health.

- Database connectivity and migration version.

- Device registration and last-seen status.

- Task and operation identifiers for troubleshooting.

- Safe retrieval of relevant logs.

- Restart behavior and recovery of interrupted tasks.

- Credential revocation and rotation.

- Database backup and restore verification.

- Dependency upgrades and regression testing.

Logs should have bounded size and retention, with secrets and private document content excluded by default. Diagnostic commands should not print stored credentials or expose unrestricted filesystem contents.

## 03.17.14 Deployment acceptance criteria

- All three developers can reproduce the documented setup.

- The designated host serves the backend on the intended private network.

- The selected model runtime has been validated on the actual AMD GPU or documented CPU fallback.

- PostgreSQL is not directly exposed to teammate clients.

- Each developer operates only their own registered computer unless explicit sharing is implemented.

- The bridge runs natively on Windows and uses locally configured directory scopes.

- Secrets and machine-specific configuration are excluded from source control.

- Database migrations work on a fresh installation and a supported upgrade path.

- Restarting a service preserves durable task state and invokes recovery where necessary.

- Host firewall behavior and WSL 2 networking have been tested.

- Backup and restore instructions are documented and tested.

- The setup includes health checks, smoke tests and troubleshooting instructions.

- The system can be developed and used without requiring a paid service.

## 03.17.15 Decisions still open

These questions should be resolved before finalizing deployment scripts:

1. Host operating system: will the designated host run the backend in WSL 2, in native Windows Python, or in a Linux environment outside WSL?

2. AMD GPU: what is the exact GPU model and VRAM capacity, and which local inference runtime performs reliably on it?

3. Service packaging: will FastAPI run inside Docker or directly in Ubuntu?

4. Bridge communication: will bridges poll the backend or maintain persistent connections?

5. Authentication bootstrap: how will the first user account and device credentials be created securely?

6. Availability: must the designated host remain online continuously, or is occasional downtime acceptable?

7. Backups: how often should the shared database be backed up, and how much history must be retained?

8. TLS: what transport protection is required for the private LAN deployment, given the final authentication and network design?

9. Version management: what Python and PostgreSQL versions will be pinned for the first release?

10. Model fallback: if the AMD GPU cannot support the selected runtime adequately, what CPU fallback is acceptable?

## Section 03.17 exit criteria

Deployment design is ready for implementation when the host topology, model-runtime compatibility, configuration format, secrets handling, service startup order, network exposure and onboarding workflow are documented and testable.
