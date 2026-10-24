## 04.17.01 Purpose

NEXUS must do more than execute individual operations. It must reliably communicate what happened, preserve useful outputs and provide evidence that the requested result exists.

A task may produce several types of output:

- Text answers and summaries.

- Search results and document references.

- Generated files on a user's Windows computer.

- Structured operation results.

- Partial results when some steps fail.

- Diagnostic information when completion cannot be verified.

This section defines how NEXUS records, verifies and presents these results without confusing a model-generated claim with a verified outcome.

Core principle: a task result must reflect persisted execution evidence, and an artifact must have a known owner, destination, provenance and verification status.

## 04.17.02 Result and artifact concepts

NEXUS should distinguish three related but separate concepts.

Task result

The overall outcome reported to the user: success, failure, partial success, cancellation or uncertainty.

Artifact

A deliverable such as a generated file, structured result set or retained summary, with a reference and ownership.

Verification evidence

Evidence from the application, database or Windows bridge supporting a claim that a step or artifact reached a particular state.

These concepts should not be collapsed into a single success flag.

For example, a file may have been created successfully even though a later summarization step failed. The task may therefore be partially successful, while the file artifact remains valid and available.

## 04.17.03 Result classification

The final result should accurately represent what the task accomplished.

| **Outcome** | **Meaning** |
| --- | --- |
| SUCCEEDED | All required steps completed and the required outcome was verified |
| FAILED | The task could not achieve its required outcome |
| PARTIAL_SUCCESS | Some useful work completed, but one or more required parts failed or could not be completed |
| CANCELLED | Cancellation completed according to the task lifecycle and external effects were reconciled |
| UNCERTAIN | The system cannot yet determine whether an important external operation succeeded |

These are proposed outcome classifications. The canonical task lifecycle from Section 03.29 still governs active and terminal task states. For example, uncertainty may require an INTERRUPTED or recovery state before a final outcome can be assigned.

A result must not be marked successful merely because:

- The model produced a plausible response.

- The bridge accepted a command.

- A request timed out without returning an error.

- A file existed before the operation.

- The task's final database update succeeded.

The system must establish the outcome required by the specific tool and task.

## 04.17.04 Artifact types and storage strategy

NEXUS should classify artifacts by where they live and how they are accessed.

| **Artifact type** | **Example** | **Proposed storage** |
| --- | --- | --- |
| Text result | Answer or summary | PostgreSQL task-result record, within size limits |
| Search result | Matching document references | Bounded structured result record |
| Windows file | A generated report in an approved workspace | File remains on the target Windows computer; backend stores metadata and a reference |
| Extracted document text | Text used for analysis | Transient processing data by default; persistent indexing is governed by Section 04.16 |
| Diagnostic result | Error code and recovery status | Task history and diagnostic records, excluding secrets |
| Large result | Large extracted output or file | External artifact storage only if a demonstrated need and secure design justify it |

### Recommended MVP decision

Keep the architecture simple:

- Store bounded task-result metadata and text in PostgreSQL.

- Keep files created by Windows tools on the target computer.

- Store a logical artifact reference, owner, target device, relative location and verification status.

- Do not automatically upload entire user files to the shared backend.

- Do not introduce a separate object-storage service until requirements justify it.

This approach avoids making the shared backend a central repository for every developer's local documents.

### Artifact references

A reference should identify the artifact without granting access by itself.

A logical artifact record may contain:

- artifact_id

- task_id

- step_id

- owner_user_id

- target_device_id

- artifact_type

- directory_id

- relative_path

- mime_type, where reliably detected

- size_bytes, where available

- verification_status

- created_at

- source_operation_id

These are proposed fields, not a final schema. The application must authorize every artifact lookup and access request using the authenticated user and applicable resource permissions.

An artifact ID must never act as a bearer credential or permit another user to access a private file.

## 04.17.05 Artifact creation and publication lifecycle

A generated file should not be treated as a published deliverable until the system has sufficient evidence that the intended file was created at the intended destination.

Proposed

Plan identifies an artifact and destination

Authorized

Tool, directory, name and permissions validated

Creation dispatched

Operation intent is persisted before the external side effect

Created and verified

Bridge provides evidence for the expected artifact

Artifact reference published

Authorized user can inspect the recorded result

