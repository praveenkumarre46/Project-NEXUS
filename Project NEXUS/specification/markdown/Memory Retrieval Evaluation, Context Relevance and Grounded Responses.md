## 04.15.01 Purpose

NEXUS must do more than store information. It must retrieve the right information for the current request, respect who is allowed to access it, distinguish current facts from outdated ones and avoid presenting unsupported conclusions as established facts.

This section defines how the team will evaluate:

- Personal memory retrieval.

- Project-context retrieval.

- Task-history lookup.

- Document evidence selection.

- Freshness, conflicts and provenance.

- Grounding and factual accuracy of model responses.

- Privacy and isolation during retrieval.

The central rule is that retrieval relevance, access authorization and factual grounding are three separate requirements.

A highly relevant memory must not be exposed to an unauthorized user. An authorized memory must not be treated as current if it has been superseded. A fluent answer must not be considered grounded merely because some retrieved text resembles the answer.

## 04.15.02 Context sources and their boundaries

NEXUS should maintain distinct logical sources even if some share PostgreSQL infrastructure.

Personal memory

User-confirmed preferences, ongoing work and durable facts. Private to its owner by default.

Project context

Project decisions, technical constraints and shared information, subject to explicit project access rules.

Task history

Persisted requests, step outcomes, errors and verified execution results. History is not automatically personal memory.

Current evidence

Documents and tool results retrieved for the current task, with source references and applicable permissions.

Each retrieved item should retain its source category, ownership or access scope, provenance, freshness information and reference ID.

A memory record must not automatically grant access to the document or task from which it originated. If the original resource is no longer accessible, NEXUS must apply the documented rules for retaining and using derived context rather than assuming the old reference grants continued access.

## 04.15.03 Retrieval pipeline

The retrieval process should be testable as a sequence of stages.

1. Resolve request and identity

2. Filter by authorized scope

3. Retrieve candidate items

Lexical, semantic or direct ID lookup

4. Rank, deduplicate and check freshness

5. Apply context budget and preserve provenance

6. Generate and validate the response

Authorization filtering must occur before unauthorized content is exposed to the model. Filtering results only after sending them to inference is too late.

The retrieval layer should also support an explicit no relevant result outcome. It must not force a match simply because the context builder needs to return something.

## 04.15.04 Retrieval strategies and ranking

NEXUS will use a hybrid retrieval approach, combining lexical matching with semantic retrieval where useful.

### Lexical retrieval

Lexical retrieval is useful for exact names, identifiers, filenames, error codes and technical terms. For example, a search for a specific task ID should not depend on embedding similarity.

### Semantic retrieval

Semantic retrieval helps when the user's wording differs from the stored wording. For example, a request about “the decision we made about the inference computer” may relate to a memory that uses the phrase “designated team host.”

Semantic similarity is a candidate-generation and ranking signal, not proof that two statements mean the same thing.

### Proposed ranking signals

| **Signal** | **Purpose** |
| --- | --- |
| Query relevance | How closely the item matches the current request |
| Exact identifier match | Prioritize an exact task, device, project or document reference |
| Provenance | Distinguish confirmed decisions from suggestions and inferences |
| Freshness | Prefer information that remains valid for the relevant time |
| Scope | Restrict results to the current authorized user or project |
| Conflict status | Avoid treating superseded or contradictory facts as settled |
| Duplication | Prevent repeated copies from consuming the context budget |

The initial implementation should prioritize correct access filtering and reliable lexical search. Semantic retrieval should be added behind an interface and evaluated against the same dataset.

Recommended implementation order: PostgreSQL lexical retrieval first, then local embeddings and hybrid ranking if evaluation demonstrates a meaningful improvement. A separate vector database is not a prerequisite for the MVP.

## 04.15.05 Freshness, conflicting facts and superseded decisions

Memory retrieval must account for facts that change over time.

Examples include:

- A project changes its database schema.

- A task is completed or cancelled.

- A previously approved tool is disabled.

- A user corrects a stored preference.

- An older architecture decision is replaced by a newer one.

