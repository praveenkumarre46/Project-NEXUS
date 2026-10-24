## 04.20.01 Purpose

NEXUS must allow each team member to configure how the system interacts with their own Windows computer without giving the shared backend or AI unrestricted access to that computer.

This section defines how users configure:

- Permitted directories for searching, reading and creating files.

- Approved applications that NEXUS may launch.

- Device identity and connectivity settings.

- Tool permissions and autonomy levels.

- Resource limits and supported capabilities.

- Permission inspection, modification, revocation and recovery.

The design must support three developers using one shared backend while maintaining independent computer permissions.

Core principle: configuration defines the boundaries within which NEXUS may operate. A user preference, model-generated plan or shared backend setting must never silently expand those boundaries.

## 04.20.02 Configuration categories

NEXUS should separate configuration by ownership and security impact.

User preferences

Default device, output format, preferred result detail and other presentation settings. These do not grant new operating-system permissions.

Device configuration

Device identity, configured directories, application allowlist, local resource limits and supported bridge capabilities.

Security policy

Permitted operations, prohibited operations, approval requirements and authorization rules enforced by the backend and Windows bridge.

Service configuration

Backend URL, database settings, model runtime, resource limits and operational settings controlled by the appropriate service administrator.

These categories may use separate configuration files or database records, but their authority must remain distinct. Changing a user preference must not implicitly change a device permission or security policy.

## 04.20.03 Ownership and configuration authority

For the initial three-developer deployment, use the following proposed authority model.

| **Setting or resource** | **Authoritative owner** |
| --- | --- |
| User display preferences | Individual user |
| Device registration and credential status | Backend identity/device service |
| Windows directory mappings | Local device configuration |
| Installed application mappings | Local device configuration |
| Global prohibited operations | Application security policy |
| Per-user and per-device grants | Authorization service, enforced by the bridge |
| Model runtime and resource limits | Deployment configuration |
| Task and approval state | Backend persistence layer |

The exact division between device owner and administrative roles remains an open decision, but the default should be private, owner-controlled devices rather than a shared team-wide permission pool.

### Required rules

- A user cannot change another user's configuration merely by supplying their ID.

- The backend must authenticate and authorize configuration changes.

- The bridge must validate local paths and applications independently.

- The AI model cannot modify security configuration.

- Device identifiers and logical directory IDs are references, not proof of permission.

- Global policy restrictions take precedence over local preferences.

- Revoked permissions must block new unauthorized operations, including operations that were queued before revocation.

## 04.20.04 Directory permission management

NEXUS should not expose the entire Windows filesystem as a single unrestricted resource. Each device should define explicit logical directory mappings, as established in Section 03.32.

Example configuration:

| **Logical directory ID** | **Local purpose** | **Proposed capabilities** |
| --- | --- | --- |
| project_documents | Designated project documents | Search and read |
| approved_workspace | Directory for generated outputs | Create files; read only if separately permitted |
| shared_team_docs | Explicitly configured shared documents | Search and read, subject to access rules |

These IDs are illustrative. The actual directories must be configured and validated on each device.

### Directory configuration fields

A logical directory configuration may include:

- directory_id

- display_name

- Local Windows path

- Permitted operations

- Enabled/disabled status

- File-size and search limits

- Configuration version

- Last validation time

### Rules for adding a directory

1. An authorized user or administrator selects a directory.

2. The bridge resolves and validates the local Windows path.

3. The system verifies that the directory can be accessed under the bridge's operating-system identity.

4. The user selects permitted operations from the supported capability set.

5. The configuration is saved and validated.

6. The bridge reports the effective capability to the backend.

7. The backend exposes only relevant, currently available capabilities to the planner.

Directory registration must not bypass the Windows user's existing filesystem permissions.

### Rules for changing or removing a directory

- A directory cannot be enabled solely because the AI references it.

- A changed path must be revalidated locally.

- Disabling a directory prevents new operations using that mapping.

