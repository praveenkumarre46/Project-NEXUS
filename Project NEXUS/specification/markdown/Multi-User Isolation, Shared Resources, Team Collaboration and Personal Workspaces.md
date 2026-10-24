## 03.37.1 Purpose

NEXUS will serve three developers through a shared backend, but each developer must retain control over their own Windows computer, private files, personal memory, task history and approvals.

A shared backend does not mean that all users share the same permissions or context.

This section defines how NEXUS separates personal workspaces from shared infrastructure, handles concurrent users and devices, and prevents information or operations from crossing boundaries without authorization.

The initial design principle is:

Shared services, private user data, individually authorized devices, and explicitly granted collaboration.

## 03.37.2 Isolation model

NEXUS must distinguish four separate ownership boundaries.

User identity

Controls personal tasks, memory, history and granted permissions.

Device identity

Identifies the Windows computer where an operation may execute.

Resource scope

Defines which directories, applications and documents are accessible on a device.

Operation authorization

Determines whether a particular action is allowed under current policy and approval.

These boundaries are related but not interchangeable.

For example, a developer may be authenticated to NEXUS but not authorized to read another developer's task history. A registered device may be online but still lack permission to execute a particular tool. A user may be permitted to access a project but not to overwrite files in its workspace.

The backend must enforce these distinctions independently of what the AI model requests.

## 03.37.3 Personal workspace model

Each user receives a logically isolated workspace within the shared NEXUS service.

The proposed initial workspace contains:

- Personal tasks and execution results.

- Personal memories and personalization settings.

- Personal task history and authorized audit views.

- Registered devices and device-specific permissions.

- Personal configuration that is safe to store centrally.

- References to accessible projects, where project membership is implemented.

The workspace is a logical security boundary, not necessarily a separate database or filesystem directory for every user.

PostgreSQL can host multiple users' records in shared tables, provided ownership, authorization checks and database constraints are designed correctly. A separate database per user is not required for the initial three-developer deployment.

### Required isolation rules

1. The authenticated identity determines the user's scope; request-body fields cannot override it.

2. Task ownership is assigned by the backend when a task is created.

3. Memory retrieval filters by authorized scope before content reaches the model.

4. Device registration does not grant another user access to that device.

5. A user cannot approve an operation merely by knowing its task or approval ID.

6. A resource identifier is never proof of authorization.

7. Administrative access, if introduced, must be separately defined and audited.

8. User deletion, device revocation and project membership changes must not silently expose or reassign existing data.

For the MVP, personal memory and task history should remain private by default.

## 03.37.4 Device ownership and cross-device execution

NEXUS has a shared backend but executes Windows operations through the bridge registered to the target computer.

The proposed initial rule is owner-only device access: a device is managed by its registering user, and other users cannot target it unless an explicit device-sharing feature is designed and enabled.

Consider three developers, each with a Windows computer:

| **Request** | **Expected behavior** |
| --- | --- |
| Developer A searches a permitted folder on their own device | Allowed if the tool and directory permissions permit it |
| Developer A submits a task targeting Developer B's device | Denied unless explicit sharing has been implemented and granted |
| Developer B knows a valid task ID belonging to Developer A | No access without authorization |
| Developer A's device disconnects | Task remains associated with that device; no silent rerouting |
| A device is revoked while a task is queued | Prevent new dispatch and apply the documented recovery rules |
| A device is revoked while an operation is running | Block subsequent unauthorized operations and reconcile any in-flight side effect |

A device-sharing feature would require explicit grants defining the permitted users, resources, operations and revocation behavior. It must not be introduced by simply allowing arbitrary target_device_id values.

The same rule applies to application sessions. NEXUS must not use one developer's interactive Windows session to satisfy another developer's request without a separately approved and technically enforced sharing model.

## 03.37.5 Shared project context versus personal memory

NEXUS needs both personalization and useful project knowledge, but these have different ownership rules.

| **Context type** | **Default visibility** | **Initial-release behavior** |
| --- | --- | --- |
| Personal memory | Owner only | Supported |
| Personal task history | Owner only | Supported |
| Project notes or design decisions | Authorized project members only | Shared-project implementation remains open |
| Current document contents | According to the resource permissions | Read only through authorized tools |
| Tool registry and system policy | Application-controlled | Not user-editable through AI memory |
| Operational logs | Restricted operational access | Minimize private content |

A memory about a developer's preferred workflow should not automatically become a team-wide preference. Similarly, a document read during one user's task should not automatically be stored in a shared project memory.

