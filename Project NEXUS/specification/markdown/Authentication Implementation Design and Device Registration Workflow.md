## 04.09.01 Purpose

NEXUS must distinguish three things that are easy to confuse:

1. Who is requesting an action? — user identity.

2. Which computer should perform it? — registered device identity.

3. Is this particular operation permitted? — authorization and policy.

A logged-in user must not automatically gain access to another developer's computer. A registered computer must not automatically be allowed to perform every tool operation. A valid task ID or device ID must not be treated as proof of permission.

This section defines the proposed authentication and device-registration workflow for the three-developer LAN deployment.

The initial design should remain small enough for a 10–12 week project while supporting revocation, task ownership, independent Windows bridges and reliable testing.

## 04.09.02 Identity model

### User identity

Represents a human using the CLI.

Authenticates requests and determines ownership of tasks, memory, approvals and personal history.

### Device identity

Represents one registered Windows computer and its bridge.

Authenticates the bridge, reports its capabilities and limits which computer may receive an operation.

### Execution identity

Represents the actual local process and its operating-system privileges.

Determines what the bridge process can physically access on Windows. NEXUS should run the bridge with the minimum privileges needed.

These identities are related but not interchangeable.

For example, a user may be authenticated successfully but still lack permission to target a device. A bridge may authenticate successfully but still reject a filesystem operation because the requested directory is outside its locally configured scope.

## 04.09.03 Authentication approach

Two user-authentication approaches are reasonable:

| **Approach** | **Advantages** | **Trade-offs** |
| --- | --- | --- |
| Local NEXUS accounts | Independent of an external identity provider; suitable for a small LAN team | NEXUS must manage passwords, sessions, account recovery and revocation |
| Existing identity provider | Can reuse organizational accounts and existing access controls | Requires an available provider and integration work |

Provisional recommendation: use local NEXUS accounts for the initial deployment unless the team already has a suitable identity provider that it is authorized to use.

This is a proposed decision, not a confirmed implementation choice.

### If local accounts are selected

The implementation should provide:

- Unique user identifiers and unique login names.

- Password hashing using a suitable password-hashing algorithm and secure parameters.

- Generic login failure messages that do not reveal whether a particular account exists.

- Rate limiting for repeated failed login attempts.

- An account-disable mechanism.

- A controlled initial account-creation process.

- No default shared password for all three developers.

- No plaintext passwords in configuration files, command-line arguments or logs.

Passwords must never be stored as reversible plaintext.

## 04.09.04 CLI session and token lifecycle

The CLI needs a way to authenticate API requests without asking the developer to enter their password for every command.

### Proposed session design

1. The user runs nexus login.

2. The CLI sends credentials over the configured authenticated API connection.

3. The backend validates the credentials and issues a short-lived access token.

4. The CLI stores the token using an approved local credential-storage mechanism.

5. Subsequent commands send the access token to the API.

6. When the token expires, the CLI uses the selected reauthentication or refresh mechanism.

7. Logout and account revocation invalidate the relevant session or refresh credentials according to the chosen session design.

A short-lived access token does not automatically provide immediate revocation. If revocation must take effect before a token expires, the backend needs an appropriate session, token-version or revocation-check mechanism.

### Token design requirements

| **Requirement** | **Rule** |
| --- | --- |
| Access token | Short-lived; exact lifetime to be selected |
| Refresh mechanism | Optional, subject to the session design |
| Logout | Revoke or invalidate the relevant session credentials |
| Account disabled | Prevent new authorized operations |
| Device credentials | Separate from user tokens |
| Token storage | Protected local storage; Windows Credential Manager is a candidate for Windows-side secrets |
| Logging | Never log complete tokens or authorization headers |
| Expiration | Expired credentials must not authorize new protected requests |

The final implementation must choose one coherent token lifecycle rather than combining access-token and refresh-token examples without defining how revocation works.

### CLI behavior

Illustrative commands:

nexus login

nexus status

nexus logout

The CLI should fail clearly when credentials are absent or expired. It must not silently fall back to another developer's credentials, a shared account or unauthenticated access.

## 04.09.05 Device registration workflow

Every Windows bridge needs its own registered identity and credentials.

The registration process should bind a backend device record to a particular bridge installation. The exact provisioning method remains open because it depends on the selected bridge transport and authentication mechanism.

