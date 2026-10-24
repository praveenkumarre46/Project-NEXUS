## 03.14.1 Purpose

NEXUS should not behave like a stateless chatbot that forgets every project, preference and previous task. It should retain useful information, retrieve the right details when needed, and use them to improve future interactions.

However, remembering everything is neither necessary nor desirable. NEXUS needs controlled memory with explicit ownership, relevance-based retrieval, user control and privacy boundaries.

The design must answer five questions:

- What information is worth remembering?

- Who owns each memory, and who may access it?

- How does NEXUS decide which memories are relevant?

- How can users inspect, correct and delete memories?

- How do we prevent stale or malicious content from influencing actions?

## 03.14.2 Scope and design principles

The architecture separates four kinds of information.

1. Personal memory

User-approved preferences, recurring instructions and facts useful across multiple tasks.

Example: preferred output format or a recurring work preference.

2. Project context

Information associated with a specific project, such as terminology, architecture decisions and known constraints.

Example: a project's approved database technology and current design decisions.

3. Task history

Durable records of task requests, execution steps, approvals and outcomes.

Example: a previous task failed because its target device disconnected.

4. Retrieved external content

Documents and files read during a task. These are source material, not automatically permanent memories.

Example: a design document that NEXUS reads to answer a question.

Core rule: task history, saved memory and source documents are separate data categories. Finding information in one category must not silently grant access to another.

## 03.14.3 Memory lifecycle

### Proposed memory-saving policy

For the MVP:

- Explicit requests such as “remember this project decision” should be supported.

- Automatic saving of every conversation or document should not be enabled by default.

- If a candidate memory is ambiguous, sensitive, contradictory or potentially temporary, NEXUS should ask or avoid saving it automatically.

- Each saved memory should retain its source and timestamps so that it can be reviewed and corrected.

- Repeated statements should not create unlimited duplicate memories.

The exact rules for automatic memory suggestions remain an open product decision.

## 03.14.4 Ownership and access control

Memory isolation is mandatory because NEXUS is a shared system used by three developers.

| **Data scope** | **Default access** |
| --- | --- |
| Personal memory | Its owning user only |
| Private task history | Its owning user only |
| Project memory | Its owner, unless project sharing is explicitly implemented |
| Device-specific context | Authorized operations targeting that registered device |
| Retrieved document contents | Only within the authorized task and user's access scope |
| System configuration | Authorized maintainers, limited to the required administrative functions |

Project memory sharing is not assumed just because teammates are working on the same project. It should be introduced only with explicit ownership and sharing rules.

Enforce access in the application and persistence queries. A memory ID supplied by a client must never be treated as proof that the requester owns that memory.

The model should receive only context the authenticated user is allowed to access. Filtering the results after sending private memories to the model would be too late.

## 03.14.5 Hybrid retrieval architecture

The selected direction is hybrid retrieval. The initial design combines two approaches:

- Lexical retrieval: finds exact words, names, IDs, technical terms and phrases.

- Semantic retrieval: finds conceptually related information even when the wording differs.

For example, a query about “the reason the file creation failed” might benefit from semantic matching, while a query for an exact error code benefits from lexical search.

### Proposed implementation direction

- Use PostgreSQL as the authoritative store for memory records.

- Evaluate PostgreSQL full-text search for lexical retrieval.

- Evaluate a local embedding model for semantic retrieval.

- Choose a compatible vector-storage approach only after a prototype demonstrates a meaningful improvement.

- Keep retrieval behind a service interface so the search implementation can change without modifying the task planner.

A separate vector database is not automatically required. It introduces another service, operational burden and synchronization concerns. The team should compare the simplest PostgreSQL-based design with alternatives using the same evaluation dataset.

### Retrieval safeguards

1. Apply user, project and device scope before ranking results.

2. Limit the number and total size of retrieved items.

3. Prefer current, explicitly confirmed information when it conflicts with old information.

4. Preserve source identifiers so that users can inspect where a result came from.

5. Treat retrieved content as untrusted data, not as executable instructions.

6. Do not use semantic similarity as an authorization mechanism.

