## 03.35.1 Purpose

The planning engine converts a user's natural-language request into a structured, bounded, verifiable plan that NEXUS can evaluate and, if authorized, execute through registered tools.

For example, a user might ask:

Find the latest project design document, summarize its main decisions, and save the summary in my approved workspace.

NEXUS should not treat this as one giant AI-generated command. It should decompose the request into individual steps, establish their dependencies, validate the plan, and execute each step only when its prerequisites are satisfied.

### Required planning pipeline

1. Understand the request

Goal, device, constraints, ambiguity

2. Build a structured plan

Registered tools, arguments, dependencies

3. Validate the plan

Schemas, capabilities, scope, policy, risk

4. Execute through the orchestrator

Dependencies, approvals, verification, recovery

5. Report verified results

Success, partial success, failure or uncertainty

Architectural rule: the planning engine proposes what should happen. The policy engine determines what is allowed. The orchestrator determines when and how steps execute. The Windows bridge determines whether an operation is valid and safe at the execution boundary.

The planner must never bypass those components.

## 03.35.2 Request understanding

Before creating a plan, NEXUS must interpret the request using the current message and only the context the user is authorized to access.

The request-understanding stage should identify:

- Goal: the outcome the user wants.

- Target device: the Windows computer on which operations must occur.

- Resources: relevant directories, documents, applications or existing task results.

- Constraints: output location, file format, scope, size limits and other requirements.

- Expected outcome: what evidence would demonstrate completion.

- Ambiguities: missing information that could materially change the operation.

- Relevant context: authorized memories and project information that genuinely help with the request.

The system must distinguish a requested outcome from an implementation guess. For example, “organize my project files” does not automatically authorize moving, renaming or deleting files.

### When NEXUS should ask a question

Ask for clarification when uncertainty could affect authorization, safety, the target or the correctness of the result.

Examples:

| **Request or condition** | **Expected behavior** |
| --- | --- |
| “Find the design document” and several documents match | Show candidates or ask which one |
| The target computer is not specified and no valid default exists | Ask the user to select a registered device |
| “Save it in my project folder” but several permitted folders match | Ask or show available choices |
| The destination file already exists | Do not overwrite; ask how to proceed if an alternative is needed |
| The request requires an unsupported tool | Explain the limitation; do not invent a capability |
| The task is clear and all required inputs are available | Continue to planning |

A clarification should be specific and minimal. NEXUS should not ask questions whose answers can be safely determined from already authorized, reliable context.

## 03.35.3 Plan representation

A plan is a versioned, structured proposal, not executable code.

The following is an illustrative logical representation, not a finalized API or database schema:

{

"plan_version": "1",

"objective": "Create a summary of the latest project design document",

"target_device_id": "registered-device-id",

"steps": [

{

"step_key": "find_document",

"tool_name": "search_files",

"tool_schema_version": "1",

"depends_on": [],

"expected_outcome": "Candidate document references"

},

{

"step_key": "read_document",

"tool_name": "read_document",

"tool_schema_version": "1",

"depends_on": ["find_document"],

"expected_outcome": "Bounded extracted document text"

},

{

"step_key": "create_summary",

"tool_name": "create_file",

"tool_schema_version": "1",

"depends_on": ["read_document"],

"expected_outcome": "Summary file created without overwriting"

}

]

}

This example illustrates dependencies only. In a real plan, the summary-generation step must also have a valid, bounded content-generation capability. NEXUS must not assume that create_file itself summarizes a document. If the required summarization capability is unavailable, planning must stop or explain what is missing.

The final representation should support these fields where applicable:

- Plan ID and plan version.

- Objective and target device.

- Relevant context references.

- Ordered step identifiers.

- Registered tool name and schema version.

- Validated tool arguments.

- Dependency references.

- Preconditions and expected outcomes.

- Verification requirements.

- Policy-computed risk and approval status.

- Resource limits, deadline and failure handling.

- Plan validation status and rejection reasons.

The backend assigns authoritative identifiers such as step IDs and operation IDs. The model may propose logical step keys, but it cannot create trusted identities, choose its own risk level or mark a step as completed.

## 03.35.4 Multi-step decomposition and dependencies

A task may contain steps that must run sequentially, steps that can run independently, and steps that cannot begin until earlier results are available.

Represent these dependencies as a directed acyclic graph (DAG) when the plan has genuine dependencies.

### Example dependency graph

### A. Find document

### B. Read document

### C. Generate summary

### D. Create summary file

Each step becomes eligible only after its dependencies have succeeded and its own authorization and preconditions have been revalidated.

Rules for dependency handling:

1. A step must not execute before all required dependencies succeed.

2. A failed or uncertain prerequisite must not be treated as successful.

3. Independent read-only steps may run concurrently if resource limits and policies allow it.

4. Steps that write to the same resource require explicit conflict handling.

5. A dependency cycle invalidates the plan.

6. Optional steps must be explicitly marked optional; failure must not silently skip a required step.

7. A plan must remain within configured limits for step count, dependency depth, model output, resource use and execution time.

For the initial release, prefer short plans that can be inspected and verified. A large, deeply nested plan increases validation, recovery and debugging complexity.

## 03.35.5 Plan validation pipeline

Every generated plan must pass deterministic validation before it is eligible for execution. A syntactically valid response from an AI model is not necessarily a valid plan.

| **Validation stage** | **Required check** | **Failure behavior** |
| --- | --- | --- |
| 1. Structure | Required fields, data types and schema version | Reject malformed plan |
| 2. Tool registry | Every tool exists, is enabled and supports the requested schema version | Reject unsupported tool |
| 3. Arguments | Arguments match the registered input schema and limits | Reject invalid arguments |
| 4. Dependencies | Referenced steps exist, graph is acyclic, required ordering is valid | Reject invalid graph |
| 5. Resources | Directory IDs, document references and device references are valid and appropriately scoped | Reject or request clarification |
| 6. Capabilities | Target device reports compatible, configured tools | Defer, clarify or report unsupported capability |
| 7. Policy | User, device, tool, arguments and requested resource are authorized | Deny or require approval |
| 8. Budget | Step count, output size, context size and time/resource limits are acceptable | Reduce scope safely or reject |
| 9. Execution readiness | Preconditions are met and required approvals are valid | Wait, revalidate or stop |

The order above is a logical pipeline, not a requirement that every check execute in one transaction. Authorization and device capability must be checked again at the relevant execution boundary because permissions, device status and configuration can change after planning.

### Important separation of responsibility

- The model proposes the objective, steps and arguments.

- The tool registry defines available tools and their contracts.

- The policy engine computes risk and authorization.

- The orchestrator manages state and dependency readiness.

- The Windows bridge validates local operation constraints.

- The verification layer determines whether the expected outcome has actually occurred.

A model-generated field such as "risk": "low" cannot lower a tool's registered risk. Likewise, a model cannot declare its own approval unnecessary.

## 03.35.6 Preconditions, postconditions and verification

Each operation should define what must be true before execution and what evidence is needed afterward.

For example, a file-creation step may require:

- A registered target device that is online.

- An approved logical directory ID.

- A valid relative filename.

- Permission to create a file in that directory.

- An absent destination, if the operation is create-only.

- A valid, bounded content payload.

Its postconditions may include:

- The file was created on the intended device.

- The destination stayed within the authorized directory.

- The file satisfies the tool's documented output contract.

- The bridge returned evidence that can be correlated with the operation.

A successful bridge response should be checked against the expected outcome. Merely dispatching an operation or receiving an HTTP success response is not sufficient evidence that the task is complete.

Verification must be proportional to the operation. A read-only search may need only a valid bounded result. A write requires stronger confirmation. If the operation may have succeeded but its outcome cannot be established, record uncertainty rather than claiming success or retrying blindly.

## 03.35.7 Planning versus execution

Planning and execution must be separate phases.

### Planning phase

- Understand the request and authorized context.

- Propose a plan and dependencies.

- Validate schemas, capabilities, scope and policy.

- Ask for clarification or required approval.

- Persist the accepted plan version.

### Execution phase

- Select an eligible step.

- Revalidate authorization and preconditions.

- Persist operation intent.

- Dispatch through the authenticated bridge.

- Record the outcome and verify it.

- Unlock dependent steps only when their prerequisites succeed.

Generating a plan must not itself modify the user's computer. Planning may perform bounded, authorized read operations only if a future design explicitly defines such behavior; the safer initial default is that the planner proposes operations and the orchestrator executes them through the normal tool pipeline.

A plan being saved does not mean that it is approved, running or completed. These are separate facts and should have separate statuses.

## 03.35.8 Clarification, replanning and changed conditions

Plans sometimes become invalid during execution. A document may disappear, a device may disconnect, an approval may expire or an earlier step may return an unexpected result.

NEXUS needs controlled replanning rather than blindly continuing with stale assumptions.

1. Detect the change. Record the actual tool result, failure or changed precondition.

2. Classify its effect. Determine whether it is safe to continue, whether the plan is blocked, or whether an external side effect is uncertain.

3. Reconcile if necessary. Establish the outcome of any operation that may already have changed the computer.

