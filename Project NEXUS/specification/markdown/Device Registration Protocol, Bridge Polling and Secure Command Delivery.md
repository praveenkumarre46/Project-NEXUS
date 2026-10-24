## 04.10.01 Purpose

NEXUS needs a reliable way to deliver an authorized operation from the shared backend to the correct Windows computer, receive its result and recover when the network or either process fails.

This is not merely an HTTP integration problem. A bridge may disconnect after receiving an operation, a backend may restart before recording a response, or a message may be delivered more than once.

The communication protocol must therefore support:

- Secure device registration and authentication.

- Device-specific operation delivery.

- Durable operation tracking.

- Duplicate-message handling.

- Heartbeats and capability reporting.

- Explicit timeouts and acknowledgements.

- Safe reconnect and recovery behavior.

- Authorization checks at both backend and bridge.

Proposed initial choice: use authenticated outbound polling from each Windows bridge to the backend. This avoids requiring the backend to initiate an inbound connection to each developer's computer. Polling interval, transport authentication and endpoint schemas remain decisions to finalize.

## 04.10.02 Communication architecture

### NEXUS backend

FastAPI · task orchestrator · policy · PostgreSQL

### Authenticated bridge protocol

Operation delivery · acknowledgements · heartbeat · results

#### Developer PC A

Windows bridge

Local tools and filesystem scope

#### Developer PCs B and C

Independent bridges

Separate identities and credentials

Each bridge initiates its connection to the backend. The backend decides whether that authenticated device is eligible to receive an operation. The bridge validates each operation before executing it.

The diagram describes the logical flow. It does not imply that the bridge receives unrestricted commands or that every registered tool is enabled on every device.

## 04.10.03 Bridge registration and authentication handshake

Registration and routine authentication should be separate operations. Registering a device creates its identity; authenticating proves that the current bridge possesses the corresponding credential.

### Proposed registration sequence

1. Initiate registration

2. An authenticated user requests registration of a new Windows bridge. The backend checks whether the user is allowed to enroll another device.

3. Provision a unique device identity

4. The backend creates or securely enrolls a device record and establishes a per-device authentication credential. The credential must not be a shared team-wide secret.

5. Store the credential securely

6. The bridge stores its credential using the selected protected Windows storage mechanism. The provisioning workflow must not expose the credential in ordinary logs or command history.

7. Authenticate to the backend

8. The bridge proves possession of its credential over the selected authenticated transport. A submitted device ID by itself is insufficient.

9. Validate registration status

10. The backend verifies the device record, ownership, credential validity and revocation status.

11. Report capabilities

12. The bridge reports its protocol version, supported tools and relevant local configuration status.

13. Enable eligible delivery

14. The backend makes the device eligible for dispatch only after successful authentication and the required readiness checks.

### Registration security rules

- A bridge must not choose its own authoritative owner or privilege level.

- Credentials must be unique per device and independently revocable.

- A revoked device must not become trusted merely by reconnecting.

- Re-registration after credential loss must follow a controlled authorization process.

- Device registration must not automatically grant access to another user's tasks or files.

The exact credential format and enrollment handshake remain open until the transport and credential-storage choices are finalized.

## 04.10.04 Polling protocol and endpoint responsibilities

With polling, the bridge periodically asks the backend whether work is available for its registered device. The backend must never return an operation merely because the request includes a matching device ID.

The following routes are proposed logical endpoints; exact HTTP methods and payloads must be agreed in the bridge contract.

| **Endpoint purpose** | **Responsibility** |
| --- | --- |
| Device authentication | Validate the bridge credential and registration status |
| Heartbeat | Record recent bridge contact and basic health |
| Capability report | Publish supported protocol and tool versions |
| Poll for work | Return an eligible operation for this authenticated device |
| Acknowledge dispatch | Record that the bridge accepted or rejected delivery |
| Report operation status | Report running, completed, failed or uncertain status |
| Retrieve operation outcome | Support reconciliation after lost responses or reconnects |

A possible route family is:

POST /v1/bridge/session

POST /v1/bridge/heartbeat

PUT  /v1/bridge/capabilities

POST /v1/bridge/poll

POST /v1/bridge/operations/{operation_id}/ack

POST /v1/bridge/operations/{operation_id}/result

GET  /v1/bridge/operations/{operation_id}

These are proposed routes, not a frozen API specification. For example, a separate session endpoint may be unnecessary if the selected authentication mechanism authenticates every request directly.

