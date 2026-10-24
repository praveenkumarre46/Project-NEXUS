## 03.34.1 Purpose

NEXUS should not behave like a stateless command-line wrapper that forgets useful information after every task. It should retain relevant, user-controlled knowledge about preferences, projects and ongoing work, then retrieve that knowledge when it helps with a new request.

However, memory creates risks. Information can become stale, different users can have conflicting preferences, project details can leak across access boundaries, and a model can mistake an old assumption for a confirmed fact.

This section defines how NEXUS stores, retrieves, ranks, combines and retires persistent context.

The design builds on:

## Section 03.14 — Memory, Context Retrieval and Personalization Architecture.

## Section 03.33 — Document Processing Pipeline and Context Limits.

## Section 03.11 — Authentication and Authorization.

## Section 03.23 — AI Safety and Tool Governance.

Core design rule: memory can improve relevance, but it never grants access, overrides current instructions or replaces authorization checks.

## 03.34.02 Context source classification

NEXUS should maintain four logically distinct sources of context.

Personal memory

User-approved preferences and durable facts relevant to future interactions.

Example: a user prefers concise task summaries.

Project context

Information about a specific project, its decisions, constraints and progress.

Example: the current project uses FastAPI and PostgreSQL.

Task history

Recorded requests, execution steps, results, failures and recovery outcomes.

Example: a previous file-creation operation ended with an uncertain outcome.

Current retrieved evidence

Content extracted from documents or other sources authorized for the current task.

Example: a passage from a design document selected for summarization.

These categories may use common retrieval infrastructure, but they must retain their distinct ownership, source, retention and access rules.

A task-history record is not automatically a memory. A document is not automatically a project fact. A personal preference must not become a shared project rule without an explicit, authorized action.

## 03.34.03 Memory scope and ownership

Every persistent memory must have a defined access scope.

The initial proposal is:

- Personal: visible only to the owning user.

- Project: visible only to explicitly authorized project members, if project sharing is implemented.

- System configuration: controlled application settings, not ordinary AI memory.

Shared project memory remains an open product decision. Until membership, ownership and revocation rules are implemented, NEXUS should default to private user memory.

### Required memory metadata

| **Field** | **Purpose** |
| --- | --- |
| memory_id | Stable identifier |
| owner_user_id | User who owns the memory |
| scope_type | Personal or an explicitly supported shared scope |
| scope_id | Scope identifier, where applicable |
| category | Preference, project fact, decision or another defined category |
| content | Stored knowledge in a bounded representation |
| source_type | User statement, confirmed decision or another approved source |
| source_reference | Optional reference to the originating interaction or artifact |
| created_at | Creation time |
| updated_at | Last update time |
| valid_until | Optional expiry for time-sensitive information |
| status | Active, archived or deleted, according to the lifecycle model |

These are logical fields, not a finalized database migration. Sensitive content should not be copied into metadata merely to improve searchability.

A memory ID is never proof that the requester owns that memory. Every read, update and deletion must enforce authorization against the authenticated user and the memory's actual scope.

## 03.34.04 Memory creation and lifecycle

NEXUS should not automatically save every statement, document or model-generated conclusion. Persistent memory should be deliberate, traceable and correctable.

### Proposed lifecycle

1

Candidate identified

A user requests a save, or NEXUS identifies information that may be useful later.

2

Validate and classify

Determine the source, ownership, scope, sensitivity and likely usefulness.

3

Save or ask

Save an explicitly requested, permitted memory; clarify ambiguous scope or uncertain content.

4

Retrieve when relevant

Apply authorization and relevance checks before adding memory to task context.

5

Review and correct

Allow the owner to inspect, update or archive inaccurate and outdated memories.

6

Delete or expire

Remove the memory from active retrieval and apply the defined retention and deletion rules.

### What should be saved?

Good candidates include:

- Explicitly requested preferences.

- Confirmed project decisions and constraints.

- Durable facts that are likely to improve future assistance.

- Ongoing project state that the user wants NEXUS to retain.

Poor candidates include:

- Temporary information that will quickly become irrelevant.

- Unverified conclusions inferred by the model.

- Full document contents when a short, sourced summary is sufficient.

- Credentials, access tokens and other secrets.

