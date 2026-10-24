## 03.39.1 Purpose

NEXUS accepts natural-language requests, retrieves personal context, plans operations and executes actions on Windows computers. This creates a security challenge beyond that of an ordinary CRUD application: a mistake can expose private information or cause an external side effect on a user's computer.

This section consolidates the architecture's security requirements into a practical threat model and defines the evidence required before NEXUS can be released to the three-developer team.

The central rule is:

No request, model response, task ID, device ID, document instruction or approval prompt is trusted merely because it exists. Every operation must pass the relevant identity, authorization, validation and execution checks.

Security must be enforced in application code and at the Windows execution boundary, not merely through instructions given to the AI model.

## 03.39.2 Assets that require protection

NEXUS should explicitly identify what could be compromised and the impact of that compromise.

| **Asset** | **Primary risk** |
| --- | --- |
| User accounts and session credentials | Account takeover and unauthorized actions |
| Device credentials | Impersonation of a registered Windows computer |
| Personal memory | Exposure or manipulation of private context |
| Task requests and execution history | Cross-user disclosure or unauthorized modification |
| Documents and filesystem access | Unauthorized reading, creation or alteration of files |
| Approval records | Unauthorized or replayed consequential operations |
| Tool registry and policy configuration | Expansion of permitted capabilities |
| Operation journals and recovery records | Duplicate side effects or false execution claims |
| PostgreSQL database and backups | Broad compromise of persistent application data |
| AI prompts and retrieved context | Prompt injection, information leakage and incorrect planning |
| Logs and diagnostic output | Accidental disclosure of credentials or private content |
| Shared inference runtime | Cross-request context contamination and resource exhaustion |

These assets have different security requirements. For example, confidentiality is central to personal memory, while integrity and recovery are especially important for operation journals and task state.

## 03.39.3 Trust boundaries and attack surface

The main trust boundaries are:

CLI and user input

Requests, credentials, commands and approval decisions

FastAPI backend

Authentication, authorization, validation, policy and orchestration

PostgreSQL

Persistent state, identity, memory and audit records

AI runtime

Untrusted proposals and retrieved context

Authenticated Windows bridge

Independent local validation and restricted execution

Windows resources and applications

Files, applications and any explicitly supported interactive operations

Each boundary needs explicit input validation, identity verification, error handling and logging rules.

The AI runtime is not a security authority. The database is not exposed directly to clients. The Windows bridge does not accept arbitrary commands simply because the backend sends them. Local operating-system permissions remain part of the final enforcement boundary.

The diagram is logical: the final network layout and bridge communication direction remain subject to the deployment decisions documented earlier.

## 03.39.4 Threat model and abuse scenarios

NEXUS should use a threat-modeling method that asks four questions for every important operation:

1. Who could initiate or influence it?

2. What resource or security boundary could be affected?

3. What could go wrong?

4. What control prevents the action, detects it or limits the damage?

The following table identifies the main threats for the initial deployment.

| **Threat** | **Example attack** | **Required controls** |
| --- | --- | --- |
| Broken object-level authorization | A user changes a task ID to access another user's task | Backend ownership checks on every read and mutation; cross-user tests |
| Device impersonation | An unauthorized client claims to be a registered Windows bridge | Unique device credentials, authenticated requests, revocation and replay protection |
| Approval replay | An old approval is reused for a modified operation | Approval bound to exact operation, arguments, target, expiry and policy |
| Prompt injection | A document instructs the model to read unauthorized files | Treat document text as untrusted; enforce permissions independently |
| Tool injection | A model proposes an unknown tool or unexpected argument | Strict tool registry and schema validation at backend and bridge |
| Path traversal | A request attempts to escape an approved directory | Windows-aware path validation, local scope enforcement and race-aware filesystem operations |
| Duplicate side effect | A lost response causes the same file creation or submission to run again | Stable operation IDs, deduplication, reconciliation and uncertain outcomes |
| Credential theft | A stolen session token is used to submit tasks | Protected credential storage, short-lived access tokens if selected, revocation and rate limits |
| Resource exhaustion | A user submits huge documents or unlimited tasks | Bounded inputs, queues, concurrency, extraction and model budgets |
| Sensitive logging | A diagnostic record contains a private document or access token | Structured, minimized logs; redaction; access control and tests |
| Configuration tampering | A tool's risk classification is lowered through an untrusted config change | Controlled configuration, validation, versioning and reviewed policy changes |
| Host compromise | An attacker obtains control of the shared backend computer | Least privilege, restricted network exposure, protected secrets, recovery and incident procedures |

