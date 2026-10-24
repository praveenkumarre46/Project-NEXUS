## 03.22.1 Purpose

NEXUS must let three developers use a shared backend while each developer retains control of their own Windows computer. This requires a clear separation between centralized services and local execution.

The deployment design must answer:

- Where do FastAPI, PostgreSQL and the AI runtime run?

- How does each developer's CLI reach the backend?

- How does the backend communicate with each Windows bridge?

- What happens when a computer goes offline?

- How are users and devices authenticated independently?

- Which network ports are exposed, and to whom?

- How can the team operate NEXUS safely on a local network without paid infrastructure?

Core principle: the shared backend coordinates tasks, but each Windows bridge enforces local execution boundaries on its own computer.

## 03.22.2 Proposed deployment topology

The current preference is to use one designated team computer for the shared backend, database and initial AI inference, subject to hardware and connectivity validation.

### Designated team computer

This diagram shows the proposed logical deployment, not a guarantee that the designated computer can run all services efficiently. Its available RAM, AMD GPU model and VRAM, operating system, network accessibility and expected uptime must be checked first.

## 03.22.03 Service placement

| **Component** | **Proposed location** | **Reason** |
| --- | --- | --- |
| CLI | Each developer's environment | Local task submission and status viewing |
| Windows bridge | Native Windows on each developer's computer | Access to that computer's files and approved applications |
| FastAPI backend | Designated team computer | Central authentication, policy enforcement and task coordination |
| PostgreSQL | Designated team computer, private to backend | Durable shared records |
| AI runtime | Initially the designated team computer | Shared inference without paid API dependency |
| Migrations and backup jobs | Controlled backend deployment environment | Consistent schema and data recovery |
| Test tools | Developer environments and CI where available | Independent, reproducible verification |

The backend may run inside WSL 2, directly on Linux or in containers. The exact deployment method remains open until the host and networking arrangement are validated.

The Windows bridge should remain a native Windows process because it needs Windows filesystem semantics, local application access and the current Windows user's execution context.

## 03.22.04 Network boundaries

NEXUS should expose only the network services needed by authorized clients.

CLI → FastAPI

Allowed for authenticated clients on the approved local network. Requests must be authorized against the user and requested resource.

Windows bridge → backend

Authenticated, device-specific communication. The backend must verify device identity and the bridge must independently validate incoming operations.

FastAPI → PostgreSQL

Internal service communication only. Database access should not be available to ordinary LAN clients.

FastAPI → model runtime

Private communication with the configured inference service. The model endpoint should not be exposed to the LAN unless a documented requirement makes that necessary.

Public internet → NEXUS

No public exposure or router port forwarding for the initial deployment. LAN access does not eliminate the need for authentication or firewall restrictions.

### Proposed port policy

Exact port numbers should be selected and recorded in deployment configuration rather than scattered through source code.

| **Service** | **Network exposure** |
| --- | --- |
| FastAPI | Reachable only from the intended clients and bridge |
| PostgreSQL | Private to the backend and authorized administrative tooling |
| Model runtime | Private to the backend unless a separate host requires controlled access |
| Windows bridge | Prefer outbound connections; no inbound LAN listener unless justified |
| SSH or remote administration | Disabled or restricted unless explicitly needed |

Do not assume that a service is private simply because it listens on a familiar port. Verify its bind address, firewall rules and reachability from a second computer.

## 03.22.05 Windows bridge communication model

Two main communication models are possible.

### Option A — Bridge polls the backend

Provisional preference

The bridge initiates outbound requests to check for authorized work or report status.

- Usually easier to operate behind Windows firewalls and common NAT configurations.

- Does not require the bridge to expose an inbound listening port.

- Polling interval affects responsiveness and request volume.

- Must securely claim work and prevent duplicate dispatch.

### Option B — Persistent outbound connection

The bridge maintains a WebSocket or another persistent connection to the backend.

- Can reduce dispatch latency and provide faster status updates.

- Requires connection lifecycle, heartbeat, reconnection and stale-session handling.

- Still requires authentication, device authorization and durable task coordination.

- Adds implementation and testing complexity.

Recommendation: start with polling for the MVP unless measured latency requirements make it unsuitable. A polling bridge can retrieve work, report heartbeats and submit operation results without requiring inbound access to each Windows machine.

Polling must not mean that the bridge blindly executes whatever it receives. Each request still needs authentication, device-target validation, schema validation, local policy checks and operation-level deduplication.

