## 04.25.01 Purpose

NEXUS depends on a designated team computer for shared backend services and initially for local AI inference. Losing that computer, its database or its storage must not leave the team guessing about accepted tasks, permissions or operations performed on Windows devices.

This section defines:

- What data and configuration must be backed up.

- Backup frequency, retention and storage separation.

- Backup integrity checks and restore testing.

- Recovery point objective (RPO) and recovery time objective (RTO).

- Recovery after host loss or database corruption.

- How restored task records are reconciled with actual Windows-side effects.

- How revocations and deleted data are handled after restoration.

Core principle: a database backup preserves recorded state, not necessarily the real-world state of every Windows operation.

## 04.25.02 Recovery objectives

Two objectives must be defined before the team can claim it has a reliable disaster-recovery plan.

Recovery Point Objective (RPO)

The maximum acceptable amount of data loss, measured in time.

Example: an RPO of 24 hours means the team accepts that up to 24 hours of database changes could be lost after a disaster.

Recovery Time Objective (RTO)

The target time to restore a defined level of service after a disaster.

Example: an RTO of 4 hours means the team aims to restore that service within 4 hours, subject to the agreed recovery scope and tested procedure.

These are examples, not approved NEXUS targets. RPO and RTO must reflect how often the team uses NEXUS, how costly task-history loss would be, and what the zero-budget infrastructure can realistically support.

### Recovery scope must be explicit

The team should distinguish:

1. Core service recovery: authentication, API, database and device registry.

2. Task recovery: accepted tasks, step history, approvals and operation journals.

3. AI recovery: the selected runtime and model configuration.

4. Device recovery: bridge installation, credentials, directory mappings and local operation records.

5. Full recovery: core services and required capabilities restored, with outstanding operations reconciled.

A service can be available before every AI feature is restored. Any degraded mode must be explicitly supported and must not weaken security or task-state correctness.

## 04.25.03 Backup inventory and recovery requirements

Not all NEXUS data should be backed up in the same way. The backup plan must account for durability, sensitivity, rebuildability and the consequences of losing each category.

| **Data category** | **Backup requirement** | **Recovery concern** |
| --- | --- | --- |
| PostgreSQL application data | Required | Users, devices, tasks, steps, approvals, memories and audit records |
| Database schema and migrations | Required | Rebuild the schema compatible with the restored data |
| Backend configuration | Required, excluding unnecessary secrets | Service addresses, settings and deployment configuration |
| Device registry and revocation state | Required | Avoid trusting previously revoked devices after restore |
| Bridge configuration | Protected device-specific backup or reproducible reconfiguration | Local directory mappings and tool configuration |
| Device credentials | Protected recovery or re-enrollment process | Never recover credentials through an insecure plaintext export |
| Model configuration | Record versions and settings; model files may be reacquired if available | Compatibility, licensing, reproducibility and download time |
| Model files | Optional protected backup or documented reacquisition | Large artifacts can consume significant storage |
| Task results and audit history | Required according to retention policy | Preserve evidence and investigate past operations |
| Bridge operation journal | Protect locally and define reconciliation procedure | Database backups alone cannot establish Windows-side outcomes |
| Application binaries | Prefer reproducible builds and versioned artifacts | Rebuild or retrieve the exact tested release |
| Logs | Retain according to operational and security needs | Diagnostics without exposing secrets or private content |

### Backup design rules

- Backups must be stored separately from the primary data they protect.

- A backup stored only on the designated host does not protect against loss of that host.

- Backup access must be restricted because task history, memory and device metadata may be sensitive.

- Secrets should be excluded where they can be safely re-provisioned; any secret that must be backed up requires protected handling.

- A backup must be identifiable by timestamp, source version and integrity metadata.

- Retention and deletion policies must cover backup copies as well as primary storage.

- Backups must not silently reactivate revoked permissions or deleted memory when restored.

## 04.25.04 Backup frequency and retention

The following is a starting proposal for a small team, not a final commitment.

Scheduled backup

Initial proposal

### Daily

Take a consistent database backup on a documented schedule, with retention based on storage capacity and data importance.

Pre-change backup

Before consequential changes

### Required

Take and verify a recovery point before risky migrations, major configuration changes or releases that affect persistent data.

Separate protected copy

Host-loss protection

### Required

Maintain a protected copy outside the primary host, using an available storage option compatible with the zero-budget constraint.

Restore validation

Operational test

### Scheduled

Restore into an isolated environment and verify that the database and application work together.

### Retention decisions

The team must specify:

- Number of daily and longer-term copies retained.

- Maximum age of a usable recovery point.

- Storage capacity and encryption requirements.

- Who can access and delete backup copies.

- How deleted memory and revoked credentials are treated in older backups.

- How failed or incomplete backups are detected.

- How the team is notified when backup storage is unavailable.

A successful backup command is not proof that the backup can be restored. The restore test is part of the backup process.

## 04.25.05 Backup implementation strategy

PostgreSQL should remain the authoritative source for NEXUS's persisted task and authorization state.

### Initial implementation