These are design threats, not evidence that any existing NEXUS component is vulnerable. The team must verify the controls against the actual implementation.

## 03.39.5 Security requirements by layer

### API and application layer

- Authenticate requests before accessing protected resources.

- Derive the acting user from the authenticated identity, not from an untrusted request field.

- Authorize each resource read, mutation, task action and approval decision.

- Validate payload sizes, types, formats, identifiers and enumerated values.

- Use parameterized database queries and safe ORM patterns.

- Apply rate limits and bounded request processing where needed.

- Avoid exposing internal exception traces or secrets to clients.

- Do not allow clients or the model to set authoritative task states, tool risk levels or permission decisions.

### Database layer

- Use a dedicated application database role with only the required privileges.

- Keep PostgreSQL inaccessible to ordinary LAN clients.

- Enforce relationships and uniqueness through database constraints.

- Use short transactions for state transitions and worker claims.

- Separate schema-migration privileges from normal application privileges where practical.

- Protect backups and test restoration with authorization and revocation rules intact.

### AI and planning layer

- Treat model output as untrusted structured input.

- Restrict executable proposals to registered tools and supported schemas.

- Apply policy outside the model.

- Scope context retrieval to authorized information before it reaches the model.

- Bound document extraction, context size, model output and retries.

- Prevent retrieved text from modifying system policy, identity, permissions or approval state.

- Fail safely when the model or runtime is unavailable.

### Windows bridge layer

- Authenticate the backend or otherwise verify each operation's trusted origin.

- Validate device identity, operation identity, tool schema, arguments, deadline and local permissions.

- Enforce local filesystem and application restrictions.

- Run with the minimum operating-system privileges required.

- Do not expose a generic shell, PowerShell or arbitrary Python execution endpoint.

- Keep a durable operation journal or another validated recovery mechanism for operations requiring deduplication.

- Reconcile uncertain external effects before retrying them.

### Network and deployment layer

- Bind services to intended interfaces only.

- Keep PostgreSQL and the model endpoint private to the components that require them.

- Do not expose NEXUS publicly or configure router port forwarding for the initial LAN deployment.

- Restrict inbound connections using host firewalls.

- Use authenticated bridge communication and unique device credentials.

- Evaluate TLS when the LAN cannot be treated as trusted.

- Test access from a second computer; a successful localhost test does not establish LAN security.

## 03.39.6 Authentication, authorization and approval hardening

Authentication establishes who is making a request. Authorization determines what that identity can do. Approval provides an additional decision for specific operations; it does not replace either of the first two controls.

Every protected operation should follow this logical sequence:

1. Authenticate the user or bridge.

2. Resolve the authoritative identity and target resource.

3. Verify ownership and applicable permissions.

4. Validate the tool, schema, arguments and resource scope.

5. Apply hard prohibitions and risk policy.

6. Verify any required approval is current and matches the exact operation.

7. Revalidate immediately before dispatch.

8. Enforce local restrictions in the Windows bridge.

9. Persist the outcome and required audit evidence.

Not every check must be implemented as one transaction, but the ordering and enforcement boundaries must be explicit.

### Approval security rules

An approval should be bound to:

- The task and step.

- The authenticated user and target device.

- The exact normalized operation and relevant arguments.

- The resource scope and risk classification.

- The applicable policy version.

- The approval expiry and decision state.

The backend must reject approvals that are expired, already invalidated, associated with a different operation or submitted by an unauthorized user.

A modified operation requires revalidation and, where necessary, fresh approval. Approval must never permit a prohibited operation or override the bridge's local safety restrictions.

### Credential handling

The final credential design is still open, but the following principles are required:

- Never store plaintext passwords or access tokens in source control.

- Store password verifiers using an appropriate password-hashing scheme if local password authentication is selected.

- Give every registered device its own revocable credential.

- Protect tokens and secrets in logs, error messages and diagnostic output.

- Document session expiry, logout, revocation and credential rotation.

- Avoid putting credentials in command-line arguments, where they may be exposed through process inspection or shell history.

- Define how credentials are recovered or replaced if a device or the backend host is compromised.

These rules must be reflected in implementation and tests, not just configuration documentation.

## 03.39.7 Prompt injection and untrusted content

NEXUS will process documents, filenames, application output and potentially model-generated summaries. Such content may contain instructions designed to manipulate the planner.