The system should distinguish at least three concepts:

- Creation time: when the memory was recorded.

- Update time: when the stored record was last changed.

- Validity: whether the information is still considered applicable.

A recently updated record is not necessarily factually correct, and an older record is not necessarily obsolete. Ranking must use provenance and validity information rather than timestamps alone.

### Conflict-handling rules

1. Prefer an explicitly confirmed correction over a superseded value when the relationship is clear.

2. Do not silently merge contradictory facts.

3. If two conflicting values remain plausible, ask for clarification when the difference affects the answer or execution.

4. Do not turn a tentative suggestion into a confirmed decision.

5. Revalidate time-sensitive facts before relying on them for consequential operations.

6. Treat current authorization, device status and approval state as authoritative application data, not as facts inferred from memory.

For project decisions, a version or supersession relationship may be useful. For simple personal preferences, a correction and update timestamp may be sufficient. The team should choose the simplest representation that supports the required behavior.

## 04.15.06 Context assembly and token budgeting

Retrieval may return more relevant items than the model can use effectively. The context builder must select a bounded subset while preserving critical constraints and provenance.

The context builder should consider:

- The current request and explicit constraints.

- Relevant confirmed project decisions.

- Relevant personal preferences, if appropriate.

- Required task history or current execution state.

- Current document excerpts and tool evidence.

- Contradictions, uncertainty and source references.

- The model's available context and output budget.

It should not automatically include the user's entire memory, every previous task or all contents of a selected document.

### Context selection rules

- Enforce access scope before ranking and assembly.

- Prefer evidence directly relevant to the current request.

- Preserve exact identifiers and critical constraints.

- Deduplicate overlapping information.

- Include source references and relevant timestamps.

- Exclude superseded information unless needed to explain a conflict.

- Do not silently truncate a critical instruction or source excerpt.

- If the available context is insufficient, narrow the task or ask a clarifying question.

Context assembly should be a deterministic, testable application component wherever possible. The model should not decide which users' records it is permitted to see.

## 04.15.07 Grounded responses and evidence attribution

When NEXUS answers questions about stored context or retrieved documents, it should distinguish supported facts from interpretation and uncertainty.

### Response evidence categories

| **Category** | **Meaning** | **Expected behavior** |
| --- | --- | --- |
| Directly supported | Source explicitly states the fact | Answer with the appropriate source reference |
| Supported synthesis | Multiple supplied sources jointly support the conclusion | Explain the conclusion and retain the relevant references |
| Inference | Conclusion goes beyond what sources explicitly state | Label the inference clearly |
| Conflicting evidence | Sources disagree | Describe the conflict or ask for clarification |
| Insufficient evidence | Available sources do not support an answer | State the limitation; do not invent a fact |

The response contract should retain source references when the task requires factual traceability. References must correspond to evidence actually supplied to the model or otherwise verified by the application.

For document questions, the system may retain a document reference and a page, section or other source location where the parser provides reliable metadata. It must not invent page numbers or claim that a source supports a statement when the relevant content was not extracted.

### Validation approach

The response validator should check that:

- Every referenced source exists and was available to the current request.

- Source references do not cross user or project boundaries.

- Required citations or evidence fields are present.

- A source location, when supplied, is valid for the extracted content.

- Unsupported claims are not automatically treated as verified facts.

- The model cannot manufacture a successful task outcome by describing one.

Automated reference validation can verify that a citation points to a real supplied source. It cannot, by itself, prove that the source logically supports every sentence. Semantic grounding therefore needs reviewed evaluation cases in addition to deterministic checks.

## 04.15.08 Retrieval evaluation dataset

Create a fixed dataset with known relevant, irrelevant, outdated, conflicting and unauthorized items. Use synthetic or explicitly approved test records so evaluation does not require exposing private user memory.

Each case should define:

- Query and authenticated user.

- Authorized and unauthorized candidate records.

- Expected relevant records or acceptable result sets.

- Freshness and conflict expectations.

- Expected source references.

- Whether the correct outcome is a result, clarification or no result.

