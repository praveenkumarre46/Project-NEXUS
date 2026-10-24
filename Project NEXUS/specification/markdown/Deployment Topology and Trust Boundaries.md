## 3.7.1 Deployment options

## Option A — Designated team computer

Recommended for the initial MVP, subject to hardware validation

Where services run

- One designated computer runs the shared FastAPI backend and PostgreSQL, potentially inside Ubuntu on WSL 2.

- A model runtime runs on that computer or another selected machine.

- Each teammate runs a NEXUS CLI client and Windows bridge on their own Windows computer.

- The clients connect to the shared backend over the trusted local network.

Advantages: Low additional cost, straightforward initial deployment, one shared source of task state.

Trade-offs: The backend is unavailable when the host is offline; resource contention is possible; the host needs appropriate network and firewall configuration.

## Option B — Dedicated always-on host

Alternative if suitable hardware is available

Where services run

- A separate machine hosts the backend, PostgreSQL and possibly model inference.

- Each teammate still runs their own Windows bridge.

- The backend remains independent of a developer's daily laptop.

Advantages: Clearer service ownership, less dependence on one developer's workstation, easier to keep services available.

Trade-offs: Requires suitable hardware, extra setup, resource planning and operational maintenance.

Provisional decision: Option A is the default MVP proposal because we have a zero-budget constraint. We will not finalize it until we confirm the host can run the required services reliably and that its model performance is acceptable. We must not assume that 16 GB of system RAM or an unknown GPU guarantees this.

## 3.7.2 Physical deployment view

This is the proposed network layout for Option A.

Teammate A — Windows 11

CLI client + local Windows bridge

Teammate B — Windows 11

CLI client + local Windows bridge

Teammate C — Windows 11

CLI client + local Windows bridge

## Shared team host

FastAPI

PostgreSQL

Model adapter / local inference

The model runtime could instead live on a different machine. That is an implementation option, not a requirement that has already been decided.

## 3.7.3 Trust boundaries

NEXUS must treat the user's computer, shared backend, model and database as separate security boundaries.

Boundary A — Client to backend

Every API request must be authenticated. The backend derives the user identity from validated credentials rather than trusting a user ID supplied in the request body.

Boundary B — Backend to model

The model receives only the context required for the task. Its output is untrusted input; it cannot authorize actions, access databases directly or bypass policy checks.

Boundary C — Backend to Windows bridge

Each bridge authenticates incoming requests, validates operation parameters and verifies that the requested action is allowed on that device.

Boundary D — Application to database

Database access goes through controlled application services and repositories. User-owned records require ownership checks; transactions preserve consistent task state.

Boundary E — Device to device

One teammate's bridge must not become a route to another teammate's files. Device registration, user permissions and per-operation authorization must be checked independently.

## 3.7.4 Network communication policy

The following is the proposed policy for the initial deployment.

| **Connection** | **Proposed policy** |
| --- | --- |
| CLI → FastAPI | Authenticated connection over the intended local network |
| FastAPI → PostgreSQL | Private service connection; database port not exposed to teammates |
| FastAPI → model runtime | Local/private endpoint; not exposed directly to the LAN |
| Backend → Windows bridge | Authenticated, device-specific connection; only registered operations |
| Windows bridge → backend | Prefer an outbound connection or another verified design that avoids opening unnecessary inbound ports on each teammate's PC |
| Internet → NEXUS | No public exposure in the initial MVP |

We must not assume that “local network” means trusted. Other devices may be present on the same network, and credentials or private document contents should not be transmitted without appropriate protection.

## 3.7.5 WSL 2 networking decision

Microsoft documents that WSL 2 normally uses NAT networking. Windows 11 also supports mirrored networking, which can improve host/WSL connectivity and enable LAN access to WSL services when the relevant firewall settings permit it. These modes have different behavior, so the choice must be validated on the actual development machine.

Proposed approach:

1. Keep the development backend inside Ubuntu on WSL 2.

2. Prove local Windows-to-WSL connectivity first.

3. Prove that a second computer can reach the backend using the intended LAN configuration.

4. Configure narrowly scoped firewall rules for the required service ports.

5. Test service behavior after WSL restarts, laptop sleep, network changes and bridge disconnections.

6. Document the supported networking configuration for the team.

We should not change networking settings merely because one configuration is theoretically convenient. First establish what works on the current machines.

## 3.7.6 Provisional deployment decision

My recommendation is to use Option A — one designated team computer — for the MVP, provided it passes the following checks:

- It can run FastAPI and PostgreSQL without unacceptable resource contention.

- The selected local model runs within available memory and provides adequate tool-use quality.

- Teammates can connect securely over the LAN.

- The host can remain available for the periods when teammates need NEXUS.

- The deployment can recover predictably after restarts and interruptions.

The model runtime may run on that host or on another approved machine. A local model service such as Ollama is one candidate because it offers a local API, but the model, runtime and host placement remain provisional until measured.

If the host cannot satisfy the checks, we should reconsider the topology rather than hide the limitation in the implementation.

## 3.7.7 Deployment acceptance tests

Before approving this subsection, the team should demonstrate the following:

- Each teammate can authenticate to the shared backend.

- Each teammate can target their own registered Windows bridge.

- A user cannot invoke another device's private operations without authorization.

- An unauthorized LAN client cannot invoke protected APIs or tools.

- PostgreSQL and model services are not unnecessarily exposed to the LAN.

- A disconnected bridge produces an accurate task status.

- The system recovers from a backend restart without falsely marking unfinished tasks successful.

- The documented deployment can be reproduced on a clean environment.