4. Replan within the original scope. Generate a revised proposal using verified state and authorized context.

5. Validate the revision. Recheck the tool registry, device, arguments, dependencies, limits and policy.

6. Obtain fresh approval when required. A materially changed operation must not inherit approval for the old operation.

7. Persist the revision. Preserve the prior plan and record why it changed.

Replanning must not be used to bypass a denial, expand directory permissions, switch to another computer silently or revive a cancelled task. If the revised plan requires a new target, a different consequential action or a wider scope, NEXUS must obtain the required authorization or ask the user.

### Example

Suppose NEXUS plans to create summary.txt, but that file already exists.

The correct response is not to silently overwrite it or generate a new arbitrary destination. NEXUS should report the conflict and ask whether the user wants a different filename or another explicitly supported action. If the original create operation timed out and the file might have been created, NEXUS must reconcile that operation before proposing a retry.

## 03.35.9 Plan persistence and versioning

The backend should preserve enough information to explain what NEXUS intended to do, what it was allowed to do and what actually happened.

Proposed logical records:

- Plan version: validated plan structure, objective, creation time, planner/provider version and validation outcome.

- Plan steps: stable step IDs, dependencies, tool/schema references, bounded arguments and expected outcomes.

- Plan revision: relationship to the previous version, reason for revision and which steps changed.

- Execution records: operation IDs, attempt IDs, state transitions, tool responses and verification evidence.

- Context references: authorized memory/document/task references used to produce the plan, where retention and privacy policy permit.

The precise database schema remains to be finalized alongside the task and step schema in Section 03.10.

Additional rules:

- Never rely on the model's conversational output as the authoritative execution record.

- Preserve enough plan information for recovery, but avoid retaining full private document contents or complete prompts by default.

- Bind approval to the exact operation and arguments, not merely the plan's title or objective.

- Do not reuse an old operation ID for a materially different operation.

- If a plan is revised, already completed steps remain completed; they must not be replayed merely because the overall plan has a new version.

- Record the model/runtime version and relevant configuration for diagnosis without logging secrets.

## 03.35.10 Planning failures and recovery behavior

Planning errors should have predictable outcomes rather than triggering unlimited model retries.

| **Failure** | **Required behavior** |
| --- | --- |
| Invalid structured output | Retry within a small configured budget; reject if still invalid |
| Unknown or disabled tool | Reject the proposed plan or explain the missing capability |
| Missing required information | Ask a targeted clarification question |
| Policy denial | Stop the denied operation; do not ask the model to evade the policy |
| Device unavailable | Mark the task as blocked or interrupted according to its lifecycle state; do not switch devices silently |
| Model unavailable | Return a clear dependency error; preserve accepted task state and avoid pretending planning succeeded |
| Dependency step fails | Block dependent steps; continue independent steps only if the plan explicitly permits it and doing so remains safe |
| Tool result is uncertain | Reconcile the operation before retrying or continuing through dependent steps |
| Revised plan fails validation | Reject the revision and preserve the last valid plan and execution history |
| Step or resource budget exceeded | Stop expansion and explain the limit; do not silently exceed it |

Retry limits, model timeouts, step limits and total planning budgets are configuration decisions that must be finalized after benchmarking the selected runtime and testing representative requests.

## 03.35.11 Limits on autonomous planning

The planning engine must not be an unrestricted agent that can invent tools, run arbitrary code or recursively generate work without bounds.

For the initial release:

- Only registered tools may appear in an executable plan.

- No model-generated shell, PowerShell or Python execution endpoint.

- No unbounded planning loops or unlimited self-replanning.

- No implicit expansion from a narrow request to a broad filesystem or system operation.

- No use of document instructions to change permissions or override approval.

- No silent changes to the target device or authorized directories.

- No treating a plausible model-generated result as proof that an operation succeeded.

- No automatic compensation that introduces additional side effects without its own defined policy.

- Every plan must have bounded steps, dependencies, output, resource usage and execution time.

The model may recommend an action that the system cannot perform. NEXUS should explain the limitation instead of fabricating an implementation or attempting an unauthorized workaround.

## 03.35.12 Testing and evaluation

Planning quality must be tested separately from tool execution reliability. A blocked unsafe proposal can demonstrate that policy enforcement works, but it does not demonstrate that the planner understood the request correctly.

### Required test categories

Plan structure and dependency tests

Validate missing fields, malformed arguments, dependency cycles, nonexistent step references, unsupported schemas and excessive plan size.

Safety and authorization tests

Test unknown tools, forged device IDs, unauthorized directories, changed approved arguments, prompt injection and attempts to bypass a denial through replanning.