- A deterministic scoring rule where feasible.

### Required evaluation scenarios

| **Scenario** | **Expected behavior** |
| --- | --- |
| Exact task ID lookup | Retrieve the correct record |
| Paraphrased project question | Retrieve the relevant confirmed decision |
| Unrelated query | Do not force irrelevant memories into context |
| Superseded decision | Prefer the valid current decision or expose unresolved conflict |
| Conflicting preferences | Avoid silently inventing a resolution |
| Missing evidence | Admit that sufficient information is unavailable |
| Unauthorized memory match | Exclude it before model context assembly |
| Revoked project membership | Do not retrieve restricted project context |
| Deleted memory | Exclude it from active retrieval and applicable indexes |
| Duplicate memories | Avoid wasting context on repeated information |
| Document prompt injection | Treat instructions inside the document as untrusted content |
| Incorrect source reference | Reject or flag the invalid reference |
| Relevant source with unsupported conclusion | Flag the grounding defect |
| Oversized context | Apply limits without silently omitting critical constraints |

The dataset should cover both exact retrieval and semantic retrieval. High semantic similarity is not sufficient if the retrieved item is outdated, contradictory or unauthorized.

## 04.15.09 Retrieval metrics

Evaluate retrieval quality separately from the quality of the final answer.

| **Metric** | **What it measures** |
| --- | --- |
| Precision at K | How many of the top K retrieved items are relevant |
| Recall at K | How many known relevant items appear in the top K |
| Mean Reciprocal Rank (MRR) | How highly the first relevant item ranks |
| Exact identifier accuracy | Whether exact-reference requests return the correct record |
| Freshness accuracy | Whether current and superseded records are handled correctly |
| Conflict handling rate | Whether contradictory evidence is surfaced appropriately |
| No-result accuracy | Whether the system abstains when no suitable evidence exists |
| Context budget compliance | Whether assembled context remains within configured limits |
| Grounding accuracy | Whether answer claims are supported by the supplied evidence |
| Source-reference validity | Whether references resolve to authorized, real evidence |
| Unauthorized exposure count | Whether any restricted item reaches the wrong context |

For cases with several acceptable relevant results, the expected result set should reflect that. Avoid scoring retrieval solely against one preferred memory if several records legitimately answer the question.

Mandatory privacy gate: zero unauthorized context exposure in the defined isolation test suite. Retrieval relevance scores cannot compensate for a privacy failure.

## 04.15.10 Deletion, correction and cache invalidation

Memory corrections and deletions must affect what NEXUS retrieves, not just what appears in a user-facing list.

When a memory is updated, superseded or deleted, the system should:

1. Persist the authorized change.

2. Update its active status and validity metadata.

3. Update or invalidate corresponding lexical and semantic index entries.

4. Invalidate applicable caches.

5. Ensure new retrieval requests cannot return the obsolete record as active information.

6. Preserve only the history required by the defined retention policy.

7. Record a privacy-safe audit event when required.

The application must define how it handles a memory deletion that occurs while an inference request is already in progress. At minimum, a subsequent request must not retrieve the deleted memory. For sensitive cases, the system should also avoid presenting a response generated from context that has become unauthorized before the response is returned.

Deleting a memory does not automatically mean deleting task history, audit records or every backup copy. These are separate data-lifecycle decisions and must be communicated accurately to users.

### Cache rules

- Cache keys must include the relevant user and scope boundaries.

- Cached results must not bypass current authorization checks.

- Updates, revocations and deletions must invalidate affected entries.

- Cache misses must fall back to the authoritative retrieval path.

- A cache failure must not cause the system to retrieve unrestricted data.

## 04.15.11 Privacy and prompt-injection safeguards

Retrieval increases the amount of information available to a model. That makes scope enforcement and context minimization essential.

Required controls:

- Authenticate the user and resolve the permitted scope before retrieving content.

- Apply ownership and project-membership filters before model exposure.

- Never treat a memory ID as proof of access.

- Avoid placing irrelevant personal information into the prompt.