### Required creation rules

1. Resolve the destination through a configured logical directory ID.

2. Validate the relative filename and content size.

3. Apply the relevant policy and approval checks.

4. Persist the operation intent.

5. Execute the registered tool on the intended device.

6. Verify the result according to the tool contract.

7. Persist the artifact metadata and operation outcome.

8. Return the artifact reference only when its status is accurately represented.

The Windows bridge should use safe create-only semantics by default. It must not silently overwrite an existing destination.

If a file was created but the backend failed to record its result, recovery must reconcile the external side effect before retrying or publishing a final outcome.

## 04.17.06 Verification levels

Different outputs require different levels of verification. NEXUS should record what it actually verified rather than claiming that every artifact has been fully validated.

| **Level** | **Verification** | **Example** |
| --- | --- | --- |
| V0 — Proposed | No external result yet | Planned output filename |
| V1 — Acknowledged | Tool accepted the operation | Bridge accepted a request |
| V2 — Existence verified | Expected resource was observed | Destination file exists |
| V3 — Content verified | Relevant content or metadata matches the intended output | File size, format or content fingerprint matches the operation's evidence |
| V4 — Goal verified | The task-specific success condition is satisfied | Required sections exist in a generated report |

These levels are a proposed internal vocabulary, not a claim that all tools can support every level.

A file's existence does not prove its content is correct. A successful application launch does not prove that the requested work inside the application was completed. A model-generated summary does not prove that the underlying document was read successfully.

### Verification requirements

- Define expected outcomes per tool before implementation.

- Associate evidence with the operation and source version.

- Validate that evidence belongs to the intended device and operation.

- Distinguish missing evidence from evidence of failure.

- Do not use a higher verification level than the tool contract supports.

- Preserve uncertainty when verification cannot establish the outcome.

Verification should be proportionate to the operation. A basic file search does not require the same checks as creating a file that the user expects to use as a deliverable.

## 04.17.07 Task result schema and persistence

Task results should be structured enough for the CLI, API, automated tests and future integrations to consume without parsing arbitrary prose.

A logical result record may contain:

| **Field** | **Purpose** |
| --- | --- |
| task_id | Identifies the task |
| outcome | Final outcome classification |
| summary | Bounded human-readable explanation |
| completed_steps | Steps verified as completed |
| failed_steps | Steps that failed |
| skipped_steps | Steps not executed, with reasons |
| uncertain_steps | Steps awaiting reconciliation |
| artifact_ids | Authorized references to task artifacts |
| evidence_refs | References to verification evidence |
| error_code | Stable error code, when applicable |
| completed_at | Time of finalization, if finalized |

This is a logical contract, not a finalized database schema.

### Persistence rules

- A final result must be derived from persisted task and step states.

- Result publication and final task transition must be consistent.

- A task must not become successful while required steps remain unresolved.

- Artifact metadata must reference the operation that produced or verified it.

- Large outputs must not exceed configured persistence limits.

- Repeated result requests must return the same recorded outcome unless the task is explicitly revised through a supported workflow.

- A result retrieval failure must not change the underlying task outcome.

The team should decide whether results are stored in the task row, a separate result table or a combination. This choice should follow the existing persistence model rather than introduce duplicate sources of truth.

## 04.17.08 Partial success and uncertain outcomes

A task may complete useful work even when its full goal cannot be achieved.

Consider a task that searches for two documents, reads both and creates a comparison file. If the first document is read successfully but the second is unavailable, NEXUS must not claim that the comparison is complete.

It should instead report:

- Which steps succeeded.

- Which steps failed and why.

- Which steps were skipped because of dependencies.

- Whether any external operation remains uncertain.

- Which artifacts, if any, were verified.

- What safe action is needed to continue.

### Example outcome table

| **Step** | **Outcome** | **Result** |
| --- | --- | --- |
| Search documents | Succeeded | Two references found |
| Read document A | Succeeded | Content extracted |
| Read document B | Failed | Access denied |
| Create comparison | Skipped | Required input unavailable |

The overall task would be a partial success only if the recorded work constitutes a meaningful partial result under the task's outcome rules. Otherwise, it may be a failure with some completed intermediate steps.

### Uncertain file creation

If a bridge times out after dispatching file creation:

1. Preserve the operation as uncertain.

