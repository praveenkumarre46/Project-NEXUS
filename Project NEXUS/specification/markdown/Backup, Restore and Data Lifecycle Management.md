## 03.21.1 Purpose

NEXUS will store task history, user identities, device registrations, approvals, memory and audit records in PostgreSQL. Losing this data could prevent users from understanding previous actions, recovering interrupted tasks or accessing their saved context.

The designated team computer also introduces a single point of failure: if it becomes unavailable or its disk fails, the shared backend, database and potentially the AI runtime may all stop working.

This section defines how NEXUS should:

- Back up persistent data.

- Restore the service after data loss or host failure.

- Manage task history, memories, audit records and credentials according to different retention needs.

- Recover interrupted operations without repeating unsafe actions.

- Validate backups rather than assuming that a successful backup command guarantees recoverability.

Core principle: backup recovery must restore NEXUS's records without falsely claiming that external Windows operations were rolled back or never happened.

## 03.21.2 Data classification

Not every NEXUS record should have the same backup, retention or deletion policy.

| **Data category** | **Examples** | **Required treatment** |
| --- | --- | --- |
| Identity and access | Users, device registrations, authorization settings | Protect against loss and unauthorized access |
| Task execution | Tasks, steps, attempts, operation identifiers and outcomes | Preserve enough state for diagnosis and safe recovery |
| Approvals | Approval decisions, operation fingerprints and expiry | Preserve integrity and relevant audit history |
| User memory | Saved facts, project context, embeddings or search metadata | Support user-controlled correction and deletion |
| Security audit | Authorization decisions, device revocations, consequential actions | Protect from unauthorized modification; define retention |
| Operational logs | Errors, timing, dependency health | Limit sensitive data and apply retention |
| Configuration | Non-secret settings and policy configuration | Version, document and back up approved configurations |
| Secrets | Signing keys, database credentials, device credentials | Protect separately; never include in ordinary logs or diagnostic bundles |

Some categories may be stored in the same PostgreSQL database, but they still need distinct access and lifecycle rules.

For example, deleting a user's saved memory should not automatically delete an unrelated task record. Conversely, retaining a database backup does not mean deleted memory should remain available for ordinary retrieval.

## 03.21.3 Backup architecture

For the initial deployment, a simple PostgreSQL backup strategy is preferable to introducing a complex backup platform.

The second copy is important. A backup stored only on the same computer as PostgreSQL does not protect against disk failure, theft or complete host loss.

A separate copy may be stored on another authorized machine or an encrypted external drive. The choice should fit the team's zero-budget constraint and data-sensitivity requirements.

Cloud backup is not required for the MVP.

## 03.21.4 Backup policy

The team should define the backup schedule and recovery objectives before the shared deployment begins.

The following is a proposed starting policy, not a confirmed requirement:

| **Item** | **Proposed starting point** |
| --- | --- |
| Backup frequency | Daily full logical backup |
| Additional backups | Before schema changes, destructive maintenance or major releases |
| Local retention | Seven daily copies |
| Separate-copy retention | At least one recent validated copy, with additional history if storage permits |
| Encryption | Encrypt backups before storing them outside the protected database environment |
| Validation | Check backup completion, file integrity and expected size |
| Restore testing | Perform a test restore before release and periodically thereafter |
| Backup ownership | Assign a named team role responsible for monitoring failures |

Daily backups imply that recent changes may be lost if the host fails between backups. If that risk is unacceptable, the team must evaluate more frequent backups or PostgreSQL point-in-time recovery using archived write-ahead logs.

Point-in-time recovery is a more complex operational commitment and should not be added unless the team can configure, monitor and test it reliably.

### Backup contents

A logical database backup should cover the required application data and schema, including task records, memory, audit events and migration metadata.

Secrets, local Windows directory mappings and deployment configuration may exist outside PostgreSQL. They need separate protection and documented reconstruction procedures.

A database backup alone is not a complete NEXUS recovery plan.

## 03.21.05 Restore procedure

A backup is useful only if the team can restore it into a working system.

The restore procedure should be documented and tested independently of the normal startup process.

1. Declare the recovery scope. Determine whether the issue is a database failure, accidental deletion, host loss or corrupted deployment.

2. Stop conflicting writes. Prevent application workers from modifying the database while the recovery procedure is in progress.

3. Select a verified backup. Identify the backup timestamp and validation result.

4. Restore into an isolated database. Do not overwrite the only available backup or immediately replace the live database.

5. Validate the restored state. Check database integrity, migrations, representative records, task relationships and expected constraints.

6. Restore configuration and dependencies. Re-establish required settings, model connectivity, authentication configuration and device registrations according to the recovery plan.

7. Reconcile active tasks. Identify tasks and operations that were in progress at the backup point or after it.

8. Run smoke tests. Verify login, task history, memory retrieval, device status and a safe test operation.

