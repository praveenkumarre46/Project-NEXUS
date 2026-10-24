## 04.13.01 Purpose

NEXUS needs a local AI capability to interpret natural-language requests, propose multi-step plans, use relevant context and produce grounded responses without requiring a paid AI API.

The initial inference host is the designated team computer. The user has reported 16 GB of RAM and a dedicated AMD GPU, but the exact GPU model, VRAM and compatible inference runtime have not yet been verified.

This section defines the service boundary and operational behavior without prematurely choosing a model or assuming GPU acceleration will work.

Recommended approach: isolate inference behind a replaceable model adapter, benchmark a compatible local runtime on the actual host, and preserve deterministic functionality when the model is unavailable.

## 04.13.02 Logical architecture

## 04.13.03 Responsibilities and trust boundaries

| **Component** | **Responsibility** | **Must not do** |
| --- | --- | --- |
| AI service | Build bounded context and request model output | Grant permissions or execute tools |
| Model adapter | Translate requests and responses for a selected runtime | Bypass schema validation |
| Inference runtime | Generate model output | Directly access arbitrary Windows files |
| Planner validator | Validate proposed plan structure and references | Treat valid JSON as proof of safety |
| Policy engine | Decide whether an operation is allowed or needs approval | Delegate authorization to the model |
| Task orchestrator | Execute validated, authorized steps | Assume the model's claimed outcome is true |

Model output is untrusted input, even when it comes from a local model. It must be parsed, validated and checked against the registered tool catalogue and current permissions.

A model response saying “the file was created” is not execution evidence. The bridge and backend must establish the actual outcome.

## 04.13.04 Model adapter contract

The rest of NEXUS should call a stable application-level interface instead of runtime-specific endpoints directly.

A conceptual Python interface is:

from typing import Any, Protocolclass ModelProvider(Protocol):    async def generate(        self,        *,        system_context: str,        user_request: str,        structured_context: dict[str, Any],        output_schema: dict[str, Any],    ) -> dict[str, Any]:        ...

This is illustrative, not a finalized interface. Planning, summarization and embedding generation may eventually require separate methods because they have different output requirements and resource profiles.

### Adapter responsibilities

- Identify the configured runtime and model version.

- Submit requests using the runtime's supported interface.

- Apply request and response timeouts.

- Enforce input and output bounds.

- Parse the response into a known representation.

- Report runtime failures using stable application errors.

- Expose latency and resource diagnostics without logging private content.

- Support a controlled readiness check.

- Avoid changing policy, task state or authorization.

### Provider-level failure categories

| **Error** | **Meaning** | **Required handling** |
| --- | --- | --- |
| MODEL_UNAVAILABLE | Runtime cannot be reached | Preserve task state and apply the configured fallback policy |
| MODEL_TIMEOUT | Generation exceeded its limit | Stop waiting, subject to runtime capabilities, and record the failure |
| MODEL_OUTPUT_INVALID | Output cannot be parsed or validated | Reject it; allow only bounded regeneration attempts |
| MODEL_CAPACITY_EXCEEDED | Inference capacity is unavailable | Queue within limits or return a controlled capacity outcome |
| MODEL_CONTEXT_LIMIT_EXCEEDED | Input or output exceeds the supported context budget | Reduce context safely or request a narrower task |
| MODEL_CONFIGURATION_INVALID | Configured model or runtime is incompatible | Fail readiness checks and report a diagnostic |
| MODEL_RESPONSE_TRUNCATED | Output ended before a complete valid response | Reject incomplete structured output |

The adapter should distinguish a generation failure from a valid model response that proposes an unsupported operation. The latter is a planning or capability issue, not a transport failure.

## 04.13.05 Runtime and model selection

The runtime and the model are separate decisions. A model that looks suitable on paper may perform poorly on the available hardware or fail to produce reliable structured plans.

Candidate runtimes, including Ollama, may be evaluated, but no specific runtime is approved until compatibility and performance are demonstrated on the designated host.

### Evaluation sequence

1. Inventory the host

2. Record the CPU, available RAM, exact AMD GPU model, VRAM, driver version, free disk space and current system load.

3. Verify runtime compatibility

4. Confirm that the runtime supports the actual GPU and operating environment. Do not assume CUDA compatibility or that a working Windows GPU driver implies GPU acceleration inside WSL2.

5. Load a candidate model

