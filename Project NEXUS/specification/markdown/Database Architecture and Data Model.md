## 03.10.1 — Database design principles

NEXUS should start with a relational PostgreSQL schema, explicit foreign keys, transactions and carefully chosen uniqueness constraints.

The design follows these principles:

1. Ownership is explicit. Every user-owned task and memory record has an identifiable owner.

2. Device targeting is explicit. A task cannot accidentally migrate to another teammate's computer.

3. History is durable. Task and step outcomes survive backend restarts.

4. Authorization is not delegated to the model. The database stores permissions and approvals, but application code enforces them.

5. Concurrent operations are expected. Constraints and transactions protect against races; Python checks alone are insufficient.

6. Sensitive data is minimized. NEXUS should not persist entire documents or raw conversations when a smaller record is sufficient.

7. Schema changes are versioned. Database migrations are reviewed and tested instead of being applied through ad hoc production changes.

## 03.10.2 — Proposed logical data model

## 03.10.3 — Core tables

### A. users

Represents a NEXUS account.

| **Column** | **Purpose** |
| --- | --- |
| id | Primary key |
| username | Unique account name |
| password_hash | Password hash if local password authentication is selected |
| status | Active, disabled or another explicitly defined state |
| created_at | Creation timestamp |
| updated_at | Last update timestamp |

Design rules:

- Store password hashes, never plaintext passwords.

- Do not assume a password column is required if the team chooses another authentication method.

- Disabling a user must prevent new requests and new operations.

- The policy for tasks already running when an account is disabled must be defined explicitly.

### B. devices

Represents an individual Windows computer registered with NEXUS.

| **Column** | **Purpose** |
| --- | --- |
| id | Stable device identifier |
| display_name | User-friendly name |
| owner_user_id | Account that owns the registration |
| status | Pending, active, revoked or another defined state |
| platform | Windows platform and supported version information |
| last_seen_at | Last successful bridge contact |
| created_at | Registration timestamp |
| revoked_at | Revocation timestamp, if applicable |

Design rules:

- A device ID is an identifier, not an authentication secret.

- The bridge must authenticate independently of merely knowing its device ID.

- Revocation must be enforced at the backend and the execution boundary.

- Device ownership and task ownership must be checked together before dispatch.

- A device may appear online based on its latest heartbeat while still failing an operation; heartbeat status is not proof that every tool is available.

Open design question: can one device be explicitly shared with multiple users, or must every device have exactly one owning user? The initial proposal is one owner per registration. Shared-device access should be added only if a real use case requires it.

### C. tasks

Represents one user-submitted request and its overall execution lifecycle.

| **Column** | **Purpose** |
| --- | --- |
| id | Primary key |
| owner_user_id | User who submitted the task |
| target_device_id | Intended Windows computer |
| client_request_id | Client-generated idempotency key |
| request_text | Original request, subject to privacy policy |
| status | Current task lifecycle state |
| outcome | Final result classification, if available |
| created_at | Submission timestamp |
| started_at | First execution timestamp |
| completed_at | Terminal completion timestamp |
| updated_at | Last state change timestamp |
| error_code | Stable error category, if applicable |

Recommended constraints:

- owner_user_id must reference a valid user.

- target_device_id must reference a registered device.

- A unique constraint on (owner_user_id, client_request_id) prevents duplicate task creation for the same user.

- Timestamps must be consistent with the task lifecycle.

- Status changes must be validated by application code; an arbitrary update must not bypass the state machine.

The request text may contain private information. Retention, access and deletion rules must be defined rather than assuming that all submitted text should be kept indefinitely.

### D. tasksteps

Stores the individual operations that make up a task.

| **Column** | **Purpose** |
| --- | --- |
| id | Primary key |
| task_id | Parent task |
| step_number | Ordering within the task |
| tool_name | Registered tool being invoked |
| arguments | Validated operation parameters |
| status | Pending, ready, running, succeeded, failed, etc. |
| operation_id | Stable identifier for retries and reconciliation |
| attempt_count | Number of recorded attempts |
| started_at | Execution start |
| completed_at | Execution completion |
| error_code | Machine-readable failure category |
| result_summary | Minimal useful outcome |

Recommended constraints:

- Unique (task_id, step_number).

- Unique operation_id.

- Every step belongs to exactly one task.

- Tool arguments must be validated against the registered tool's schema before execution.