For example, a document could contain text asking NEXUS to ignore prior rules and read a different directory. The document may be relevant to the user's task, but its contents must not grant additional authority.

The required behavior is:

- Label retrieved content as untrusted evidence, not policy.

- Keep user instructions, application policy and document content conceptually separate.

- Do not let a document modify tool availability, device identity, resource permissions or approval decisions.

- Validate all model-proposed operations against registered tool contracts.

- Filter memory and document retrieval by authorization before constructing model context.

- Revalidate permissions when the resulting operation is actually dispatched.

- Treat tool outputs as untrusted data as well; a compromised or unexpected tool response must not change the security policy.

Prompt wording is useful defense in depth, but prompt instructions alone are not a security boundary.

### Required adversarial scenarios

The test suite should include:

1. A document that requests access to files outside the permitted directory.

2. A document that instructs NEXUS to reveal another user's memory.

3. A retrieved memory that contradicts current authorization rules.

4. A model proposal that uses an unknown tool.

5. A model proposal that changes its arguments after approval.

6. A document that asks NEXUS to suppress errors or falsely report success.

7. A tool output containing instructions to invoke a different operation.

8. A malicious filename or extracted text containing shell-like syntax.

The expected outcome is that application-level controls remain effective regardless of the model's response. Evaluation must check for actual unauthorized side effects, not merely whether the model's final message sounds safe.

## 03.39.8 Data privacy and retention

NEXUS should collect and retain only the information required to operate, troubleshoot and satisfy explicitly defined product requirements.

The following data categories must have separate access and retention rules:

| **Data category** | **Required handling** |
| --- | --- |
| Authentication secrets | Never log; protected storage and revocation |
| Personal memories | Private by default; inspectable, correctable and deletable through supported controls |
| Document contents | Process only within authorized scope; no permanent storage by default |
| Task and step records | Owner-scoped; retain enough information for execution history and recovery |
| Approval and audit records | Restrict access; retain the evidence needed for security and accountability |
| Application logs | Minimize sensitive data; apply access control and retention limits |
| Operation journals | Retain enough information to prevent unsafe duplicate execution and support reconciliation |
| Backups | Protect against unauthorized access and define retention separately |

Deleting a memory from active retrieval is not necessarily equivalent to erasing every historical copy in logs or backups. The product must describe its actual deletion and retention behavior accurately.

Similarly, a task's result should not automatically include the full contents of a document simply because the document was read during execution.

The team must define retention periods, backup handling and deletion semantics before promising comprehensive erasure.

## 03.39.9 Security testing and release gates

Security checks should be integrated into development from the first working end-to-end flow. They must not be postponed until the final week.

### Mandatory security test groups

Identity and access tests

Verify authentication, ownership, cross-user access denial, device revocation, approval ownership and protected resource mutations.

Persistence and concurrency tests

Test duplicate requests, competing worker claims, transaction failures, stale workers, migration behavior and restoration from backup.

Filesystem and execution tests

Test path traversal, sibling-directory confusion, links and reparse points, create-if-absent behavior, operation replay and uncertain writes on Windows.

AI and prompt-injection tests

Test malicious documents, unauthorized tool proposals, changed arguments, context isolation, oversized requests and honest handling of unsupported tasks.

Network and deployment tests

Verify LAN access controls, private database/model endpoints, device authentication, firewall assumptions, service restart and credential rotation.

### Proposed release-blocking findings

A release candidate must not proceed with unresolved critical or high-severity security defects.

Examples of release blockers include:

- Cross-user access to private tasks or memories.

- Unauthorized execution on another user's device.

- A route that bypasses required authorization or approval.

- Model-generated arbitrary command execution.

- A path traversal or similar flaw that permits access outside the approved filesystem scope.

- Reuse of an approval for a materially different operation.

- An unsafe automatic retry that can repeat a consequential side effect.

- Exposure of credentials or private content through ordinary logs or diagnostics.

- A deployment configuration that exposes PostgreSQL or other protected services to unauthorized clients.

Severity must be determined using the actual impact and exploitability, not simply the number of affected lines or modules.

Lower-severity findings must still be documented, assigned an owner and given a resolution or explicitly accepted remediation plan. A deadline does not justify waiving a critical safety control.

## 03.39.10 Security acceptance matrix

Use this checklist during integration and release review. It records the required evidence rather than assuming the controls already work.

### Release evidence checklist

### 0/12

Cross-user task and memory isolation

Automated negative tests with at least two user accounts

Device identity and revocation