### Polling behavior

1. The bridge authenticates.

2. It polls using its authenticated device context.

3. The backend verifies device status, eligibility and pending work.

4. The backend atomically claims an eligible operation for that device.

5. The bridge validates the operation and acknowledges receipt.

6. The bridge executes only after its local checks pass.

7. The bridge reports progress or the final outcome.

8. The backend validates the response and persists the result.

An empty poll means no eligible operation is available at that moment. It does not imply that the device has no tasks waiting for approval or blocked by another dependency.

### Polling interval

The interval should be configurable and measured during integration testing. A fixed starting interval is an implementation choice, not yet a confirmed requirement.

The design should consider:

- Responsiveness for interactive requests.

- Load from three concurrently polling devices.

- Idle CPU and network usage.

- Backoff when the backend is unavailable.

- Jitter to avoid all devices polling simultaneously.

- Prompt detection of credential revocation and changed capabilities.

The backend must enforce the real dispatch deadline and task state regardless of how frequently the bridge polls.

## 04.10.05 Operation delivery, acknowledgement and execution

The protocol must distinguish delivery from execution.

| **Event** | **What it proves** | **What it does not prove** |
| --- | --- | --- |
| Backend records a dispatch intent | The operation is durably prepared for dispatch | The bridge received it |
| Backend sends a response containing the operation | Delivery was attempted | The bridge accepted it |
| Bridge acknowledges the operation | The bridge received and accepted or rejected the request according to the acknowledgement contract | The operation completed |
| Bridge reports RUNNING | The bridge reports active execution | The side effect will necessarily complete |
| Bridge reports SUCCEEDED | The bridge claims completion and provides an outcome | The backend has persisted or verified that outcome |
| Backend persists a verified result | The backend has recorded the established outcome | That the outcome can never be affected by later external changes |

### Acknowledgement requirements

An acknowledgement should correlate to the exact operation_id, attempt_id and target device. The backend must reject mismatched identifiers or stale attempts according to the protocol rules.

An acknowledgement should distinguish at least:

- Accepted for execution.

- Rejected before execution.

- Already known or duplicate operation.

- Unable to accept because the bridge is busy or incompatible.

The precise status names belong in the frozen bridge contract.

### Why an acknowledgement is not enough

Suppose the bridge receives a file-search operation, executes it and loses network connectivity before returning the result. The backend cannot conclude that the search failed merely because it did not receive a response.

For a read-only search, a controlled retry may be acceptable. For a later write operation, retrying could duplicate an external side effect. The bridge and backend must follow the operation's retry and reconciliation policy rather than applying a universal retry rule.

## 04.10.06 Heartbeats, health and capability reporting

A heartbeat tells the backend that a bridge recently communicated. It does not prove that every tool works, that the desktop session is available or that a file operation can succeed.

### Proposed device statuses

| **Status** | **Meaning** |
| --- | --- |
| REGISTERED | Device identity exists, but readiness has not been established |
| ONLINE | Recent authenticated communication is established |
| DEGRADED | Bridge is reachable but one or more expected capabilities or dependencies are unavailable |
| OFFLINE | No qualifying contact has been received within the configured threshold |
| REVOKED | Device is administratively or security-wise disabled |

The exact state names and timeout thresholds remain open. REVOKED must take precedence over a heartbeat: a revoked device must never become usable simply by sending another heartbeat.

### Heartbeat contents

A heartbeat should contain only the information needed for routing and operations, such as:

- Device identity established by authentication.

- Bridge version and protocol version.

- Timestamp or server-validated contact time.

- Current bridge health.

- Bounded active-operation summaries, if required for recovery.

- Capability or configuration version.

It should not include document contents, passwords, private memory or unrestricted filesystem listings.

### Capability reporting

The bridge reports what it implements and what is locally configured. The backend compares that report with its authoritative tool catalogue.

For example, a bridge might implement search_files but lack a configured directory for that tool. In that case, the tool implementation exists, but the capability is not ready for the corresponding operation.

Capability reporting is advisory. The backend must revalidate capability at dispatch, and the bridge must independently validate the actual operation.

## 04.10.07 Duplicate delivery and operation deduplication

Polling can return the same logical operation more than once if acknowledgement or result delivery is interrupted. NEXUS must treat duplicate delivery as a normal failure scenario, not an exceptional impossibility.

