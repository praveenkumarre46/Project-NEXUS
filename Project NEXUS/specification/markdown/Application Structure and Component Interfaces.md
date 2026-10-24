Design principle: start with a modular monolith for the shared backend, plus a separate Windows bridge process on each user's computer. Do not start with microservices. This gives us clear module boundaries without adding distributed-service complexity inside the backend itself.

## 3.8.1 Proposed application topology

NEXUS CLI

User input · Task status · Approval prompts

FastAPI — HTTP interface

Authentication · Request validation · Response schemas

Application services

Task management · Planning · Memory · Device routing

Domain rules

Permissions · Risk policy · Task states · Tool contracts

Infrastructure adapters

PostgreSQL · Model provider · Bridge transport

Execution engine

Step scheduling · Timeouts · Cancellation · Recovery

Per-device Windows bridge

Allowlisted local tools · Path validation · Local execution

Logical dependency map. Exact interfaces and transport mechanisms are defined in subsequent subsections.

The arrows do not mean every module can call every other module. The dependency rules below define which interactions are permitted.

## 3.8.2 Proposed repository layout

The following is the initial repository structure. It is a proposal, not a claim that files have already been created.

nexus/

├── apps/

│   ├── api/                    # FastAPI application

│   ├── cli/                    # Terminal client

│   └── windows_bridge/         # Per-device Windows process

├── nexus_core/

│   ├── domain/

│   │   ├── tasks.py

│   │   ├── approvals.py

│   │   ├── devices.py

│   │   └── permissions.py

│   ├── services/

│   │   ├── task_service.py

│   │   ├── planning_service.py

│   │   ├── memory_service.py

│   │   └── device_service.py

│   ├── execution/

│   │   ├── orchestrator.py

│   │   ├── state_machine.py

│   │   └── recovery.py

│   ├── tools/

│   │   ├── registry.py

│   │   ├── contracts.py

│   │   └── policies.py

│   ├── ai/

│   │   ├── provider.py

│   │   ├── planner.py

│   │   └── context_builder.py

│   ├── infrastructure/

│   │   ├── database/

│   │   ├── model_adapters/

│   │   └── bridge_transport/

│   └── observability/

├── migrations/

├── tests/

│   ├── unit/

│   ├── integration/

│   ├── contract/

│   └── end_to_end/

├── deploy/

│   ├── docker-compose.yml

│   └── config/

├── docs/

└── pyproject.toml

### Why these boundaries?

- domain/ defines core concepts and rules without depending on FastAPI, PostgreSQL or a model vendor.

- services/ implements application use cases by coordinating domain rules and infrastructure interfaces.

- execution/ owns task-step execution, lifecycle transitions, cancellation and recovery.

- tools/ defines the supported operations and their policy metadata.

- ai/ converts user requests and context into structured proposals; it does not authorize or execute them directly.

- infrastructure/ contains replaceable implementations for storage, model inference and communication with bridges.

- apps/windows_bridge/ is a separate process because it runs with access to the local Windows environment.

- tests/ separates fast unit tests from tests that need a database, model or actual Windows machine.

We should avoid creating empty abstractions for every possible future feature. Add modules when there is a real responsibility to isolate.

## 3.8.3 Component contracts

Every component needs a defined responsibility, an input contract, an output contract and a clear failure behavior.

| **Component** | **Receives** | **Returns** | **Owns** |
| --- | --- | --- | --- |
| Request API | Authenticated request, task intent and target device | Task ID, accepted state or validation error | HTTP contract |
| Planning service | User request and permitted context | Structured plan or clarification request | Plan generation |
| Policy engine | User, device, proposed operation and approval state | Allow, deny or require approval | Authorization decision |
| Task orchestrator | Validated plan and task ID | State transitions and step outcomes | Execution lifecycle |
| Tool registry | Tool identifier and arguments | Validated tool contract or rejection | Available tool definitions |
| Bridge transport | Registered device and authorized operation | Bridge response or communication error | Backend-to-device communication |
| Windows bridge | Authenticated tool request | Structured local operation result | Local operation execution |
| Memory service | User identity and memory operation | Authorized memory result | Memory lifecycle |
| Persistence layer | Domain records and queries | Persisted records or storage errors | Database interaction |

A component must not silently assume that another component succeeded. For example, the orchestrator must inspect the bridge result before marking a step successful.

## 3.8.4 Dependency rules

The codebase should enforce the following rules from the beginning.

