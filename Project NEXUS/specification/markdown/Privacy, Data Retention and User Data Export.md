## 04.26.01 Purpose

NEXUS will handle personal memory, task history, document content, device information, authentication records and evidence of computer operations. These data types have different purposes, sensitivity levels and retention needs.

This section defines how NEXUS collects, stores, exposes, exports, retains and deletes user data without weakening task recovery, auditability or security.

The objectives are to:

- Collect only data needed for a defined feature.

- Keep each user's private data isolated.

- Give users visibility and control over their memory and task history.

- Prevent private document contents and secrets from leaking into logs.

- Define deletion and retention behavior across databases, indexes, caches and backups.

- Allow users to export their own eligible data.

- Preserve necessary operational evidence without treating it as unrestricted access to personal content.

Core principle: user data is private by default, and each stored copy must have a clear purpose, access rule and lifecycle.

## 04.26.02 Data classification

NEXUS should classify data according to sensitivity and operational purpose.

| **Category** | **Examples** | **Handling requirements** |
| --- | --- | --- |
| Authentication secrets | Password hashes, access tokens, device credentials | Strong access controls; never log raw secrets |
| Personal memory | User preferences, confirmed project facts, ongoing work context | Private to the owner by default; inspectable and deletable |
| Task records | Requests, states, steps, errors and outcomes | Owner-scoped access; bounded retention |
| Document-derived data | Extracted text, chunks, summaries and embeddings | Treat as potentially sensitive document content |
| Windows resource metadata | Logical directory IDs, relative paths, file metadata | Enforce device and user scope; avoid unnecessary path disclosure |
| Security audit records | Login failures, access denials, approvals, revocations | Restricted access; retention based on audit purpose |
| Operational logs | Errors, durations, dependency status and correlation IDs | Minimize personal content and secrets |
| Backups | Historical copies of database and configuration | Protected access, explicit retention and recovery procedures |
| Configuration | Device mappings, permissions, policy and model settings | Separate user preferences from authoritative security policy |

A field's classification should follow the information it can reveal, not merely its database column name. An embedding, for example, is derived data but may still reveal information about its source.

## 04.26.03 Data collection and minimization

NEXUS should store only what is necessary to provide its intended functionality.

### Required rules

1. Do not save every conversation or document as permanent memory by default.

2. Store explicit memory entries with their source and relevant timestamps.

3. Prefer bounded task summaries and structured results over unrestricted copies of document contents.

4. Keep transient document extraction separate from persistent memory.

5. Do not log passwords, tokens, private keys or raw device credentials.

6. Avoid recording complete model prompts, private memories or document contents in ordinary operational logs.

7. Bound request text, extracted content, model output and tool-result sizes.

8. Do not collect screenshots or full desktop recordings unless a separately approved feature genuinely requires them.

9. Keep test data separate from real user files and private records.

10. Record why a data category exists and which component is responsible for it.

When full content must be stored to support a feature, the specification and retention policy should explicitly say so.

## 04.26.04 Ownership and access control

Data ownership must be enforced by the backend, not inferred from an identifier supplied by the CLI or AI model.

### Default access policy

- Personal memory: accessible only to its owner and authorized system operations.

- Task history and results: accessible to the task owner unless a specific sharing capability is implemented.

- Documents on Windows: accessible only through an authorized bridge and its configured local resource scope.

- Project data: private by default; shared access requires an explicit project membership model.

- Security audit records: restricted to authorized operational roles.

- System configuration: accessible according to configuration ownership and administrative permissions.

- Backups: restricted to authorized recovery operators and protected storage processes.

A team member being a developer or backend maintainer does not automatically grant unrestricted access to another member's private documents or memory.

### Authorization requirements

For every read, export, update or deletion operation, NEXUS must:

1. Authenticate the requester.

2. Resolve the authoritative user identity.

3. Load the requested resource.

4. Check ownership and any applicable sharing permissions.

5. Enforce the operation-specific policy.

6. Return only authorized fields.

7. Record relevant security-sensitive actions without unnecessarily recording private content.

These checks apply to individual records, search results, exports, background jobs and cached results. Knowing a memory ID or task ID is not proof of permission.

## 04.26.05 Retention policy

Retention should be defined separately for each data category. A single retention period for everything would either delete useful recovery evidence too early or retain private data longer than necessary.

The following are proposed starting rules. Exact durations remain open.