### Required behavior

- The same operation_id and same operation fingerprint must map to the same logical operation.

- A duplicate delivery must not create a new logical task step.

- Reuse of an operation ID with different arguments, tool version or target device must be rejected.

- An active duplicate should return its known status where possible.

- A completed duplicate should return the known outcome when the bridge has sufficient durable evidence.

- An operation with an unresolved external effect must be reconciled before a potentially unsafe retry.

- The backend must persist operation intent before dispatch.

- The bridge should maintain a durable operation journal if the chosen local persistence design supports it.

The operation fingerprint should represent the normalized tool, schema version, arguments and target device. It must not be used as a substitute for authentication or authorization.

### Important crash window

Consider this sequence:

1. The bridge receives an operation.

2. The bridge creates an external side effect.

3. The bridge crashes before recording the result.

4. The bridge restarts and receives the same operation again.

A deduplication table alone cannot prove whether the external action happened if the crash occurred between steps 2 and 3.

The correct response is to reconcile the external state when possible. If the result remains unknowable, retain UNCERTAIN rather than pretending that exactly-once execution has been achieved.

## 04.10.08 Disconnects, reconnects and recovery

The bridge protocol must support both short network interruptions and longer outages.

### Backend unavailable

When the backend cannot be reached:

- The bridge stops requesting new operations.

- It uses bounded exponential backoff with jitter rather than polling continuously.

- It preserves any locally recorded operation journal.

- It does not invent new work or change task ownership.

- It reports unresolved operations after reconnection.

The bridge should not queue arbitrary new user instructions locally in the first release. Durable task acceptance and scheduling remain backend responsibilities.

### Bridge unavailable

When a target bridge becomes unavailable:

- The backend stops new dispatches to that device.

- Tasks that have not dispatched remain recoverable according to their state.

- Operations already dispatched are assessed for possible execution.

- The backend does not silently move the task to another developer's computer.

- The user receives a truthful status and a useful next step.

### Reconnection procedure

1. Reauthenticate the bridge.

2. Verify the device is still registered and not revoked.

3. Verify protocol and capability compatibility.

4. Exchange bounded information about unresolved operations.

5. Compare the bridge's operation journal with backend records.

6. Reconcile dispatched or uncertain operations.

7. Revalidate current permissions and approvals.

8. Resume only operations that are safe and eligible to continue.

A stale approval must not become valid merely because a device reconnects. Similarly, restoring a backend database backup must not silently reinstate a revoked device.

## 04.10.09 Timeouts, leases and stale dispatches

The protocol must define distinct time limits for different stages.

| **Timeout category** | **Purpose** |
| --- | --- |
| Poll request timeout | Limits how long a bridge waits for a polling response |
| Dispatch deadline | Limits how long an operation remains eligible for dispatch |
| Acknowledgement timeout | Detects that delivery acknowledgement is missing |
| Tool execution timeout | Bounds a specific tool's execution |
| Result-report timeout | Detects that an outcome has not reached the backend |
| Heartbeat threshold | Determines when a bridge should be considered offline |
| Claim or lease expiry | Allows recovery from a worker that may have stopped progressing |

These timeouts are related but not interchangeable. For example, an acknowledgement timeout does not establish that execution failed.

### Lease requirements

If the backend uses leases to coordinate workers:

- Claims must be atomic.

- Claims should include a worker identity and generation or fencing token.

- A stale worker must not overwrite a newer authoritative task state.

- Lease expiry does not prove that an old bridge operation stopped.

- Any external side effect that might have happened must be reconciled before unsafe retry.

- Expired dispatch deadlines must be enforced when the bridge receives or executes the request.

Actual timeout values should be selected after measuring normal network behavior, tool durations and recovery scenarios.

## 04.10.10 Security requirements for bridge communication

The transport must not be considered trustworthy merely because it runs on a private LAN.

Required controls:

- Authenticate each bridge independently.

- Validate the intended target device on every operation.

- Authorize the user, task, tool and operation before dispatch.

- Reject revoked credentials and unsupported security-sensitive protocol versions.

- Protect against replay and duplicate side effects.

- Apply payload-size and request-rate limits.

- Keep PostgreSQL and the model endpoint private to their intended consumers.

- Avoid public internet exposure and port forwarding for the initial deployment.

- Use TLS where required by the LAN threat model and selected authentication scheme.

