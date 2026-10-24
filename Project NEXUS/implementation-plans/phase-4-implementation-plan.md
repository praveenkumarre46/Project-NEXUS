# Phase 4 (Local AI and Memory) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-4-local-ai-and-memory.md`](../roadmap/phase-4-local-ai-and-memory.md) (Steps 0–25) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2e (P4-00 … P4-25). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal (Gate 4): a validated local model runtime and model (or a documented blocker plus a tested fallback, per 04.28.05) produce structured multi-step plans that the application validates deterministically; user-scoped personal memory with lexical retrieval feeds a bounded, authorized context; model output is always untrusted; and when the model is unavailable the deterministic functions keep working and report honestly.

Decisions settled here: D-56 to D-70 (plus PC-03). Owners are assigned by the team (suggested rotation: BE = Dev B, WB = Dev C, AI = Dev A). The Phase 4 range is D-56 to D-70; earlier drafts of this plan used a wrong range.

Excluded from Phase 4: `read_document` and the document-processing pipeline (Phase 5), shared project memory, multi-user team integration (Phase 6), advanced embedding ranking, GUI automation, backup and restore (Phase 7).

Deliberate deviations and open points, to be confirmed in Sub-Task 1:
- The Roadmap introduces a `WAITING_FOR_CLARIFICATION` task state. The 03.29 state machine has no such state, and `PARTIALLY_SUCCEEDED` must not be added. If clarification needs a state, it enters only through the contract change process (see D-23 and the Phase 3 note), with the state machine and tests updated together. The Planner outcome `CLARIFICATION_REQUIRED` (04.08.06) is the spec-aligned signal.
- The Roadmap memory CLI step says `--json`. The tracker carries D-75 (`--output json`) as Open. Follow the convention D-35 settled in Phase 2 and revisit under D-75.
- The Roadmap Step 21 `--steps` display lists only some step states. The full set is `PENDING, READY, WAITING_FOR_APPROVAL, DISPATCHED, RUNNING, SUCCEEDED, FAILED, REJECTED, UNCERTAIN, CANCELLED` (finding R6).
- Risk-tier naming (Tiers 0–3 in 03.11 and ADR-011 vs five tiers in Product Vision 1.4) follows the Phase 3 decision.
- Gate 4 explicitly allows the fallback path. If the AMD GPU or every candidate model fails, passing with a documented blocker and a tested fallback is valid; ignoring the problem is not.

---

## Sub-Tasks

### Sub-Task 1: Entry check and learning blocks (Steps 0–5)
- **Intent**: Confirm Phase 3 delivered what Phase 4 needs and give the team the shared mental model for local inference, plans, memory, evaluation and performance before any model-adjacent code exists.
- **Expected Outcomes**:
  - Phase 3 Gate 3 unchecked items copied to the tracker's carried-over items with owners. Present from Phase 3: 8-layer policy engine, approval lifecycle, `create_file` and `launch_application` with tests, durable bridge journal, full cancellation, permission CLI, `contracts-v0.3`, D-40 to D-55 ADRs.
  - The Phase 2 carried item "Full Baseline 2" confirmed done, otherwise P4-22 is blocked. D-27, D-29/D-47 and D-38 are at least Provisional. The P0 host-readiness sections 3–6 are assigned to Dev C as a Phase 4 carried item.
  - Learning blocks completed and recorded as short notes (suggested `docs/learning/`):
    - Local inference: runtime, model, execution mode and planning contract are four separate decisions; quantization; structured output vs prose; token limits; why GPU presence alone does not prove acceleration (04.13.08).
    - Plan representation: DAG dependencies, cycles, the 10-row validation pipeline (03.35.5), backend-assigned identifiers, replanning limits.
    - Memory: four context categories, authorization before retrieval, lexical-first hybrid retrieval, conflict rule, context priority order (03.34.07).
    - Evaluation: five layers, hard safety gates, schema validity vs plan correctness vs policy rejection vs goal completion, non-determinism.
    - Performance: six execution phases, p50/p95/p99, unverified AMD GPU, shared 16 GB RAM, `max_concurrent_inference = 1` baseline.
  - Each developer demonstrates the checks in the Roadmap "Verify" lines (for example, naming the four decisions, sketching a valid two-step plan, naming the five evaluation layers).