- Queued operations using the mapping must be revalidated before dispatch.

- In-flight operations follow the defined cancellation and reconciliation rules.

- Removing a mapping must not be reported as deleting the underlying files.

- If the mapping becomes unavailable, NEXUS must report that state rather than silently switch to another directory.

Security requirement: string-prefix comparisons alone are insufficient for checking Windows path containment. Junctions, symbolic links, alternate path representations and filesystem races must follow the validation rules defined in Section 03.32.

## 04.20.05 Application allowlist management

The initial application integration should support launching explicitly approved applications, not arbitrary executables or commands.

An application mapping may contain:

- app_id

- Display name

- Locally configured executable or application identifier

- Permitted launch behavior

- Optional supported arguments

- Enabled/disabled status

- Configuration version

Example logical application IDs might include code_editor or approved_browser. These IDs do not imply that the applications are installed or approved on any particular computer.

### Allowlist rules

- The bridge owns the actual local application mapping.

- The backend can request only registered application IDs.

- The model cannot supply an arbitrary executable path to bypass the allowlist.

- Shell interpretation and arbitrary command execution remain prohibited.

- Arguments, if supported, must be validated against the application's contract.

- Launching an application is not proof that a task inside it has completed.

- Disabling an application mapping blocks new launch requests.

- Changes to mappings require local validation before use.

For the MVP, a simple explicit allowlist is preferable to a dynamic plugin system or unrestricted desktop automation.

## 04.20.06 Permission model and autonomy settings

NEXUS should represent permissions as explicit grants tied to an authenticated user, a target device, a capability and an allowed resource scope.

A logical grant may include:

| **Field** | **Purpose** |
| --- | --- |
| permission_id | Identifies the grant |
| subject_user_id | User whose authority is being evaluated |
| device_id | Device where the operation may execute |
| tool_name | Supported tool covered by the grant |
| resource_scope | Allowed directory, application or other logical resource |
| allowed_operations | Permitted actions |
| status | Active, disabled or revoked |
| created_at / updated_at | Change tracking |
| policy_version | Policy context for evaluating the grant |

This is a logical model, not a finalized database schema.

### Proposed permission behavior

Read-only capabilities

Search or read within configured directories when the user and device have an active grant. No extra approval is required for each operation if the grant and policy already permit it.

Limited, reversible capabilities

Create a new file within an approved workspace or launch an allowlisted application, subject to the specific tool contract and configured limits.

Consequential capabilities

Overwrite, move important data or modify settings only if the capability is explicitly supported and the applicable policy and approval requirements are satisfied.

Prohibited capabilities

Bypass access controls, access another user's private data without authorization or execute unrestricted model-generated commands. Ordinary approval cannot override a hard prohibition.

These categories align with the existing autonomy model; they do not authorize the team to introduce new operations merely by adding a configuration option.

### Effective permission evaluation

The effective permission for an operation should be the intersection of all applicable constraints:

1. The authenticated user's authority.

2. Ownership and access rights for the target device.

3. The registered tool's supported capability.

4. The user's active permission grant.

5. The locally configured directory or application scope.

6. Global security policy and hard prohibitions.

7. Resource limits and current execution conditions.

8. Any required, valid approval.

If any required condition fails, dispatch must be blocked. A broad grant must not override a narrower local restriction or a global prohibition.

## 04.20.07 Permission inspection and change workflow

Users need a clear way to understand what NEXUS is allowed to do on each computer.

Proposed CLI commands:

nexus devices

nexus config show

nexus permissions list

nexus permissions show <permission-id>

nexus permissions revoke <permission-id>

nexus directories list

nexus directories validate <directory-id>

nexus apps list

These are proposed commands and must be reconciled with the existing CLI contract before implementation. Any command that modifies security-sensitive configuration requires an authenticated, authorized workflow.

### Permission change lifecycle

Inspect

Show current grants and effective scope

Request a change