A simple implementation can use PostgreSQL's supported backup tooling, a scheduled script and a protected destination. The exact tooling depends on the chosen PostgreSQL deployment.

The backup workflow should:

1. Verify database availability.

2. Create a consistent backup using the selected method.

3. Record backup time, schema version, application release and completion status.

4. Verify that the output is non-empty and passes an integrity check.

5. Transfer or copy it to the protected backup location.

6. Verify the protected copy.

7. Apply the configured retention rules.

8. Record the outcome without logging secrets.

9. Alert the team if a required backup fails or becomes overdue.

If the team later requires point-in-time recovery, PostgreSQL write-ahead log (WAL) archiving can be evaluated. It adds operational complexity and should not be introduced without a tested recovery procedure.

### Backup consistency

A database backup must represent a consistent database state. Separately copied configuration and device journals may reflect different moments in time, so recovery must account for those differences.

Do not assume a database backup, a bridge journal copy and a Windows filesystem snapshot are one atomic snapshot. NEXUS does not have a distributed transaction spanning those systems.

## 04.25.06 Host-loss recovery procedure

This procedure covers loss of the designated team computer through hardware failure, operating-system corruption, disk failure or an unrecoverable deployment problem.

### Recovery sequence

1. Declare host unavailable

Stop dispatch assumptions and identify the last known healthy state

2. Secure the recovery environment

Select a replacement host and protect credentials and backup access

3. Restore required configuration and database

Install compatible versions and validate restored data

4. Reconcile identities and outstanding tasks

Check revocations, task state and external Windows effects

5. Restore required dependencies

Validate backend, database, model runtime and network configuration

6. Verify and resume

Run security, connectivity, recovery and end-to-end smoke tests

### Detailed requirements

Before restoring:

- Identify the newest verified usable backup.

- Establish whether the original host may still be running or accessible.

- Prevent two backend instances from independently dispatching work against the same restored state.

- Determine whether credentials or signing keys may have been exposed or lost.

- Identify which operations may have occurred after the selected backup.

During restoration:

- Install the compatible application and database versions.

- Restore into a controlled environment.

- Verify migration state, constraints, relationships and ownership boundaries.

- Restore required configuration without blindly reactivating stale credentials.

- Keep task dispatch disabled until recovery validation passes.

After restoration:

- Reconcile device identities and revocations.

- Authenticate each bridge and verify its capabilities.

- Reconcile tasks whose external effects might have occurred after the backup.

- Verify current policy and approval state.

- Run smoke tests using isolated test resources.

- Record the recovery point and any known data loss.

- Resume service only after an authorized recovery owner approves it.

### Single-host deployment limitation

The designated host remains a single point of failure. Backups help restore service but do not provide uninterrupted availability.

If continuous availability later becomes a requirement, the team can evaluate a separate always-on host or a more resilient deployment. That is a future architecture decision, not an assumed capability of the initial MVP.

## 04.25.07 Reconciling database state with Windows-side effects

This is one of the most important NEXUS-specific recovery requirements.

Consider this sequence:

1. The backend records that a file-creation operation is about to be dispatched.

2. The Windows bridge creates the file.

3. The backend fails before recording the successful result.

4. The database is restored from an earlier backup.

5. The restored task record indicates that the operation was dispatched but its final outcome is unknown.

The file may already exist even though the restored database does not contain the final result.

### Required reconciliation procedure

- Identify the original task, step, operation and target device.

- Authenticate the correct bridge.

- Query its operation journal if available.

- Inspect external evidence within the permitted resource scope.

- Determine whether the operation succeeded, failed or remains unresolved.

- Record the evidence and recovered outcome.

- Retry only when the tool's recovery contract permits it.

- Preserve uncertainty when the available evidence is insufficient.

### Rules that must never be violated

- Do not blindly replay all tasks that appear incomplete in the restored database.

- Do not assume that a file with the expected name was created by NEXUS.

- Do not treat a missing operation journal as proof that the operation never happened.

- Do not use an old backup to bypass current policy, device revocation or approval requirements.

- Do not mark a task successful without the required verification evidence.

A database restore must trigger reconciliation for potentially affected operations, not just a normal worker restart.

## 04.25.08 Recovery of credentials, policies and device registration

Backups can preserve stale authorization data. Recovery must therefore distinguish restoring application state from restoring trust.

### User accounts and sessions

- Restore user records only through the approved recovery procedure.

- Revoke or invalidate sessions when their signing keys or token trust cannot be established.

- Re-provision credentials if their integrity is uncertain.

- Do not store plaintext passwords or tokens in backup manifests.

### Device identities

- Restore the device registry and relevant audit records.

- Verify the current revocation status before accepting a bridge.

- Re-register devices whose credentials were lost or whose trust cannot be established.

- Do not assume that an old database snapshot represents the latest device status.

### Permissions and policy

- Verify the current approved policy version.

- Preserve known revocations and prohibitions.

- Revalidate queued tasks before dispatch.

- Require fresh approval when the operation or applicable policy requires it.

- Do not reactivate previously disabled directories or applications without an explicit, authorized configuration decision.

### Recovery principle

If the system cannot establish that a credential, device or permission is still trusted, it must not restore that trust merely for convenience.