- Result data should be bounded in size and should not automatically contain full document contents.

Important design distinction: a step and an attempt are not necessarily the same thing. If one logical operation is attempted several times, overwriting the previous attempt's details destroys useful evidence. For that reason, I recommend adding a separate task_step_attempts table.

### E. taskstepattempts

Records each dispatch or execution attempt for a logical step.

| **Column** | **Purpose** |
| --- | --- |
| id | Attempt identifier |
| task_step_id | Parent logical step |
| attempt_number | Attempt sequence |
| worker_id | Worker that initiated the attempt, if applicable |
| bridge_request_id | Identifier used for bridge-side deduplication |
| status | Prepared, dispatched, succeeded, failed, uncertain |
| started_at | Attempt start |
| finished_at | Attempt end, if known |
| error_code | Failure category |
| result_summary | Bounded structured outcome |

Recommended uniqueness constraint: (task_step_id, attempt_number).

This table helps answer questions such as:

- Did NEXUS attempt this operation?

- Did it receive a response?

- Was the response persisted?

- Is retrying safe?

- Is there evidence that the previous attempt may have completed?

It does not magically guarantee that the bridge's filesystem operation and PostgreSQL commit happen atomically. That limitation remains part of the execution design.

### F. approvals

Stores approval decisions for consequential operations.

| **Column** | **Purpose** |
| --- | --- |
| id | Approval identifier |
| task_step_id | Exact operation being reviewed |
| requested_by_user_id | User associated with the request |
| decided_by_user_id | User who approved or rejected it |
| decision | Pending, approved, rejected or expired |
| operation_fingerprint | Stable representation of the approved operation |
| created_at | Approval request time |
| expires_at | Approval expiry |
| decided_at | Decision time |

The fingerprint must cover the meaningful operation details, including the target device and relevant arguments. The exact canonicalization and hashing mechanism will be designed later.

A changed operation must not reuse an approval intended for the earlier version. The backend must revalidate the approval immediately before dispatch.

### G. memories

Stores user-controlled information that can improve future requests.

| **Column** | **Purpose** |
| --- | --- |
| id | Memory identifier |
| owner_user_id | Memory owner |
| content | Stored memory text or structured content |
| category | Preference, project context or another defined category |
| source | How the information was obtained |
| created_at | Creation timestamp |
| updated_at | Last update |
| deleted_at | Optional logical deletion marker |

Initial design recommendation:

- Keep memory private to the owning user by default.

- Separate durable user preferences from temporary task context.

- Allow the user to inspect, update and delete memories.

- Retrieve only relevant memories for a request.

- Do not automatically convert every conversation or file into permanent memory.

- Treat model-generated inferences as uncertain unless explicitly confirmed.

- If semantic search is required, evaluate PostgreSQL full-text search first; add vector search only after choosing an embedding model and measuring its resource cost.

Logical deletion alone is not enough to meet a permanent-deletion promise. The backup, retention and any derived-index policies must be addressed in the privacy design.

### H. auditevents

Records security-relevant decisions and important actions.

| **Column** | **Purpose** |
| --- | --- |
| id | Event identifier |
| actor_user_id | User responsible, if applicable |
| device_id | Related device, if applicable |
| task_id | Related task, if applicable |
| event_type | Login, approval, revocation, dispatch, etc. |
| outcome | Allowed, denied, succeeded or failed |
| correlation_id | Identifier linking related events |
| metadata | Bounded, non-secret structured details |
| created_at | Event timestamp |

Audit records should not be used as a dumping ground for complete prompts, passwords, authentication tokens or document contents.

Access to audit events must be restricted. Retention and deletion rules must be defined, especially when a user requests deletion of their task history or memory.

## 03.10.4 — Supporting tables and authorization data

The core tables are not sufficient by themselves to enforce every security and concurrency requirement.

### Additional tables to consider

| **Table** | **Why it may be needed** | **Initial recommendation** |
| --- | --- | --- |
| device_credentials | Store device authentication material or credential references | Include if bridge authentication requires persisted credentials |
| device_permissions | Represent which users can operate which devices and which capabilities are granted | Include if device sharing is supported; otherwise start with owner-based access |
| worker_claims | Record worker ownership and lease metadata | May be represented directly on tasks or steps initially; choose one consistent model |
| task_events | Store a durable task progress timeline | Useful if task history needs reliable progress reconstruction |
| user_sessions | Support revocable login sessions | Include if the selected authentication design uses sessions or refresh tokens |

