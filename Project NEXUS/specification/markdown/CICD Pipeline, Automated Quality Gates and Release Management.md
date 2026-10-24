## 04.22.01 Purpose

NEXUS needs a repeatable way to validate code before merging it, detect integration failures early and produce releases that the entire team can reproduce.

Because NEXUS can operate on real Windows computers, passing ordinary unit tests is not enough. The pipeline must also test authorization, device isolation, operation recovery, filesystem restrictions, database migrations and AI-generated plans.

The goals are to:

- Catch defects before they reach the shared deployment.

- Prevent incompatible API, bridge and tool-contract changes from merging unnoticed.

- Ensure every accepted change has appropriate tests.

- Verify Linux backend and native Windows behavior separately.

- Prevent security regressions from entering release candidates.

- Make every release traceable to a specific version of the code, database schema, bridge protocol and AI configuration.

Core principle: CI verifies changes automatically; CD promotes a verified build through controlled environments. Neither process should automatically grant NEXUS new computer permissions.

## 04.22.02 Proposed pipeline architecture

1. Pull request opened

Code, tests, contracts, configuration and migrations

2. Fast automated checks

Formatting, static analysis, type checks and unit tests

3. Integration and contract tests

PostgreSQL, migrations, API, bridge and tool schemas

4. Security and reliability gates

Authorization, prompt injection, duplicate operations and recovery

5. Native Windows integration

Bridge tests, filesystem boundaries and packaging checks

6. Merge and build artifact

Reviewed change, reproducible build and version metadata

7. Controlled integration or release deployment

Migrations, smoke tests, recovery checks and release sign-off

This is the proposed logical pipeline. The specific CI provider and deployment automation tool remain open decisions.

## 04.22.03 Environments and promotion rules

NEXUS should use separate environments for separate purposes.

| **Environment** | **Purpose** | **Data and permissions** |
| --- | --- | --- |
| Developer local | Rapid implementation and debugging | Synthetic data and test directories |
| Automated CI | Repeatable checks on each change | Isolated database, temporary files and test credentials |
| Team integration | Validate combined work across developers | Dedicated test users, devices and directories |
| Release candidate | Validate the exact build intended for release | Controlled configuration and explicit test permissions |
| Team deployment | Run the approved shared installation | Real team accounts, protected credentials and configured permissions |

### Mandatory environment rules

1. Automated tests must not use real personal documents or uncontrolled production resources.

2. CI must not receive real device credentials or unrestricted access to a developer's computer.

3. Integration and test databases must be separate from the team's operational database.

4. Model tests should use deterministic fixtures for ordinary CI; live-model evaluation can run in a separate controlled job.

5. A release candidate must be tested using the same artifact that will be promoted, not an independently rebuilt variant.

6. Environment-specific settings and secrets must remain outside source control.

A test that requires a dependency unavailable in the current runner must be reported as not run, not silently counted as passed.

## 04.22.04 CI workflow for every pull request

Every pull request should run a consistent baseline. Expensive hardware-dependent and live-model tests can run in dedicated jobs, but required checks must remain visible.

Gate A — Code quality

- Formatting and linting.

- Static analysis and type checking.

- Dependency and import validation.

- Configuration examples validated against the current settings schema.

Gate B — Unit tests

- Task and step state transitions.

- Authorization and policy decisions.

- Idempotency and retry classification.

- Plan and tool-schema validation.

- Memory scope and retrieval filtering.

Gate C — Database and contract tests

- Fresh PostgreSQL initialization.

- Migration upgrade tests.

- Uniqueness and transaction behavior.

- API, bridge and tool-schema compatibility.

- Concurrent claim and ownership enforcement tests.

Gate D — Security regression

- Cross-user and cross-device access denial.

- Approval replay and modified-argument rejection.

- Path traversal and unapproved filesystem access.

- Unknown-tool rejection and prompt-injection fixtures.

- Secret leakage checks.

Gate E — Platform-specific validation

- Backend tests on the supported Linux environment.

