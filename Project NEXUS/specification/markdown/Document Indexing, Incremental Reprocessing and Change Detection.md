## 04.16.01 Purpose

NEXUS needs a reliable way to find and understand documents on each user's Windows computer without repeatedly extracting and embedding every file.

Document indexing can improve search and context retrieval, but it introduces additional concerns: stale content, unauthorized indexing, disk and memory consumption, concurrent file changes, and invalid cached results.

This section defines how NEXUS should:

- Discover documents only within explicitly permitted locations.

- Track document metadata and indexing status.

- Detect changes, renames, moves and deletions.

- Reprocess only documents that need updating.

- Keep extracted text and embeddings consistent with the source file.

- Handle interrupted indexing and document-processing failures.

- Bound resource consumption on the designated host and individual Windows computers.

Recommended MVP approach: start with on-demand search and document reading. Add incremental indexing for a small, explicitly configured set of directories only after the basic filesystem and document-processing workflows are reliable.

Indexing is an optimization, not a prerequisite for the core NEXUS experience.

## 04.16.02 Scope and design principles

Document indexing must follow the filesystem security rules already defined for NEXUS.

- A registered device does not grant access to all its files.

- Only configured logical directory IDs may be indexed.

- The Windows bridge remains responsible for local filesystem authorization.

- The model cannot expand the indexing scope by proposing additional paths.

- Indexing must not execute macros, scripts or document-embedded code.

- Extracted text and embeddings are sensitive derived data.

- A search result is not permanent authorization to read a file later.

- The index is a derived representation; the original file remains the source of truth.

### Initial document scope

| **Document type** | **Initial approach** |
| --- | --- |
| Plain text | Candidate for initial indexing |
| PDF | Add after extraction quality and resource limits are validated |
| DOCX | Add after parser and resource behavior are validated |
| Spreadsheets | Defer |
| Presentations | Defer |
| Scanned documents requiring OCR | Defer |
| Encrypted or password-protected documents | Report unsupported unless a safe supported workflow is defined |

The supported formats must be finalized based on parser reliability, licensing, security and performance testing—not just whether a library can open the file.

## 04.16.03 Logical architecture

Windows bridge

Scoped discovery · file metadata · safe source access

Indexing coordinator

Eligibility · scheduling · change detection · retry control

Document processing pipeline

Extraction · normalization · chunking · provenance

PostgreSQL metadata

Source identity, versions and processing status

Derived index

Extracted text, lexical index and optional embeddings

Logical architecture only. The exact placement of extraction, storage and embedding generation remains an implementation decision.

The Windows bridge must not become a general-purpose remote filesystem service. Indexing requests should identify an already configured logical directory and a bounded operation.

The index coordinator should reuse the task scheduler and resource controls from Sections 04.11–04.12 rather than introducing an independent, unbounded worker system.

## 04.16.04 Document identity and metadata model

A document needs a stable logical identity within its authorized scope, while its path and contents may change.

A filename alone is not a sufficient identity: different directories can contain files with the same name, and a file can be renamed without changing its contents.

### Proposed document metadata

| **Field** | **Purpose** |
| --- | --- |
| document_id | NEXUS identifier for the indexed document |
| owner_user_id | Owner of the indexed data |
| device_id | Windows computer containing the source |
| directory_id | Configured logical directory scope |
| relative_path | Source location relative to that scope |
| document_status | Current indexing and availability status |
| source_fingerprint | Evidence used to detect source changes |
| extractor_version | Version of the extraction implementation |
| index_version | Version of the indexing pipeline |
| last_seen_at | Last time discovery confirmed the source existed |
| last_indexed_at | Last successful indexing time |
| last_error_code | Bounded failure category, if applicable |

These are logical fields, not a finalized database schema. Exact constraints, fingerprint strategy and storage layout remain open.

### Ownership and scope

The index must be associated with its owner, device and configured directory scope. Queries must filter by the authenticated user's authorized scope before exposing indexed text or embeddings.

If NEXUS later supports shared project indexes, sharing must be implemented through an explicit access model. Placing documents on a shared computer does not automatically make their contents available to all users.

## 04.16.05 Document and indexing lifecycle

The source file and its derived index have separate lifecycles.

Discovered

Source is within an authorized scope

Eligible for indexing

Format and resource limits are satisfied

Processing

Extraction and derived index generation

Indexed and searchable

Derived content is associated with a verified source version

Additional outcomes are required for real-world failures.

| **Proposed state** | **Meaning** |
| --- | --- |
| DISCOVERED | Source found, not yet processed |
| QUEUED | Eligible and waiting for indexing capacity |
| PROCESSING | Extraction or index generation is in progress |
| INDEXED | Current source version was processed successfully |
| STALE | Source or pipeline changed; prior derived content may no longer be current |
| FAILED | Processing failed for a recorded reason |
| UNSUPPORTED | Format or operation is not supported |
| MISSING | Previously indexed source was not found during an authoritative check |
| EXCLUDED | Source is outside current indexing policy or explicitly excluded |
| DELETED | Indexed record is retired according to the deletion policy |