2. Query the bridge journal or reconcile the target destination.

3. Validate that the observed file is the intended artifact.

4. Record success if adequate evidence is obtained.

5. Retry only if the tool-specific recovery rules establish that doing so is safe.

6. If the result cannot be determined, report uncertainty and avoid blind repetition.

A matching filename alone may not be enough to prove that a file was created by the current operation. The available evidence must be evaluated against the tool contract.

## 04.17.09 API and CLI result delivery

The API should provide task results through the existing task/result interfaces defined in Section 03.16. Artifact handling should extend those contracts rather than create a separate uncoordinated API.

Proposed endpoints remain:

- GET /v1/tasks/{task_id}/result

- GET /v1/tasks/{task_id}/steps

- GET /v1/tasks/{task_id}

If artifact-specific operations are needed later, such as retrieving metadata or requesting a controlled file transfer, they should have explicit authorization and resource-scope rules.

### CLI presentation

The CLI should communicate the outcome first, followed by concise supporting details.

For example:

Task: task-123

Outcome: PARTIAL_SUCCESS

Completed:

- Found two document references

- Read the first document

Failed:

- Could not read the second document

- Error: FILESYSTEM_ACCESS_DENIED

Artifacts:

- No comparison file was created

Next action:

Check access to the second document and retry the task.

This is an illustrative display, not a fixed output format or real task result.

### CLI rules

- Show the task ID and actual persisted outcome.

- Distinguish an artifact reference from a local file path.

- Never claim a file was created until the required verification has completed.

- Display errors using stable codes and useful explanations.

- Support bounded machine-readable output for automation.

- Keep diagnostic details out of standard JSON output where they would break its schema.

- Do not expose another user's artifact metadata through guessed IDs.

- Avoid printing sensitive document content by default.

A CLI session ending does not remove the artifact or cancel its task. Results must remain retrievable according to the task-history and retention policies.

## 04.17.10 Artifact access, ownership and retention

Artifact ownership must follow the task and the source device's authorization rules.

### Access rules

- The backend derives the user identity from the authenticated session.

- Artifact ownership and task ownership are checked on every retrieval.

- A registered device does not grant the requesting user access to every file on that device.

- An artifact reference does not bypass the bridge's local filesystem restrictions.

- Revoked device credentials block new access through that device.

- Project sharing, if introduced, requires explicit membership and artifact-access rules.

- A task result may reference a source document without copying its contents into the shared backend.

### Retention categories

NEXUS should define separate retention policies for:

- Task summaries and outcomes.

- Artifact metadata and references.

- Generated files on Windows devices.

- Extracted document content.

- Diagnostic and audit records.

- Backups and recovery records.

Deleting a task result should not silently delete a user's Windows file unless an explicitly authorized file-deletion workflow exists. Similarly, deleting a generated file should not automatically imply that all task history or audit records must be erased.

If a referenced artifact is no longer available, the CLI should report that state rather than silently treating the artifact as valid.

## 04.17.11 Failure handling and error taxonomy

The result layer should use stable errors that distinguish execution failures from artifact verification and retrieval failures.

| **Proposed error code** | **Meaning** |
| --- | --- |
| RESULT_NOT_AVAILABLE | No result has been published yet |
| RESULT_NOT_FOUND | No accessible result exists for the requested identifier |
| ARTIFACT_NOT_FOUND | The referenced artifact cannot be found |
| ARTIFACT_ACCESS_DENIED | The user lacks permission to access the artifact |
| ARTIFACT_VERIFICATION_FAILED | Required verification did not pass |
| ARTIFACT_CONTENT_MISMATCH | Observed content does not match the expected evidence |
| ARTIFACT_SOURCE_UNAVAILABLE | The target device or source location is unavailable |
| ARTIFACT_REFERENCE_STALE | The reference no longer identifies the expected source version |
| RESULT_PERSISTENCE_FAILED | The result could not be durably recorded |
| RESULT_OUTCOME_UNCERTAIN | The system cannot establish the final external outcome |

These codes are proposed and must be reconciled with the shared error catalogue in Section 04.08 before implementation.

### Failure rules

- Do not convert an unrecorded result into success.

- Do not repeat a consequential external operation just because result persistence failed.

- Do not assume that a missing artifact proves it was never created.