- Native Windows bridge tests on a Windows runner.

- Package and startup checks.

- End-to-end tests on designated integration runs.

### Required behavior on failure

- A failed required check blocks merging.

- A flaky test is investigated and tracked; it is not permanently excluded merely to keep CI green.

- Skipped tests are identified with their reason.

- A dependency outage is distinguished from an application defect.

- Security-sensitive failures require a fix and regression test, not just a manual override.

- Changes to a shared contract trigger tests for the components that consume it.

## 04.22.05 Test execution strategy

Not every test belongs in every pipeline stage. The team should balance fast feedback with sufficiently strong release evidence.

| **Test class** | **Pull request** | **Release candidate** |
| --- | --- | --- |
| Formatting, static checks and unit tests | Required | Required |
| API and tool contract tests | Required | Required |
| PostgreSQL integration tests | Required | Required |
| Core authorization regressions | Required | Required |
| Native Windows bridge tests | Required for relevant changes; baseline required before release | Required |
| Failure-injection and recovery suite | Targeted tests on relevant changes | Full required suite |
| Full three-device end-to-end suite | Selected integration runs | Required |
| Live AI quality benchmark | When planner, model or context changes warrant it | Required for the selected model configuration |
| Hardware performance benchmark | Targeted when relevant | Required baseline comparison |
| Backup and restore drill | When backup, schema or recovery behavior changes | Required before release |

The exact runtime and runner allocation can be tuned later. The team must not remove a release-critical test simply because it is slower than unit tests.

### Deterministic testing policy

Most application tests should not depend on unpredictable model output.

Use a deterministic planner fixture that can return:

- A valid plan.

- An invalid schema.

- An unsupported tool.

- A request requiring clarification.

- A plan containing unauthorized arguments.

- A plan that triggers approval.

- A model timeout or unavailable error.

Then verify that the same authorization, state-transition and execution controls apply in every case.

The real model is evaluated separately for planning quality and performance. A mock planner passing tests does not establish that the chosen model is suitable for production use.

## 04.22.06 Database migration quality gates

Database migrations deserve their own release controls because a broken migration can prevent startup or damage persistent task state.

Every migration pull request should include:

1. The migration file and associated model changes.

2. Relevant constraints and indexes.

3. Tests against a fresh database.

4. Tests upgrading a database created from the previous supported schema.

5. Tests for important ownership, uniqueness and concurrency invariants.

6. A documented deployment and recovery procedure when the migration is consequential.

### Migration safety rules

- The schema version must be discoverable.

- Migration failure must be visible and must block normal readiness when the schema is incompatible.

- Shared integration databases must not be migrated by arbitrary developer test runs.

- Destructive data changes require explicit review and a recovery plan.

- A schema rollback is not assumed to undo a Windows-side effect.

- If a migration changes the meaning of persisted task or operation records, recovery compatibility must be tested before deployment.

Where a migration is not safely reversible, the release plan should describe a forward-fix or restore strategy rather than promise a rollback that cannot work.

## 04.22.07 API, bridge and tool-contract compatibility

NEXUS has multiple independently running components. A backend update must not silently break an installed Windows bridge.

The pipeline should validate three distinct compatibility boundaries:

- Public API: CLI ↔ FastAPI.

- Bridge protocol: FastAPI ↔ Windows bridge.

- Tool contract: planner and backend ↔ registered tool implementation.

### Contract-change procedure

1. Identify the contract being changed.

2. Update the canonical schema and examples.

3. Identify all producers and consumers.

4. Add positive and negative contract tests.

5. Verify version compatibility.

6. Update the relevant implementations.

7. Test mixed-version behavior if mixed versions are supported.

8. Document the minimum compatible version and rollout order.

### Compatibility policy

- Unknown security-sensitive fields or unsupported protocol versions must not be interpreted optimistically.

- A bridge must not execute a tool schema it does not support.

- A backend must not assume that a reported capability is still available at execution time.

- Disabling a tool must prevent new dispatches, while in-flight operations follow the defined recovery protocol.