The final polling interval and protocol remain open decisions until the team tests three concurrent users and representative task durations.

## 03.22.06 Device identity and routing

Each bridge represents one registered device. A device ID is an identifier, not proof of identity.

The backend must maintain a mapping between:

- The authenticated user.

- The registered device.

- The device's current authorization and revocation status.

- The task's requested target device.

- The bridge credential used to authenticate that device.

### Routing rules

1. Every task must have an explicit target device, or use a clearly displayed default device already configured by the user.

2. The backend must verify that the user is authorized to target that device.

3. The bridge must verify that the operation targets its own registered device.

4. An offline device must not cause silent execution on a different computer.

5. A revoked device must not receive new authorized work.

6. A task assigned to one device cannot be moved to another device without an explicit, authorized change to the task's execution plan.

7. The system must distinguish a registered device from an online and execution-ready device.

For the initial MVP, device ownership should remain owner-only unless an explicit device-sharing feature is designed and tested.

## 03.22.07 WSL 2 and Windows networking

The backend's WSL 2 environment and the native Windows bridge operate in related but distinct networking contexts.

The correct configuration depends on where the backend runs and which machines need to connect.

| **Deployment arrangement** | **What must be verified** |
| --- | --- |
| Backend inside WSL 2, CLI on the same Windows computer | Windows-to-WSL connectivity |
| Backend inside WSL 2, bridge on another computer | LAN reachability to the backend and applicable Windows/firewall rules |
| Backend in a Linux container | Container port publishing, host binding and network reachability |
| Backend directly on the host OS | Host firewall and service bind address |
| Model runtime on another machine | Authenticated connectivity and model endpoint restrictions |

WSL 2 commonly uses NAT networking by default. Windows 11 also supports mirrored networking in supported configurations. Neither mode should be assumed to work correctly for NEXUS without testing the actual host, firewall and network setup.

### Required connectivity checks

- From the designated host, verify that FastAPI is listening on the intended interface.

- From a second developer's computer, verify that the API is reachable through the approved LAN address.

- Verify that PostgreSQL is not reachable from an ordinary client machine.

- Verify that the model endpoint is not unintentionally exposed.

- Verify that each bridge can authenticate and maintain communication through disconnect/reconnect cycles.

- Repeat the checks after a host restart and after relevant firewall or WSL changes.

A successful localhost request on the host does not prove that another computer can reach the backend.

## 03.22.08 Network security requirements

The initial LAN deployment should use defense in depth.

Minimum requirements:

- Authentication for API clients and registered bridges.

- Authorization on every protected resource and operation.

- Firewall rules restricting access to intended clients and services.

- No public router port forwarding.

- No direct database access for ordinary clients.

- No shared bridge credential across all three devices.

- Protection against replayed or duplicated operation requests.

- Bounded request sizes, timeouts and connection limits.

- Safe handling of malformed or excessive requests.

- Redaction of secrets and private document content from network diagnostics.

A local network is not automatically trusted. Other devices on the same network may be compromised, misconfigured or unauthorized.

If the network is shared with untrusted devices, or if credentials and sensitive data cross a network where interception is a concern, use properly configured TLS. Do not treat an IP address or a device's network location as authentication.

## 03.22.09 Host availability and failure handling

The designated team computer is a potential single point of failure.

If it shuts down:

- The shared API becomes unavailable.

- New tasks cannot be accepted through that backend.

- AI inference may become unavailable.

- Connected bridges may lose contact with the coordinator.

- Existing tasks may remain incomplete or have uncertain external outcomes.

Each component must communicate its own status honestly. The CLI should distinguish backend unavailability from a target device being offline.

### Recovery rules

- A disconnected bridge must not execute newly received work after its authorization or deadline has expired.

- A task that has already been dispatched must be reconciled before an unsafe retry.

- The backend must recover task state from durable storage when it restarts.

- A replacement host must not begin dispatching restored work until its database, credentials, device registrations and active-task recovery have been validated.

- An offline device should retain enough local evidence to help reconcile operations if local persistence is part of the final bridge design.

Whether the bridge will persist operation outcomes in a local SQLite database or use another durable mechanism remains open. The selected design must be able to address the case where a Windows action succeeds but the backend never receives its response.

## 03.22.10 Deployment startup and shutdown

The team should have one documented startup and shutdown procedure. Starting services in arbitrary order creates confusing partial-failure states.

### Startup sequence

1. Start PostgreSQL and verify readiness.