Recovery and consistency tests

Test a failed prerequisite, uncertain file creation, device disconnection, model failure, cancellation during execution and replanning after verified state changes.

Planning-quality evaluation

Use a fixed test set to assess tool selection, argument validity, dependency correctness, unnecessary steps, clarification behavior, unsupported requests and scope adherence.

### Representative acceptance scenarios

1. A clear request produces a valid plan using only available tools.

2. An ambiguous request asks a focused question rather than guessing a consequential detail.

3. A dependent step cannot run while its prerequisite is pending, failed or uncertain.

4. A cyclic dependency graph is rejected.

5. A model cannot lower risk, grant itself permission or approve its own operation.

6. An approved step whose arguments change requires revalidation and any necessary new approval.

7. A failed step does not cause the planner to claim that the overall objective succeeded.

8. A model outage produces a clear error without corrupting accepted task state.

9. A revised plan cannot silently expand the target device or authorized scope.

10. A completed external side effect is not blindly repeated after a lost response.

11. Three users can plan tasks concurrently without mixing their private context.

12. Every reported result is traceable to persisted execution evidence.

The evaluation set should include both straightforward tasks and adversarial or misleading requests. Results should be repeatable across model/runtime changes.

## 03.35.13 Implementation priorities

| **Priority** | **Scope** |
| --- | --- |
| P0 — Safe planning foundation | Structured plan contract, registered-tool validation, dependency graph validation, clarification handling, bounded plans, policy separation, plan persistence and deterministic tests |
| P1 — Useful autonomous workflows | Dependency-aware scheduling, result-conditioned replanning, provenance-aware context assembly, planning evaluation and improved failure recovery |
| P2 — Advanced planning | More sophisticated plan optimization, cost-aware scheduling, broader workflow composition and advanced plan comparison |

P0 is not a license to ship a product without AI or context awareness. It defines the safe planning foundation on which the complete NEXUS experience is built.

### Suggested ownership

- Developer 1 — Backend and execution: plan persistence, plan validation orchestration, dependency scheduling, state transitions and recovery.

- Developer 2 — Windows bridge: tool capability reporting, local tool contracts, execution evidence and reconciliation support.

- Developer 3 — AI and context: request interpretation, structured plan generation, clarification, context assembly and planning-quality evaluation.

These are proposed ownership boundaries. All three developers should review the plan contract and safety rules together before parallel implementation.

## 03.35.14 Open decisions and assumptions

The following decisions must remain visible until the team validates or approves them.

| **Decision** | **Current position** | **Status** |
| --- | --- | --- |
| Plan representation | Versioned structured plan with dependency references | Proposed |
| Dependency model | DAG for plans with dependencies | Proposed |
| Planner authority | Propose only; no authorization or direct execution | Required design rule |
| Plan-size limits | Bounded steps, depth, output and execution time | Required; numeric limits open |
| Invalid-output retries | Small bounded retry budget | Proposed; exact value open |
| Dynamic replanning | Allowed only after validation and with scope preserved | Proposed |
| Parallel execution | Only for independent steps within resource limits | Proposed |
| Plan storage | Persist plan versions and execution evidence | Proposed |
| Planning model/runtime | Selected after evaluation on the designated AMD-GPU computer | Open |
| Clarification policy | Ask when ambiguity materially affects safety or correctness | Proposed |
| Model evaluation thresholds | Define using a fixed evaluation set | Open |

Important dependency: the planning engine relies on the contracts established in Sections 03.11, 03.15, 03.24 and 03.31. If the team changes approval binding, operation identity, task states or tool schemas, the planning design must remain compatible with those changes.

## 03.35.15 Definition of done

## Section 03.35 is ready for implementation when the team agrees that:

- The planner produces a documented, versioned structured plan.

- Each executable step references a registered tool and supported schema.

- Dependencies, prerequisites and expected outcomes are represented explicitly.

- Cycles, invalid arguments and unsupported capabilities are rejected.

- Ambiguity triggers focused clarification when necessary.

- Risk and permissions are determined outside the model.

- The planner cannot execute tools or modify task state directly.

- Plans are bounded and persisted with sufficient version and provenance information.

- Replanning preserves scope, respects existing task state and obtains fresh approval where required.

- Uncertain external side effects are reconciled before unsafe continuation or retry.

- Fixed planning evaluations and adversarial tests are part of the test suite.

- The three developers agree on interfaces and responsibilities.

Section exit criterion: a valid plan can move through validation and execution without allowing AI-generated output to bypass authorization, tool contracts, task-state rules or recovery safeguards.