- A rollback must not reinterpret a previously dispatched operation under a different schema.

- If compatibility cannot be established, fail closed and report a stable error.

Proposed release rule: contract-breaking changes require an explicit compatibility plan. Supporting mixed versions is a deliberate feature, not an assumption.

## 04.22.08 Native Windows CI and integration testing

Linux CI alone cannot establish that the Windows bridge behaves correctly on Windows 11.

Native Windows testing should cover:

- Installation and startup in a clean environment.

- Protected credential access.

- Windows path normalization and access-control behavior.

- File creation without overwriting existing files.

- Reparse-point and directory-boundary handling.

- Application allowlist enforcement.

- Operation deduplication and journal recovery.

- Timeouts, disconnects and reconnects.

- Package creation and documented launch instructions.

### Runner strategy

A practical initial approach is to use hosted CI runners for general code checks where suitable, and a native Windows runner for bridge-specific validation.

The team may use a self-hosted Windows runner if the required environment cannot be reproduced reliably on hosted runners. If so, it must be isolated from real user files, use restricted credentials and execute only trusted pipeline code.

No CI job should have unrestricted access to a developer's normal Windows session or personal directories.

## 04.22.09 AI evaluation and model promotion

A model change can affect planning behavior even when application code has not changed. NEXUS therefore needs a model-evaluation gate independent of ordinary code tests.

### Changes that trigger reevaluation

- Switching models or model versions.

- Changing model quantization or runtime configuration.

- Changing planner prompts or output schemas.

- Changing tool descriptions or capability discovery.

- Changing context assembly, retrieval ranking or chunking.

- Changing output limits, inference concurrency or retry behavior.

### Promotion requirements

The candidate model must pass:

1. Structured-output validation.

2. Tool-selection and argument-correctness evaluation.

3. Dependency and clarification tests.

4. Context grounding and source-reference tests.

5. Prompt-injection and scope-adherence tests.

6. Runtime-failure and timeout tests.

7. Latency and resource benchmarks on the designated host.

Hard safety gates cannot be offset by a better average score. For example, a model that plans faster but proposes unauthorized file access more often is not an acceptable upgrade.

### AMD hardware requirement

The model promotion record must identify the actual tested runtime, GPU or CPU execution mode, model artifact and relevant settings. AMD GPU support must be demonstrated on the selected machine rather than inferred from another developer's environment.

If the model fails evaluation, retain the previously approved configuration where operationally feasible. Do not automatically upgrade all users to an unvalidated model.

## 04.22.10 Security gates and release blockers

Security checks must be required pipeline gates, not optional reporting jobs.

| **Security scenario** | **Required outcome** |
| --- | --- |
| User requests another user's task | Access denied |
| User targets an unauthorized device | No dispatch |
| Approval is expired or its operation has changed | No dispatch |
| Model proposes an unknown tool | Rejected |
| Document attempts to override policy | No change to authorization |
| File path escapes an approved directory | Rejected |
| Bridge response has mismatched operation identity | Rejected or isolated for investigation |
| Operation times out after a possible write | Outcome remains uncertain until reconciled |
| Logs contain credentials or prohibited private content | Security test fails |
| Database or model endpoint is exposed beyond intended boundaries | Deployment gate fails |

### Release-blocking defects

A release candidate cannot be approved with an unresolved critical or high-severity defect involving:

- Cross-user data access.

- Unauthorized device execution.

- Authentication or approval bypass.

- Filesystem scope escape.

- Arbitrary model-generated command execution.

- Unsafe duplicate side effects or task-state corruption.

- Credential leakage.

- Uncontrolled exposure of private services.

- Recovery behavior that falsely reports an uncertain operation as successful.

A waiver should never be used to turn an unresolved core security invariant into an accepted product behavior. If a feature is unsafe, disable it or exclude it from the release.

## 04.22.11 Build artifacts, versioning and provenance

Every release candidate should be identifiable and reproducible enough for the team to determine exactly what was tested.

### Required release metadata