### Proposed first-registration sequence

### 1

User authenticates

The CLI establishes the user's identity.

### 2

Registration is initiated

The backend verifies that the user is permitted to register a device.

### 3

Device identity is provisioned

A unique device identity and credential are created or securely enrolled.

### 4

Bridge authenticates

The Windows bridge proves possession of its credential.

### 5

Device is verified

The backend checks identity, status and ownership.

### 6

Capabilities are reported

The bridge reports supported tools and local configuration status.

### 7

Device becomes usable

The device can receive only authorized operations.

A device must not be marked usable merely because a registration request was received. The backend must verify that the bridge can authenticate using the registered identity.

### Device record

The logical device record should include:

- device_id

- owner_user_id

- Human-readable device name

- Device status

- Credential reference or credential metadata

- Registration timestamp

- Last successful authentication or heartbeat

- Revocation timestamp, if applicable

- Reported bridge protocol and tool capabilities

- Configuration or capability version, where needed

Do not store a raw device credential in ordinary device metadata. Store only what is required for the selected authentication mechanism, with protected key material handled separately.

The device ID is an identifier, not a secret.

## 04.09.06 Device ownership and targeting

For the initial release, use owner-only device targeting as the proposed default.

A user may target their own registered devices. Cross-user device sharing is deferred until a deliberate sharing model exists.

Authorization must check the authenticated user against the authoritative device record and the task's target device.

The following must be denied unless a later, explicit sharing feature authorizes them:

- User A targeting User B's device.

- User A reading task results associated with User B.

- A request body claiming a different user identity.

- A bridge attempting to impersonate a different registered device.

- A task silently moving to another device because its intended target is offline.

A default device can be convenient for the CLI, but the resolved device must be displayed or otherwise unambiguously determined before submission. The backend must persist the actual target rather than relying on a mutable CLI preference later.

## 04.09.07 Request authorization sequence

Authentication alone is insufficient. Every protected request must pass authorization checks appropriate to that operation.

The proposed backend sequence is:

1. Authenticate the caller.

2. Resolve the authoritative user identity.

3. Validate request structure and limits.

4. Load the task, device or other resource from authoritative storage.

5. Verify resource ownership and the requested action.

6. Validate the registered tool and device capability.

7. Evaluate the active security policy.

8. Verify any required approval against the exact operation.

9. Recheck relevant permissions immediately before dispatch.

10. Record the outcome and security-relevant decision.

Not every read request needs all ten steps. For example, listing a user's devices does not require a tool approval. However, any operation that dispatches a computer action must perform the relevant device, policy and execution-time checks.

### Important implementation rule

Never trust a user_id, device_id, risk_tier or approved field simply because a client or model supplied it.

- User identity comes from the authenticated session.

- Device ownership comes from the registered device record.

- Tool risk comes from the authoritative tool definition and policy.

- Approval comes from the persisted approval record and must match the operation.

- Execution state comes from the authoritative task lifecycle.

The backend must not rely on the CLI to enforce these rules.

## 04.09.08 Credential storage, rotation and revocation

### User credentials

If local password accounts are selected, store password hashes using a suitable password-hashing scheme. Session credentials must be handled separately from passwords.

The CLI should avoid storing tokens in plaintext configuration files. For Windows-side secrets, Windows Credential Manager is a candidate; the chosen mechanism must be validated for the actual CLI and bridge processes.

### Device credentials

Each registered bridge needs its own credential. Shared credentials across all developers' devices would make individual revocation and incident investigation much harder.

The team must define:

- Initial credential provisioning.

- Where credentials are stored.

- How authentication proves possession of a credential.

- Credential rotation.

- Device re-registration after credential loss.

- Revocation propagation.

- Handling of a bridge that is offline during revocation.

The exact credential type—such as a random per-device secret or a public-key-based method—remains an open design decision.

### Revocation behavior

| **Event** | **Required behavior** |
| --- | --- |
| User account disabled | Block new protected requests |
| User session revoked | Reject subsequent use of the revoked session |
| Device revoked | Block new dispatches to that device |
| Device credential rotated | Reject the old credential after the defined transition |
| Device goes offline | Do not silently reroute its tasks |
| Device reconnects | Reauthenticate and reconcile unresolved operations before resuming them |