Bridge authentication and revoked-credential tests

Approval binding and replay protection

Changed-argument, expired-approval and unauthorized-approval tests

Restricted filesystem access

Windows path traversal, link and scope-boundary tests

No arbitrary model-generated commands

Registry enforcement and negative tool-contract tests

Safe handling of uncertain side effects

Lost-response, restart and reconciliation tests

Prompt-injection resistance

Adversarial document and tool-output evaluation

Secret-safe diagnostics

Automated log redaction and diagnostic-output tests

Private service exposure

Network reachability tests from an unauthorized LAN client

Backup and restore safety

Isolated restore drill, migration checks and authorization reconciliation

Three-user concurrent operation

End-to-end test with separate users and Windows bridges

Clean installation and configuration

Reproducible setup using documented configuration and fresh credentials

This checklist is a planning aid only. Checking an item records your selection in this interface; it does not run the test or certify that the control is implemented.

## 03.39.11 Incident response and recovery

Even with preventive controls, NEXUS needs a documented response when a credential is compromised, unauthorized access is suspected or the backend host becomes untrusted.

The initial incident procedure should be practical enough for three developers to follow.

1. Contain: disable affected accounts, revoke device credentials or isolate the affected service as appropriate.

2. Preserve evidence: retain relevant task IDs, audit events and bounded diagnostic records without unnecessarily copying private documents.

3. Assess impact: identify affected users, devices, tasks, credentials and resources.

4. Reconcile operations: determine whether in-flight external actions occurred before deciding whether they can be retried.

5. Restore trust: rotate or replace compromised credentials, correct configuration and restore from a verified backup if required.

6. Validate: rerun relevant security and integration tests before reopening affected functionality.

7. Document: record the incident, scope, response, unresolved risks and preventive changes.

If the shared host is compromised, simply restarting the backend is insufficient. The team must consider whether its credentials, database, configuration and device registrations can still be trusted.

The initial release does not need a sophisticated security operations platform, but it does need a clear way to disable access, rotate credentials, inspect relevant audit records and recover safely.

## 03.39.12 Implementation priorities

| **Priority** | **Scope** |
| --- | --- |
| P0 — Release blockers | Authentication and authorization, user/device isolation, approval enforcement, restricted tools, filesystem security, secret protection, safe recovery and critical security regression tests |
| P1 — Hardening | More extensive adversarial testing, credential rotation workflows, database defense in depth, improved incident diagnostics and regular restore drills |
| P2 — Advanced security operations | Centralized security monitoring, advanced access analytics, automated anomaly detection and independent security assessment |

P0 controls must be designed and tested while the relevant features are built. Security hardening is not a separate final-stage task.

### Proposed ownership

- Developer 1: API authorization, database permissions, task/approval integrity, audit and recovery.

- Developer 2: Windows bridge authentication, filesystem boundaries, local privilege restrictions and operation replay.

- Developer 3: prompt-injection evaluation, context isolation, model-output validation and sensitive-data handling.

- All developers: threat-model review, integration tests, release sign-off and incident-response rehearsal.

## 03.39.13 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| Local authentication design | Open; choose and document one supported approach |
| Access-token and session lifecycle | Open |
| Device credential format and rotation | Open |
| TLS on the private LAN | Evaluate based on network trust and deployment |
| PostgreSQL row-level security | Consider as defense in depth; test if selected |
| Audit and log retention | Must be defined |
| Security administrator role | Minimal operational access preferred; formal role model open |
| Incident-response authority | Must be assigned among the team |
| Security review method | Automated tests required; independent review scope open |
| Release severity policy | Critical/high findings block release; detailed triage process open |

## 03.39.14 Definition of done

- The team has reviewed the trust boundaries and threat scenarios.

- Authentication, authorization, device identity and approval checks are implemented at their designated enforcement layers.

- Prompt injection cannot grant access or bypass policy.

- Filesystem and bridge security tests cover the relevant Windows-specific behavior.

- Operation uncertainty and replay protection are tested.

- Sensitive data is excluded from ordinary logs and diagnostic output.

- Database and model services are not unnecessarily exposed to the LAN.

- Cross-user, cross-device and concurrent-operation tests pass.

- Backup restoration and credential revocation have been tested.

- Incident containment and recovery procedures are documented.

- No unresolved critical or high-severity security defects remain at release.

Section exit criterion: NEXUS has an evidence-based security baseline in which each important trust boundary has explicit controls, negative tests and defined behavior when those controls fail.