| **Item** | **What to record** |
| --- | --- |
| Application | Git commit and release version |
| Python dependencies | Lock-file version or digest |
| Database | Schema and migration version |
| API | API contract version |
| Windows bridge | Build version and bridge protocol version |
| Tools | Enabled tool definitions and schema versions |
| AI | Runtime version, model identifier and artifact digest where available |
| Policy | Policy version and relevant configuration version |
| Evaluation | Test suite and dataset version, pass/fail results |
| Deployment | Environment identifier and deployment configuration version, excluding secrets |

The artifact and its metadata should make it possible to answer:

- Which code is running on the shared host?

- Which bridge version is installed on each device?

- Which model configuration passed the release evaluation?

- Which migration was applied?

- Which test suite validated this candidate?

### Artifact rules

- Do not include secrets in build artifacts.

- Do not bundle user documents, memories or task history into an application package.

- Do not silently download a different model version during deployment.

- Validate artifact integrity before installation.

- Keep release notes and known limitations with the release.

- Retain the previous approved artifact for controlled rollback where feasible.

## 04.22.12 Deployment and release promotion

Deployment should be a controlled sequence rather than an unrestricted action triggered by a successful merge.

Development branch

Local tests and implementation

Reviewed pull request

Required CI checks and approvals pass

Main branch build

Versioned artifact and test evidence

Release candidate

Integration, security, recovery and AI evaluation

Controlled deployment

Backup, compatibility checks, migration and smoke test

Release approved

Version recorded; rollback or recovery procedure available

### Deployment procedure

1. Identify the exact release candidate.

2. Review required CI results and known defects.

3. Back up the database and necessary configuration.

4. Check backend, bridge, API and schema compatibility.

5. Apply migrations through the approved procedure.

6. Deploy the versioned backend artifact.

7. Verify readiness and authenticated API behavior.

8. Verify the model runtime and selected configuration.

9. Verify bridge connectivity and capability compatibility.

10. Run the release smoke tests.

11. Approve the release only if all mandatory gates pass.

12. Record the deployed versions and any remaining limitations.

For the initial team deployment, a documented manual release procedure is acceptable. Automated deployment can be added once the process is stable.

### Rollback considerations

A code rollback may not reverse a database migration, restore a revoked credential or undo a file created on a Windows computer.

The release procedure must distinguish:

- Application artifact rollback.

- Database recovery or forward-fix.

- Configuration restoration.

- Device credential rotation or re-registration.

- Reconciliation of operations already dispatched to a bridge.

Never blindly replay all unfinished tasks after rollback.

## 04.22.13 Branch protection and review policy

The existing short-lived branch approach remains the recommended workflow:

- feat/<short-name>

- fix/<short-name>

- docs/<short-name>

- test/<short-name>

### Pull request requirements

Every pull request should contain:

- A description of the problem and intended behavior.

- Links to the relevant requirement or architecture decision.

- Tests added or updated.

- API, database, bridge or tool-contract impact.

- Security and failure-mode implications.

- Configuration and migration impact.

- Relevant manual validation results.

At least one other developer should review ordinary changes. Security-sensitive changes—authentication, policy, filesystem access, operation recovery, credentials or network exposure—should receive cross-component review from another developer familiar with the affected boundary.

No developer should be the sole reviewer and sole validator of a security-critical change.

### Shared-contract changes

If a pull request changes a shared contract, the author must identify affected consumers. A bridge schema change, for example, requires reviewing the backend dispatcher and bridge implementation rather than checking only the schema file.

## 04.22.14 Three-developer ownership

| **Responsibility** | **Primary owner** | **Shared review** |
| --- | --- | --- |
| Backend, persistence, task lifecycle and migrations | Developer 1 | Developer 2 or 3 as appropriate |
| Windows bridge, filesystem safety and packaging | Developer 2 | Developer 1 for authorization and recovery |
| AI adapter, planning, context and model evaluation | Developer 3 | Developer 1 for policy and execution boundaries |
| Shared API and bridge contracts | Relevant producer | All affected consumers |
| Security gates and release readiness | Shared responsibility | At least one cross-component reviewer |
| Integration tests and release sign-off | Shared responsibility | All three developers |