### Proposed project-sharing model

If shared project context is approved for a later phase, introduce explicit project membership rather than a global shared-memory collection.

A project could have:

- project_id

- A project owner or responsible administrator.

- Explicit membership records.

- Member roles and permitted actions.

- Project-scoped memory and document references.

- Defined rules for membership changes and deletion.

These are logical design elements, not a finalized schema.

Important: membership in a NEXUS project does not automatically grant access to every local file in that project's name. The Windows bridge must independently verify access to the actual resource.

For the initial release, the safer choice is to keep personal memory private and defer shared project memory until authorization and deletion behavior are fully specified.

## 03.37.6 Concurrent requests from multiple users

All three developers may submit tasks at the same time. NEXUS must isolate data and enforce resource limits without requiring separate application instances for each person.

A task should carry its authenticated owner, explicit target device, resource scope and correlation identifiers through the execution pipeline.

The following invariants apply:

- User A cannot read, cancel, approve or modify User B's task merely by knowing its ID.

- Two users cannot claim the same task or step through competing workers.

- A task cannot be reassigned to another device simply because the original device is busy.

- Per-user and per-device concurrency limits must be enforced by backend code.

- Model and database capacity must be managed independently of user authorization.

- Queue fairness must prevent one user from monopolizing shared resources.

- A model's context must be assembled from the current user's authorized information, not from whichever request was processed previously.

The scheduler design in Section 03.28 remains applicable: a conservative PostgreSQL-backed scheduler, bounded queues and fair scheduling are preferable to adding a separate message broker before there is evidence that it is needed.

### Example: overlapping tasks

Suppose Developer A asks NEXUS to read a project document, Developer B requests a summary of a different document, and Developer C launches an approved application.

The backend may coordinate these requests concurrently, subject to resource limits. However, each task retains its own owner, device, context and execution records. The fact that tasks share a model runtime or database connection pool does not permit their private content to be mixed.

The AI runtime adapter must also handle concurrent requests safely. If the selected model runtime serializes inference, NEXUS should queue requests fairly rather than assuming that three simultaneous API calls mean three simultaneous model generations.

## 03.37.7 Database enforcement and query isolation

Application-level authorization is essential, but it should not be the only protection against accidental cross-user access.

For user-owned records, database access patterns should consistently include ownership or authorized-scope constraints. The precise enforcement approach—application-level checks alone, PostgreSQL row-level security, or a combination—must be chosen deliberately.

### Proposed baseline

- Every user-owned task has a required owner identifier.

- Every personal memory has an owner identifier.

- Every device has an owner or explicit access grants.

- Project-scoped records require valid project membership when shared projects are enabled.

- Foreign keys and uniqueness constraints protect data relationships.

- Queries that return lists must apply the same authorization rules as queries for individual records.

- Update and delete operations must include authorization checks, not just retrieval.

- Database sessions must not accidentally carry a previous user's authorization context.

- Background workers must obtain the authoritative owner and target device from persisted task records.

If PostgreSQL row-level security is selected, its policies and connection-pool behavior require dedicated tests. A correctly written policy can provide additional defense in depth, but a misconfigured database session or overly privileged application role can undermine that protection.

The team should not claim database-enforced isolation unless it has been configured and tested at the database boundary.

## 03.37.8 Authorization changes and revocation

Permissions can change while a task is queued, waiting for approval or executing. NEXUS must respond to those changes explicitly.

Proposed rules:

1. User disabled: reject new requests and deny subsequent protected operations.

2. Device revoked: reject new dispatches and reconcile in-flight operations as necessary.

3. Project membership removed: prevent new access to project-scoped data and context.

4. Directory mapping disabled: prevent operations that depend on that mapping.

5. Tool disabled: prevent new dispatches; already dispatched operations follow the established uncertainty and recovery protocol.

6. Approval invalidated: prevent the associated operation from proceeding unless it receives a valid replacement approval.

7. Credential rotated: invalidate the old credential according to the documented rotation procedure.

Revocation cannot always undo an action that has already occurred. If a file was created before the system learned of revocation, NEXUS must preserve the evidence and report the outcome accurately.

Authorization should be checked at request handling, task planning and immediately before dispatch as appropriate. The Windows bridge should also enforce its local restrictions.

## 03.37.9 Shared infrastructure and operational access

A shared backend creates operational responsibilities. Someone may need to restart the service, investigate failures, run migrations or restore the database.

Operational responsibility must not silently grant unlimited access to users' private memories and document contents.

