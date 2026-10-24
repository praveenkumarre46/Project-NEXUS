## 03.32.1 Purpose

NEXUS must be able to search files, read documents and create files on each developer's Windows 11 computer without giving the AI unrestricted access to the filesystem.

This is more complicated than checking whether a path starts with an approved directory. Windows supports drive-letter paths, UNC network paths, case-insensitive path comparisons in common configurations, symbolic links, junctions, reparse points, alternate path representations and files that can change between validation and use.

A path that appears to be inside an approved workspace may resolve somewhere else. A file that was safe to access during validation may be replaced before the operation executes.

Core design rule: the Windows bridge owns filesystem access and enforces the configured local boundaries. The backend and AI planner must not be trusted to supply safe absolute paths.

This section builds on the existing NEXUS decisions:

- Filesystem tools run in the native Windows bridge.

- Tools accept logical directory IDs instead of unrestricted absolute paths.

- The AI cannot grant itself permissions or expand a directory's scope.

- File creation is create-only by default.

- Uncertain file operations require reconciliation before retry.

- Each developer's device remains an independent execution target.

## 03.32.02 Security objectives

The filesystem layer must:

1. Restrict every operation to configured directory scopes.

2. Prevent traversal outside the permitted scope.

3. Handle Windows path representations consistently.

4. Account for links, junctions and other reparse-point behavior.

5. Avoid validation-to-use race conditions where practical.

6. Reject unauthorized UNC/network paths unless explicitly supported.

7. Enforce file size, search depth, result count and execution-time limits.

8. Prevent silent overwrite during file creation.

9. Avoid leaking private paths or file contents into logs.

10. Return a clear, auditable outcome when safety cannot be established.

The security boundary must remain effective even when a request contains malicious text, a document attempts prompt injection, the model invents a path, or a bridge receives a malformed operation.

## 03.32.03 Filesystem trust boundaries

AI planner

Proposes a logical directory ID and operation

Backend validation and policy

Validates the registered tool, user, device, scope and approval

Windows bridge security boundary

Resolves local configuration, canonicalizes paths and revalidates the operation

Windows filesystem

Actual file and directory operations under the bridge process's OS permissions

The operating system's permissions remain an important final boundary. NEXUS should run the bridge as the normal logged-in user, not as an administrator, unless a separately justified requirement exists.

Application-level authorization does not replace Windows access controls, and Windows access controls do not replace NEXUS's own user and device authorization.

## 03.32.04 Logical directory IDs

NEXUS tools should refer to directories using identifiers such as:

- project_documents

- approved_workspace

- shared_team_documents — only if explicitly configured and authorized.

These names are illustrative. The actual IDs must be configured per device.

A bridge might map approved_workspace to a locally configured directory such as C:\Users\Developer\NexusWorkspace. Another developer may map the same logical ID to a different path.

The model should never choose that absolute path directly.

### Proposed directory configuration

Each configured directory entry should have:

| **Field** | **Purpose** |
| --- | --- |
| directory_id | Stable logical identifier |
| configured_path | Locally configured Windows path |
| allowed_operations | Search, read, create or another explicitly supported operation |
| enabled | Whether the mapping is active |
| limits | Applicable file size, result count and related limits |
| configuration_version | Identifies the configuration used for validation |

The mapping must be stored and managed on the Windows bridge. The backend may know the logical ID and its authorized uses, but it should not need the user's complete local directory configuration.

The actual configuration format and storage location remain open implementation decisions.

### Example request

A planner should propose a request resembling:

{

"tool_name": "search_files",

"arguments": {

"directory_id": "project_documents",

"query": "design"

}

}

It should not be permitted to substitute an arbitrary path such as C:\Users\OtherUser\Documents or \\server\share\private to escape the configured scope.

The bridge must reject unknown directory IDs, disabled mappings and operations not allowed for the selected mapping.

## 03.32.05 Windows path canonicalization

Canonicalization means converting a path into a consistent representation suitable for comparison and further validation. It does not, by itself, prove that accessing the path is safe.

Windows paths can have different textual representations that refer to the same location or behave differently under the filesystem's rules. For example:

- C:\NexusWorkspace\Reports

- C:\NexusWorkspace\Reports\..\Reports

- c:\nexusworkspace\reports

A naive string comparison can produce incorrect authorization decisions.

### Required validation sequence

For each filesystem operation, the bridge should:

1. Validate the tool's arguments and the logical directory ID.

2. Resolve the directory ID using trusted local configuration.

3. Reject disallowed path forms and unsupported namespaces.