- Information that the user has not authorized NEXUS to retain.

If the user explicitly requests saving information, NEXUS should still validate the request against its privacy and security rules. A request to remember a fact does not make it appropriate to store a secret in ordinary memory.

### Memory provenance

Each memory should preserve enough provenance to explain why it exists. For example, a stored project decision should be distinguishable from a tentative suggestion generated during brainstorming.

The system should not turn “we could use PostgreSQL” into “the project uses PostgreSQL” unless that decision has actually been confirmed.

## 03.34.05 Retrieval architecture

The existing design favors hybrid retrieval: combining exact-term search with semantic similarity. The memory service should expose one retrieval interface while allowing the underlying retrieval strategy to evolve.

### Proposed retrieval pipeline

1. Authenticate the requester.

2. Determine the permitted personal or project scopes.

3. Filter records by ownership, scope and active status.

4. Retrieve lexical candidates for exact names, identifiers and phrases.

5. Retrieve semantic candidates for conceptually related information, if available.

6. Merge candidates and remove duplicates.

7. Rank them using relevance, freshness, provenance and conflict signals.

8. Apply a context budget.

9. Return the selected memories with source references and status metadata.

Authorization filtering must happen before content is exposed to the model. Similarity ranking cannot make an otherwise inaccessible memory eligible for retrieval.

### Lexical retrieval

Lexical search is useful when the request contains:

- Exact project names.

- Error codes.

- File names.

- API routes or identifiers.

- Specific configuration keys.

- Distinctive phrases from previous decisions.

A PostgreSQL full-text search implementation is a reasonable starting point. Its exact indexing and ranking configuration should be tested against representative queries.

### Semantic retrieval

Semantic retrieval can help when the user describes an idea differently from how it was originally recorded.

For example, a memory about “resuming an interrupted file operation safely” may be relevant to a question about “what to do after a lost write response.”

A local embedding model is a candidate for semantic retrieval, consistent with the project's local-first constraint. The specific model, runtime and embedding storage approach remain open pending hardware and quality benchmarks.

### Combining the results

The retrieval layer should normalize and combine lexical and semantic candidates rather than assume that either score is directly comparable to the other.

A possible approach is rank-based fusion, followed by relevance and freshness adjustments. This is a proposed method, not a confirmed algorithm.

Avoid introducing a separate vector database before measuring whether PostgreSQL-based retrieval meets the MVP's quality and performance needs.

## 03.34.06 Ranking, freshness and conflicting memories

Retrieval relevance alone is not enough. A highly similar memory can be outdated, uncertain or contradicted by a newer confirmed decision.

### Proposed ranking signals

| **Signal** | **Intended use** |
| --- | --- |
| Query relevance | How closely the memory matches the current request |
| Exact identifier match | Prioritize exact names, error codes and project identifiers when relevant |
| Source confidence | Distinguish confirmed decisions from tentative suggestions |
| Freshness | Reduce the influence of time-sensitive information that may have changed |
| Current validity | Exclude deleted, expired or superseded records from ordinary retrieval |
| Scope match | Prefer the relevant project or personal context after access checks |
| Duplication | Avoid spending context budget on repeated information |

The ranking implementation must not allow a relevance score to override an access denial or a known contradiction.

### Handling conflicts

Suppose NEXUS has two memories:

- An earlier project note says the service uses SQLite.

- A later confirmed decision says the service uses PostgreSQL.

The system should not simply return both as equally current facts. It should determine whether the later decision explicitly supersedes the earlier one and retain the provenance of that change.

Proposed rules:

1. Preserve confirmed historical decisions when they matter for understanding project history.

2. Mark superseded information as inactive for ordinary current-state retrieval.

3. Do not resolve genuine ambiguity solely by choosing the most recent timestamp.

4. Ask for clarification when conflicting information cannot be resolved safely.

5. Do not let a model-generated inference silently overwrite a confirmed fact.

6. Retain enough history to explain important changes, subject to the deletion and retention policy.

### Time-sensitive memory

Some information should expire or be revalidated. A temporary task status, short-lived configuration or pending decision may no longer be accurate after a defined period.

The system should support optional expiry or revalidation rules where useful. It should not impose the same expiry policy on every memory category.

## 03.34.07 Context assembly for an individual request