These states describe indexing, not task execution. A task may still be running while a document index is stale, and a successful indexing operation does not establish that every task using that document has succeeded.

### State transition rules

- A discovered eligible file may be queued.

- A successful processing run may become INDEXED only after the derived records are committed consistently.

- A source change must invalidate the claim that the previous index represents the current source.

- A transient parser or runtime failure may be retried within defined limits.

- Unsupported files should not be retried indefinitely.

- A missing file should not be treated as deleted until the system has sufficient evidence to distinguish deletion from an incomplete or failed scan.

- A revoked directory scope must block new indexing and retrieval, even if derived content remains stored.

## 04.16.06 Detecting source changes

Change detection should balance correctness, performance and privacy. No single metadata signal is sufficient for every filesystem scenario.

### Candidate change signals

| **Signal** | **Benefit** | **Limitation** |
| --- | --- | --- |
| File size | Cheap to inspect | Different content can have the same size |
| Last-modified timestamp | Cheap change indicator | Timestamp resolution and copying behavior vary |
| File identity metadata | Can help identify renames or replacements | Availability and behavior vary across filesystem types |
| Content fingerprint | Strong evidence that content differs | Requires reading file content |
| Extractor/index version | Detects changes to processing logic | Does not detect source changes by itself |

Recommended baseline: use metadata to identify likely changes and a content fingerprint when reliable change detection is required. The precise fingerprint strategy should be benchmarked against the intended directories and file sizes.

Do not assume that file size and modification time prove content equality. Conversely, avoid reading and hashing every large file on every polling cycle if a cheaper, reliable change signal is sufficient for the configured freshness requirement.

### Change-detection workflow

1. Discover a file within an authorized directory.

2. Read bounded source metadata.

3. Compare it with the last known source record.

4. If no change is detected under the configured strategy, retain the current index.

5. If a change is suspected, mark the prior index stale and queue reprocessing.

6. Revalidate source identity and scope before reading.

7. Process the source and record the version evidence.

8. Commit new derived data only if it corresponds to the source version actually processed.

9. If the file changed during processing, reject the stale result or mark it stale and schedule another bounded attempt.

This final check is important: otherwise, NEXUS could index an old version of a file and incorrectly mark it current after the source has changed.

## 04.16.07 Incremental indexing and reprocessing

An indexing system should not reprocess every file whenever it runs. It should identify the subset of documents whose source or processing requirements have changed.

### Reprocessing triggers

- A newly discovered eligible file.

- A source content change.

- A supported file being renamed or moved within the indexed scope.

- An extractor version change that affects output.

- A chunking or normalization change.

- An embedding model or embedding configuration change.

- A change to indexing policy that makes a previously excluded document eligible.

- An explicit user request to refresh or rebuild an index.

### Reprocessing decisions

| **Change** | **Expected behavior** |
| --- | --- |
| New eligible file | Process and index |
| Content changed | Re-extract and rebuild affected derived records |
| Rename with confidently identified same source | Update source metadata; avoid reprocessing if the content and pipeline remain valid |
| Move outside permitted scope | Stop access and apply the defined retirement/deletion policy |
| Extractor version changed | Reprocess if the new version affects extracted output |
| Embedding model changed | Recompute embeddings where applicable; do not assume text extraction must be repeated |
| Temporary read failure | Retry within the configured policy |
| Unsupported format | Record the reason and skip until relevant conditions change |
| Explicit index rebuild | Rebuild within the configured scope and resource limits |

A change to the embedding model should not automatically require re-reading every source document if trusted, versioned extracted text is still available and valid. Similarly, a change to document extraction may invalidate text chunks and all downstream embeddings.

The implementation should model these dependencies explicitly instead of treating the entire pipeline as one indivisible operation.

## 04.16.08 Consistency between source, extracted text and embeddings

Derived data must be associated with the exact source version and processing configuration from which it was produced.

A logical processing record should identify:

- The source version or fingerprint.

- The extraction implementation version.

- The normalization and chunking configuration.

- The embedding model and version, when applicable.

- The completion status.

- The time of processing.

- The relevant error or warning information.

### Required consistency rules

1. Do not expose partially written derived data as a completed current index.

2. Do not mix chunks from different source versions under one current document version.

3. Do not mix embeddings generated by incompatible models without explicit versioning and compatible retrieval logic.

4. Do not mark an index current if source validation fails.

5. If processing fails, preserve the previous derived version only according to an explicit stale-content policy.