Ownership means responsibility for driving the work, not permission to change shared contracts without review.

### CI maintenance

- Developer 1 owns backend and database CI reliability.

- Developer 2 owns Windows runner and bridge test reliability.

- Developer 3 owns model evaluation and AI regression reporting.

- All three review failures that cross component boundaries.

A pipeline failure should have an owner, a reproducible explanation and a resolution plan.

## 04.22.15 CI performance and cost control

NEXUS has a zero-budget constraint, so CI should provide strong coverage without requiring paid runners, hosted inference or unnecessary infrastructure.

Recommended approach:

- Run fast checks first so obvious defects fail early.

- Reuse dependency caches where safe.

- Use isolated PostgreSQL instances for integration tests.

- Use deterministic model fixtures for routine CI.

- Run hardware-intensive model benchmarks on the designated team computer when needed.

- Avoid running every long end-to-end test for every documentation-only change.

- Never skip mandatory security or contract tests just to reduce pipeline duration.

### Proposed pipeline service levels

These are initial targets to measure, not confirmed commitments.

| **Pipeline** | **Proposed target** |
| --- | --- |
| Fast checks and unit tests | Under 3 minutes |
| Standard pull-request pipeline | Under 10 minutes |
| Full release-candidate validation | Under 30 minutes, excluding lengthy hardware/model evaluations |

Track actual pipeline duration, failure rate, flaky-test rate, queue wait and time spent diagnosing failures. Optimize based on measurements rather than adding infrastructure prematurely.

## 04.22.16 Implementation priorities

P0 — Required

Trustworthy changes and releases

- Automated code-quality and unit checks.

- PostgreSQL integration and migration tests.

- API, bridge and tool-contract checks.

- Security regression gates.

- Native Windows bridge validation.

- Required code review and protected main branch.

- Release metadata and documented deployment procedure.

P1 — Stronger automation

Reliable integration and promotion

- Automated end-to-end release tests.

- Model-evaluation reports and regression comparison.

- Automated artifact packaging and integrity checks.

- Backup and restore validation.

- Release-candidate promotion automation.

P2 — Future maturity

Advanced delivery operations

- Automated staged deployment and rollback orchestration.

- More comprehensive release dashboards.

- Signed artifacts and stronger provenance controls.

- Automated compatibility testing across multiple supported versions.

## 04.22.17 Open decisions

The team must resolve these before finalizing the pipeline:

1. Which Git hosting and CI platform will be used?

2. Can the selected platform provide an appropriate native Windows runner within the zero-budget constraint?

3. Which dependency manager, lock-file format and code-quality tools will be standardized?

4. Which tests run on every pull request versus only during release validation?

5. How will the designated host run hardware-dependent AI benchmarks?

6. Which artifact format will be used for the backend and Windows bridge?

7. Who approves a release and controls deployment credentials?

8. How will migration recovery and application rollback be tested?

9. What pipeline-duration targets are achievable on the selected infrastructure?

These decisions should be recorded in the architecture decision register rather than silently embedded in CI configuration.

## 04.22.18 Definition of done

- The repository has a functioning CI pipeline.

- Required quality and unit checks run on pull requests.

- PostgreSQL integration and migration tests run against an isolated database.

- API, bridge and tool contracts are validated.

- Security-critical regression tests block merging when they fail.

- Native Windows bridge tests run on a suitable Windows environment.

- Model changes trigger the appropriate evaluation suite.

- Builds and releases have traceable version metadata.

- Main-branch protection and review requirements are documented.

- Release deployment, backup and recovery procedures are documented.

- The team has validated the release process using a real release candidate.

- No unresolved critical or high-severity security defects remain.

Section exit criterion: all three developers can contribute changes through a common pipeline and produce a tested, traceable release without relying on one person's machine or informal manual checks.