| **Data category** | **Proposed lifecycle** |
| --- | --- |
| Personal memory | Retain until the user deletes it or an applicable expiry rule removes it |
| Task history and results | Retain according to an explicit user-data retention policy |
| Transient document extraction | Discard after the operation unless persistence is required by a documented feature |
| Document indexes and embeddings | Retain only while permitted and useful; invalidate when the source or authorization changes |
| Authentication sessions | Expire and revoke according to the session policy |
| Device credentials | Retain while active; revoke and securely retire when replaced |
| Security audit records | Retain for the defined security and operational purpose |
| Operational logs | Use bounded retention and avoid unnecessary personal content |
| Bridge operation journals | Retain long enough to support duplicate detection and uncertain-operation recovery |
| Backups | Retain under the backup schedule, access controls and deletion-reconciliation policy |

### Retention rules

- Define retention in configuration or documented policy rather than relying on accidental database cleanup.

- Make cleanup jobs idempotent, bounded and observable.

- Do not delete operation records while they are needed to resolve uncertain external effects.

- Do not assume that deleting a task result also deletes a Windows file created by that task.

- Do not claim complete erasure while applicable backups or other retained copies still contain the data.

- Document any retention exception, including its purpose, access restrictions and eventual deletion behavior.

The team must define actual retention durations before production-like use.

## 04.26.06 User data deletion

Deletion is not one universal database command. NEXUS must distinguish active-data deletion from historical retention and external side effects.

### Proposed deletion workflow

1. Authenticate and authorize

Verify ownership and the requested deletion scope

2. Identify affected data

Primary records, indexes, caches, derived data and applicable copies

3. Apply deletion or deactivation

Remove the data from active use and retrieval

4. Invalidate dependent data

Clear relevant caches, indexes and derived records

5. Verify and report

Confirm the defined deletion scope and communicate any retention limitations

### Memory deletion

When a user deletes a memory:

- It must no longer appear in active memory retrieval.

- Associated lexical and semantic index entries must be removed or invalidated.

- Relevant caches must be invalidated.

- A later context-assembly request must not use the deleted memory.

- Task history and audit evidence remain separate unless their own deletion policy applies.

- Backup retention must be handled according to the documented policy.

### Task and artifact deletion

Deleting a task record, if supported, must not be treated as deleting every external effect of the task.

For example, if NEXUS created a file on a Windows computer, removing the task result must not silently remove that file. Conversely, deleting a task record must not be presented as complete deletion of all evidence if security or recovery records are retained.

If an operation remains uncertain, preserve the minimum required evidence until safe recovery and applicable retention requirements have been addressed.

### Deletion limitations

NEXUS must report the actual scope of deletion. It must not claim that information has been erased from every backup, log or device when those locations have not been verified.

## 04.26.07 User data export

Users should be able to retrieve their own eligible data without requiring direct database access.

For the MVP, a structured export file is sufficient. A dashboard or self-service web portal is not required.

### Proposed export command

An illustrative CLI interface is:

nexus data export --scope personal

The final command syntax is an implementation decision. The important requirement is a documented, authenticated export workflow.

### Export scope

A personal export may include:

- User-owned memory entries and their available provenance metadata.

- Task history, states and bounded results.

- User-owned artifact metadata.

- User preferences and non-secret configuration.

- A manifest describing export time, included categories and limitations.

Exporting document content, credentials, device secrets, security-sensitive audit records or another user's data should not happen implicitly. Those categories need separate authorization and handling rules.

### Export requirements

1. Authenticate the user and verify ownership of every included record.

2. Define the requested categories and export format.

3. Apply the same access controls used by normal API reads.

4. Bound export size and processing time.

5. Avoid exporting credentials, access tokens or secret configuration.

6. Record relevant export metadata without copying private contents into ordinary logs.

7. Protect the resulting export file and explain where it was written.

8. Ensure repeated requests cannot bypass authorization or retrieve another user's data.

A JSON export is a reasonable initial format for structured records. If a future feature supports full document export, it must separately define which source files are included and how their permissions are verified.

## 04.26.08 Privacy in AI processing and context retrieval

NEXUS's local-first AI approach reduces the need to send data to a paid external API, but local inference does not automatically guarantee privacy. The model runtime, logs, temporary files, indexes, backups and network interfaces still require protection.

### Required safeguards

- Retrieve context only after checking the requester's authorization.

- Filter private memory and project data by scope before supplying it to the model.

- Send only context relevant to the current task.

- Treat document text, memory entries and tool outputs as untrusted input.

- Do not allow document instructions to override permissions or disclosure rules.

- Avoid logging complete prompts and private source content by default.

- Keep the model endpoint private and restrict access to authorized application components.

- Define whether inference requests are retained by the selected runtime and where temporary data is stored.

- Treat embeddings, summaries and extracted snippets as potentially sensitive.