6. Retrieval must not silently treat stale content as current evidence.

7. Updating derived data must not grant new filesystem permissions.

### Atomic publication

Where practical, process a new version separately and publish it only after the required steps succeed. In PostgreSQL, this may mean storing a new processing-version record and switching the active version in a short transaction.

The team must define what happens when a source changes while indexing is underway. The safest baseline is to validate the source again before publication and retry or mark the result stale if the source version no longer matches.

The database transaction can make publication of derived records consistent, but it cannot make the Windows source file and PostgreSQL update one atomic operation. That gap must be handled through source revalidation and recovery.

## 04.16.09 Rename, move and deletion handling

Document changes must not be interpreted solely by matching filenames.

### Rename or move

A rename may preserve content but change the source path. NEXUS should update the source reference only when the implementation has sufficient evidence that the file is the same logical source.

If identity cannot be established reliably, treat the file as a new candidate and retire the old source reference according to policy.

Moving a document between authorized and unauthorized directories is a scope change, not merely a cosmetic path update. The old index must not remain retrievable through a scope the user no longer controls.

### Missing source

A failed scan or offline device must not cause the system to mark every unseen file as deleted.

Use a completed, successful discovery pass as evidence for absence. If the scan was interrupted, permissions changed or the device disconnected, preserve the appropriate uncertain or stale status.

### Deletion

When a source is confirmed deleted or removed from the permitted scope:

- Prevent new retrieval through the old source reference.

- Retire or delete the associated index according to the configured retention policy.

- Invalidate applicable caches and search entries.

- Handle embeddings and extracted text as derived data subject to the same access restrictions.

- Record the required audit event without logging the document contents.

- Avoid reintroducing deleted content during later index rebuilds or backup restoration.

The exact retention period and whether stale derived data may be retained for recovery remain open decisions.

## 04.16.10 Index scheduling and resource limits

Indexing is background work. It must not starve interactive computer tasks, model inference or the other developers' requests.

### Scheduling policy

- Assign indexing a background workload class.

- Use the existing scheduler and fair resource controls where applicable.

- Apply bounded indexing queues.

- Limit concurrent extraction and embedding generation.

- Enforce per-device limits on file discovery and reading.

- Respect file-size, extraction-time and output-size limits.

- Pause or defer indexing when host resource pressure exceeds configured thresholds.

- Avoid occupying an execution worker while a document is waiting for a device or an external condition.

- Give interactive tasks appropriate access to shared inference capacity, subject to the agreed fairness policy.

Indexing should not silently increase its priority simply because many documents are waiting. If a backlog persists, the team should measure it and adjust capacity or indexing scope deliberately.

### Resource controls

| **Resource** | **Required control** |
| --- | --- |
| Disk | Bound derived index storage and temporary files |
| CPU and RAM | Limit concurrent extraction and parsing |
| GPU/VRAM | Bound embedding or inference concurrency where GPU acceleration is used |
| PostgreSQL | Use bounded batches and short transactions |
| Windows bridge | Limit concurrent filesystem operations |
| Network | Bound data transferred from each device |
| Queue | Define maximum pending indexing work |
| Parser | Enforce size and time limits; consider isolation for risky formats |

Exact numerical limits should be established from representative files on the actual host, rather than invented before the first benchmark.

## 04.16.11 Recovery and failure handling

Indexing must remain recoverable if the backend, bridge, database or model runtime restarts.

### Recovery requirements

- A task that was queued but not started may be reconsidered after restart.

- An expired worker claim does not prove an earlier processing attempt had no effect.

- Partial derived records must not be presented as a completed index.

- Reprocessing should use stable job or operation identifiers where appropriate.

- Retrying a parser failure must respect retry limits.

- A model or embedding runtime outage must not invalidate otherwise usable source documents.

- A bridge disconnect must not be interpreted as proof that source files were deleted.

- Database restore must not blindly reactivate stale or unauthorized index records.

For a crash during publication, the recovery process should determine whether the new index version was committed. If it was not, it should safely resume or repeat the necessary processing. If it was committed, it should avoid publishing a duplicate active version.

### Error categories

Proposed stable errors include:

- INDEX_SOURCE_UNAVAILABLE

- INDEX_SOURCE_CHANGED

- INDEX_SCOPE_DENIED

- INDEX_FORMAT_UNSUPPORTED

- INDEX_EXTRACTION_FAILED

- INDEX_RESOURCE_LIMIT_EXCEEDED

- INDEX_RUNTIME_UNAVAILABLE

- INDEX_PUBLICATION_FAILED

- INDEX_OUTCOME_UNCERTAIN

The exact catalogue should be aligned with the shared error conventions from Section 04.08.

## 04.16.12 Security and privacy requirements