9. Resume service deliberately. Enable normal execution only after the team confirms that the recovered state is safe.

10. Record the recovery. Document the incident, selected backup, data-loss window and unresolved operations.

A restore test should never run against the live database by accident. Use an isolated database name and verify the target before executing destructive restore commands.

## 03.21.06 Recovery objectives

NEXUS needs two operational targets.

- Recovery Point Objective (RPO): how much recent data the team can tolerate losing.

- Recovery Time Objective (RTO): how long the team can tolerate the service being unavailable.

These targets are not the same as task-execution timeouts.

For example, a daily backup schedule can leave up to roughly a day's worth of recent database changes at risk, depending on when the failure occurs. It does not guarantee that recovery will finish within a day.

The team should measure restore time using the actual database size and hardware before promising a recovery time.

| **Decision** | **Proposed initial position** |
| --- | --- |
| RPO | Agree on acceptable data loss; daily backups alone may be insufficient |
| RTO | Measure a clean restore and service restart before setting a target |
| Lost-host recovery | Rebuild on a replacement computer or designated recovery host |
| Recovery testing | Include a full database restore, not just a backup-file check |

For the MVP, the main objective is a tested and repeatable recovery procedure. Highly available infrastructure is not required, but the team must understand the consequences of losing the designated host.

## 03.21.07 Task recovery after restoring a backup

Restoring PostgreSQL may restore an old view of a task while the corresponding Windows operation has already occurred.

Consider this scenario:

1. NEXUS records the intention to create a file.

2. The Windows bridge creates the file.

3. The bridge reports success.

4. The database host fails before that success is durably recorded.

5. The database is restored from an earlier backup.

The restored database may show an operation as dispatched or unresolved even though the file exists.

Therefore:

- Do not automatically rerun all nonterminal tasks after restoration.

- Treat externally dispatched operations as potentially uncertain.

- Reconcile the operation with the target Windows bridge when possible.

- Use stable operation identifiers and any retained bridge-side operation records.

- Revalidate device identity, permissions and approvals before resuming.

- Keep tasks in recovery status when evidence is insufficient.

- Tell the user when the outcome cannot be established.

A PostgreSQL backup cannot reverse file creation, undo an application launch or prove that an external operation never happened.

Release-blocking rule: restored tasks must not blindly repeat uncertain external side effects.

## 03.21.08 Task history and audit retention

Task history and security audit records serve different purposes.

Task history helps users understand their requests, progress and results. Audit records help investigate security-sensitive decisions, such as device revocation, authorization denials and approvals.

A proposed initial policy:

- Retain enough task and step history to support ordinary debugging and user review.

- Bound stored tool output and error details to prevent unbounded database growth.

- Keep security audit events separate from ordinary diagnostic logs.

- Define retention and deletion rules for both categories before the team deployment.

- Avoid retaining full document contents or full AI prompts simply for debugging.

- Record the actor, event type, target object, timestamp, outcome and relevant correlation identifiers for consequential actions.

Exact retention periods remain an open decision. They should be based on the team's operational needs and privacy expectations rather than assumed to be indefinite.

Audit records must not be editable through ordinary user-facing task or memory operations. Any privileged maintenance process that modifies or removes audit records must be explicitly authorized and documented.

## 03.21.09 Memory deletion and lifecycle

NEXUS memory needs user-controlled correction and deletion. Its lifecycle must include the main record and any derived representations used during retrieval.

When a user deletes a memory, NEXUS should:

1. Authorize the user against the memory's owner and identifier.

2. Remove or deactivate the memory in the active memory store.

3. Remove it from active lexical and semantic retrieval.

4. Invalidate relevant caches or derived indexes.

5. Confirm the deletion result to the user.

6. Preserve only the separate records required by the documented audit and retention policy.

If semantic embeddings or cached context are stored separately, deleting the primary record without removing those derived representations is insufficient.

### Backups complicate deletion

A backup may contain a memory that has since been deleted from the active database. The system must not restore such a memory into active retrieval without applying the applicable deletion rules.

For the MVP, the team should document:

- How long deleted data may remain in protected backups.

- How restored databases reconcile with deletion records or retention requirements.

- Whether backup expiration is the mechanism for removing old copies.

- Which audit metadata may legitimately remain after memory deletion.

Do not promise immediate erasure from every historical backup unless the system actually supports and verifies that behavior.

## 03.21.10 Device credentials and configuration recovery

Recovering the database does not automatically restore every device's ability to connect safely.

The recovery plan must account for:

- User authentication configuration and signing keys.

- Device registrations and revocation status.

- Device credentials stored outside PostgreSQL.

- Approved directory and application mappings on each Windows computer.

- Backend and model runtime addresses.

- Environment-specific settings.

- Database connection credentials and encryption keys, where applicable.