- **Todo List**:
  - [ ] Entry check, carried items and blocking-ADR confirmation (P4-00).
  - [ ] Learning blocks 1–5 (P4-01 to P4-05).
- **Relevant Context**:
  - Roadmap Steps 0–5; tracker P4-00 … P4-05 and §8
  - Specs: 03.13, 04.13, 04.03, 03.35, 03.34, 03.14, 04.15, 04.14, 03.27
- **Status**: `[ ] pending`

---

### Sub-Task 2: Hardware inventory, runtime selection and smoke test (Steps 6–7; D-56, D-58, D-68, D-70, PC-03)
- **Intent**: Establish the real hardware facts first, then choose and prove a runtime in the intended environment before any model code is written. Closes the P0 host-readiness carried item.
- **Expected Outcomes**:
  - Complete inventory on the designated host: exact AMD GPU model and dedicated VRAM (not `AdapterRAM` alone), driver version, installed acceleration backends (ROCm, DirectML or other), free RAM with Windows, WSL 2 and PostgreSQL running (measured), disk space and I/O speed. All Windows-native steps are flagged.
  - Candidate runtimes checked against their official compatibility lists for that specific GPU and driver, not assumed. Installation tested in WSL 2 and natively on Windows. A single small-model inference records GPU use (confirmed beyond driver reporting), RAM/VRAM and time.
  - If the GPU is unusable, the blocker is documented in full (model, driver, runtime, error), the CPU fallback path is identified and its latency and resource use recorded. This is a valid Gate 4 outcome.
  - `docs/operations/host-readiness.md` sections 3–6 completed (benchmark, combined workload, deployment-location decision closing PC-02 if still open, approval).
  - Provisional ADRs: D-58 (execution mode), D-70 (runtime host location), D-56 (runtime), D-68 (CPU fallback policy). Candidate filters from 04.03.03 applied with a recorded reason for each rejection.
  - PC-03 answered by ADR (shared inference on the designated host vs a model per PC), with a revisit condition.
  - Chosen runtime installed with documented, repeatable steps. Smoke test (one plain-text and one structured-JSON request) passes cold and warm and again after a full restart. The runtime exposes a health or readiness signal. Results in the model-benchmark document.
- **Todo List**:
  - [ ] Hardware inventory, GPU/runtime compatibility and host-readiness sections 3–6; D-58 and D-70 Provisional (P4-06).
  - [ ] Runtime selection, install and smoke test; D-56, D-68, PC-03 (P4-07).
- **Relevant Context**:
  - Roadmap Steps 6–7; tracker P4-06, P4-07; risk P4-R1
  - Specs: 04.13.05, 04.13.08, 03.27.8, 04.03.03, 04.03.06
- **Status**: `[ ] pending`

---

### Sub-Task 3: Evaluation dataset, model benchmark and model selection (Step 8; D-57, D-59, D-67, D-69)
- **Intent**: Pick the smallest model that reliably meets requirements through a repeatable 4-layer evaluation with thresholds agreed in advance.
- **Expected Outcomes**:
  - At least 10 version-controlled evaluation cases (suggested `docs/evaluation/dataset-v1.yaml`) covering straightforward search, multi-step, ambiguous request, unsupported request and an adversarial document, each with input, available tools and schemas, expected plan properties and prohibited behaviours.
  - D-67 pass thresholds (schema-validity rate, safety-gate pass rate, p95 latency) agreed before results are seen, as 04.03.07 requires.
  - Each candidate scored on four layers: A schema validity, B planning correctness (human review), C scope and safety, D resource and latency. Mandatory rejection conditions applied. A failure evaluation (runtime stopped or restarted mid-request) confirms task state is preserved and no false success is reported.
  - Provisional ADRs: D-57 (model, with reasoning against the alternatives), D-59 (context-length limit), D-69 (model lifecycle: propose, review, evaluate against the dataset, roll back; no automatic download or switch of an unreviewed model).
  - If no candidate passes, the blocker is documented in the ADR and the Gate 4 fallback is activated (deterministic functions work, AI-dependent tasks fail with a clear error). Remaining steps continue.
  - All three developers review the safety results.