- Do not send private data to an external provider unless that integration is explicitly selected, authorized and documented.

### Context deletion and invalidation

If a memory, project membership or source document is deleted or access is revoked, the context retrieval layer must stop exposing the affected information according to the applicable policy.

A stale cache must not bypass a current authorization check. Semantic similarity must never override ownership or permission boundaries.

## 04.26.09 Logging, auditing and privacy boundaries

Operational diagnosis must remain possible without turning logs into a second copy of users' private data.

### Logging policy

Permitted by default when appropriately bounded:

- Correlation, task and operation identifiers.

- Component and version identifiers.

- Event type and timestamp.

- Duration, status and stable error code.

- Relevant non-sensitive configuration versions.

- Approval and policy-decision metadata.

Prohibited in ordinary logs by default:

- Passwords, access tokens and device credentials.

- Full document contents.

- Full private memory entries.

- Unrestricted model prompts and outputs.

- Secret configuration values.

- Unnecessary absolute filesystem paths or personal content.

### Audit versus privacy

Audit records may need to retain evidence that an access denial, approval, revocation or consequential operation occurred. That does not mean the audit record should contain the full private document or memory involved.

The team must document which audit metadata is retained, who can read it, how long it remains available and how deletion requests interact with it.

If an audit or recovery record must be retained, the system should preserve the minimum information necessary to satisfy its defined purpose.

## 04.26.10 Data protection tests

The following tests are required for privacy-related release validation.

| **Test** | **Acceptance criterion** |
| --- | --- |
| User exports personal memory | Only the authenticated user's authorized records are included |
| User requests another user's task ID | Access is denied |
| User deletes a memory | It is no longer returned by active retrieval |
| Deleted memory exists in an old backup | Restore does not silently reactivate it |
| Document content is processed | Full content does not appear in ordinary logs |
| Semantic cache contains old content | Current authorization and deletion rules are enforced |
| User requests task deletion | External files are not silently deleted |
| Export includes configuration | Secrets are excluded |
| User is removed from a shared scope, if implemented | New retrievals are denied according to the membership policy |
| Diagnostic output is generated | Credentials and private content are not exposed |
| Backend restarts after deletion | Deleted content remains excluded from active retrieval |
| Backup retention expires | Cleanup follows the defined retention procedure |

The test suite should use synthetic records and isolated directories. Passing these tests is evidence of the tested behavior, not a guarantee that every possible privacy risk has been eliminated.

## 04.26.11 Implementation priorities

P0 — Required foundation

Private and controlled data handling

- User-scoped memory, tasks and results.

- Documented data categories and retention rules.

- Secret-safe logging and diagnostics.

- Memory deletion and retrieval-cache invalidation.

- Backup-aware deletion and revocation handling.

- Authenticated personal data export.

- Tests for cross-user access and data leakage.

P1 — Stronger lifecycle management

Reliable cleanup and visibility

- Automated retention and cleanup jobs.

- Export manifests and clearer deletion-status reporting.

- Better tracking of derived data and index invalidation.

- Scheduled privacy regression tests.

P2 — Future enhancements

Advanced user controls

- Selective exports by category or time range.

- Richer data lifecycle diagnostics.

- Self-service privacy interface, if user feedback justifies it.

## 04.26.12 Open decisions

1. What retention periods apply to task history, audit records, logs and operation journals?

2. Which user-data categories must be exportable in the first release?

3. Should export support JSON only initially?

4. Which data, if any, must be retained after a user requests deletion?

5. How will deletion information survive restoration from older backups?

6. Where will temporary document extraction and model-related data be stored?

7. How will the team verify that no unauthorized external AI service receives private content?

8. Which operational roles may access audit records, and under what conditions?

9. How will retention jobs report failures and overdue cleanup?

10. What privacy information should the CLI show when an export or deletion is completed only partially?

These decisions must be recorded before the relevant features are treated as production-ready.

## 04.26.13 Definition of done

- Data categories, owners and access rules are documented.

- Personal memory, tasks and results remain isolated between users.

- Retention policies exist for all major stored data categories.

- Deletion removes data from active retrieval and relevant indexes or caches.

- Backup restoration does not silently reactivate deleted memory or revoked permissions.

- User export is authenticated, bounded and excludes secrets.

- Document content and private memory are not logged by default.

- AI context retrieval checks authorization before exposing data.

- Privacy regression tests cover cross-user access, deletion, exports and caches.

- The system accurately describes any deletion or retention limitations.

Section exit criterion: users have enforceable control over their private memory and eligible data, while NEXUS retains only the operational evidence required for its documented reliability and security purposes.
