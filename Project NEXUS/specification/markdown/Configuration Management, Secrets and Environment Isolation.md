## 03.20.1 Purpose

NEXUS will run across different environments: Ubuntu on WSL 2 for backend development, a designated team computer for shared services and AI inference, and a native Windows bridge on each developer's computer.

These environments cannot safely share one universal configuration file. Each computer has different filesystem paths, credentials, network settings and potentially different hardware capabilities.

This section defines how NEXUS configuration is supplied, validated, isolated and protected.

The objectives are to:

- Let all three developers run NEXUS without manually editing application source code.

- Keep secrets out of Git, logs and diagnostic output.

- Separate development, testing and team deployment settings.

- Configure Windows-specific paths on the computer where those paths exist.

- Prevent a misconfigured environment from silently weakening security.

- Make a clean installation reproducible.

## 03.20.2 Configuration architecture

NEXUS should distinguish four types of configuration.

Application configuration

API settings, task limits, timeout defaults, logging levels and other application behavior.

Secrets

Database passwords, authentication signing keys, access credentials and per-device bridge credentials.

Machine-specific configuration

Windows directory mappings, approved application IDs, device identity, host addresses and local runtime settings.

Policy configuration

Permitted tools, autonomy tiers, approval requirements, resource limits and security restrictions.

These categories must not be conflated. A normal setting such as a log level may be editable by a developer, but a model-generated request must never be able to change a security policy or grant itself additional permissions.

## 03.20.3 Environment separation

NEXUS should support at least three logically distinct environments.

| **Environment** | **Purpose** | **Required characteristics** |
| --- | --- | --- |
| Development | Individual developer implementation and debugging | Local settings, test data, developer-owned credentials |
| Test/CI | Automated correctness and security testing | Isolated database, fake model responses where appropriate, temporary files and test credentials |
| Team deployment | Shared use across the three developers | Restricted network access, controlled credentials, registered devices and durable data |

The team deployment should not use development secrets or an unrestricted test configuration.

A test must not accidentally connect to the team's real database or operate on a developer's actual documents. Environment selection should be explicit, and tests should fail safely if the target database or test filesystem is not the expected one.

Proposed rule: production-like configuration should require explicit confirmation of its environment, while test suites should refuse to execute destructive fixtures against an unrecognized database.

## 03.20.4 Configuration files and precedence

A practical initial approach is:

- Commit safe defaults and an .env.example file.

- Keep machine-specific and secret-bearing .env files out of version control.

- Use typed application settings with validation at startup.

- Load separate configuration for the backend and Windows bridge.

- Allow deployment-specific overrides through environment variables or protected configuration files.

- Reject unknown or invalid security-sensitive settings rather than silently ignoring them.

A proposed repository arrangement:

nexus/

├── .env.example

├── .gitignore

├── apps/

│   ├── api/

│   ├── cli/

│   └── windows_bridge/

├── deploy/

│   └── config/

│       ├── development.example.yaml

│       └── team.example.yaml

├── tests/

└── docs/

This is a proposed layout, not a finalized implementation requirement.

The actual secrets should not be stored in the committed example files. Examples must use unmistakable placeholders.

### Precedence rule

The exact precedence must be documented once and implemented consistently. A reasonable proposal is:

1. Built-in safe defaults.

2. Environment-specific configuration file.

3. Environment-variable overrides.

4. Explicit command-line overrides for settings that are safe to override.

Secrets should use a separate, deliberate loading path rather than being mixed indiscriminately with ordinary configuration.

Avoid having multiple conflicting configuration sources silently override one another. Startup diagnostics should identify the effective non-secret settings and their sources.

## 03.20.5 Typed configuration and startup validation

FastAPI, the bridge and the CLI should validate their configuration at startup instead of discovering errors halfway through a task.

The backend should validate:

- Database connection settings.

- Authentication and token-signing configuration.

- API bind address and permitted network exposure.

- Model runtime configuration and request timeouts.

- Maximum request sizes, task concurrency and other resource limits.

- Logging and diagnostic settings.

- Any required encryption or credential-management configuration.

The Windows bridge should validate:

- Registered device identity and credential availability.

- Backend address and connection settings.

- Configured directory identifiers and their local path mappings.

- Approved application identifiers and executable mappings.

- Enabled tools and their resource limits.

- Local diagnostic storage permissions.

The CLI should validate:

- Backend URL.

- Authentication state.

- Selected device or explicit target-device requirement.

- Output mode and timeout settings.

### Failure behavior

If a mandatory security setting is absent or invalid, startup must fail with an actionable, non-secret error.