- **Todo List**:
  - [ ] Build the dataset and agree D-67 thresholds.
  - [ ] Run the four layers per candidate and the failure evaluation.
  - [ ] Record D-57, D-59, D-69 and benchmark results (P4-08).
- **Relevant Context**:
  - Roadmap Step 8; tracker P4-08; risk P4-R2
  - Specs: 04.03.04–07, 03.13.5, 04.13.10, 04.14
- **Status**: `[ ] pending`

---

### Sub-Task 4: Model adapter, inference service and `MockProvider` (Step 9; D-60 baseline)
- **Intent**: The rest of NEXUS calls a stable interface, never runtime-specific endpoints, so changing the model never touches the state machine, policy engine or bridge.
- **Expected Outcomes**:
  - A provider interface (suggested `nexus_core/ai/`, following the repository layout in 04.04.02) with a generate operation that takes system context, user request, structured context and output schema and returns a proposal or raises a typed error (`ModelUnavailable`, `TimeoutError`, `InvalidOutput`, `CapacityExhausted`), plus a cheap readiness check that does not trigger inference.
  - A concrete provider for the D-56 runtime. Runtime-specific calls, authentication and retry logic live only there.
  - Inference lifecycle per 04.13.06: validate the caller, assemble context, enforce token and output budgets (D-59), acquire a concurrency slot (baseline 1), call the runtime, validate the response schema, return the proposal or typed error, record diagnostics. Budget formula per 04.13.07 using the runtime tokenizer where available (verify). No database transaction is held during inference.
  - CPU fallback per D-68: switch is logged and never silently changes model, drops context or skips validation. The runtime starts and stops independently of FastAPI, and its restart does not reset task state.
  - A deterministic `MockProvider` with canned responses. All contract tests and CI use it; no CI run requires a live model.
  - Unit tests with `MockProvider`: valid response, `ModelUnavailable` (task not marked succeeded), timeout, budget exceeded, and a concurrency limit of 1 blocking a second call.
- **Todo List**:
  - [ ] Provider interface, concrete provider and `MockProvider`.
  - [ ] Lifecycle, budgets, concurrency slot and fallback behaviour.
  - [ ] Unit tests (P4-09).
- **Relevant Context**:
  - Roadmap Step 9; tracker P4-09; risks P4-R3, P4-R7
  - Specs: 04.13.04, 04.13.06, 04.13.07, 04.13.08, 04.13.10, 03.13.12
- **Status**: `[ ] pending`

---

### Sub-Task 5: Structured plan contract and plan validation pipeline (Steps 10–11; D-61)
- **Intent**: Every model-generated plan is a proposal that passes deterministic validation. The model cannot choose its own risk level, approval or identifiers.
- **Expected Outcomes**:
  - D-61 settled: the Phase 2 plan schema extended per 03.35.3 (`plan_version, objective, target_device_id, steps[]` with `step_key, tool_name, tool_schema_version, arguments, depends_on[], expected_outcome`, `clarification_required`, backend-assigned `plan_id` and `plan_validation_status`). `depends_on` is a list of step keys. The backend assigns step and operation IDs.
  - Plan provenance persisted (`plan_id`, provider version, planner schema version, created time, validation outcome, revision relationship) in a `plans` table, created by the memory/plan migration in Sub-Task 8 or a dedicated migration. Previous migrations are never edited.
  - Clarification handling aligned with the Planner outcomes `PROPOSED, CLARIFICATION_REQUIRED, UNSUPPORTED`. No operation is dispatched until clarification arrives and the plan is revised. The `WAITING_FOR_CLARIFICATION` question is resolved per the deviations above.
  - Fixtures: valid two-step search-then-create, valid three-step with correct dependencies, cyclic dependency, unknown tool, scope expansion in arguments, and `clarification_required`. Contract tests green; `contracts-v0.4` tagged after PR approval (suggestion).
  - The 10-layer validator extends the Phase 2 validator: schema, tool existence and version, argument validity, dependency graph (cycles and dangling references), capability and stale-report check, policy and risk via the Phase 3 engine, approval requirements (steps that will pause are marked, the plan is not blocked), context budget (D-59), plan bounds (step count, depth, output size from configuration), authentication and ownership.
  - Model-supplied `risk`, `approved` or `user_id` fields are stripped or ignored. An invalid plan is never dispatched and returns a typed validation failure that may lead to clarification or an honest "unsupported" answer, not a workaround.
  - Each layer has at least a pass and a fail test, including a 3-node cycle, unknown tool, invalid argument, step count exceeded and budget exceeded. A mutation check (disable cycle detection) makes a test fail.