Revocation cannot undo a file already created or another side effect already completed. NEXUS must report what has occurred and reconcile any uncertain operations.

For a queued task, revocation should prevent dispatch. For an operation already in flight, the system must apply its cancellation and recovery rules rather than falsely claiming the operation was stopped.

## 04.09.09 Authentication and device-registration tests

The following cases should be implemented before authentication is considered complete.

| **Test** | **Expected outcome** |
| --- | --- |
| Valid user login | Session issued |
| Invalid credentials | Generic authentication failure |
| Disabled account login | Rejected |
| Expired access token | Protected request rejected unless valid refresh/re-auth succeeds |
| Revoked session | Revoked session rejected |
| User guesses another user's task ID | Access denied |
| User supplies another user_id in request data | Does not change authenticated identity |
| Unregistered bridge connects | Rejected |
| Bridge uses another device's credential | Rejected |
| Revoked device reconnects | Authentication or dispatch remains blocked |
| User targets another user's device | Access denied |
| Device goes offline during a task | Task remains tied to its target and follows recovery rules |
| Credential is accidentally logged | Security test fails |
| Two devices register concurrently | Each receives a distinct identity and credential |
| Backend restarts | Identity and revocation records remain consistent |

Tests should include concurrent requests and restart behavior, not only isolated login examples.

## 04.09.10 Implementation order and team ownership

| **Work item** | **Owner** | **Completion condition** |
| --- | --- | --- |
| User authentication contract | Developer 1 | Login, identity and error semantics agreed |
| User/session persistence | Developer 1 | Session lifecycle and revocation tests pass |
| Device registration contract | Developer 1 + Developer 2 | Registration, ownership and status semantics agreed |
| Windows credential handling | Developer 2 | Credentials are protected and independently revocable |
| Bridge authentication | Developer 2 | Invalid, unknown and revoked credentials are rejected |
| Authorization integration | Developer 1 | Cross-user and cross-device access is denied |
| Planner identity boundary | Developer 3 | Planner cannot assign authoritative identity or permission |
| Security integration tests | All three | Authentication, revocation and dispatch checks pass |

Developer 3 should implement the planner against the authenticated task context supplied by the application. The planner should not authenticate users, provision devices or decide access rights.

### Recommended implementation sequence

1. Agree on the user-authentication and device-registration contracts.

2. Implement user records and the selected session mechanism.

3. Implement login and protected API requests.

4. Add device registration and unique credential provisioning.

5. Authenticate the bridge independently of the CLI.

6. Add device ownership checks to task submission and retrieval.

7. Add revocation behavior and tests for queued and in-flight tasks.

8. Verify the complete workflow with multiple users and devices.

Do not add shared device access or administrative impersonation during this milestone.

## 04.09.11 Open decisions

These decisions must be closed before the corresponding implementation begins.

| **Decision** | **Current status** | **Evidence required** |
| --- | --- | --- |
| Local accounts vs existing identity provider | Provisional: local accounts | Confirm no suitable existing provider is required |
| Access-token and session design | Open | Threat model and CLI lifecycle |
| Refresh tokens | Open | Need for persistent CLI sessions and revocation |
| Device credential type | Open | Transport choice and credential-storage feasibility |
| Device registration authorization | Open | Initial enrollment and recovery workflow |
| Windows credential storage | Provisional: Credential Manager candidate | Test access from intended process |
| Revocation of in-flight operations | Partly specified | Fault-injection and recovery tests |
| Device sharing | Deferred | Explicit sharing requirements and authorization design |
| Administrative access | Open | Determine who can disable accounts or revoke devices |

## 04.09.12 Definition of done

- User and device identities are distinct.

- Authentication is required for protected API operations.

- Task ownership is derived from authenticated identity.

- Device registration and bridge authentication work independently of user login.

- Each device has independently revocable credentials.

- Device ownership and targeting are enforced server-side.

- Revocation prevents new unauthorized dispatches.

- Tokens and device credentials are not exposed in logs or ordinary configuration.

- Multi-user and multi-device isolation tests pass.

- Offline-device and in-flight revocation behavior is documented.

- No critical or high-severity authentication or authorization defects remain.

Section exit criterion: NEXUS can identify the requesting user, authenticate the target bridge and enforce access restrictions before any computer operation is dispatched.