For example, NEXUS should not generate a new token-signing key every time the backend restarts. That could invalidate sessions unexpectedly and create inconsistent multi-process behavior.

Likewise, an invalid directory mapping must not silently fall back to the entire user's home directory or filesystem root.

## 03.20.6 Secrets management

NEXUS will have multiple secrets with different purposes. They must not all share one hard-coded password.

| **Secret** | **Intended protection** |
| --- | --- |
| Database credentials | Backend-only access; never needed by the CLI or Windows bridge |
| Authentication signing key | Restricted to the service that validates or issues the relevant tokens |
| User credentials | Secure password hashing; never store plaintext passwords |
| Device credential | Unique to the registered device and revocable |
| CLI session credentials | Protected local credential storage where available |
| Model runtime access credentials, if any | Stored only if the selected runtime requires them |

### Required rules

1. No real secret may be committed to Git.

2. No secret may be embedded in source code, container images, test fixtures or example configurations.

3. Secrets must be redacted from logs, API responses and diagnostic bundles.

4. Each device must have its own credential rather than sharing one team-wide bridge secret.

5. Revoking a device must prevent its credential from authorizing new operations.

6. Secrets should have a documented rotation or replacement procedure.

7. Test credentials must be separate from team-deployment credentials.

For a Windows-native bridge, Windows Credential Manager is a candidate for protecting device credentials. The final mechanism must be selected and tested for the chosen bridge implementation. Plaintext credentials in a general configuration file are not an acceptable default.

For a local development environment, protected environment variables or ignored local configuration files may be adequate for initial development, provided access is restricted and secrets never enter Git or logs.

## 03.20.7 Windows paths and local capabilities

Each developer's computer may have different usernames, drive letters and directory layouts. Therefore, the backend must not store or generate assumed absolute paths for every user's Windows machine.

Instead, the bridge should maintain local mappings from logical directory identifiers to approved locations.

Example of a conceptual mapping, not a final schema:

directories:

project_workspace:

path: "D:\\NexusWorkspace"

allowed_operations:

- search_files

- read_document

- create_file

The actual location belongs to each developer's local configuration. Another developer may map project_workspace to a different directory.

The bridge must independently enforce the mapping and the permitted operations. The model should only see the logical identifier and the relevant bounded information, not receive authority to invent arbitrary filesystem paths.

### Startup checks

- The configured path exists or can be safely created when explicitly permitted.

- The path is accessible to the Windows user running the bridge.

- The configured operation scope matches the policy.

- The bridge does not follow a path outside the approved scope through traversal or unsafe reparse-point behavior.

- Missing or inaccessible directories produce a clear configuration error.

Approved application IDs should follow the same principle: a logical identifier maps to a locally configured executable and allowed arguments. A request cannot override that mapping by supplying an arbitrary executable path.

## 03.20.8 Security policy configuration

Security policies require stricter treatment than ordinary application settings.

The following must be controlled by trusted application configuration and policy code:

- Tool allowlist.

- Directory scope and filesystem operation restrictions.

- Risk classification and approval requirements.

- Device ownership and credential validity.

- Operation size, timeout and concurrency limits.

- Prohibited operations.

- Whether a specific feature is enabled.

The AI planner must not be able to edit these settings through natural-language instructions, document content or generated plans.

A configuration change that expands permissions should be treated as a security-sensitive administrative action. It should be validated, audited and take effect according to a defined policy.

Important: approval is not a substitute for a hard prohibition. A setting that prohibits unrestricted command execution must not be overridden by a user approving a model-generated command.

## 03.20.9 Configuration versioning and migration

Configuration schemas evolve as the project develops. NEXUS should define a versioned configuration format for settings whose structure may change.

Required behavior:

- Invalid configurations fail with a clear message.

- Deprecated settings are identified explicitly.

- Breaking changes include migration guidance.

- Unknown security-sensitive settings are not silently accepted.

- Example configuration files are updated alongside the implementation.

- Startup diagnostics report the configuration schema version.

- Secrets are never included in configuration-validation error messages.

Database schema migrations and configuration migrations are separate concerns. Alembic, if selected for database migrations, does not automatically migrate local YAML files, environment variables or Windows Credential Manager entries.

Configuration changes must not silently broaden permissions or erase device-specific mappings.

## 03.20.10 Container and WSL 2 considerations

NEXUS's backend development environment uses Ubuntu on WSL 2, while the Windows bridge runs natively on Windows.

This distinction matters because:

- A Windows path such as D:\NexusWorkspace is not automatically a valid native Linux path.