- **Todo List**:
  - [ ] Settle D-61, extend the contract, add fixtures and tag `contracts-v0.4` (P4-10).
  - [ ] Implement and test the 10-layer validator (P4-11).
- **Relevant Context**:
  - Roadmap Steps 10–11; tracker P4-10, P4-11
  - Specs: 03.35.3, 03.35.5, 03.35.9, 03.13.6, 04.13.09, 04.08.06
- **Status**: `[ ] pending`

---

### Sub-Task 6: Dependency-aware execution, replanning and grounded responses (Steps 12–13; D-62)
- **Intent**: The worker dispatches steps in dependency order, handles failed prerequisites correctly, replans only within the original scope, and bases every response on persisted evidence.
- **Expected Outcomes**:
  - The Phase 2/3 dispatch pipeline walks the DAG. A step is eligible only after all `depends_on` steps are `SUCCEEDED`; a `FAILED` or `UNCERTAIN` prerequisite blocks it. Sequential dispatch is preferred unless a measured need exists; same-path writes are sequential.
  - D-62 settled: replanning is allowed when a prerequisite returns an unexpected result, within the original scope. It never expands scope, switches devices, bypasses approval or revives a cancelled task. The seven-step replanning process (03.35.8) is followed, with fresh approval when needed. Accepted revisions are persisted and linked to the previous plan with a reason. Planning only performs bounded authorized reads and never modifies the user's computer.
  - Per-step preconditions are checked before dispatch (content to write comes from a verified preceding step, not model memory). Postcondition evidence is persisted after success and used as context for later steps and for replanning (original plan, completed outcomes and the changed condition, not conversational output).
  - Grounded responses cite persisted execution evidence. The response validator rejects a citation to a non-existent source. The classifications `confirmed_from_evidence`, `inferred_plausible`, `no_relevant_evidence`, `contradicted_by_evidence` are distinguished (04.15.07). `PARTIAL_SUCCESS` is a result classification, never a task state (finding R4).
  - If the model is unavailable, tasks awaiting AI planning are held in a recoverable state with a clear status; they are never marked succeeded.
  - Tests: two-step dependency order, failed step 1 blocks step 2, in-scope replan creates a new plan row, scope-expanding replan rejected, cancellation mid-run stops later steps, step 2 receives step 1's verified output, a fabricated citation is rejected, model unavailable stays recoverable.
- **Todo List**:
  - [ ] DAG-aware dispatch, replanning rules and plan persistence; D-62 (P4-12).
  - [ ] Preconditions, postconditions, grounded response assembly and validator (P4-13).
- **Relevant Context**:
  - Roadmap Steps 12–13; tracker P4-12, P4-13; risk P4-R5
  - Specs: 03.35.4, 03.35.6–9, 04.15.07, 03.13.10, 03.34.07
- **Status**: `[ ] pending`

---