Avoid creating a table simply because it sounds architecturally sophisticated. Each table should represent a real lifecycle, integrity rule or query requirement.

### Ownership enforcement

Application code should check that a task belongs to the authenticated user before returning its data or permitting an action. PostgreSQL foreign keys alone do not enforce this ownership relationship.

For example, a valid task_id is not sufficient authorization to retrieve a result. The query must constrain the task by both its identifier and the authenticated user's permitted scope.

For device execution, the authorization check must additionally establish that:

- The target device is registered and active.

- The requester is permitted to use that device.

- The task is still eligible to execute.

- The requested tool and its arguments are allowed.

- Any required approval is valid and applies to the exact operation.

The bridge should enforce its own local restrictions as well. Backend authorization and bridge validation serve different trust boundaries.

## 03.10.5 — Relationships and integrity constraints

The intended relationships are:

- One user can submit many tasks.

- One user can register multiple devices, subject to the eventual device-sharing policy.

- One task targets one device.

- One task contains an ordered collection of steps.

- One logical step may have multiple execution attempts.

- One step may require an approval record, depending on its risk and permission policy.

- One user can own multiple memories.

- Audit events can reference users, devices and tasks where applicable.

The schema should use foreign keys for these relationships rather than relying on application conventions alone.

### Deletion policy

Deletion behavior must be chosen deliberately:

- Deleting a user should not accidentally cascade into deleting security evidence that is still subject to retention requirements.

- Removing a device should revoke access and preserve relevant task history.

- Deleting a task must not automatically erase unrelated memories.

- Deleting a memory must make it unavailable to future context retrieval.

- Audit and backup retention may differ from normal application-data retention.

For the MVP, revocation or deactivation is generally safer than cascading deletion for users and devices. A dedicated data-retention policy will determine when physical deletion is appropriate.

## 03.10.6 — Transactions and concurrency

This is where the database model connects directly to NEXUS's execution engine.

### Example A: duplicate task submissions

Two API requests arrive concurrently with the same (owner_user_id, client_request_id).

A Python-level sequence such as “check whether it exists, then insert” is unsafe: both requests can observe that the row does not exist.

The unique database constraint must arbitrate the race. The losing request should retrieve the existing task if its payload matches, or return a conflict if the payload differs.

### Example B: two workers claim the same task

A worker must not simply read status = 'queued' and then update it later without coordination.

The claim should be an atomic database operation that grants ownership to one worker. A transaction with row-level locking or a carefully designed atomic update is a possible implementation. The exact query and isolation behavior should be tested against the selected PostgreSQL version.

### Example C: task and step updates

When a worker records a step outcome, it may need to update both the step and the parent task.

Those database changes should be committed in a single transaction when they form one logical database-state change. The transaction should remain short and must not include waiting for the bridge to finish a Windows operation.

### Example D: approval races

Suppose a user approves a step just as another process cancels the task.

NEXUS needs defined ordering and transition rules so that approval cannot accidentally revive a cancelled task. The approval endpoint and worker must re-read and validate the relevant state under appropriate transactional coordination.

Database transactions protect NEXUS's records. They do not roll back external Windows operations. This distinction must remain explicit throughout implementation.

## 03.10.7 — Indexing and query performance

Indexes should support actual application queries. Adding indexes to every column increases write cost and storage use, so the initial set should be small and evidence-driven.

| **Proposed index** | **Query it supports** |
| --- | --- |
| UNIQUE users(username) | Resolve a username |
| UNIQUE tasks(owner_user_id, client_request_id) | Prevent duplicate task submissions |
| INDEX tasks(owner_user_id, created_at) | List a user's recent tasks |
| INDEX tasks(target_device_id, status) | Find tasks eligible for a device or worker |
| UNIQUE task_steps(task_id, step_number) | Retrieve ordered task steps |
| UNIQUE task_steps(operation_id) | Resolve an operation identity |
| UNIQUE task_step_attempts(task_step_id, attempt_number) | Retrieve a step's attempts |
| INDEX approvals(task_step_id, decision) | Resolve approval status for a step |
| INDEX memories(owner_user_id, category) | Retrieve a user's memories by category |
| INDEX audit_events(created_at) | Retrieve recent audit events |