- A Linux path inside WSL 2 is not automatically accessible as the same path to a native Windows process.

- A container's filesystem may differ from both the WSL and Windows filesystems.

- Network addressing and service reachability depend on the chosen WSL 2 and deployment configuration.

The bridge should own Windows-native paths and Windows application launching. The backend should exchange logical directory IDs and structured operations rather than assuming it can directly manipulate every developer's Windows filesystem.

Docker Compose is a candidate for reproducibly running PostgreSQL and possibly the backend. Model-runtime GPU acceleration must be verified on the actual AMD GPU; it must not be assumed to work simply because a container starts.

### Required environment checks

1. The backend can reach PostgreSQL.

2. The CLI can reach the intended backend address.

3. Each bridge can authenticate to the backend.

4. The backend can communicate with the intended model runtime.

5. PostgreSQL and internal services are not unnecessarily exposed to the LAN.

6. The setup works after a full restart, not just in the original terminal session.

## 03.20.11 Testing requirements

Configuration and secret-handling tests must include:

- Missing required environment variable.

- Invalid database URL or inaccessible database.

- Missing or invalid authentication key.

- Malformed YAML or unsupported configuration version.

- Duplicate or unknown directory identifiers.

- Directory path outside permitted scope.

- Missing local directory or insufficient permissions.

- Attempt to load a production secret in a test environment.

- Attempt to connect tests to a non-test database.

- Secret leakage checks against logs and error responses.

- Device credential revocation.

- Configuration change that attempts to enable a prohibited tool.

- Restart with unchanged secrets and machine-specific settings.

All test fixtures should use synthetic credentials and temporary directories. Tests must not print actual secret values when they fail.

## 03.20.12 Developer onboarding workflow

The onboarding guide should allow a new team member to configure NEXUS without copying another developer's private files or credentials.

1. Clone the repository and create the local Python environment.

2. Copy the example configuration to the documented local configuration location.

3. Configure local database and backend settings using the approved development setup.

4. Initialize the database and apply versioned migrations.

5. Start the backend and verify health/readiness.

6. Configure the native Windows bridge's own device identity, credentials and local directory mappings.

7. Register the device and verify authentication.

8. Run automated tests and a safe, non-destructive smoke test.

Onboarding is complete only when the developer can run the documented workflow without undocumented manual configuration changes.

## 03.20.13 Implementation priorities

| **Priority** | **Deliverable** |
| --- | --- |
| P0 | .env.example, ignored local secrets, typed configuration, startup validation and separate backend/bridge configuration |
| P0 | Per-device identity and local filesystem mappings |
| P0 | Safe policy defaults, secret redaction and environment separation |
| P1 | Configuration versioning, migration guidance and diagnostic reporting |
| P1 | Credential rotation/revocation workflow and automated leakage tests |
| P2 | More advanced secret management, configuration administration UI and centralized deployment management |

These priorities are proposals for the 10–12-week MVP. Security essentials cannot be postponed simply because a more sophisticated management interface is out of scope.

## 03.20.14 Open decisions

- Which settings are stored in environment variables versus YAML or another configuration format?

- Will the team use Docker Compose for the backend, database or both?

- How will the team deployment provision its initial administrator and user accounts?

- Which credential-storage mechanism will the Windows bridge use?

- How will signing keys and device credentials be rotated?

- Which local paths and applications are approved for the MVP?

- What happens when a required model runtime is unavailable at startup?

- Who may change shared policy, and how are those changes audited?

- What retention period applies to local diagnostics and operational logs?

These decisions must be resolved before production-like deployment. They do not all need to be resolved before implementing basic configuration loading, but no unresolved choice should be silently converted into a permissive default.

## 03.20.15 Acceptance checklist

### Configuration readiness

0/10

Clean setup works using documented configuration instructions.

Secrets are excluded from Git and redacted from logs and errors.

Backend, CLI and Windows bridge use clearly separated configuration.

Invalid mandatory configuration fails safely at startup.

Windows directory mappings are local, explicit and independently enforced by the bridge.

Test runs cannot accidentally operate on team data or a non-test database.

Device credentials can be revoked without sharing a team-wide secret.

Security policy cannot be expanded by AI-generated content or plans.

WSL 2, Windows bridge, database and model connectivity are validated on the real environment.

Configuration changes and schema updates are documented and reproducible.

Copy checklist

## Section 03.20 exit criterion: every developer can configure NEXUS independently, secrets remain protected, Windows-specific permissions stay local to each bridge, and invalid configuration cannot silently weaken security.