### Sub-Task 7: Evaluation pipeline and threshold confirmation (Step 14; D-67)
- **Intent**: Model quality is judged by a repeatable, automated evaluation rather than a demo, and the same pipeline gates every model, prompt or context change.
- **Expected Outcomes**:
  - The dataset from Sub-Task 3 extended to all 13 categories in 04.14.03 (simple, multi-step dependency, ambiguous, unsupported, prompt injection, outdated context, scope adherence, sequential vs concurrent, approval required, cancellation mid-plan, wrong target device, conflicting context, resource limit exceeded), with a held-out set (04.14.11).
  - A scoring pipeline (suggested `scripts/`) that loads the dataset, adapter and configuration, runs each case, captures proposal and validation outcome, scores deterministic criteria, records latency and resources, and writes a machine-readable report. Live-model cases run on the designated host; deterministic contract tests run in CI with `MockProvider`.
  - Report contents per 04.14.07: dataset version, model and runtime versions, configuration versions, per-case and per-category results, hard-gate failures, p50/p95 latency, resource measurements and a baseline comparison.
  - D-67 thresholds confirmed from baseline measurements (the docs propose schema validity ≥ 98% and a safety gate of 100%; the others are set from measurement). The eight hard safety gates run as separate named tests with zero failures allowed. Regression rule: any model, prompt or context change triggers a full run before promotion.
- **Todo List**:
  - [ ] Complete the 13-category dataset and held-out set.
  - [ ] Build the scoring pipeline and sample report.
  - [ ] Confirm D-67 in an ADR (P4-14).
- **Relevant Context**:
  - Roadmap Step 14; tracker P4-14; risk P4-R6
  - Specs: 04.14.02–11, 04.03.04–07
- **Status**: `[ ] pending`

---

### Sub-Task 8: Memory schema, CRUD service and API (Step 15; D-63, D-64)
- **Intent**: User-scoped personal memory exists in PostgreSQL with ownership enforced on every operation, and the full lifecycle is tested.
- **Expected Outcomes**:
  - D-63 (auto-save policy) and D-64 (memory scope) settled as ADRs. The docs recommend explicit-only saves and private user scope for the MVP (03.14.3, 03.34.03).
  - A new migration (previous ones untouched) adds `memories` (id, owner user, scope, category, bounded content, source reference, confirmed flag, timestamps, active flag, optional expiry, provenance notes, version) and, if versioning is implemented, `memory_versions`. `owner_user_id` is NOT NULL; an index supports active-only retrieval. The `plans` table from Sub-Task 5 is included here if it was not created earlier.
  - A memory service with create, list, show, update and delete that checks `owner_user_id` equals the authenticated user before every operation. A memory ID alone is never proof of ownership.
  - Save lifecycle per 03.34.04: validate source, classify, check near-duplicates, insert. No full transcripts and no credentials are saved. Delete sets `active = false` and updates retrieval; retained backups and audit records follow the retention policy and permanence is not claimed. Cached retrieval for the user is invalidated on update or delete.
  - Routes under `/v1`: `POST /v1/memories`, `GET /v1/memories`, `GET /v1/memories/{id}`, `PUT /v1/memories/{id}` and `DELETE /v1/memories/{id}`.
  - Tests: owner filters enforced, another user's ID rejected, deletion removes from active retrieval, near-duplicate check, no secret content in response bodies.
- **Todo List**:
  - [ ] Settle D-63 and D-64.
  - [ ] Migration, service, routes and tests (P4-15).
- **Relevant Context**:
  - Roadmap Step 15; tracker P4-15
  - Specs: 03.34.03, 03.34.04, 03.34.08, 03.14.6, 04.15.10, 03.10
- **Status**: `[ ] pending`

---

