# Product vision

NEXUS is a personal AI computer companion that combines two equally important capabilities:

- Computer automation: Understand requests and safely execute useful, multi-step tasks on a user's Windows 11 computer.

- Context awareness: Maintain useful knowledge of the user's projects, preferences, ongoing tasks, and prior interactions to provide relevant assistance.

NEXUS should progress beyond a chatbot. It should plan, act through explicitly permitted tools, observe outcomes, recover from supported failures, and explain what happened.

## 1.2 Confirmed product decisions

Target platform

Windows 11 on each user's own computer

Development

Ubuntu on WSL 2

Backend

Python and FastAPI

Database

PostgreSQL

Interface

Terminal-first

AI strategy

Local-first, hybrid-capable, zero-budget

Execution policy

Tiered autonomy governed by explicit permissions and risk

Context

Persistent, user-controlled memory

Initial deployment

Local network

Team and timeline

3 people; 10–12 weeks

Engineering focus

Practical usefulness, deep backend learning, reliability and performance

## 1.3 Updated system concept

The proposed system has three main layers.

Per-user Windows computer

Terminal client · Windows bridge · Restricted local tools

NEXUS backend

Authentication · Permissions · Planning · Task execution · API

Shared services

PostgreSQL · Task history · User memory · Model adapter · Audit records

Conceptual architecture only. The physical placement of services is not yet finalized.

**Why this separation matters**

If a user asks NEXUS to summarize a document on their own laptop, the backend must not accidentally read a similarly named document on another teammate's machine.

We therefore need to distinguish:

- User identity: Who issued the request?

- Device identity: Which registered computer is the intended target?

- Authorization: Which actions may that user perform on that device?

- Task ownership: Who can view, cancel, or inspect the resulting task?

- Execution location: Which computer actually performs the operation?

These must be enforced by the backend and Windows bridge, not left to the AI model's judgment.

## 1.4 Tiered autonomy policy

The proposed default is to allow automation only within explicitly configured permissions. The following risk tiers are an initial design proposal to validate in the detailed requirements.

| **Tier** | **Action class** | **Proposed behavior** |
| --- | --- | --- |
| 0 — Read | Search permitted folders, read allowed documents, inspect task history | Execute without per-action approval when the user has granted the relevant permission |
| 1 — Reversible | Create a draft or file in a designated workspace, launch an approved application | Execute automatically only when the operation falls within a clearly configured permission |
| 2 — Consequential | Overwrite files, move important data, change system settings or perform other high-impact operations | Require explicit confirmation before execution |
| 3 — Prohibited | Bypass access controls, access another user's private files without authorization, execute unrestricted model-generated commands | Reject, even if requested by the model |

Approval requirements should be determined by the operation, its scope, and the user's permissions—not merely by the wording of a request. We will specify how approval is bound to the exact operation, expires, and is audited in the security design.

## 1.5 MVP scope

The MVP will target a working end-to-end experience for multiple team members using their own registered Windows computers.

Included in the proposed MVP

- Terminal interaction and multi-step task planning.

- A Windows bridge on each participating computer.

- Restricted file search and supported document reading.

- Approved file creation and selected application launching.

- User identity, device registration and ownership enforcement.

- Persistent tasks, progress reporting, cancellation and defined recovery behavior.

- User-controlled memory for relevant preferences and project context.

- Tiered permissions, approval flows and audit logs.

- Automated tests, installation instructions and measured performance.

Excluded from the initial release

- Always-listening voice and full desktop GUI.

- Unrestricted shell execution or unrestricted screen/mouse control.

- Training a foundation model.

- Paid infrastructure requirements.

- Public internet exposure of the initial deployment.

## 1.6 Architectural implications

The new decisions introduce several requirements that were less important in the original single-host proposal.

### A. Device registration and trust

Every Windows bridge needs a way to register, authenticate, identify its device, and establish which user is allowed to invoke it. A device must not trust arbitrary requests simply because they originate on the local network.

### B. Distributed task execution

The backend and a user's Windows computer can become disconnected independently. Tasks need explicit states for pending, running, waiting for approval, succeeded, failed and cancelled, plus carefully defined recovery behavior.

### C. Multi-tenant data isolation

Conversations, memories, tasks, approvals and device records must be scoped to the right user. Database constraints and authorization checks should reinforce one another.

### D. Network and deployment topology

A local-network deployment needs authenticated communication, firewall rules, appropriate transport security, and a strategy for clients reconnecting after a laptop sleeps or changes networks.

### E. AI and computer capabilities must be decoupled

The model proposes plans and tool arguments; backend policy checks authorize them; the bridge executes only supported operations. We should be able to replace the model without rewriting the computer integration.

## 1.7 Unresolved questions and assumptions

These remain open and should not be silently treated as decisions.

| **ID** | **Open question** | **Why it matters** |
| --- | --- | --- |
| PC-01 | Does every team member need NEXUS to work when disconnected from the shared backend? | Determines whether any core backend or AI capability must run on each PC |
| PC-02 | Where should the shared backend, PostgreSQL and model runtime run? | Determines resource requirements and deployment topology |
| PC-03 | Will each computer have its own local model, or will inference be shared? | Affects privacy, RAM, latency and network load |
| PC-04 | How should users authenticate during the MVP? | Determines login, token handling and device enrollment |
| PC-05 | Which directories and applications are permitted by default? | Required to define practical yet safe computer operations |
| PC-06 | Which actions can run automatically, and what specifically requires approval? | Determines policy rules and acceptance tests |
| PC-07 | What happens to an executing task if its target PC goes offline? | Determines retry, timeout and recovery behavior |
| PC-08 | What context may be shared across devices, and what remains private? | Defines memory isolation and privacy expectations |
| PC-09 | What GPU, disk space and available RAM do the machines have? | Needed to choose and validate the local model strategy |
| PC-10 | Which document formats must the MVP support? | Determines document-processing scope and test coverage |

## 1.8 Section 01 acceptance criteria

We can consider the charter ready to approve when:

- The product vision and intended users are clear.

- MVP and long-term scope are distinguished.

- Each user's own computer is explicitly supported by the architecture.

- Tiered autonomy and prohibited actions are documented.

- Multi-user privacy and device boundaries are explicit.

- Success can be measured through acceptance tests.

- Unknown decisions are recorded with owners or resolution milestones.
