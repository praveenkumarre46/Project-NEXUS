## 04.23.01 Purpose

NEXUS consists of multiple components that may not be updated at exactly the same time: the shared FastAPI backend, CLI, native Windows bridge, PostgreSQL schema, local AI runtime and registered tool definitions.

This section defines how these components are packaged, versioned, upgraded and recovered without corrupting task state or accidentally repeating Windows operations.

The objectives are to:

- Make installation reproducible across the three developers' computers.

- Keep backend and bridge versions compatible.

- Detect unsupported protocol and tool-schema combinations.

- Apply database migrations safely.

- Preserve task, approval and operation-recovery records across upgrades.

- Prevent updates from silently broadening permissions.

- Support controlled rollback or forward-fix when an upgrade fails.

Core principle: an upgrade is not complete merely because the new application process starts. Compatibility, persistent data, device connectivity and recovery behavior must also be verified.

## 04.23.02 Packaging boundaries

NEXUS should be packaged according to where each component runs, rather than forcing the entire product into one deployment artifact.

Backend package

FastAPI application, shared application modules, configuration validation and database access.

Runs in the selected backend environment, initially expected to be the designated team's host.

CLI package

Terminal commands, API client, authentication handling and result presentation.

Installed separately for each user.

Windows bridge package

Device authentication, local configuration, registered tools, filesystem safeguards and operation journal.

Runs natively on each registered Windows computer.

Persistent data and configuration

PostgreSQL schema, migrations, task state, approvals, memory, audit events and recovery metadata.

Managed separately from application binaries; backups and retention rules apply.

AI runtime and model

Selected inference runtime, model artifact, configuration and evaluation metadata.

Versioned independently because model upgrades can change behavior without application-code changes.

### Proposed packaging decisions

- Package the backend as a versioned Python application or container image, depending on the deployment approach selected in Section 04.21.

- Package the CLI as a versioned Python CLI initially; a standalone executable can be considered later.

- Keep the native Windows bridge independently versioned so it can be upgraded without rebuilding the backend.

- Keep PostgreSQL data and device-specific configuration outside replaceable application packages.

- Keep the AI runtime and model versions explicit rather than silently downloading a newer model during startup.

The exact package formats remain open decisions. The team should choose the simplest format that can be installed and upgraded reliably in the actual environment.

## 04.23.03 Versioning strategy

NEXUS should distinguish the overall product release from the versions of its independently evolving components.

| **Version identifier** | **What it identifies** |
| --- | --- |
| Product release | A tested combination of component versions |
| Backend version | FastAPI application and shared backend logic |
| CLI version | Terminal commands and API client behavior |
| Bridge version | Native Windows execution implementation |
| API version | Public client/backend contract |
| Bridge protocol version | Backend/bridge communication contract |
| Tool schema version | Inputs, outputs and behavior of an individual registered tool |
| Database schema version | Applied PostgreSQL migration state |
| Policy version | Effective security-policy definition |
| AI runtime/model version | Inference runtime and model artifact |
| Configuration schema version | Supported configuration structure and semantics |

A product release might therefore reference a backend version, CLI version, bridge version, database schema version and model version. The exact version values should come from the build and release records, not be manually copied into unrelated files.

### Versioning rules

1. Each independently deployable component has a discoverable version.

2. The backend exposes its version through an authenticated or appropriately limited diagnostics endpoint.

3. Each bridge reports its version during authenticated communication.

4. Tool capability reports include supported tool-schema versions.

5. Database migrations identify the schema version they establish.

6. The release record captures the combination that passed testing.

7. A model version change is recorded even if the application code is unchanged.

8. Unknown or unsupported security-sensitive versions fail closed.

Semantic versioning is a candidate for application packages, but the team must document what counts as a breaking change for each component. Database migrations and tool schemas have their own compatibility requirements and should not be treated as interchangeable with application versions.

## 04.23.04 Compatibility matrix

The backend must know which client and bridge versions it can safely support.

The following matrix defines the policy to implement, rather than claiming any particular version combination is already compatible.

