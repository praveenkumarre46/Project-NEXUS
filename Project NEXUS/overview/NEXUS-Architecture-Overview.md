# NEXUS — High-Level Architecture Overview
> Prepared for team presentation · Source: all specification/ and roadmap/ specs

---

## What is NEXUS?

NEXUS is a **personal AI computer companion** that combines two equally important capabilities:

1. **Computer automation** — understand natural-language requests and safely execute multi-step tasks on a user's Windows 11 computer.
2. **Context awareness** — maintain useful knowledge of a user's projects, preferences, ongoing tasks, and prior interactions.

NEXUS goes beyond a chatbot: it plans, acts through explicitly permitted tools, observes outcomes, recovers from failures, and explains what happened.

---

## Core Technology Decisions

| Concern | Decision |
|---|---|
| Target platform | Windows 11 (per-user) |
| Development environment | Ubuntu on WSL 2 |
| Backend | Python + FastAPI (modular monolith) |
| Database | PostgreSQL |
| Interface | Terminal-first CLI |
| AI strategy | Local-first, hybrid-capable, zero-budget |
| Execution policy | Tiered autonomy — explicit permissions + risk classification |
| Context | Persistent, user-controlled memory |
| Initial deployment | Local network (LAN) |
| Team / timeline | 3 developers · 10–12 weeks |

---

## System Layers

```
┌─────────────────────────────────────────────────────────┐
│   CLIENT LAYER  (on each user's Windows PC)             │
│   Terminal CLI — auth, commands, progress, approvals    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS (authenticated)
┌──────────────────────────▼──────────────────────────────┐
│   NEXUS BACKEND  (shared — modular monolith)            │
│                                                         │
│  FastAPI  →  Application Services  →  Domain Rules     │
│                     ↓                      ↓            │
│          Task Orchestrator         Policy Engine        │
│                     ↓                      ↓            │
│            AI Services           Infrastructure         │
│         (model adapter,          (PostgreSQL,           │
│          planner, memory)         bridge transport)     │
└──────────────────────────┬──────────────────────────────┘
                           │ Authenticated outbound poll
┌──────────────────────────▼──────────────────────────────┐
│   PER-DEVICE EXECUTION  (on each user's Windows PC)     │
│   Device Registry + Routing  ↔  Windows Bridge         │
│   (allowlisted tools · path validation · local exec)    │
└─────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│   PERSISTENCE                                           │
│   PostgreSQL — tasks, steps, memory, approvals, audit   │
└─────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Does | Must NOT do |
|---|---|---|
| CLI client | Submit requests, display task status, collect user decisions | Make authorization decisions on behalf of the server |
| FastAPI layer | Validate requests, authenticate callers, expose API contracts | Execute arbitrary model-generated code |
| Identity & access service | Resolve users, devices and permissions | Trust a user-supplied device ID without verification |
| Planning service | Interpret requests, propose structured plans | Grant permissions or declare unverified success |
| Policy engine (8 layers) | Validate tool, user, device, approval requirements | Delegate authorization to the AI model |
| Task orchestrator | Manage states, step ordering, cancellation, recovery | Lose durable state when a process restarts |
| Model adapter | Provide a stable interface to the selected model runtime | Couple business logic to one model's format |
| Memory service | Retrieve and manage authorized context | Expose another user's memories |
| PostgreSQL repository | Persist and query application state | Bypass ownership rules |
| Device registry & router | Resolve authorized target device and connection status | Silently redirect work to a different computer |
| Windows bridge | Execute registered, permitted local operations | Accept unrestricted shell commands |
| Audit & diagnostics | Record state transitions and outcomes | Store secrets or unnecessary private content |

---

## Trust Boundaries

| Boundary | Rule |
|---|---|
| **A** Client → Backend | Every API request is authenticated. Identity comes from validated credentials, never from a user ID in the request body. |
| **B** Backend → Model | Model gets only the context it needs. Model output is **untrusted input** — it cannot authorize actions, touch the database, or bypass policy. |
| **C** Backend → Bridge | Bridge authenticates and validates every operation independently. Bridge verifies the action is allowed on *that* device. |
| **D** Application → Database | Access via controlled repositories. Ownership checks on all user-owned records; transactions keep task state consistent. |
| **E** Device → Device | One teammate's bridge is never a route to another's files. Registration, permissions, and per-operation authorization are checked independently. |

> **Critical rule:** "Local network" does not mean "trusted."

---

## Tiered Autonomy Policy

| Tier | Action class | Behavior |
|---|---|---|
| **0 — Read** | Search permitted folders, read allowed documents, inspect task history | Execute without per-action approval when the user has granted the relevant permission |
| **1 — Reversible** | Create draft/file in a designated workspace, launch an approved application | Execute automatically only within a clearly configured permission |
| **2 — Consequential** | Overwrite files, move important data, change system settings | Require explicit user confirmation before execution |
| **3 — Prohibited** | Bypass access controls, access another user's files without authorization, execute unrestricted model-generated commands | **Reject**, even if requested by the model |

---

## Task State Machine

```
          ┌──────────┐
          │  QUEUED  │◄── submit task (idempotency key committed)
          └──────────┘
             │     │
    claim    │     │ cancel before dispatch
             ▼     ▼
          ┌─────────┐   unrecoverable   ┌────────┐
          │ RUNNING │──────────────────►│ FAILED │
          └─────────┘                   └────────┘
             │   │   │
  needs      │   │   │ all work verified
  approval   │   │   ▼
             │   │  ┌───────────┐
             │   │  │ SUCCEEDED │
             │   │  └───────────┘
   recovery  │   │
  needed     │   └──────────────────────────────┐
             ▼                                  │
  ┌──────────────────────┐            ┌──────────────┐
  │ WAITING_FOR_APPROVAL │            │ INTERRUPTED  │
  └──────────────────────┘            └──────────────┘
        (approve/reject/expire/cancel)   (reconcile first)