6. Measure startup time, model memory usage, CPU/GPU utilization and whether the model fits without exhausting host resources.

7. Run the planning evaluation set

8. Test structured output, tool selection, argument validity, dependency handling, ambiguity and prompt-injection resistance.

9. Benchmark concurrent usage

10. Test the workload with three developers submitting tasks, including overlapping inference requests.

11. Test failure and recovery

12. Stop the runtime during a request, exhaust available capacity, restart the service and verify that task states remain correct.

### Selection criteria

A candidate must meet the following minimum conditions:

- Runs within the available hardware budget.

- Supports the chosen model adapter contract.

- Produces sufficiently reliable structured plans.

- Meets the team's measured latency requirements or has an acceptable documented fallback.

- Does not require a paid inference API.

- Has a license suitable for the intended use.

- Can be installed and reproduced by the team.

- Does not require the model to have unrestricted access to the computer.

The exact model, quantization, context length and inference mode remain open until the benchmark is complete.

## 04.13.06 Inference request lifecycle

Every model request should have a bounded lifecycle that can be observed and diagnosed.

1. Validate the caller: confirm the application service is authorized to request inference for the relevant task.

2. Assemble context: include only relevant, authorized context and the required tool descriptions.

3. Apply budgets: enforce input-size, output-size, time and concurrency limits.

4. Acquire capacity: obtain an inference slot or place the request in the bounded inference queue.

5. Call the adapter: send the request to the configured local runtime.

6. Validate the response: parse the output, enforce the expected schema and reject invalid results.

7. Return a proposal: hand the structured proposal to the planner validator and policy pipeline.

8. Record diagnostics: persist necessary task-stage information and emit privacy-safe performance metrics.

Planning must remain separate from execution. Generating a plan does not dispatch an operation, satisfy an approval requirement or mark a task as running successfully.

### Cancellation

If a task is cancelled while waiting for inference, the request should be removed from the pending queue where possible.

If generation is already underway, NEXUS should request cancellation when the runtime supports it. If the runtime cannot reliably stop generation, the application must still prevent the result from reviving a cancelled task or initiating new work.

Cancellation of an inference request and cancellation of the overall task are related but distinct operations.

## 04.13.07 Context budgets and resource management

The model's maximum context length is not a target that every request should fill. NEXUS must reserve capacity for the system instructions, current request, structured context, tool descriptions and output.

Conceptually:

\[ B_{\text{input}} = B_{\text{context}} - B_{\text{instructions}} - B_{\text{request}} - B_{\text{output}} - B_{\text{safety}} \]

The adapter or context builder must enforce the actual model's limits. Token counting should use a compatible tokenizer when available; character limits alone are not a reliable substitute for model token limits.

### Required limits

- Maximum input and output tokens.

- Maximum queued inference requests.

- Maximum concurrent generations.

- Maximum request duration.

- Maximum retries for invalid structured output.

- Maximum relevant memory and document excerpts.

- Maximum document extraction size before context assembly.

- Maximum time spent waiting for inference capacity.

The initial limits should be conservative and configurable. The team should measure actual resource usage before choosing numerical defaults.

### Shared-host protection

The designated computer must continue to support the backend, PostgreSQL and Windows or development workloads as applicable.

Monitor:

- Available RAM and peak process memory.

- GPU utilization and VRAM use where supported.

- CPU utilization and thermal or throttling indicators where available.

- Model load and warm-up duration.

- Inference queue wait and generation latency.

- PostgreSQL latency and connection usage during inference.

- Host behavior when several developers submit requests concurrently.

If inference causes sustained resource pressure, reduce concurrency or model size before introducing additional infrastructure.

## 04.13.08 AMD GPU and CPU fallback strategy

The user has reported an AMD dedicated GPU, but its model and VRAM are not yet known. Therefore, GPU acceleration is an evaluation goal, not a guaranteed deployment capability.

The team must test the actual combination of GPU, driver, runtime, model format and execution environment.

### Proposed fallback sequence

1. Attempt the validated, configured inference path.

2. If the runtime is unavailable or incompatible, return a controlled readiness or inference error.

3. If a tested CPU fallback is configured, allow the application to use it according to the fallback policy.

4. Apply stricter concurrency and timeout limits if CPU inference is substantially slower.

5. If neither execution path is usable, preserve task state and explain that AI-dependent work cannot currently proceed.

A fallback must not silently change the model, discard context, bypass validation or claim a task has succeeded.