| **Component combination** | **Required behavior** |
| --- | --- |
| Supported CLI + current API | Normal authenticated operation |
| Unsupported CLI + API | Clear compatibility error or documented upgrade path |
| Supported bridge + current protocol | Normal capability negotiation |
| Unsupported bridge protocol | Reject incompatible operations |
| Bridge supports older tool schema only | Use a verified compatible schema or disable that tool |
| Database schema incompatible with backend | Block readiness and provide an actionable diagnostic |
| Model runtime unavailable | Report degraded capability; do not corrupt task state |
| Unknown policy or configuration schema version | Reject unsafe interpretation and require an explicit migration |

### Compatibility negotiation

When a bridge connects, the backend should establish:

- The authenticated device identity.

- The bridge protocol version.

- The bridge implementation version.

- Supported tool names and schema versions.

- Device configuration and capability status.

- Whether the reported versions are supported by the backend.

Capability negotiation is not authorization. Even if a bridge supports a tool, the backend must independently validate user ownership, device targeting, permissions, approval and current policy before dispatch.

### Mixed-version operation

During a controlled upgrade, the backend and bridges may temporarily run different versions. This must be explicitly supported and tested.

If the team cannot prove that a mixed-version combination is safe, the affected operations should remain disabled until the versions are compatible. NEXUS must not silently reinterpret an in-flight operation under a new tool schema.

## 04.23.05 Upgrade classification

Not all changes carry the same risk. NEXUS should classify updates before deployment so the team knows which validation and recovery steps are necessary.

Class A — Low risk

Compatible application update

Examples: CLI output improvement, documentation change or a backend bug fix that does not alter contracts or persistent data.

Required checks: CI, compatibility checks, smoke test and release record.

Class B — Contract change

Backend, CLI, bridge or tool interface update

Examples: a new required request field, bridge protocol update or changed tool behavior.

Required checks: producer/consumer contract tests, version negotiation, mixed-version testing if supported and controlled rollout.

Class C — Persistent data change

Database or configuration migration

Examples: new task-state fields, revised approval metadata or a change to the configuration schema.

Required checks: backup, migration tests, upgrade compatibility, failure recovery and post-migration validation.

Class D — Security or execution change

Policy, permissions, filesystem or recovery behavior

Examples: modifying directory-scope validation, changing approval semantics or altering operation retry rules.

Required checks: focused security tests, failure-injection tests, cross-component review and explicit release approval.

Class E — Model/runtime change

Change that can alter AI behavior or resource usage

Examples: switching models, quantization, inference runtime or planner prompts.

Required checks: model evaluation, safety regression, hardware benchmark and a documented promotion or rollback plan.

A single release may contain several classes. In that case, apply the combined requirements of all relevant classes.

## 04.23.06 Standard upgrade workflow

Every upgrade should follow a controlled sequence.

1. Prepare

Identify versions, changes, dependencies and risks

2. Validate

CI, compatibility, migration and security checks

3. Protect existing state

Backup required data and configuration; identify unresolved operations

4. Deploy in a controlled order

Apply compatible schema and application changes

5. Verify

Readiness, authentication, bridge compatibility and smoke tests

6. Approve or recover

Record success or execute the documented recovery procedure

### Step 1 — Prepare

The release owner identifies:

- Current and target component versions.

- API, bridge and tool-contract changes.

- Required database and configuration migrations.

- Model/runtime changes.

- Required downtime or bridge reconnection.

- Known compatibility limitations.

- Recovery steps and the responsible person.

### Step 2 — Validate

The candidate must pass all required CI and release-candidate checks. Class C, D and E updates require their respective additional tests.

### Step 3 — Protect existing state

Before a consequential upgrade:

- Take and verify the required PostgreSQL backup.

- Preserve necessary configuration and credential-recovery information securely.

- Check for active, approval-waiting, interrupted or uncertain tasks.

- Confirm the current version combination and recovery procedure.

- Ensure a rollback will not silently reinstate revoked permissions or credentials.

A backup that has not been validated is not sufficient evidence that recovery will work.

### Step 4 — Deploy

Use the rollout order appropriate to the change. Do not update the backend, all bridges, database and model simultaneously without a tested compatibility plan.