- Treat documents, memories and tool results as untrusted data.

- Prevent retrieved content from changing system policy, identity or approval state.

- Avoid logging full memory content, prompts or document excerpts by default.

- Ensure diagnostic and evaluation reports do not expose real user records unnecessarily.

- Revalidate permissions when access or membership changes while a task is waiting.

A local embedding or lexical index must not become a separate authorization authority. It may locate candidates, but the authoritative application rules determine which records can be returned.

## 04.15.12 Testing strategy and implementation ownership

| **Work package** | **Owner** | **Deliverable** |
| --- | --- | --- |
| Retrieval evaluation dataset | Developer 3 | Versioned cases and expected result sets |
| Lexical and semantic ranking | Developer 3 | Retrieval implementation and measurable metrics |
| Scope and ownership enforcement | Developer 1 | Authorization checks and isolation tests |
| Source references and grounding | Developer 3 | Response provenance and validation tests |
| Index and cache invalidation | Developer 1 + Developer 3 | Correct update, revocation and deletion behavior |
| Document evidence fixtures | Developer 2 + Developer 3 | Safe test documents and extraction references |
| Cross-user and adversarial review | All three | Security regression results |

### Mandatory tests

- Exact lookup and paraphrased retrieval.

- Irrelevant and no-result cases.

- Superseded and conflicting facts.

- User and project isolation.

- Revocation and deletion.

- Cache invalidation.

- Source-reference correctness.

- Unsupported claims and incorrect citations.

- Prompt injection inside retrieved content.

- Context budget limits.

- Concurrent updates and retrievals.

- Reproducible metrics across dataset versions.

Use deterministic fixtures for retrieval and authorization tests. Run live-model evaluations separately to assess whether generated answers actually use the retrieved evidence correctly.

## 04.15.13 Implementation priorities

P0 — Required foundation

Correct and private retrieval

- User-scoped lexical retrieval.

- Explicit separation of memory, task history and current evidence.

- Provenance and freshness metadata.

- No-result and conflict handling.

- Context-size limits.

- Cross-user isolation and deletion tests.

P1 — Complete MVP capability

Hybrid retrieval and grounding

- Local semantic retrieval.

- Hybrid ranking and deduplication.

- Grounded responses with source references.

- Retrieval evaluation and regression reports.

- Cache/index invalidation.

P2 — Future improvements

Advanced personalization

- Shared project-memory retrieval.

- More advanced ranking and memory consolidation.

- Larger document indexes.

- More sophisticated freshness and conflict resolution.

The initial system should favor trustworthy, scoped retrieval over retrieving a larger number of potentially relevant items. Semantic search should only be promoted when it improves the measured results without compromising isolation or grounding.

## 04.15.14 Open decisions

| **Decision** | **Required evidence** |
| --- | --- |
| Hybrid ranking weights | Fixed retrieval dataset |
| Semantic retrieval implementation | Quality and latency comparison against lexical search |
| Freshness and expiry rules | Defined memory categories and realistic conflict cases |
| Citation format | Available document parser metadata |
| Context budget | Selected model's measured limits |
| Cache design | Workload measurements and invalidation tests |
| Deletion and backup retention | Agreed data-lifecycle policy |
| Project-memory sharing | Explicit membership and authorization model |
| Grounding threshold | Reviewed answer-evidence evaluation set |

## 04.15.15 Definition of done

- Retrieval is scoped before content reaches the model.

- Personal memory, project context, task history and current evidence remain distinct.

- Freshness, provenance and conflicts are handled explicitly.

- The system can return no result rather than force a match.

- Context assembly respects token and privacy budgets.

- Responses can retain valid references to supplied evidence.

- Deleted or revoked information is excluded from subsequent retrieval.

- Retrieval quality and answer grounding are measured separately.

- Unauthorized context exposure remains zero in the defined security suite.

- The evaluation process is reproducible by all three developers.

Section exit criterion: NEXUS can retrieve relevant, authorized and appropriately current information, assemble bounded context, and produce responses whose evidence can be checked.