The context builder combines information from several sources into a bounded package for the model.

It must not indiscriminately concatenate the user's entire history, every memory, all task logs and all documents.

### Proposed context assembly order

01

Current request

The authenticated user's immediate instruction and relevant request metadata.

02

Execution constraints

Permitted target device, available tools, policy restrictions and applicable task state.

03

Relevant project context

Authorized current decisions, project constraints and active work.

04

Relevant personal memory

Only preferences and facts useful to this request.

05

Task history

Relevant previous outcomes, failures or unresolved operations.

06

Current document evidence

Selected excerpts with source references, if the task requires them.

07

Budget and consistency checks

Deduplicate, resolve known supersession, bound context and preserve source labels.

This is a logical sequence, not a rule that every request must include every source. A simple file search may need no personal memory or document excerpts beyond the search parameters.

### Context item contract

Each selected item should retain:

- Source category.

- Source identifier or reference.

- Relevant content.

- Scope and authorization status.

- Provenance or confidence metadata where applicable.

- Freshness or validity information when relevant.

The final prompt can format these items for the chosen model, but the application must preserve the source metadata outside the prompt so that results can be audited and citations validated.

### Conflicting instructions

Current user instructions, stored preferences and project memories may differ. NEXUS must not treat a remembered preference as more authoritative than a clear current request.

For example, if a user's stored preference is for short answers but the user now requests a detailed technical specification, the current request should guide the response.

Security policy is separate from this preference hierarchy. Neither the current request nor stored memory can override hard prohibitions.

## 03.34.08 Memory access, inspection and correction

Users need practical control over what NEXUS remembers.

The existing API proposal includes endpoints for listing, viewing, creating, updating and deleting memory. Their final schemas remain open, but the following behaviors are required.

### Proposed CLI experience

nexus memory list

nexus memory show <memory-id>

nexus memory update <memory-id>

nexus memory delete <memory-id>

These commands are illustrative. The update interaction, confirmation behavior and output format must be specified before implementation.

### Required behavior

- List only memories the authenticated user is authorized to see.

- Display enough provenance and scope information for the user to recognize a memory.

- Allow corrections without silently changing unrelated memories.

- Require appropriate confirmation for destructive operations.

- Reject attempts to update or delete another user's memory.

- Ensure deleted memories are excluded from active retrieval.

- Invalidate relevant caches and indexes after changes.

- Avoid echoing sensitive content unnecessarily in command output or logs.

A memory update should preserve a clear distinction between correcting a current fact and recording a new historical decision.

### Deletion semantics

The product must clearly distinguish active-memory deletion from deletion of task history, security audit events and backups.

Deleting a memory should remove it from active retrieval and applicable indexes. Any retained backup copies or audit records must follow an explicitly documented retention policy. The system must not claim that all copies have been permanently erased if that has not been established.

## 03.34.09 Database and index design

The existing PostgreSQL architecture can support the initial memory lifecycle without introducing another database service.

The following logical entities are proposed:

| **Entity** | **Responsibility** |
| --- | --- |
| memories | Current memory content, owner, scope, status and provenance |
| memory_versions | Optional history of corrections and superseded values |
| memory_embeddings | Optional semantic vectors associated with memory versions |
| projects | Project identity and metadata, if project-level memory is enabled |
| project_memberships | Explicit project access, if shared memory is implemented |
| memory_retrieval_events | Optional bounded diagnostics for evaluating retrieval behavior |

These are logical entities, not a finalized schema. The MVP may need fewer tables.

### Database constraints

- Enforce memory ownership and required scope fields.

- Index records used frequently for owner- and scope-filtered retrieval.

- Exclude inactive or deleted records from ordinary retrieval queries.

- Ensure an embedding belongs to the correct memory version.

- Prevent duplicate records where a stable source identifier and category can establish duplication.

- Apply updates and relevant index invalidation consistently.

- Keep sensitive content out of diagnostic event payloads.

If a separate vector index is introduced later, it must not become an independent authorization authority. Results from that index must be checked against current authoritative records and permissions.

## 03.34.10 Privacy, retention and isolation

Persistent memory can be more sensitive than an individual task because it aggregates information across time. Its retention and access rules must be explicit.

### Required controls

- Default to private user memory.