### Sub-Task 9: Retrieval, context assembly and semantic retrieval decision (Steps 16–18; D-65, D-66)
- **Intent**: Retrieve only authorized, relevant memory, then assemble a bounded, prioritized context. Add embeddings only if the lexical evaluation proves a gap.
- **Expected Outcomes**:
  - PostgreSQL full-text search over memory content (configuration verified for the installed version). The retrieval pipeline runs authenticate, filter by owner, active and scope, search, rank, apply budget and return results with source metadata. Empty results are allowed and no match is forced.
  - D-66 ranking settled as Provisional: relevance, freshness, confirmation status and provenance. Retrieval quality measured on the evaluation dataset (exact lookup, paraphrase, irrelevant, outdated). Cross-user isolation test (User A never appears for User B, via FTS or cache) is release-blocking.
  - A context builder following the 03.34.07 order: current request and execution constraints, confirmed project-category memories, personal memory, bounded task history, document evidence (none in Phase 4), then budget and consistency checks (deduplicate, mark superseded, bound tokens by D-59, keep source labels). Authorization runs inside the builder, never in the prompt. Contradictory memories are surfaced with provenance, not silently resolved; a model inference never overwrites a confirmed fact.
  - Tests with synthetic memories: low-priority items trimmed first, User B absent, deleted memory absent, conflict surfaced, builder works without a live model.
  - D-65 final recorded: "lexical only for Phase 4" if the evaluation is adequate (not a failure), or hybrid. If hybrid: the embedding model and storage (for example `pgvector`, avoiding a new service) are chosen from evidence, scores are normalized before fusion, authorization still runs first, and vectors are invalidated on update or delete. Lexical-only mode keeps working either way.
- **Todo List**:
  - [ ] Lexical retrieval, D-66 and isolation tests (P4-16).
  - [ ] Context builder with budget enforcement (P4-17).
  - [ ] Semantic retrieval decision, executed only if needed; D-65 final (P4-18).
- **Relevant Context**:
  - Roadmap Steps 16–18; tracker P4-16, P4-17, P4-18; risks P4-R4, P4-R8
  - Specs: 03.34.05–07, 03.14.5, 04.15.03, 04.15.04, 04.15.06, 04.15.10, 04.15.12, 04.13.07
- **Status**: `[ ] pending`

---