4. Normalize and resolve the requested relative path using Windows-aware filesystem APIs.

5. Confirm that the resolved target remains inside the permitted scope.

6. Inspect relevant filesystem attributes and link behavior.

7. Perform the operation using the safest available filesystem primitive.

8. Verify the result and record its outcome.

The sequence is a security design, not a guarantee that ordinary path-string checks prevent every attack. Steps involving the actual filesystem must account for changes between validation and use.

### Why string-prefix checks are insufficient

Consider an approved directory:

C:\NexusWorkspace

A prefix check could mistakenly treat this path as inside the workspace:

C:\NexusWorkspace-Private

The second path begins with the same characters but is a different directory.

Comparing path components is better than checking raw string prefixes, but even component-aware comparisons are insufficient if symbolic links, junctions or other filesystem indirections can redirect access.

Required rule: do not authorize filesystem access solely because a normalized path string starts with an approved root.

## 03.32.06 Symbolic links, junctions and reparse points

Windows supports filesystem features that can redirect a path to another location. These include symbolic links, junctions and other reparse-point types.

Suppose NEXUS is authorized to read:

C:\NexusWorkspace

Inside that directory, an entry named External points to a location outside the workspace. Searching recursively through External could expose files the user never intended to include in the approved scope.

### Proposed MVP policy

- Do not follow directory links or junctions during recursive search by default.

- Inspect relevant filesystem attributes before traversing entries.

- Do not assume that a link's displayed path determines the location it ultimately accesses.

- Reject or safely skip entries whose target cannot be validated.

- Apply equivalent restrictions to file reads and file creation.

- Treat unsupported reparse-point types as unsafe until their behavior is explicitly handled and tested.

A simple policy of not following links is easier to reason about than attempting to support every Windows filesystem redirection feature during the first release.

However, merely checking a path's attributes and then reopening it by name can still leave a race window. Stronger protection requires safer operating-system APIs and handle-based checks where practical.

The precise implementation should be selected and tested against the actual Windows environment rather than assumed from a generic path-normalization example.

## 03.32.07 Drive paths, UNC paths and special namespaces

The bridge must explicitly define which path types are supported.

| **Path category** | **Proposed MVP behavior** |
| --- | --- |
| Ordinary local drive paths | Supported only through configured directory IDs |
| Relative paths | Allowed only when resolved against a trusted configured root |
| UNC paths such as \\server\share | Deny by default |
| Windows device namespaces | Reject unless a specific supported use case is reviewed |
| Environment-variable expressions | Do not expand model-provided values |
| Paths containing traversal components | Resolve and validate safely; reject if scope cannot be proven |
| Alternate data stream syntax | Reject unless explicitly supported and justified |
| Reparse points and links | Do not follow by default; validate explicitly where needed |
| Network-mounted or removable drives | Unsupported by default unless configured and tested |

These are proposed restrictions for the first release, not claims that every listed path type is inherently malicious.

If the team later needs network shares or removable drives, add them as explicit capabilities with their own permissions, configuration and tests. Do not make them available implicitly through general path handling.

## 03.32.08 The time-of-check-to-time-of-use problem

A time-of-check-to-time-use (TOCTOU) race occurs when a resource changes after validation but before an operation uses it.

Example:

1. The bridge validates that C:\NexusWorkspace\report.txt is inside an approved directory.

2. Another process replaces an intermediate directory or changes a link.

3. The bridge opens the path by name.

4. The actual operation reaches a different location than the one validated.

The same class of issue can affect file creation if an attacker changes a directory entry after validation.

### Required engineering response

- Keep path resolution and access as closely coupled as practical.

- Prefer safe handle-based operations when available.

- Revalidate security-relevant attributes at the point of access.

- Avoid following untrusted links or reparse points.

- Use restrictive directory permissions to reduce the ability of other processes to manipulate the workspace.

- For writes, use an operation that fails if the destination already exists rather than a separate existence check followed by an ordinary write.

- If the bridge cannot establish that the operation stayed within scope, reject it or report an uncertain outcome.

No portable path-validation helper should be treated as a complete defense against filesystem races. The team must verify the guarantees of the actual Windows APIs and libraries selected.

## 03.32.09 Safe file creation

The initial create_file tool must be designed to avoid accidental data loss and unauthorized writes.

### Required behavior

1. Accept an approved logical directory ID and a relative destination name.

2. Validate path components and reject unsupported path syntax.

3. Resolve and verify the destination against the configured workspace.

4. Enforce content size and encoding constraints.

5. Create the destination only if it does not already exist.