1. Domain rules do not depend on frameworks. Task transitions and authorization concepts should be testable without starting FastAPI or PostgreSQL.

2. AI proposes; application code decides. A model response must pass schema validation, policy evaluation and operation-specific checks before execution.

3. Services use explicit interfaces. Planning should not import database implementation details; it should receive the context it needs through defined dependencies.

4. Only the persistence layer accesses database sessions directly. Business operations use repositories or clearly defined persistence services.

5. The Windows bridge has its own trust boundary. It independently validates authentication, allowed operations and local paths. It must not blindly trust a tool request because it came from the backend.

6. The CLI is not a security authority. Hiding a button or omitting a command is not sufficient authorization; the backend must enforce the same rule.

## 3.8.5 Shared data contracts

Backend modules and the Windows bridge should communicate through explicit, versioned contracts rather than informal dictionaries with undocumented fields.

For example, a proposed tool invocation could use this logical shape:

{

"tool_name": "search_files",

"device_id": "registered-device-id",

"arguments": {

"directory_id": "project-documents",

"query": "design"

}

}

This is an illustrative payload, not the final API schema. Actual identifiers, authentication headers, request IDs, validation constraints and error responses belong in Section 04.

Every tool contract should define:

- A stable operation name and contract version.

- Typed input fields and validation constraints.

- Required permissions and risk classification.

- Execution timeout and retry safety.

- A typed success result.

- Defined failure categories.

- Whether the operation changes local state.

- Whether it requires approval.

## 3.8.6 Error-handling contract

We should distinguish four kinds of failure because each requires different behavior.

| **Failure category** | **Example** | **Required response** |
| --- | --- | --- |
| Validation failure | Unsupported tool or malformed argument | Reject before execution |
| Authorization failure | User requests access to an unauthorized directory | Deny and record the relevant event |
| Operational failure | File is locked or the application cannot launch | Return a structured failure; do not claim success |
| Uncertain outcome | Bridge disconnects after a file write begins | Mark the outcome as uncertain and reconcile before retrying |

Internal exceptions should be logged with a correlation or task identifier. User-facing responses should provide a useful explanation without revealing credentials, stack traces or sensitive implementation details.

## 3.8.7 Testing strategy for module boundaries

Each interface needs tests at the level where its contract matters.

- Unit tests: Task-state transitions, permission evaluation, argument validation and retry decisions.

- Integration tests: Database transactions, repository behavior, task persistence and model-adapter integration.

- Contract tests: Backend and Windows bridge agree on request fields, response fields and error handling.

- End-to-end tests: A terminal request results in a verified operation on the correct Windows computer.

- Security tests: Forged device IDs, unauthorized paths, replayed approvals and cross-user access attempts are rejected.

- Failure tests: Database unavailable, bridge offline, model timeout, interrupted execution and uncertain write outcome.

Tests should not require a real model for every run. Most core tests should use deterministic fake model responses and a simulated bridge, with a smaller set of real integration tests validating the actual environment.

## 3.8.8 Parallel development across the three-person team

The architecture should let the team work concurrently while keeping shared interfaces stable.

| **Owner** | **Primary responsibility** | **Deliverable** |
| --- | --- | --- |
| Developer 1 — Backend and execution | Task lifecycle, persistence, orchestrator, concurrency and recovery | Reliable task execution with tested state transitions |
| Developer 2 — Windows integration | Device registration integration, bridge, filesystem tools, application launching | Restricted Windows operations and bridge contract tests |
| Developer 3 — AI and context | Model adapter, planning, structured tool proposals and memory retrieval | Testable planning and context services |

These are proposed ownership boundaries. Everyone should review security-sensitive code and understand the end-to-end architecture. Before parallel work begins, the team should agree on the shared data contracts so each developer can use a mock implementation while another component is still being built.

## 3.8.9 Decisions and acceptance criteria

The following decisions are now proposed for the architecture baseline:

- Use a modular monolith for the shared FastAPI backend.

- Run each Windows bridge as a separate process on its corresponding device.

- Separate AI planning from authorization and execution.

- Use explicit component and tool contracts.

- Test components independently with deterministic mocks.

- Assign primary ownership across the three-person team.

Still open:

- Exact package and module names.

- Final API schemas and authentication protocol.

- Database schema and transaction boundaries.

- Bridge transport and connection management.

- The need for a separate worker process or durable queue.

- Deployment host and model placement.

We should finalize those in the relevant design sections instead of making premature decisions here.