## 04.25.09 Memory deletion, retention and backup restoration

Memory deletion requires particular care because older backups may still contain records that are no longer present in the live database.

NEXUS should distinguish:

- Deletion from active memory retrieval.

- Removal from lexical and semantic indexes.

- Invalidation of caches.

- Retention of task history and audit evidence.

- Expiration of backup copies under the retention policy.

These are separate operations with separate retention requirements.

### Required behavior after restoration

1. Restore the backup into the controlled environment.

2. Apply the documented retention and deletion reconciliation procedure.

3. Reapply authoritative deletion and revocation information when available.

4. Invalidate stale retrieval indexes and caches as needed.

5. Ensure deleted memories are not made active simply because they exist in an older snapshot.

6. Verify user-scoped retrieval before restoring normal access.

7. Document any limitation caused by the loss of deletion or revocation records.

If the system cannot determine whether a memory was deleted after the selected backup, it must not claim that full deletion has been preserved. This is a recovery limitation that the team must address through appropriate retention and deletion-record design.

## 04.25.10 Disaster-recovery exercises

A backup policy is incomplete until the team has demonstrated that it can restore service.

The three developers should rehearse recovery using isolated data and test devices, not by deliberately damaging the live team deployment.

### Required exercises

| **Exercise** | **Acceptance criterion** |
| --- | --- |
| Restore a database backup | Database opens and required records pass integrity checks |
| Restore on a clean environment | Backend starts using documented installation instructions |
| Lose the designated host | Team can identify a usable recovery point and rebuild required services |
| Restore after a migration failure | Compatible application and schema can be recovered safely |
| Restore with a revoked device | The revoked device remains blocked |
| Restore with deleted memory records | Deleted content is not silently reactivated in active retrieval |
| Restore tasks with uncertain writes | External operations are reconciled before unsafe retries |
| Restore bridge configuration | Device identity and local mappings are verified before use |
| Recover without the AI runtime | Core service behavior and AI-dependent limitations are reported accurately |
| Validate the protected backup copy | The copy can actually be restored, not merely listed |

### Exercise evidence

For each exercise, record:

- Start and end time.

- Backup identifier and recovery point.

- Application, schema and model versions.

- Data that was restored and any known data loss.

- Tasks or operations that required reconciliation.

- Smoke-test results.

- Deviations from the documented procedure.

- Corrective actions and owners.

Recovery time and data loss should be measured during these exercises before the team commits to RTO and RPO targets.

## 04.25.11 Roles and operational ownership

| **Work area** | **Primary owner** | **Shared responsibility** |
| --- | --- | --- |
| Database backup and schema recovery | Developer 1 | Recovery validation |
| Task, step and operation reconciliation | Developer 1 | Developer 2 supplies bridge-side evidence |
| Bridge-local state and device re-enrollment | Developer 2 | Credential and policy review |
| Memory, retrieval indexes and model configuration | Developer 3 | Privacy and recovery validation |
| Host-loss exercise | Assigned incident owner | All three participate |
| RPO/RTO selection and sign-off | All three | Based on measured recovery results |

No single developer should be the only person who knows how to restore the system.

## 04.25.12 Implementation priorities

P0 — Required foundation

Recoverable team deployment

- Consistent PostgreSQL backups.

- Protected backup storage outside the primary host.

- Version and integrity metadata.

- Documented restore procedure.

- Task and external-operation reconciliation.

- Safe handling of credentials, revocations and deleted memory.

- A successful isolated restore test.

P1 — Stronger recovery

Measured resilience

- Scheduled backup verification.

- Automated failure notification.

- Regular disaster-recovery exercises.

- Measured RPO and RTO.

- Improved reconciliation records and restore automation.

P2 — Future resilience

Reduced downtime and data loss

- Point-in-time recovery with WAL archiving, if justified.

- More frequent protected recovery points.

- A separate always-on recovery host.

- More automated failover and recovery orchestration.

## 04.25.13 Open decisions

- What RPO and RTO can the team realistically support?

- How many daily and longer-term backup copies should be retained?

- Where will the protected backup copy be stored?

- Who can access, verify and restore backups?

- Which secrets should be re-provisioned rather than backed up?

- How will the team preserve revocation and deletion information across restore points?

- Is daily backup sufficient, or is point-in-time recovery required?

- How often will restore drills be performed?

- What is the approved procedure if the designated host is permanently lost?

- How will the team handle an operation whose Windows-side outcome cannot be established after restoration?

## 04.25.14 Definition of done

- Backup scope and retention policy are documented.

- A verified backup exists outside the primary host.

- The team can restore PostgreSQL into an isolated environment.

- Required application versions and configuration can be reconstructed.

- Device revocations and security restrictions survive recovery.

- Deleted memory is not silently reactivated.

- Uncertain Windows operations are reconciled before unsafe retries.

- A host-loss exercise has been completed and documented.

- Recovery time and potential data loss have been measured.

- Every developer understands the recovery procedure.

Section exit criterion: NEXUS can recover from database or host loss with a known recovery point, documented data-loss limitations and a safe process for reconciling external operations.