Identify the exact permission or mapping to change

Authorize and validate

Check identity, policy and local configuration

Persist and apply

Record the new version and enforce it at execution

Verify effective state

Confirm the actual permission state, or report that it remains unconfirmed

A configuration change is not complete merely because the CLI accepted the command. The backend and bridge must agree on the effective security state before new operations rely on the change.

## 04.20.08 Revocation and in-flight operations

Revocation must prevent future unauthorized actions without falsely claiming that an already executed external action has been undone.

### Required behavior

- Before dispatch: a revoked permission blocks the operation.

- Queued operation: authorization is rechecked before dispatch.

- Dispatched operation: the system determines whether execution has started and follows the recovery protocol.

- In-flight operation: stop further work where safely possible; reconcile any external effect whose outcome is uncertain.

- Completed operation: preserve the recorded outcome. Revocation does not erase or reverse it.

- Offline device: record the revocation centrally and enforce it when the device reconnects. The system must not dispatch new work based on stale authorization.

The team must define the maximum acceptable revocation propagation delay. If the bridge cannot establish that an operation remains authorized, it should fail closed for operations requiring that authorization.

A disconnected device cannot be assumed to have received a revocation merely because the backend recorded it.

## 04.20.09 Configuration versioning and consistency

A shared backend and multiple Windows bridges create a risk that different components operate under different configuration versions.

NEXUS should track configuration changes and distinguish:

- Backend policy version.

- User permission grant version.

- Device configuration version.

- Directory mapping version.

- Application mapping version.

- Tool definition and schema version.

- Bridge capability version.

These versions need not all share one global number. Each should have a clearly defined owner and compatibility rule.

### Required rules

1. Security-sensitive changes are persisted and versioned.

2. The bridge reports the effective local configuration version.

3. The backend checks that the operation is compatible with the current tool and capability versions.

4. Operations queued before a relevant configuration change are revalidated.

5. Unknown or incompatible security-sensitive configuration fails closed.

6. A configuration rollback must not silently reinstate revoked credentials or grants.

7. A stale bridge must not be treated as having the latest policy merely because it remains connected.

### Configuration change during execution

If a directory mapping changes while a task is running, NEXUS must not assume that the original authorization still covers the new location.

The task should stop dispatching affected future steps until the operation's scope has been revalidated. Any already dispatched side effect follows the existing reconciliation rules.

This does not require freezing every device setting for the lifetime of every task. It requires identifying which settings affect a specific operation and rechecking those settings at the appropriate execution boundary.

## 04.20.10 Configuration storage and deployment

Configuration should be separated according to whether it is shared, machine-specific or secret.

| **Configuration type** | **Proposed location** |
| --- | --- |
| Backend operational settings | Backend environment configuration |
| Database credentials and signing secrets | Protected secret storage |
| User preferences | User-scoped persistence or local CLI settings, depending on the setting |
| Windows directory mappings | Protected local bridge configuration |
| Application mappings | Local bridge configuration |
| Authoritative permission grants | Backend persistence |
| Device credentials | Protected per-device storage |
| Example/default configuration | Version-controlled, secret-free templates |

### Storage rules

- Do not commit real credentials or local user paths to source control.

- Do not store raw device credentials in ordinary configuration records.

- Prefer Windows Credential Manager or another appropriate protected store for bridge secrets, subject to implementation validation.

- Use .env.example for documented placeholders, not real secrets.

- Validate configuration at startup and when security-sensitive settings change.

- Keep database migrations separate from configuration migrations.

- Back up the configuration required for recovery, but protect it independently from ordinary application data.

- Ensure restored configuration does not silently reinstate revoked permissions.

Configuration files should be human-readable where practical, but ease of editing must not bypass authorization checks. Directly editing a local configuration file should not grant new backend permissions.

## 04.20.11 Testing strategy

