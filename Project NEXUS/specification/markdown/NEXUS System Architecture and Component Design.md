## 3.1 Architectural objectives

The architecture must support:

1. Multiple users operating their own Windows computers.

2. A shared backend that authenticates requests and coordinates tasks.

3. Safe execution of permitted operations on the correct computer.

4. Local-first AI without a mandatory paid inference API.

5. Persistent task state and user-specific memory.

6. Concurrent requests, disconnections and recoverable failures.

7. Clear component boundaries that enable independent testing and future extension.

The architecture should be as simple as possible for a three-person team while preserving the boundaries required for security and correctness.

## 3.2 Proposed logical architecture

Client layer

Terminal CLI · Authentication · User commands · Progress display

### API and application layer

Identity & Access

Request Handling

Policy Engine

Task Orchestrator

AI services

Model adapter, planning, context retrieval and structured tool proposals.

Persistence

PostgreSQL, task records, task steps, memory, approvals and audit events.

### Per-device execution layer

Device Registry & Routing

Windows Bridge

Restricted filesystem and application tools on each registered Windows computer.

Logical components, not a finalized physical deployment. Arrows represent conceptual communication, not all required network connections.

## 3.3 Component responsibilities

| **Component** | **Responsibility** | **Must not do** |
| --- | --- | --- |
| CLI client | Submit requests, display task status, collect user decisions | Make authorization decisions on behalf of the server |
| FastAPI layer | Validate requests, authenticate callers, expose API contracts | Execute arbitrary model-generated code |
| Identity and access service | Resolve users, devices and permissions | Trust a user-supplied device ID without authorization |
| Agent/planning service | Interpret requests and propose structured plans | Grant permissions or declare unverified success |
| Policy engine | Validate tool, user, device and approval requirements | Delegate authorization to the model |
| Task orchestrator | Manage task states, step ordering, cancellation and recovery | Lose durable state when a process restarts |
| Model adapter | Provide a stable interface to the selected model runtime | Couple business logic to one model's response format |
| Memory service | Retrieve and manage authorized context | Expose another user's memories |
| PostgreSQL repository layer | Persist and query application state | Bypass ownership rules in application operations |
| Device registry and router | Resolve an authorized target device and connection status | Silently redirect work to a different computer |
| Windows bridge | Execute registered, permitted local operations | Accept unrestricted shell commands or arbitrary operations |
| Audit and diagnostics | Record relevant state transitions and outcomes | Store secrets or unnecessary private content |

## 3.4 Request execution sequence

The following sequence describes the proposed happy path. Failure and retry paths will be documented separately.

Important design note: This is a logical interaction sequence, not a commitment that every operation will execute synchronously inside one HTTP request. Long-running work should use a durable task lifecycle, with clients able to retrieve progress separately. The API and execution mechanics will be specified in later sections.

## 3.5 Proposed deployment boundary

We know each user needs a bridge on their own Windows computer. We do not yet know where the shared services will run.

Two plausible topologies remain:

### Option A — One designated team computer

Fastest initial setup if the machine is available and has sufficient resources. It hosts the backend, database and potentially the model runtime; teammates connect over the LAN.

### Option B — Separate always-on machine

Provides a dedicated service host and reduces dependence on a developer laptop being online, but requires another suitable machine and additional deployment work.

Both options must preserve the per-user Windows bridge boundary. Running the backend on one computer does not mean that all computer operations should run on that host.

## 3.6 Decisions deliberately deferred

We should not lock these before the next design stages:

- The physical host and service topology.

- The exact local model and whether inference is shared.

- The transport and authentication mechanism between backend and bridge.

- Whether a durable queue is needed or whether PostgreSQL-backed task coordination is sufficient.

- The detailed database schema and transaction boundaries.

- The exact task state machine and legal transitions.

- The approval expiry, timeout and retry defaults.

- The numerical latency and concurrency targets.

These are not forgotten requirements. They are tracked architecture decisions that need evidence or a more detailed design.