A CPU fallback also needs its own benchmark. It may be acceptable for occasional planning but unsuitable for three concurrent users.

### Operational separation

The model runtime should have a clear lifecycle separate from FastAPI:

- Runtime readiness is checked independently.

- A runtime restart does not reset task state.

- Model configuration changes are controlled and recorded.

- In-flight requests are handled according to their actual outcome.

- The backend does not expose the model endpoint to the LAN unless a documented architecture requires it.

The exact choice between a Windows-hosted runtime and a WSL2-accessible runtime remains open until compatibility and network behavior are verified.

## 04.13.09 Model safety, prompt injection and structured output

NEXUS must treat all model output as a proposal, not an instruction to execute directly.

### Required validation sequence

- Parse the response against the expected structure.

- Reject unknown tools and unsupported tool versions.

- Validate every argument against the registered schema.

- Resolve logical resource identifiers against authorized resources.

- Validate dependency references and reject cyclic plans.

- Enforce step, context, output and time limits.

- Apply authorization and policy independently of the model.

- Require approval for operations that need it.

- Revalidate the exact operation immediately before dispatch.

A schema-valid plan can still be unsafe. For example, a correctly formatted request to read a directory outside the user's permitted scope must be denied.

### Prompt-injection handling

Documents, retrieved memories, task history and tool results can contain malicious instructions. The model may interpret them incorrectly even when instructed not to.

NEXUS must therefore ensure that:

- Retrieved content cannot change a user's identity or device ownership.

- A document cannot grant new permissions.

- A model response cannot approve its own proposed action.

- Unknown tools cannot be introduced through model output.

- The model cannot request arbitrary shell, PowerShell or Python execution through a generic endpoint.

- Invalid plans are rejected by application code.

- The bridge performs its own local validation.

The model evaluation suite should include malicious documents, misleading tool results, attempts to access another user's memory and instructions to bypass approval.

## 04.13.10 Model lifecycle and configuration management

The team needs a repeatable way to configure, start, validate, update and diagnose the model runtime.

### Proposed lifecycle

| **Phase** | **Required behavior** |
| --- | --- |
| Configuration | Validate runtime endpoint, model identifier, limits and permitted execution mode |
| Startup | Check runtime reachability and configured model availability |
| Readiness | Verify the runtime can perform the required basic inference operation |
| Normal operation | Enforce concurrency, timeout, input and output limits |
| Degradation | Record the dependency failure and prevent unsafe progression |
| Recovery | Recheck readiness and resume only eligible work |
| Upgrade | Record the new runtime/model version and rerun evaluation tests |
| Rollback | Restore a previously validated configuration and reconcile affected tasks |

A health check should not repeatedly trigger expensive model generation. Readiness can use a lightweight runtime check, while a controlled smoke test can be performed during setup or deployment verification.

### Version information

For reproducibility, record the applicable:

- Runtime name and version.

- Model identifier and exact version or artifact digest where available.

- Quantization or model format, if applicable.

- Context and generation settings.

- Adapter and planner schema versions.

- Evaluation dataset version and results.

- Host hardware and execution mode.

Avoid automatically downloading or switching to an unreviewed model at runtime. Model changes can affect planning quality, latency and resource use even when the API contract remains unchanged.

## 04.13.11 Observability and failure diagnosis

AI-specific diagnostics should distinguish model quality problems from runtime failures and application validation failures.

| **Metric or event** | **Why it matters** |
| --- | --- |
| Inference request count and error rate | Shows availability and stability |
| Queue wait time | Identifies capacity bottlenecks |
| Generation duration | Measures user-facing latency |
| Input/output token counts | Helps tune context and output budgets |
| Model load duration | Reveals startup and recovery costs |
| CPU, RAM, GPU and VRAM use | Establishes hardware pressure |
| Invalid structured output rate | Measures contract reliability |
| Plan rejection rate | Reveals planning or capability mismatches |
| Bounded regeneration attempts | Detects recurring model-output problems |
| Context retrieval duration | Separates retrieval delays from inference delays |
| Model version and evaluation result | Supports reproducibility |

Use task and request correlation IDs to connect these metrics to the relevant execution stage.

Do not log full prompts, private memories, document contents, credentials or unrestricted model responses by default. Record bounded error details and the necessary validation failure category instead.

### Diagnostic workflow

When inference becomes slow or unreliable:

1. Check runtime readiness and model version.