Indexing increases the amount of derived content NEXUS stores. Extracted text, chunks, embeddings, fingerprints and source metadata may reveal information about the original documents.

Required controls:

- Index only explicitly configured directories.

- Validate directory scope on the Windows bridge.

- Authenticate and authorize indexing requests.

- Apply user and project scope filters before returning index results.

- Treat extracted document text as untrusted content.

- Do not execute macros, scripts or embedded active content.

- Avoid logging document contents and embeddings by default.

- Protect stored indexes and backups using the defined data-access controls.

- Invalidate cached results after access revocation or deletion.

- Do not assume a content fingerprint is harmless; it may still reveal information about the source.

- Keep indexing disabled for a directory if its access policy cannot be validated.

A directory becoming unauthorized must block retrieval immediately according to the applicable policy, even if background cleanup has not yet removed every derived record.

## 04.16.13 Testing strategy

| **Test** | **Expected result** |
| --- | --- |
| New eligible document | Indexed successfully |
| Unchanged document | Not unnecessarily reprocessed |
| File content changes | Prior index becomes stale and a new version is processed |
| File changes during extraction | Old processing result is not incorrectly published as current |
| Extractor version changes | Affected documents are reprocessed |
| Embedding model changes | Embeddings are rebuilt as required without unnecessary extraction |
| Rename within scope | Source reference updates only when identity is sufficiently established |
| Move outside scope | Old reference becomes inaccessible |
| Interrupted directory scan | Unseen files are not incorrectly treated as deleted |
| Confirmed file deletion | Active retrieval no longer returns the deleted source |
| Unsupported document | Error is recorded without endless retries |
| Oversized document | Resource limits are enforced |
| Bridge disconnect | Indexing pauses or recovers without false deletion |
| Backend restart | Partial processing is recovered safely |
| Duplicate indexing job | Duplicate work is controlled and only one valid active version is published |
| Unauthorized retrieval | No indexed content is exposed |
| Deleted memory or source with cached results | Cache invalidation prevents stale exposure |

### Performance measurements

Record:

- Discovery duration per directory.

- Number of files scanned and changed.

- Percentage of files requiring reprocessing.

- Extraction and embedding duration.

- Index publication duration.

- Queue wait time.

- Resource consumption.

- Failed, stale and unsupported document counts.

- Index freshness and retrieval quality.

The team should compare an initial full index with repeated incremental runs. The expected benefit is that an unchanged directory can be checked without repeatedly extracting and embedding every document.

## 04.16.14 Implementation priorities

P0 — Core document workflows

On-demand processing first

- Secure scoped file search and document reading.

- Bounded extraction and explicit supported formats.

- Source references and provenance.

- Safe handling of files that change during reading.

- No permanent document indexing required.

P1 — Incremental indexing

Add only after the core is reliable

- Metadata and source-version tracking.

- Change detection and incremental reprocessing.

- Versioned extracted text and embeddings.

- Deletion, revocation and cache invalidation.

- Background scheduling and restart recovery.

P2 — Advanced indexing

Defer until evidence justifies it

- Large-scale indexing.

- OCR and additional document formats.

- Filesystem event-based monitoring.

- Advanced deduplication and cross-document indexing.

- More sophisticated index retention and storage optimization.

## 04.16.15 Open decisions

| **Decision** | **Evidence needed** |
| --- | --- |
| Whether persistent indexing belongs in the MVP | Measure on-demand search and retrieval first |
| Default indexed directories | Agreed directory permissions and user experience |
| Supported formats | Extraction-quality and security tests |
| Change-detection strategy | Filesystem behavior and performance benchmarks |
| Fingerprint method | Reliability, cost and privacy assessment |
| Index storage and versioning | Data volume and update workload |
| Embedding implementation | Model/runtime compatibility and retrieval evaluation |
| Stale-content retention | Security and data-lifecycle policy |
| Indexing concurrency and queue size | Three-user workload measurements |
| File event monitoring versus periodic scans | Correctness, reliability and resource comparisons |

## 04.16.16 Definition of done

- Indexed sources are tied to an authorized user, device and directory scope.

- Document metadata and processing versions are tracked.

- Source changes cannot silently leave an index marked current.

- Reprocessing is incremental and bounded.

- Extracted text and embeddings remain consistent with the published source version.

- Rename, move, deletion and failed-scan behavior are defined.

- Recovery does not publish partial or stale data as current.

- Unauthorized or deleted content cannot be retrieved through stale indexes or caches.

- Indexing respects resource limits and does not starve interactive tasks.

- Automated tests cover change detection, recovery, privacy and concurrency.

- Index freshness, resource consumption and processing failures are measurable.

Section exit criterion: NEXUS can optionally maintain a current, scoped document index without repeatedly processing unchanged files or exposing stale and unauthorized content.