### Step 5 — Verify

Run health checks, authentication tests, bridge capability checks and the relevant smoke tests. A successful process start alone is not enough.

### Step 6 — Approve or recover

Record the release as successful only after all mandatory checks pass. If validation fails, stop further rollout and follow the documented rollback, forward-fix or recovery procedure.

## 04.23.07 Database migration and application compatibility

Database changes need special treatment because application binaries can be replaced, but persistent data may remain changed.

### Recommended migration approach

Use expand → migrate → contract when a change affects persisted fields or requires compatibility across application versions.

1. Expand: introduce compatible schema changes, such as an optional field or new table.

2. Migrate: populate or transform existing data with an explicit, tested process.

3. Switch: deploy application code that uses the new representation.

4. Verify: check record integrity and application behavior.

5. Contract: remove obsolete schema only after no supported code path depends on it.

Not every migration requires all five stages. A simple additive change may need less work, while a destructive change needs stronger safeguards.

### Migration invariants

- Existing task, step, approval and operation identities must remain consistent.

- Ownership and uniqueness constraints must remain enforced.

- Recovery metadata must retain its meaning across upgrades.

- Old records must not become executable merely because a field was added or defaulted.

- A schema migration must not automatically reauthorize old tasks.

- In-flight operations must be reconciled according to their recorded execution state.

- If the schema is incompatible with the running backend, the backend must not continue normal execution.

### Rollback limitations

Rolling the backend code back does not necessarily reverse a database migration. If the old version cannot safely read the new schema, the team must use a compatible forward-fix or a tested database recovery strategy.

Restoring an old database can also reintroduce stale records. In particular, revoked device credentials, deleted memory and uncertain Windows side effects require explicit reconciliation rather than automatic replay.

## 04.23.08 Windows bridge upgrade strategy

The Windows bridge is especially sensitive because it can perform external side effects on a user's computer.

A bridge upgrade must preserve local configuration, protect credentials and handle operations that may already have been dispatched.

### Required upgrade sequence

1. Confirm that the target bridge is authenticated and identified correctly.

2. Check compatibility with the proposed backend and tool schemas.

3. Stop accepting new local operations during the controlled upgrade.

4. Report the status of in-flight operations.

5. Reconcile uncertain operations before resuming work.

6. Install the new bridge version while preserving protected configuration and the operation journal.

7. Authenticate again if required by the credential or protocol change.

8. Report the new version and capability manifest.

9. Run a permitted read-only test.

10. Re-enable eligible operations only after compatibility and policy checks pass.

### Bridge upgrade failure

If the bridge cannot start or authenticate after an update:

- Report the device as unavailable or incompatible.

- Do not accept new work through the failed bridge.

- Preserve the operation journal and diagnostic evidence.

- Do not delete local state as part of a routine reinstall.

- Do not automatically replay all previously dispatched operations after restoring the older version.

- Reconcile outstanding work before resuming normal operation.

### Credential changes

If an upgrade changes the credential format or protocol, credential rotation and bridge re-registration must be explicit. The upgrade must not log secrets or silently fall back to an unauthenticated communication mode.

## 04.23.09 CLI upgrade strategy

The CLI can usually be upgraded independently, provided the backend API remains compatible.

### Requirements

- Show the CLI version and the backend version during diagnostics.

- Detect unsupported API versions and return a useful compatibility error.

- Preserve user configuration without copying secrets into logs or package files.

- Avoid silently resetting the selected device, output format or other user preferences.

- Document the supported upgrade and reinstall procedure.

- Test authentication renewal or reauthentication after a CLI update.

A CLI upgrade must not change server-side permissions. A new CLI command is not evidence that the backend supports or authorizes that action.

If the backend does not support a requested command, the CLI should report the limitation rather than emulate the operation through an unrestricted local shell command.

## 04.23.10 AI runtime and model upgrades

Model upgrades are separate from ordinary code deployment because they can change tool selection, planning behavior, latency and resource consumption.

### Promotion procedure

1. Record the currently approved model and runtime configuration.

2. Obtain the candidate model artifact and verify its identity and integrity.

3. Run the fixed evaluation dataset.