2. Determine whether time was spent waiting for capacity or generating output.

3. Inspect CPU, RAM, GPU and VRAM utilization.

4. Check context size and output limits.

5. Inspect structured-output and plan-validation failure rates.

6. Compare with the last known-good benchmark.

7. Change one variable at a time and rerun the same evaluation set.

Do not respond to poor planning quality by simply increasing the model's permissions.

## 04.13.12 Test plan and acceptance criteria

### Runtime and adapter tests

- Configured runtime is reachable.

- Missing model or invalid configuration produces a clear diagnostic.

- Valid output is parsed into the expected structure.

- Malformed and truncated outputs are rejected.

- Timeouts do not corrupt task state.

- Queue capacity and inference concurrency limits are enforced.

- Cancellation does not revive a cancelled task.

- Runtime restart does not lose persisted task state.

- CPU fallback works when configured and passes its own benchmark.

### AI quality and safety tests

- Supported requests produce valid tool proposals.

- Ambiguous requests trigger clarification where needed.

- Unsupported requests receive an honest response.

- Dependency references are valid and acyclic.

- Out-of-scope resource requests are rejected.

- Malicious document instructions cannot bypass application policy.

- The model cannot approve its own proposed operations.

- Invalid output receives only bounded regeneration attempts.

- Model unavailability does not create false task success.

### Hardware and integration tests

- Actual AMD GPU and VRAM are identified.

- Runtime compatibility is demonstrated on the intended host.

- Cold and warm inference measurements are recorded.

- Three-user concurrent requests are benchmarked.

- API and PostgreSQL performance remain acceptable during inference.

- Resource pressure and runtime failure produce controlled degradation.

- Model configuration can be reproduced by another team member.

The model must pass the defined safety tests with zero unauthorized operations actually executed in the tested scenarios. A model that proposes unsafe operations may still be blocked by policy, but its planning defect must be recorded and evaluated.

## 04.13.13 Priorities for the 10–12 week MVP

P0 — Foundation

Required for safe integration

- Model-provider interface and controlled runtime configuration.

- Request limits, timeouts and bounded concurrency.

- Structured output validation.

- Runtime health checks and actionable errors.

- Safe behavior when inference is unavailable.

- No direct model authority over policy or execution.

P1 — MVP AI capability

Required for the complete NEXUS vision

- Benchmark and select a suitable local model.

- Reliable structured task planning.

- Hybrid context integration.

- Prompt-injection evaluation.

- Three-user inference and resource benchmarks.

- Validated GPU execution or a documented CPU fallback.

P2 — Later improvements

Defer until evidence justifies them

- Multiple inference hosts.

- Dynamic model routing.

- Advanced inference batching.

- Automatic model switching.

- Distributed inference and dedicated scaling infrastructure.

## 04.13.14 Open decisions

These items must be resolved through hardware inventory, compatibility checks or benchmark evidence rather than assumptions.

| **Decision** | **Evidence required** | **Owner** |
| --- | --- | --- |
| Exact GPU model and VRAM | Hardware inventory | Developer 1 |
| Runtime and execution environment | Compatibility and smoke tests | Developer 3 |
| Model and quantization | Fixed planning evaluation | Developer 3 |
| CPU fallback | Latency and resource benchmark | Developer 3 |
| Inference concurrency | Three-user workload test | Developer 1 + Developer 3 |
| Context and output limits | Model limits and task evaluation | Developer 3 |
| Runtime placement | Windows/WSL2 connectivity and resource measurements | Developer 1 + Developer 3 |
| Numeric latency targets | End-to-end benchmark | All three |
| Model update and rollback policy | Reproducibility and recovery tests | All three |

## 04.13.15 Definition of done

- The model adapter isolates runtime-specific details.

- The selected runtime and model are recorded and reproducible.

- AMD GPU compatibility is verified, or the CPU fallback is explicitly selected and benchmarked.

- Structured model output is validated independently of policy.

- Context, concurrency, output and time limits are enforced.

- Model failures preserve durable task state.

- Cancellation and runtime recovery are tested.

- Prompt-injection and invalid-plan tests pass.

- Three-user performance and resource measurements are recorded.

- No secrets or private document content are exposed by default in diagnostics.

- Model upgrades require controlled evaluation and rollback procedures.

Section exit criterion: NEXUS can use a reproducible local AI runtime to produce bounded, validated proposals without making task execution dependent on the model being continuously available.