- Ensure that the bridge does not expose an inbound listener unless the architecture explicitly requires one.

A polling design can reduce inbound firewall complexity, but it does not eliminate the need for authenticated transport, server-side authorization or local validation.

### Security failure behavior

| **Condition** | **Required behavior** |
| --- | --- |
| Invalid device credential | Reject the request |
| Revoked device | Block new dispatch and execution |
| Mismatched operation or device IDs | Reject and record a safe diagnostic |
| Unknown tool | Reject locally |
| Invalid or expired approval | Do not execute |
| Unavailable policy service | Fail closed for operations requiring policy validation |
| Invalid response correlation | Do not record success |
| Missing result after possible execution | Reconcile or retain uncertainty |

## 04.10.11 Implementation work packages

| **Work item** | **Owner** | **Acceptance condition** |
| --- | --- | --- |
| Bridge protocol schema | Developer 2, reviewed by all | Request and response fixtures agreed |
| Device authentication | Developer 1 + Developer 2 | Invalid and revoked credentials rejected |
| Polling and dispatch | Developer 1 | Only eligible operations are returned to the authenticated target |
| Bridge request validation | Developer 2 | Invalid operations rejected before execution |
| Heartbeat and capabilities | Developer 2 | Online status and capability readiness distinguished |
| Operation deduplication | Developer 1 + Developer 2 | Duplicate delivery does not create duplicate logical operations |
| Recovery and reconciliation | Developer 1, supported by Developer 2 | Lost-response cases do not trigger unsafe blind retries |
| Integration and security tests | All three | Disconnect, revocation, replay and cross-device tests pass |

Developer 3 should provide valid, invalid and malicious planner proposals as test fixtures, but must not implement an alternative bridge communication protocol.

## 04.10.12 Required integration tests

The initial protocol must pass these scenarios:

- A registered bridge authenticates and reports its capabilities.

- An unregistered bridge cannot poll for work.

- A bridge cannot receive another device's operation.

- An offline device does not cause silent rerouting.

- Repeated polling does not create duplicate task steps.

- Repeated delivery of the same operation ID does not blindly repeat a side effect.

- Reusing an operation ID with different arguments is rejected.

- A lost acknowledgement is handled without assuming execution did not occur.

- A lost result after execution triggers reconciliation.

- A backend restart recovers eligible and uncertain operations correctly.

- A revoked bridge remains blocked after reconnecting.

- An expired approval cannot authorize dispatch.

- Unsupported protocol or tool versions fail closed.

- Three bridges can communicate concurrently without mixing task ownership.

- Heartbeat and diagnostics do not expose secrets or private file contents.

These tests must be automated where practical, with real Windows integration tests for bridge behavior and PostgreSQL tests for durable coordination.

## 04.10.13 Recommended initial decisions

The following choices are recommended for the first release, subject to the evidence and compatibility checks already identified.

| **Decision** | **Recommendation** | **Status** |
| --- | --- | --- |
| Bridge communication | Authenticated outbound polling | Provisional |
| Operation authority | Backend task and policy state | Required architectural invariant |
| Local execution validation | Independent Windows bridge checks | Required architectural invariant |
| Device credentials | Unique, independently revocable credentials | Required architectural invariant |
| Operation identity | Stable operation ID plus per-attempt ID | Required architectural invariant |
| Duplicate delivery | Deduplication plus reconciliation | Required architectural invariant |
| Retry behavior | Tool-specific, never blindly retry uncertain side effects | Required architectural invariant |
| Capability discovery | Versioned capability report with dispatch-time revalidation | Proposed implementation |
| Real-time updates | Polling first; persistent connection only if measured need justifies it | Provisional |

## 04.10.14 Definition of done

- The registration and authentication protocol is documented.

- The bridge communication schema is versioned and tested.

- Polling returns only eligible operations for the authenticated device.

- Heartbeat and capability states have distinct meanings.

- Acknowledgement, execution and result persistence are separate events.

- Duplicate delivery and crash-window recovery are tested.

- Disconnect and reconnect behavior is deterministic and safe.

- Revocation blocks new unauthorized operations.

- Security-sensitive failures fail closed.

- Three-device integration tests pass on the intended LAN.

- The team documents unresolved timeout, transport and credential decisions.

Section exit criterion: NEXUS can securely deliver an authorized operation to the correct Windows bridge and recover from communication failures without confusing delivery with execution or assuming exactly-once behavior.