- Do not share project memory until membership and authorization are implemented.

- Avoid saving secrets and unnecessary raw document content.

- Do not log full memories or complete retrieval prompts by default.

- Apply access checks before content enters the model context.

- Invalidate caches after updates, deletions and permission changes.

- Define separate retention policies for memory, task history, audit events, logs and backups.

- Ensure restored backups do not silently reactivate revoked access or deleted memories in active retrieval.

- Test cross-user isolation through the API, database queries, caches and semantic retrieval.

A shared backend does not imply shared personal context. Each developer must be able to use NEXUS on their own Windows computer without exposing their private memories to other team members.

## 03.34.11 Evaluation and testing

Memory quality should be measured rather than judged only by a few successful demonstrations.

### Functional tests

- Explicitly save a permitted memory and retrieve it later.

- List, inspect, correct and delete a memory.

- Verify that deleted memories are absent from active retrieval.

- Confirm that task history and memory remain separate.

- Verify that a new confirmed decision supersedes an older decision when appropriate.

- Check that expired or inactive memories are not presented as current facts.

- Confirm that memory unavailable or retrieval failure does not silently invent context.

### Security tests

- User A cannot retrieve, modify or delete User B's memories.

- A forged memory ID does not bypass ownership checks.

- Semantic retrieval cannot expose content outside the authorized scope.

- Prompt injection in stored memory cannot grant permissions.

- A revoked project membership, if sharing is supported, prevents further retrieval.

- Cache invalidation prevents recently deleted or restricted content from appearing.

- A database restore does not silently reactivate revoked access.

### Quality evaluation

Create a fixed test set containing:

- Exact identifier lookups.

- Paraphrased queries.

- Relevant versus irrelevant memories.

- Outdated and superseded facts.

- Conflicting facts with different provenance.

- Requests where no memory should be retrieved.

- Requests where personal and project scopes must remain separate.

Measure retrieval relevance, source accuracy, stale-memory retrieval, unauthorized exposure and context size.

The team should not optimize only for recall. Retrieving more memories is not beneficial if it increases privacy risk or supplies irrelevant and contradictory context.

## 03.34.12 Implementation priorities

P0

Required foundation

- User-scoped memory records.

- Explicit save, list, inspect, update and delete operations.

- Provenance and scope metadata.

- Authorization before retrieval.

- Bounded context assembly.

- Clear separation between memory, task history and current documents.

- Tests for cross-user isolation and deletion from active retrieval.

P1

Quality and personalization

- Hybrid lexical and semantic retrieval.

- Conflict and freshness handling.

- Memory versioning where useful.

- Retrieval evaluation and source-grounded context diagnostics.

- Cache invalidation and controlled retention.

P2

Later expansion

- Shared project memory with membership controls.

- Advanced ranking and automated revalidation.

- Larger persistent document indexes.

- More sophisticated memory consolidation workflows.

## 03.34.13 Open decisions

The team still needs to decide:

1. Whether shared project memory is in the initial release.

2. Which memory categories can be saved automatically, if any.

3. How the CLI confirms ambiguous save requests.

4. Which local embedding model and retrieval implementation to use.

5. How to detect and resolve conflicting memories.

6. Which memory types expire and how expiry is determined.

7. Whether version history is retained for all memories or only selected categories.

8. How long task history, audit records and memory-related diagnostics are retained.

9. How deleted memories interact with backups and recovery.

10. What quality thresholds must be met before semantic retrieval is enabled by default.

## 03.34.14 Definition of done

- Memory ownership and access scope are enforced.

- Users can inspect, correct and delete their own memories.

- Provenance and relevant freshness information are preserved.

- Retrieval is bounded and respects authorization before content is exposed.

- Known superseded information is not presented as the current truth.

- Context assembly preserves source distinctions and obeys the model's budget.

- Memory, task history and document evidence remain separate.

- Cache and index invalidation work after updates, deletion and access revocation.

- Retrieval quality and isolation are evaluated using repeatable tests.

- Retention and deletion promises match actual system behavior.

Recommended engineering decision: implement user-scoped, explicitly managed memory first, then add hybrid retrieval and better ranking behind a stable interface. Keep personal memory, project decisions, execution history and current document evidence distinct throughout retrieval and context assembly.