These are proposed indexes. Exact definitions should follow the final column types, access patterns and query plans. For example, a partial index for queued tasks may be beneficial if most tasks are not queued, but it should be justified by the actual worker query and measured workload.

### Performance measurements

Capture a baseline for:

- Task submission latency.

- Task status lookup latency.

- Recent task history query latency.

- Worker claim latency under concurrent submissions.

- Memory retrieval latency.

- Database connection-pool saturation.

- Lock waits and transaction duration.

Do not claim database performance is acceptable based only on a few successful manual requests. The team should establish realistic test data and concurrent workloads before setting numerical service targets.

## 03.10.8 — Schema migrations and development workflow

Use a versioned migration tool such as Alembic with SQLAlchemy, subject to the team's final dependency decision.

The database workflow should be:

1. Define the domain change and integrity requirements.

2. Write a migration with a reviewable upgrade path.

3. Test the migration against a fresh database.

4. Test it against a database containing representative existing data.

5. Verify constraints, indexes and application compatibility.

6. Document how to recover if the migration fails.

7. Commit migration files alongside the corresponding application change.

Do not let each developer independently modify the shared database schema through manual SQL and then try to reconstruct those changes later.

A local Docker Compose environment can provide a repeatable PostgreSQL instance. The exact PostgreSQL version, database name, credentials management, connection-pool size and migration configuration remain deployment decisions.

### Test database requirements

The test suite should include:

- Fresh schema creation.

- Migration upgrade tests.

- Foreign-key and uniqueness violations.

- Concurrent duplicate submissions.

- Concurrent worker claims.

- Approval versus cancellation races.

- Task recovery after backend restart.

- Data-isolation tests between users.

- Memory deletion and retrieval tests.

Unit tests may mock the persistence interface. However, tests for transactions, locking, uniqueness and isolation must run against PostgreSQL rather than relying entirely on mocks.

## 03.10.9 — Data privacy and retention

NEXUS can access private documents and maintain long-term context. The data model therefore needs a privacy policy before the team implements unrestricted logging or memory capture.

Proposed defaults:

- Store only the information needed to execute tasks, recover safely and provide useful history.

- Do not store complete document contents in task records by default.

- Avoid persisting model prompts and responses unless there is a defined product need.

- Exclude secrets and authentication credentials from audit metadata.

- Keep user memories separate from task execution history.

- Make memory inspection, editing and deletion available to the owner.

- Define retention periods for task history, execution attempts and audit records.

- Document whether database backups retain deleted data and for how long.

An additional unresolved decision is whether task history is retained indefinitely, for a fixed period, or according to a user-configurable setting. This should be decided before the application advertises specific deletion guarantees.

## 03.10.10 — Database acceptance criteria

Use this checklist when reviewing the database implementation.

### Database review

0/13

All core tables have explicit primary keys, appropriate foreign keys and documented ownership.

Duplicate task submission is prevented by a database-enforced uniqueness constraint.

Task and step states cannot be changed through unvalidated application paths.

Worker coordination prevents two valid workers from simultaneously owning the same step.

Execution attempts preserve enough evidence for safe recovery.

Approval records bind to the exact operation being authorized.

One user cannot retrieve another user's tasks, memories or unauthorized device records.

Device revocation blocks new execution while preserving required history.

Memory deletion prevents future retrieval and follows the documented retention policy.

Migrations work on both a fresh database and a representative existing database.

Concurrency and transaction tests run against PostgreSQL.

Indexes are justified by actual queries and measured access patterns.

Logs and audit metadata do not expose credentials or unnecessary private content.

## 03.10.11 — Decisions still open

These questions should remain visible in the design document rather than being silently settled during coding.

| **Decision** | **Why it matters** |
| --- | --- |
| Authentication method | Determines user/session tables and credential handling |
| Device-sharing policy | Determines device authorization relationships |
| Memory search method | Affects schema, model dependencies and performance |
| Task-history retention | Affects privacy, storage and deletion behavior |
| Audit retention | Affects security investigations and deletion guarantees |
| Worker claim design | Determines locking, leases and stale-worker recovery |
| PostgreSQL version | Affects supported features and deployment consistency |
| Task and result size limits | Prevents unbounded database growth |
| Backup and restore strategy | Determines disaster recovery and deletion semantics |