6. Avoid overwriting existing files, following an unsafe link or creating files outside the approved root.

7. Verify the resulting file and report its outcome.

8. Record enough operation metadata to support recovery without logging the entire document content.

### Existing destination

If the destination already exists, return a clear conflict result. Do not silently append to, truncate or replace it.

A future version could offer an explicitly approved replacement operation, but it should be a separate, reviewed capability or operation mode with its own risk classification and approval semantics.

### Atomicity considerations

A create-if-absent filesystem operation is preferable to this unsafe pattern:

# Illustrative unsafe pattern.if not destination.exists():    destination.write_text(content)

Another process can create or replace the destination between the check and the write.

The implementation should use an appropriate create-new/exclusive-create primitive and verify its semantics on the target filesystem. Temporary-file-and-rename strategies also require care: replacement semantics and atomicity depend on the specific API and filesystem.

### Lost response after a successful write

If a file was created but the bridge crashed before reporting success, NEXUS must not blindly retry.

The backend should reconcile the operation using its stable operation ID, the bridge's operation journal and available filesystem evidence. If it cannot reliably establish whether the intended operation completed, the result remains uncertain and the user is informed.

File existence alone may not prove that a particular operation created the file, especially if another process could have created it independently.

## 03.32.10 Safe file search

The search_files tool must have explicit limits so that a single request cannot trigger an unbounded scan of a user's computer.

Proposed limits include:

- Permitted directory IDs only.

- Maximum traversal depth.

- Maximum number of returned results.

- Maximum execution duration.

- Explicit rules for hidden and system files.

- No recursive traversal through links or junctions by default.

- Bounded query length and supported matching behavior.

- Cancellation checks during long-running searches.

- Restricted error reporting that does not expose unrelated local paths.

The numeric limits should be established through performance testing on the team's actual hardware.

### Search result contract

A result should include enough information to identify and later reference a permitted file without exposing unnecessary local information.

Proposed fields:

- A stable result identifier for the current operation.

- A display name.

- A path relative to the configured logical directory.

- Relevant metadata, such as size and modification time.

- A status for inaccessible, skipped or unsupported entries when appropriate.

Absolute paths should not be sent to the AI unless there is a specific, reviewed reason. A relative path is generally sufficient for planning a follow-up read.

### Search consistency

A filesystem can change during a search. A returned entry may be renamed or removed before the next operation.

Therefore, a search result is not a permanent authorization grant. Before reading a selected file, the bridge must resolve and validate it again under the current permissions and filesystem state.

## 03.32.11 Safe document reading

The read_document tool needs protections against oversized files, malformed documents and hostile content.

### Input checks

- The file must be inside the authorized scope.

- The file must be of an explicitly supported format.

- File size and extraction time must be bounded.

- Unsupported or malformed documents must produce controlled errors.

- Extraction must not execute macros, scripts or embedded active content.

- Extracted content must be treated as untrusted data by the planner.

- Output length must be bounded before sending content to the model.

Plain text, PDF and DOCX were previously identified as candidate formats. The exact MVP format list is still open; the team should not promise support until the corresponding extraction libraries and security tests are selected.

### Content and privacy

The bridge should not log full document content by default. Diagnostics can record the operation ID, logical directory ID, safe file reference, duration, extraction outcome and bounded error code.

Document content must not be allowed to:

- Grant access to another directory.

- Change the tool registry.

- Approve a pending operation.

- Change the target device.

- Override the application's policy.

- Cause NEXUS to execute arbitrary commands.

These restrictions are enforced by the application and bridge, not by relying on the model to ignore malicious instructions.

## 03.32.12 Error handling and outcome classification

Filesystem errors should use stable machine-readable codes and safe user-facing explanations.

| **Error code** | **Meaning** | **Expected behavior** |
| --- | --- | --- |
| DIRECTORY_NOT_CONFIGURED | Logical directory ID is unknown or unavailable | Reject; request configuration if appropriate |
| FILESYSTEM_SCOPE_DENIED | Requested resource is outside permitted scope | Deny without accessing it |
| UNSUPPORTED_PATH_TYPE | Path uses an unsupported namespace or form | Reject |
| LINK_TARGET_NOT_ALLOWED | Operation encounters a prohibited link or reparse point | Skip or reject safely |
| FILE_NOT_FOUND | Selected file no longer exists | Report; refresh search if appropriate |
| FILE_ALREADY_EXISTS | Create-only destination already exists | Reject without overwriting |
| FILE_TOO_LARGE | File exceeds configured limit | Reject or use a separately designed bounded extraction path |
| DOCUMENT_FORMAT_UNSUPPORTED | Format is not supported | Report honestly |
| FILESYSTEM_ACCESS_DENIED | OS or application permissions deny access | Reject without privilege escalation |
| FILESYSTEM_OPERATION_TIMEOUT | Operation exceeded its allowed duration | Reconcile if an external effect might have occurred |
| OPERATION_OUTCOME_UNCERTAIN | Completion cannot be reliably established | Preserve uncertainty; do not blindly retry |