2. Apply approved database migrations.

3. Start FastAPI and verify its health endpoints.

4. Verify model-runtime readiness if AI functionality is required.

5. Start or connect the Windows bridges.

6. Verify each bridge's identity, authorization and health.

7. Reconcile tasks left active during a previous shutdown.

8. Enable normal task dispatch after required checks pass.

Not every service needs to be globally healthy for every feature to work. For example, NEXUS may still allow users to inspect task history while the model runtime is unavailable. Readiness should reflect actual dependencies rather than reducing the entire product to one all-or-nothing status.

### Shutdown sequence

1. Stop accepting new work if a controlled shutdown is planned.

2. Stop dispatching new operations.

3. Allow bounded time for in-flight operations to report outcomes.

4. Persist known task and step states.

5. Mark unresolved operations for recovery rather than fabricating results.

6. Shut down workers and services cleanly.

Forced termination can happen at any time, so restart recovery remains necessary even with a graceful shutdown procedure.

## 03.22.11 Configuration and addressing

The backend URL must be configurable rather than hard-coded into the CLI or bridge.

A conceptual example:

NEXUS_API_URL=<approved-backend-address>

NEXUS_DEVICE_ID=<registered-device-id>

These are illustrative setting names, not final configuration requirements. A device ID is not a secret; its associated credential must be protected separately.

The deployment documentation must explain:

- How the designated host's LAN address is discovered and maintained.

- How clients are configured when that address changes.

- How the backend bind address and firewall are configured.

- How device registration and revocation work.

- How to verify connectivity without exposing secrets.

- How the system behaves if the backend address is unavailable.

A stable local hostname or a reserved DHCP address may be useful, depending on the team's router and network administration capabilities. The team should select the simplest reliable option available rather than assume it has access to managed DNS or static network infrastructure.

## 03.22.12 Deployment and integration testing

The following tests are required before the multi-device deployment is considered ready.

| **Test** | **Expected result** |
| --- | --- |
| Each of three developers authenticates | Each user has the correct identity and access |
| Each bridge registers independently | Credentials and device IDs remain distinct |
| User submits a task to their device | The intended bridge receives the task |
| User attempts unauthorized cross-device access | Request is denied |
| One bridge disconnects | Other users and devices remain operational where dependencies allow |
| Backend restarts | Persistent task history is available and active tasks are reconciled |
| Host shuts down during a dispatched operation | The operation is not blindly repeated after recovery |
| Client attempts direct database access | Connection is refused |
| Client attempts direct access to the model endpoint | Access is refused unless explicitly authorized by the deployment design |
| Unauthorized device contacts the backend | It cannot claim work or execute operations |
| Backend address changes | Clients fail clearly until correctly reconfigured |
| Firewall rules are tightened | Required communication works; unnecessary exposure remains blocked |

Tests must be performed from a separate client machine, not solely from the host running the services.

## 03.22.13 Deployment acceptance criteria

The proposed deployment is acceptable when:

- All three developers can use their own registered Windows computers.

- The shared backend is reachable only through the intended network path.

- PostgreSQL and the model runtime are not unnecessarily exposed.

- Each bridge authenticates independently and enforces its local policy.

- Target-device selection is explicit and cannot silently fall back to another machine.

- Task and operation identifiers support recovery across disconnects and restarts.

- WSL 2, firewall and LAN connectivity have been tested in the real environment.

- Host failure behavior and recovery steps are documented.

- A fresh setup and restart procedure is reproducible by another team member.

## 03.22.14 Open decisions

| **Decision** | **Status** |
| --- | --- |
| Designated host's operating system and availability | Open |
| Backend deployment mode: WSL 2, native Linux or containers | Open |
| Bridge polling versus persistent connection | Polling provisionally preferred |
| Stable host addressing | Open |
| Exact API and database network exposure | Must be finalized and tested |
| TLS configuration | Depends on network trust and deployment arrangement |
| Device credential provisioning and rotation | Must be finalized |
| Bridge-side durable operation records | Open |
| Host-failure recovery procedure | Must be tested before release |
| AI runtime placement and AMD GPU compatibility | Still requires hardware validation |

## 03.22.15 Exit criterion

The team can explain and demonstrate how a task travels from a user on one Windows computer to the shared backend and back, how each boundary authenticates and authorizes that task, and what happens if any component disconnects.

The design must not rely on a trusted LAN, an assumed WSL networking mode or a model's willingness to follow instructions as a substitute for enforceable security.