4. Run prompt-injection, scope-adherence and invalid-output tests.

5. Benchmark resource use and latency on the designated host.

6. Test behavior under the expected three-user workload.

7. Record the evaluation results.

8. Promote the candidate only if the required gates pass.

9. Preserve the previous approved configuration for recovery where feasible.

### Runtime failure during upgrade

If the new runtime fails:

- Report AI capability as unavailable or degraded.

- Preserve the state of accepted tasks.

- Do not mark AI-dependent tasks as completed.

- Do not bypass planning validation or policy enforcement to compensate.

- Restore the prior validated runtime or model configuration when safe.

- Reconcile tasks whose external operations may already have occurred.

A model rollback must not cause an old plan to be re-executed blindly. Any retry or replanning must follow the task lifecycle, approval and operation-recovery rules.

## 04.23.11 Configuration and policy upgrades

Application configuration, device configuration and security policy must be upgraded independently.

A configuration schema migration may change how a setting is represented, but it must not accidentally broaden permissions.

### Configuration migration requirements

- Each configuration format has a version.

- Supported migrations are explicit and tested.

- Unknown security-sensitive settings are not silently accepted.

- Missing permission fields do not default to unrestricted access.

- Device-specific directory mappings remain local to the appropriate bridge.

- Backend policy remains authoritative for central authorization.

- Local bridge restrictions remain independently enforced.

- Revoked permissions remain revoked after application rollback or configuration restoration.

### Policy changes

A policy upgrade should include:

1. A reviewed policy change.

2. Tests covering newly allowed and denied operations.

3. A documented effective policy version.

4. Explicit treatment of pending approvals.

5. Revalidation of queued operations before dispatch.

6. Audit evidence of the policy change.

If an operation was approved under an older policy, that approval must not automatically override a newer prohibition. The backend should revalidate the operation under the applicable current policy and require a new approval where necessary.

## 04.23.12 Upgrade behavior for active tasks

Application upgrades must preserve the task state machine defined in Section 03.29.

| **Task condition** | **Required upgrade behavior** |
| --- | --- |
| Queued, not dispatched | Preserve the task and revalidate compatibility, permissions and policy |
| Waiting for approval | Preserve the pending state; invalidate or revalidate approval if the operation or policy changed |
| Running a read-only operation | Finish or safely interrupt according to the tool contract |
| Dispatched write with unknown outcome | Preserve uncertainty and reconcile before retry |
| Device offline | Keep the task bound to the registered target device |
| Terminal task | Preserve its recorded outcome and history |
| Cancel requested | Continue cancellation and reconciliation; do not revive the task |
| Interrupted task | Recover according to persisted state and verified external evidence |

### Critical invariant

A deployment must not transform an uncertain operation into a successful one simply because the new version starts correctly.

Likewise, a terminal task must not become active again as a side effect of a migration, application rollback or recovery routine.

### Deployment coordination

Before upgrading a component, the release procedure should determine whether the change requires:

- Draining new task dispatches.

- Waiting for safe in-flight completion.

- Reconciliation of unresolved operations.

- Temporary disabling of incompatible tools.

- Reauthentication or bridge reconnection.

- A maintenance window.

The exact requirements depend on the change classification. A documentation-only update does not need the same procedure as a change to operation identity or task persistence.

## 04.23.13 Rollback and recovery strategy

Rollback must be planned before deployment, not improvised after a failure.

### Recovery decision process

Upgrade validation fails

Stop further rollout and preserve diagnostic evidence

Classify the failure

Application, contract, database, configuration, model or external operation

Choose a safe recovery path

Rollback, forward-fix, compatible mode or database restore

Reconcile persisted and external state

Task records, operation journal, credentials, policy and Windows side effects

Revalidate before resuming

Health checks, security checks, smoke tests and release approval

### Recovery options

- Application rollback: restore a previously validated application artifact when it remains compatible with the current schema and protocol.

- Forward-fix: deploy a corrected version when the new database schema cannot safely support the old application.

- Configuration restoration: restore compatible configuration while preserving current revocations and security restrictions.