The proposed distinction is:

- Ordinary user: accesses only authorized personal or shared-project functionality.

- Operational maintainer: can perform explicitly granted service-management tasks.

- Security administrator: may manage users, devices, credentials or policy if that role is implemented.

- AI planner: has no administrative authority and cannot grant permissions.

The last two roles are proposed future role categories, not confirmed MVP requirements. For the initial release, use the smallest practical set of administrative capabilities and document who is authorized to perform them.

Operational diagnostics should expose service status, task identifiers, error codes and bounded metadata where possible. Private file contents, complete prompts, access tokens and memory contents should not be included by default.

### Host compromise consideration

The shared host is a significant trust boundary because it may contain the database, task records, credentials and AI context. A fully compromised host could undermine application-level isolation.

The MVP should reduce exposure through private network binding, restricted database access, protected secrets, least privilege, backups and auditability. It should not claim that logical multi-user isolation protects users against a fully compromised backend host.

## 03.37.10 Testing and acceptance scenarios

Multi-user isolation must be verified with multiple test accounts and devices, not just by reviewing code.

| **Test** | **Expected result** |
| --- | --- |
| User A requests User B's task by ID | Access denied without revealing private task details |
| User A supplies User B's ID in a request body | Backend ignores or rejects the unauthorized identity claim |
| User A attempts to access User B's memory | No private memory is returned to the caller or model context |
| User A targets User B's device | Denied unless an explicit sharing grant exists |
| User A guesses an approval ID | Cannot approve another user's operation |
| User B submits a task while User A is running one | Both tasks retain their own ownership and context |
| A project member loses membership | Subsequent project access is denied |
| A device is revoked while a task is queued | No new operation is dispatched to that device |
| A device disconnects | Task is not silently rerouted |
| A background worker processes a task | Owner, target device and policy are derived from trusted persisted state |
| A database query returns task history | Only authorized records are included |
| A shared model receives concurrent requests | Context and outputs remain isolated between users |
| An administrator runs diagnostics | Diagnostics do not expose private content unnecessarily |
| A database backup is restored | Revoked credentials and authorization state are reconciled before normal operation resumes |

Tests should include positive cases as well: a user must still be able to access their own tasks, memory, devices and authorized project resources.

## 03.37.11 Implementation priorities

| **Priority** | **Scope** |
| --- | --- |
| P0 — Required for initial release | User isolation, private memory, private task history, owner-bound devices, cross-user authorization tests and concurrent-task isolation |
| P1 — Controlled collaboration | Project membership, shared project context, explicit device-sharing grants if needed, administrative role separation |
| P2 — Advanced governance | Fine-grained project roles, centralized administration, detailed access reporting and advanced retention controls |

P0 must be completed before NEXUS is used by all three developers with real files. P1 should only be added when there is a specific collaboration requirement and a fully defined permission model.

### Proposed ownership

- Developer 1: backend authorization, ownership constraints, database isolation, task access and revocation.

- Developer 2: device ownership, bridge credentials, local execution boundaries and device revocation.

- Developer 3: personal-memory isolation, context assembly, retrieval filters and concurrent model-request testing.

- All developers: cross-user security tests and review of any feature that exposes shared data.

## 03.37.12 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| Personal memory visibility | Private by default |
| Task history visibility | Private by default |
| Device ownership | Owner-only initially |
| Shared project memory | Deferred pending a defined membership model |
| Device sharing | Not enabled by default |
| Database isolation mechanism | Application checks required; row-level security approach open |
| Administrative roles | Minimal operational access; exact role model open |
| User and device revocation | Required behavior; detailed workflows to be finalized |
| Shared-data retention | Must be specified before shared memory is introduced |
| Multi-user concurrency | Three users are the initial validation target |

## 03.37.13 Definition of done

- User, device, resource and operation authorization are separate concepts.

- Personal tasks, memory and history are private by default.

- Task ownership comes from authenticated backend state.

- Device targeting and revocation are enforced.

- Project membership is required for any implemented shared project data.

- Concurrent tasks cannot mix private context or execution results.

- Database queries, background workers and API routes follow consistent authorization rules.

- Access changes and revocation have defined behavior for queued and in-flight work.

- Diagnostics and audit records minimize private content.

- Cross-user and cross-device tests pass on the integrated deployment.

- Operational access and the limits of host-level security are documented.

Section exit criterion: three developers can use one NEXUS backend concurrently while retaining private workspaces, with no unauthorized access to another user's memory, tasks, devices or execution results.