A highly similar memory belonging to another user must remain inaccessible.

## 03.14.6 Proposed data model

The following is a logical schema, not final SQL or a migration specification.

| **Entity** | **Important fields** | **Purpose** |
| --- | --- | --- |
| memories | id, owner_user_id, scope, content, category, source_type, source_id, created_at, updated_at, deleted_at | Stores saved memory and ownership |
| memory_versions | id, memory_id, version, content, created_at | Optional history for correcting or reviewing memory changes |
| memory_embeddings | memory_id, model_id, embedding, created_at | Optional semantic retrieval representation |
| projects | id, owner_user_id, name, created_at | Optional project grouping |
| project_memberships | project_id, user_id, role | Required only if explicit project sharing is implemented |

Important design considerations:

- A memory needs a defined owner and scope.

- A project-scoped memory needs a valid project association.

- Semantic representations must be traceable to the memory version from which they were generated.

- Database constraints should prevent duplicate version numbers and invalid ownership relationships.

- Deleting or updating a memory must invalidate its stale retrieval representation.

- Any retention of old versions, audit entries or backups must be documented separately from active-memory deletion.

The final schema depends on whether shared project memory is in the MVP and how semantic retrieval is implemented.

## 03.14.7 Updating, conflicting memories and deletion

### Updating a memory

When a user corrects an existing fact, NEXUS should update the appropriate memory rather than keep returning conflicting copies indefinitely.

The system should preserve enough source information to distinguish a correction from a genuinely different fact. For example, a project changing its database technology is not necessarily a contradiction; it may be a new architectural decision that supersedes the old one.

### Deleting a memory

A deletion workflow should:

1. Authenticate the requester and verify ownership.

2. Mark or remove the memory from active retrieval.

3. Remove or invalidate associated embeddings and search indexes.

4. Prevent stale cached context from reintroducing the deleted memory.

5. Apply the documented retention rules to audit records, version history and backups.

6. Report the deletion status accurately.

Deleting a memory must not silently delete an independently retained task record unless the user explicitly requested that broader deletion and the retention policy permits it.

### Conflicting information

When two sources disagree, NEXUS should not invent certainty. It should consider source, confirmation status, timestamp and scope. If the conflict materially changes an action, it should ask the user before proceeding.

## 03.14.8 Privacy and operational limits

The memory subsystem should:

- Avoid saving entire documents when a short, useful summary is sufficient.

- Avoid storing credentials, access tokens or secrets as ordinary memories.

- Keep personal and project context separated.

- Limit the amount of memory sent to the model per request.

- Avoid logging full memory contents or retrieved documents by default.

- Support memory export and inspection as the design matures.

- Define backup and retention behavior before promising permanent deletion.

- Test that one user cannot retrieve another user's memories through either lexical or semantic search.

## 03.14.9 Testing and acceptance criteria

- Users can explicitly save, inspect, update and delete their own memories.

- Personal memories are isolated across user accounts.

- Project sharing is denied unless explicitly supported and authorized.

- Lexical and semantic retrieval can be evaluated independently.

- Hybrid retrieval improves measured relevance on the team's test set, or the simpler approach is retained.

- Stale or deleted memories are not returned by active retrieval.

- Conflicting facts can be surfaced without silently choosing an unsupported answer.

- Retrieved documents cannot grant permissions or modify policy.

- Retrieval failures produce a clear result instead of fabricated context.

- The amount of context supplied to the model is bounded.

- Memory deletion and retention behavior is documented and tested.

## 03.14.10 Open decisions

The following still need agreement:

- Whether project memory is private by default for the entire MVP or whether any shared project memory is required.

- Whether memory saving is always explicit or can include user-configurable suggestions.

- The initial embedding model and where it runs.

- Whether PostgreSQL alone is sufficient for hybrid retrieval.

- The ranking strategy and relevance thresholds.

- Retention of task history, memory versions, audit records and backups.

- Whether memory export is a P0 or a later feature.

Section exit criterion: the team agrees on memory ownership, saving rules, retrieval boundaries, correction/deletion behavior and a measurable evaluation approach before implementing persistent memory.