- Do not expose filesystem paths or document contents in errors unless authorized and necessary.

- Preserve completed work when later steps fail.

- Return the current task state when the final outcome is not yet known.

## 04.17.12 Testing strategy

| **Test** | **Expected behavior** |
| --- | --- |
| Successful file creation | Artifact is recorded with verification evidence |
| Existing destination | Creation is rejected or handled under an explicitly approved policy; no silent overwrite |
| Bridge reports success but verification fails | Artifact is not marked fully verified |
| Timeout after file creation | Recovery reconciles before retrying |
| Result persistence fails after a side effect | Operation is reconciled; no blind duplicate execution |
| Required step fails | Overall result accurately represents failure or partial success |
| Artifact ID belongs to another user | Access is denied |
| Device becomes unavailable | Artifact state reflects the actual uncertainty or unavailability |
| Artifact is deleted externally | Retrieval reports the current availability accurately |
| Result is requested before completion | Current state is returned; no fabricated final outcome |
| Large output exceeds configured limit | Bounded failure or supported external storage path |
| Repeated result requests | Persisted result remains consistent |
| Task cancellation follows file creation | Created file is preserved and reported; no false claim of rollback |
| Source document changes | Result provenance identifies the version actually processed |
| JSON output requested | Response remains valid machine-readable output |

Tests should use temporary directories and isolated test devices. They must not modify real user files as a side effect of ordinary CI runs.

## 04.17.13 Work packages and ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Result contract and persistence | Developer 1 | Durable result records and consistent task finalization |
| Artifact metadata and authorization | Developer 1 | Ownership checks and artifact references |
| Windows file creation and verification | Developer 2 | Tool-specific evidence and recovery behavior |
| Summary grounding and provenance | Developer 3 | Source references and bounded result generation |
| Partial success and uncertainty tests | All three | Failure-injection coverage |
| CLI result display | Developer 1 + Developer 3 | Human-readable and machine-readable output |
| Security and privacy review | All three | Artifact isolation and sensitive-data controls |

The result schema, tool contracts and task state machine must remain aligned. In particular, the artifact layer must not independently decide that a task has succeeded.

## 04.17.14 Implementation priorities

P0 — Required foundation

Trustworthy results

- Structured task outcomes.

- Durable result persistence.

- Artifact ownership and access checks.

- Verification requirements for file creation.

- Partial-success and uncertain-outcome reporting.

- Safe recovery after lost responses.

P1 — Complete MVP experience

Useful deliverables

- Artifact metadata and references.

- Source provenance and verification evidence.

- CLI result inspection.

- Consistent machine-readable output.

- Retention and artifact-availability handling.

P2 — Later improvements

Advanced artifact management

- Dedicated artifact storage.

- Controlled file-transfer endpoints.

- Artifact version history and richer previews.

- Cross-device artifact transfer.

- Advanced retention and storage optimization.

## 04.17.15 Open decisions

| **Decision** | **Evidence or agreement required** |
| --- | --- |
| Task-result schema | Alignment with existing task and step contracts |
| Artifact metadata schema | Ownership, reference and verification requirements |
| Result-size limits | Representative output sizes and PostgreSQL measurements |
| Verification levels | Tool-specific capabilities and test evidence |
| Generated-file retention | User requirements and data-lifecycle policy |
| Large artifact storage | Demonstrated need and security assessment |
| Artifact retrieval across devices | Explicit authorization and transfer design |
| Partial-success classification | Agreed required-versus-optional step semantics |
| Content fingerprints | Verification value and privacy implications |

## 04.17.16 Definition of done

- Task outcomes are derived from persisted execution evidence.

- Result metadata and artifact references are access-controlled.

- Windows files remain on their intended target device unless a supported transfer is explicitly requested.

- Creation and verification behavior is defined per tool.

- Partial success and uncertainty are represented accurately.

- Recovery does not blindly repeat external side effects.

- Result retrieval is consistent and supports machine-readable output.

- Artifact retention, deletion and source availability are handled explicitly.

- Security, concurrency and failure-injection tests pass.

- Result reporting does not leak private document content or credentials.

Section exit criterion: NEXUS can provide trustworthy, retrievable task outcomes and artifact references, backed by appropriate evidence, while accurately reporting partial work and uncertain external effects.