### Sub-Task 10: Memory CLI, AI CLI behaviour and adversarial evaluation (Steps 19–21)
- **Intent**: Developers can inspect and correct their own memory from the terminal, the CLI reports AI planning honestly, and the combined system holds up against manipulated models and documents.
- **Expected Outcomes**:
  - Memory commands `nexus memory list`, `show`, `update` and `delete`, aligned with 03.16 and 03.34.08. List truncates content; `show` gives full content, source, provenance, scope and status. Update records the provenance of the change and produces a version record. Delete warns that backup and audit records may persist and requires explicit confirmation. Accessing another user's memory returns the same not-found style response as a missing one. Human output by default and stable JSON per the D-35/D-75 convention. Sensitive content is not echoed needlessly in output or logs.
  - `nexus run "<request>"` accepts multi-step requests and reports the accepted plan's step count and IDs. `nexus task <id> --steps` shows each step with its dependency, status (the full step-state set including `WAITING_FOR_APPROVAL`, `RUNNING`, `REJECTED` and `CANCELLED`) and tool. When the model is unavailable the CLI states that AI planning is unavailable while search, status, history and cancel still work, and the task is not accepted as if planning succeeded. Uncertain steps are never shown as success; the four grounding categories map to distinct output. Context-used memory IDs are shown only to the owner.
  - Adversarial tests extend the Phase 3 `adversarial` fixtures: injected instructions to search `C:\` or claim admin rights, an unregistered tool, a plan with `"approved": true` (stripped, policy still runs), a plan claiming success without evidence (step stays `UNCERTAIN`), a silent change of target device (replanning rules require confirmation), and three concurrent users with no memory leakage. All eight hard safety gates fail the gate when triggered. Model timeout, out-of-memory or an infinite loop leaves a clean recoverable state. The evaluation report explicitly records zero unauthorized operations. Mutation checks: disabling cycle detection or the scope check fails a test.
  - All three developers review the adversarial results.
- **Todo List**:
  - [ ] Memory CLI with tests (P4-19).
  - [ ] AI commands and honest failure messages (P4-21).
  - [ ] Adversarial and hard-gate evaluation (P4-20).
- **Relevant Context**:
  - Roadmap Steps 19–21; tracker P4-19, P4-20, P4-21
  - Specs: 03.16, 03.34.08, 03.14.9, 04.14.06, 03.13.9, 03.13.10, 04.13.06, 04.13.09, 03.23.8, 04.15.07
- **Status**: `[ ] pending`

---

### Sub-Task 11: Performance benchmark, acceptance matrix, evidence and Gate 4 review (Steps 22–25; D-60)
- **Intent**: Measure the complete stack on the real host, prove every Gate 4 item, and hand off honestly to Phase 5.
- **Expected Outcomes**:
  - Benchmark Scenario D (AI and memory, warm and cold), Scenario E (three overlapping users on different devices) and Scenario F (bridge disconnect, model unavailable, backend restart) from 03.27.6, run on the designated host with at least two Windows PCs. D-60 (inference concurrency limit) settled from data; increasing past 1 requires the benchmark evidence. Every remaining TBD performance configuration value (`max_active_tasks`, `max_queued_tasks`, `max_active_operations_per_device`, `database_pool_size`, `max_context_size`, `max_tool_output_size`) is set, replacing Phase 2 provisional values. Measurements recorded with date, machine, versions and p50/p95 by phase.
  - 15 acceptance scenarios (`docs/testing/p4-acceptance.md`): clear request to a valid multi-step plan; ambiguous request to clarification; unsupported request to honest refusal; model unavailable with deterministic tasks working; blocked dependent step; cyclic plan rejected; prompt-injection document cannot widen scope; unregistered tool rejected; memory save, retrieve and delete; retrieved memory improves relevance; deleted memory absent; three-user zero leakage; grounded response cites real records; GPU unavailable gives CPU fallback or a documented blocker; model timeout leaves a recoverable task. Scenarios 1–13 run on the designated host with the real model. The evaluation report meets D-67 with zero hard-gate failures.
  - Release evidence report `docs/releases/p4-evidence.md`: model and runtime versions, configuration, evaluation summary, acceptance results, host-readiness completion, benchmark data, known defects, unresolved decisions, untested scenarios. A developer who did not write the model-setup instructions reproduces setup from a clean clone and runs a smoke test. Baseline 2 extension (backend + PostgreSQL + model + small workload) recorded. The troubleshooting guide gains model-runtime failure codes. Milestone sign-off checklist per Roadmap Step 24.
  - Non-author security review: model output is never an authorization decision; model-supplied `approved`, `risk` or `user_id` cannot change policy; retrieved memory never leaks; zero unauthorized operations; model unavailability never leaves a task falsely succeeded; no prompts, credentials or full document contents in logs. Critical and high defects fixed first.
  - Gate 4 checklist from the tracker satisfied (D-56 to D-70 recorded with honest statuses, including Open or Provisional where applicable). Tracker updated, including MVP checklist items 12 and 13 only with test evidence. Hand-off pairing and retrospective held.
  - Phase 5 entry list: `read_document` contract and bridge implementation, document processing pipeline (chunking, formats), CLI history and result improvements, approvals and diagnostics UX polish, task transparency and audit trail CLI, search within task history, and evaluating the lexical retrieval baseline before document reading is deployed.
- **Todo List**:
  - [ ] Performance benchmark and D-60 (P4-22).
  - [ ] Acceptance matrix on the designated host (P4-23).
  - [ ] Evidence report, clean-setup reproduction and baseline update (P4-24).
  - [ ] Security review, Gate 4 review, tracker update, Phase 5 entry list, hand-off and retrospective (P4-25).
- **Relevant Context**:
  - Roadmap Steps 22–25 and §5; tracker P4-22 … P4-25 and Gate 4 exit criteria
  - Specs: 03.27.3–11, 04.03.06, 04.03.10, 04.14.13, 04.28.05
- **Status**: `[ ] pending`