```

Terminal states: `SUCCEEDED` · `FAILED` · `CANCELLED`

**Forbidden transitions:** `SUCCEEDED` → `RUNNING` · `CANCELLED` → `QUEUED` · `WAITING_FOR_APPROVAL` → `SUCCEEDED` without execution · `INTERRUPTED` → `SUCCEEDED` without reconciliation.

---

## Physical Deployment (Option A — MVP default)

```
                     ┌─── Designated Team Host (LAN) ───┐
                     │  FastAPI backend                  │
                     │  PostgreSQL                       │
                     │  Local AI model runtime           │
                     └──────────┬────────────────────────┘
                     HTTPS (LAN)│
          ┌──────────────┬──────┴───────────────┐
          │              │                       │
   ┌──────────┐   ┌──────────┐           ┌──────────┐
   │  PC-A    │   │  PC-B    │           │  PC-C    │
   │  CLI-A   │   │  CLI-B   │           │  CLI-C   │
   │ Bridge-A │   │ Bridge-B │           │ Bridge-C │
   └──────────┘   └──────────┘           └──────────┘
   (User A)       (User B)               (User C)
```

Bridges poll **outbound** to the backend — no inbound firewall holes needed.

---

## 8-Layer Policy Engine (P3)

Every proposed operation passes all 8 layers in strict order. A DENY at any layer cannot be overridden:

```
Proposed operation
        │
  L1: Hard prohibitions (prohibited / unsupported)
        │
  L2: Tool capability registered and enabled
        │
  L3: Identity and ownership
        │
  L4: Resource permissions (active grant for directory / app)
        │
  L5: Operation constraints (arguments valid, limits not exceeded)
        │
  L6: Risk classification (Tier 0–3)
        │
  L7: Approval validation (valid, unexpired, fingerprint matches)
        │
  L8: Execution-time revalidation (all layers rechecked)
        │
     ALLOW → persist intent → dispatch
```

All decisions (ALLOW / DENY / REQUIRE_APPROVAL) are persisted to audit.

---

## AI / Planning Pipeline (P4)

```
User request
     │