These codes are proposed and should be aligned with the shared error contract in Section 03.24.

Do not return detailed absolute paths, account names or other private information in errors unless the requesting user is authorized to see them and the information is necessary.

## 03.32.13 Testing strategy

The team should use isolated temporary directories and dedicated test fixtures. Tests must never rely on modifying a developer's real documents.

### Required test groups

Path authorization

Test path traversal, sibling-directory prefix confusion, case differences, relative paths, alternate path forms, unknown directory IDs and unauthorized roots.

Links and filesystem redirection

Test symbolic links, junctions, reparse points and links introduced after initial validation. Verify that unsupported or unsafe targets are not accessed.

Safe writes

Test existing destinations, simultaneous create attempts, invalid names, oversized content, interrupted writes and a successful write with a lost response.

Search and document extraction

Test depth and result limits, inaccessible entries, unsupported formats, oversized documents, malformed files and prompt injection inside document contents.

Recovery and concurrency

Test files changed after search, bridge restarts, duplicate operation delivery, concurrent writers, timeouts and reconciliation after an uncertain result.

### Important acceptance scenarios

- A traversal attempt cannot read or write outside the approved directory.

- A sibling directory with a similar name cannot bypass scope validation.

- A prohibited link cannot expose files outside the workspace.

- An existing file is never overwritten by create_file.

- Two concurrent create requests cannot both claim successful creation of the same new destination.

- A file changed after search is revalidated before reading.

- Search limits are enforced even when the model requests a larger result set.

- Malicious document text cannot alter permissions or enable tools.

- A timeout after a possible write does not trigger an unsafe blind retry.

- Diagnostics do not leak document contents, credentials or unauthorized absolute paths.

Run these tests on Windows itself, because filesystem behavior and APIs must be validated on the actual execution platform. WSL2-only Linux tests are not a substitute for Windows bridge integration tests.

## 03.32.14 Implementation priorities

| **Priority** | **Deliverables** |
| --- | --- |
| P0 — MVP | Logical directory IDs, strict scope enforcement, safe path handling, bounded search, bounded document reading, create-only writes, safe errors and core security tests |
| P1 — Hardening | Stronger handle-based access checks where practical, race-condition testing, enhanced filesystem diagnostics and robust recovery |
| P2 — Expansion | Explicitly supported network shares, advanced filesystem capabilities and additional document-processing tools |

P0 does not mean that ordinary string canonicalization alone is sufficient. The implementation must demonstrate that its actual Windows filesystem operations respect the defined boundaries.

## 03.32.15 Open decisions

The team must settle the following before finalizing filesystem implementation contracts:

1. Which Windows directories are permitted by default?

2. Which document formats are supported in the first release?

3. What are the maximum search depth, result count, file size and extraction duration?

4. Are hidden files included in search?

5. Are network shares and removable drives completely excluded from the MVP?

6. Which Windows APIs and libraries will be used for safe path resolution and create-if-absent operations?

7. How will the bridge journal and filesystem evidence be used to reconcile uncertain writes?

8. What local permissions protect the configured workspace?

9. Which path and diagnostic details can be shown to the user?

10. How will configuration changes affect queued or pending operations?

## 03.32.16 Definition of done

- Filesystem tools accept logical directory IDs rather than arbitrary model-provided absolute paths.

- Directory mappings and permitted operations are configured locally and enforced by the bridge.

- Canonicalization, scope validation and link handling are documented and tested.

- Search and extraction have enforceable resource limits.

- File creation does not overwrite an existing destination by default.

- Race conditions and uncertain outcomes have explicit handling.

- Windows-specific security tests pass.

- The bridge does not require administrator privileges for ordinary MVP operations.

- Private content and sensitive local paths are not unnecessarily exposed in logs or model context.

- Unsafe or ambiguous filesystem operations fail closed.

Recommended engineering decision: keep filesystem access deliberately narrow for the first release. Use locally configured logical directory IDs, bounded search and reading, and create-only writes. Treat path resolution as a security-sensitive operation rather than a string-processing task.