- Database restore: use a verified backup when necessary, then reconcile task, approval and external operation state.

- Feature disablement: disable an incompatible tool or capability while preserving unrelated safe functions.

### What rollback cannot promise

Rollback cannot guarantee that a Windows file was not created, an application was not launched or a side effect was reversed. Those are external outcomes that require evidence and tool-specific recovery.

The team must not automatically retry consequential operations just because the application was rolled back.

## 04.23.14 Compatibility and upgrade test plan

The following tests should be part of release readiness.

| **Test scenario** | **Acceptance requirement** |
| --- | --- |
| Backend upgraded with supported CLI | CLI continues to operate |
| Bridge upgraded with supported backend | Bridge authenticates and reports compatible capabilities |
| Unsupported bridge protocol | New operations are rejected safely |
| Schema migration succeeds | Data integrity and ownership constraints remain valid |
| Migration fails midway | Readiness is blocked and the documented recovery path works |
| Backend rollback after additive migration | Previous version works only if compatibility is explicitly supported |
| Model upgrade fails | AI-dependent work is not falsely marked successful |
| Bridge crashes during a write | Outcome is reconciled before any unsafe retry |
| Device credential is revoked | Restored application version cannot bypass revocation |
| Configuration schema changes | Existing valid configuration migrates without broadening permissions |
| Task is waiting for approval | Upgrade does not accidentally dispatch it |
| Task is already terminal | Upgrade preserves its terminal state |
| Old bridge reconnects after an upgrade | Version compatibility is rechecked before work resumes |
| Database restore follows upgrade | Stale permissions and uncertain side effects are reconciled |
| Package reinstall occurs | Device identity and protected local recovery state are handled explicitly |

Release-candidate testing must use isolated test directories and accounts. These tests must never be run against uncontrolled personal files.

## 04.23.15 Implementation priorities

P0 — Required foundation

Safe packaging and upgrades

- Independently versioned backend, CLI and Windows bridge.

- Version and capability reporting.

- Explicit API, bridge and tool-schema compatibility.

- Versioned database and configuration migrations.

- Protected state and credential preservation.

- Documented upgrade, rollback and recovery procedures.

- Tests for in-flight and uncertain operations.

P1 — Controlled rollout

More reliable maintenance

- Automated package creation and integrity checks.

- Upgrade preflight validation.

- Automated compatibility reports.

- Controlled bridge rollout and reconnect verification.

- Model promotion and rollback workflow.

P2 — Future maturity

Advanced release management

- Signed packages and stronger artifact provenance.

- Automated staged deployment.

- Advanced multi-version compatibility testing.

- More automated recovery orchestration.

## 04.23.16 Open decisions

1. Will the backend be distributed as a Python package or a container image?

2. Will the CLI and Windows bridge remain Python applications initially, or will either be packaged as standalone executables?

3. Which versioning scheme will be used for applications, protocols and tools?

4. Which mixed-version combinations must be supported?

5. Will database migrations follow expand–migrate–contract wherever necessary?

6. How will bridge packages be distributed and upgraded on the three computers?

7. How will the team verify package integrity and protect release artifacts?

8. Which updates require a maintenance window or draining active work?

9. Which recovery actions require a manual operator?

10. How will model artifacts and runtime versions be pinned and restored?

These decisions should be closed as the initial deployment and first upgrade workflow are implemented.

## 04.23.17 Definition of done

- Backend, CLI and bridge have independently identifiable versions.

- The overall release records the tested component combination.

- API, bridge and tool-schema incompatibilities are detected.

- Database and configuration migrations are versioned and tested.

- Bridge upgrades preserve credentials and required recovery state.

- Model changes require appropriate evaluation before promotion.

- Queued, in-flight and uncertain tasks survive upgrades safely.

- Rollback limitations and forward-fix procedures are documented.

- Revoked permissions cannot be restored accidentally through rollback.

- Upgrade and recovery tests pass on the intended deployment topology.

- The team has successfully tested at least one controlled upgrade and recovery scenario.

Section exit criterion: NEXUS can be upgraded component by component without silently breaking compatibility, losing required recovery information or repeating unsafe Windows operations.