| **Test** | **Expected behavior** |
| --- | --- |
| User edits another user's permission | Access denied |
| Directory mapping points outside the configured scope | Validation fails |
| Directory is disabled after a task is queued | Dispatch is blocked or revalidated under the new policy |
| Application is removed from the allowlist | New launch requests are denied |
| Bridge has stale configuration | Affected security-sensitive operations are blocked until revalidated |
| Device is revoked while offline | Backend blocks new dispatch; reconnection applies revocation before new work |
| User requests an unsupported permission | Request is rejected rather than silently accepted |
| AI proposes an unauthorized directory | Backend or bridge denies the operation |
| Configuration contains a secret | Secret does not appear in diagnostics or logs |
| Configuration is malformed | Startup or reload fails safely |
| A permission is revoked during execution | In-flight work follows defined cancellation and reconciliation rules |
| Configuration is restored from backup | Previously revoked credentials and grants are not silently reactivated |
| Path contains traversal or link tricks | Bridge denies unsafe access |
| Two configuration updates race | Conflicting changes cannot produce an inconsistent effective state |
| User changes a display preference | Security permissions remain unchanged |
| Backend and bridge versions are incompatible | Dispatch fails closed where required |

Tests must cover both API authorization and native Windows bridge enforcement. A passing backend permission check alone is insufficient if the bridge accepts an unsafe operation.

## 04.20.12 Work packages and ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Permission and configuration data model | Developer 1 | Versioned grants and authorization checks |
| Configuration API and CLI commands | Developer 1 | Inspect and change workflows |
| Windows directory and application mappings | Developer 2 | Locally enforced resource boundaries |
| Credential storage and revocation behavior | Developer 1 + Developer 2 | Protected credentials and safe revocation |
| Capability reporting and model-facing descriptions | Developer 3 | Planner receives only relevant capabilities |
| Security and consistency tests | All three | Cross-user, stale-configuration and revocation coverage |

The shared contracts should define how permission changes reach the bridge, how the bridge reports effective configuration and what happens when the backend cannot confirm the current state.

## 04.20.13 Implementation priorities

P0 — Required foundation

Explicit, enforceable permissions

- Per-user and per-device authorization.

- Logical directory mappings.

- Explicit application allowlist.

- Permission inspection and revocation.

- Bridge-side validation.

- Versioned configuration and stale-state handling.

P1 — Operational maturity

Reliable configuration changes

- Configuration validation and diagnostics.

- Credential rotation and recovery workflows.

- Effective permission reporting.

- Configuration change history.

- Better user-facing permission inspection.

P2 — Future administration

Advanced management

- Fine-grained administrative roles.

- Optional shared resource grants.

- Rich configuration management interface.

- Advanced policy review and change analytics.

## 04.20.14 Open decisions

- Who is authorized to enroll the first users and devices?

- Can a device have multiple authorized users, or is the initial model strictly owner-only?

- Which directories should be suggested during setup, if any?

- Which applications belong in the initial allowlist?

- How are permission changes versioned and propagated to offline devices?

- What revocation propagation delay is acceptable?

- Which settings are user-managed versus administrator-managed?

- Which configuration and audit records must be retained?

- What credential storage and rotation workflow will be implemented?

- Should permission changes require confirmation in the CLI, and which changes qualify?

## 04.20.15 Definition of done

- Every developer can inspect their own registered devices and effective permissions.

- Directory and application scopes are explicit and locally validated.

- User preferences cannot change security authority.

- Backend and bridge independently enforce relevant restrictions.

- Revocation blocks new unauthorized dispatch and handles in-flight work safely.

- Stale configuration is detected for security-sensitive operations.

- Secrets are protected and excluded from routine diagnostics.

- Configuration changes are versioned and auditable.

- Restore and offline-device behavior are tested.

- Cross-user, path-security and revocation tests pass.

Section exit criterion: every developer can configure and inspect NEXUS's effective permissions on their own Windows computer, while the shared backend and AI remain constrained by explicit, independently enforced access rules.