Context Builder ─► retrieve authorized memories (PostgreSQL FTS)
     │              apply priority order + token budget
     │
Model Adapter ─► structured inference request
     │           validate output against plan schema
     ▼
Plan proposal (untrusted — model cannot authorize, touch DB, or bypass policy)
     │
10-layer application-side validation:
  schema ✓ · known tools ✓ · no cycles ✓ · no scope expansion ✓ · ...
     │
Persist accepted plan version
     │
Dependency-aware orchestrator dispatches steps in order
```

The model proposes; backend policy authorizes; bridge executes.

---

## Memory & Context Assembly (P4)

1. Authenticated user filter → candidates scoped by `owner_user_id`
2. PostgreSQL full-text search on active memories
3. Rank by relevance, freshness, confirmation weight
4. (Optional) Semantic embedding search if lexical gap detected
5. Context builder: apply token budget with priority order:
   `request → project context → personal memory → task history → document evidence`
6. Conflicting memories are surfaced with provenance — never silently merged
7. Response grounded in persisted source references (citations validated)

---

## Document Processing Pipeline (P5)

```
User task: "Summarize document"
     │
Bridge: authorize file access via directory_id + relative_path
     │
Format + resource checks → DOCUMENT_UNSUPPORTED_FORMAT / DOCUMENT_TOO_LARGE
     │
Text extraction (library TBD) → normalize → chunk (boundary-aware)
     │
Label chunks as UNTRUSTED DOCUMENT CONTENT — not instructions
     │
Lexical retrieval over relevant chunks → context budget
     │
Model receives: system instructions SEPARATE from document chunks
     │
Response with source references → validate citations
     │
confirmed_from_evidence  OR  no_relevant_evidence
```

---

## Development Phases (12-week plan)

| Phase | Weeks | Milestone | Gate |
|---|---|---|---|
| P0 Foundation & environment | 1 | Repo, tooling, hardware inventory, LAN test | — |
| P1 Contracts & persistence | 2 | API contracts frozen, DB schema, auth skeleton | Gate 1 |
| P2 First vertical slice | 3–4 | CLI → backend → bridge → file search → result | Gate 2 |
| P3 Safe side effects | 5–6 | Policy, approvals, create-file, idempotency, recovery | Gate 3 |
| P4 Local AI & memory | 7–8 | Validated local model, structured planner, memory | Gate 4 |
| P5 User-facing workflows | 9 | CLI history, approvals UX, document processing | — |
| P6 Team integration | 10 | 3 users/devices, isolation, concurrency, reconnect | Gate 5 |
| P7 Hardening & RC | 11–12 | Backup/restore, security regression, clean install | Gate 6 |

---

## MVP Scope

**Included:**
- Terminal interaction and multi-step task planning
- Windows bridge on each participating computer
- Restricted file search and supported document reading
- Approved file creation and selected application launching
- User identity, device registration, and ownership enforcement
- Persistent tasks, progress reporting, cancellation, and defined recovery
- User-controlled memory for preferences and project context
- Tiered permissions, approval flows, and audit logs
- Automated tests, installation instructions, and measured performance

**Excluded from initial release:**
- Always-listening voice and full desktop GUI
- Unrestricted shell execution or screen/mouse control
- Training a foundation model
- Paid infrastructure requirements
- Public internet exposure

---

## Key Design Rules (Non-negotiable)

1. The CLI never writes directly to PostgreSQL.
2. The planner proposes — application code authorizes. The planner cannot call arbitrary Windows functions.
3. API route handlers do not contain task state machine or authorization logic.
4. The bridge executes only registered local tools after its own independent validation.
5. A timeout is not proof of failure — uncertain outcomes are surfaced, not assumed.
6. A task is only `SUCCEEDED` after a correlated result is persisted and verified.
7. "Local network" does not mean "trusted."
8. Model output is always untrusted input.
9. Authorization filter runs before any content is exposed to the model.
10. Revoked devices remain revoked even after a database restore.