Secrets should not be copied into ordinary database backups or diagnostic archives merely for convenience. If a signing key is lost, the team may need to invalidate existing sessions and provision a replacement. If a device credential is missing or potentially compromised, re-registration or credential rotation may be safer than attempting to reconstruct it.

After restoring a database, the team must verify that previously revoked devices remain revoked. Restoring an older database must not silently reinstate access that was intentionally removed after the backup was taken.

This requires an explicit recovery policy for security changes made after the selected backup.

## 03.21.11 Database migrations and backups

Database migrations can make recovery more difficult if the application version and database schema do not match.

Required rules:

- Create and verify a backup before a potentially destructive migration.

- Test migrations against both a clean database and a representative prior schema.

- Record the application version and migration revision associated with a release.

- Restore backups into an isolated environment before testing schema upgrades.

- Do not assume that rolling back application code automatically rolls back database changes.

- Define forward-fix or restore procedures for migrations that fail after partially changing the schema.

Alembic is a candidate for managing PostgreSQL schema migrations, but the migration and recovery workflow must be tested with whichever tool the team selects.

## 03.21.12 Backup and recovery testing

The following tests should be part of release preparation and periodic maintenance.

| **Test** | **Pass condition** |
| --- | --- |
| Backup creation | Backup completes and produces a valid artifact |
| Backup integrity | The artifact can be inspected and its expected contents are present |
| Database restoration | Backup restores into an isolated PostgreSQL database |
| Application compatibility | The selected application version can operate with the restored schema |
| Relationship integrity | Tasks, steps, approvals, users and devices retain valid relationships |
| Memory recovery | Active memories and retrieval indexes behave as specified |
| Deleted memory | Previously deleted memory is not reintroduced into active retrieval by recovery |
| Revoked device | Revocation remains effective after restoration or is reapplied before service resumes |
| Interrupted task | External operations are reconciled before unsafe retries |
| Host-loss drill | Team can rebuild the essential service on a replacement environment |
| Migration failure | Documented recovery or forward-fix procedure works |
| Backup access | Unauthorized users cannot read or modify protected backup files |

Use synthetic data for these tests. Never use a real user's private document collection merely to validate a restore process.

## 03.21.13 Operational ownership

Backup responsibility must not be left to an undocumented manual habit.

Proposed ownership:

- Backend/execution developer: validates database consistency, migrations and task recovery.

- Windows integration developer: validates bridge reconnection, local operation reconciliation and device re-registration.

- AI/context developer: validates memory restoration, deletion propagation and retrieval-index consistency.

- All three developers: participate in a host-loss recovery drill before the project is considered operationally ready.

One person may run a particular backup, but at least another team member should be able to follow the documented restore procedure. This prevents recovery from depending on one developer's undocumented knowledge.

Backup failures should be visible through diagnostics. A backup that has not run successfully within the expected interval should be treated as an operational problem, not silently ignored.

## 03.21.14 MVP implementation priorities

#### P0

Essential recovery

Automated or repeatable PostgreSQL backups, protected backup storage, documented restoration, migration-aware recovery and safe handling of interrupted tasks.

#### P1

Data lifecycle

Defined task-history and audit retention, memory deletion propagation, device revocation handling and tested recovery on a replacement environment.

#### P2

Advanced recovery

Point-in-time recovery, more frequent backups, automated recovery monitoring and reduced-downtime deployment. Adopt only if measured requirements justify the added complexity.

The MVP should prioritize a reliable, tested restore procedure over a sophisticated backup architecture that nobody has verified.

## 03.21.15 Open decisions

| **Decision** | **What must be established** |
| --- | --- |
| Backup frequency | Acceptable data-loss window |
| Backup location | Separate machine or encrypted external storage |
| Backup encryption | Method and key-recovery procedure |
| Retention | Daily backup, audit and task-history retention periods |
| RPO and RTO | Measured and agreed recovery objectives |
| Point-in-time recovery | Whether the added operational complexity is justified |
| Memory deletion | Treatment of embeddings, caches, audit metadata and backups |
| Revocation recovery | How security changes after a backup are preserved |
| Host replacement | Which computer can take over if the designated host fails |
| Recovery ownership | Who performs, verifies and signs off on restoration |

## 03.21.16 Acceptance checklist

### Recovery readiness

0 / 10

PostgreSQL backups can be created and their integrity verified.

At least one protected backup copy exists outside the designated host.

A backup has been restored successfully into an isolated environment.

The restore procedure includes migrations, configuration and dependency checks.

Interrupted external operations are reconciled before unsafe retries.

Deleted memories are excluded from active retrieval after restoration.

Device revocations are not silently reversed by restoring an older backup.

Task history and audit retention policies are documented.

At least two developers can follow the recovery documentation.

Recovery time and potential data loss have been measured or explicitly remain open.

Copy checklist

## Section 03.21 exit criterion: the team can restore NEXUS's essential persistent data, recover the service, preserve security decisions and handle uncertain external operations without blindly repeating actions.
