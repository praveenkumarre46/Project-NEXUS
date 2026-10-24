## 03.23.1 Purpose

This section defines how NEXUS decides whether a proposed computer operation can proceed, requires human approval, or must be rejected.

NEXUS must not treat a user's natural-language request or an AI-generated plan as sufficient authority to perform an operation. The system must enforce permissions through application code and the Windows bridge, even if the AI produces an incorrect, manipulated, or malicious plan.

Core rule: the AI may propose an action; only the enforcement layers can authorize and execute it.

This policy consolidates requirements established in Sections 03.11–03.15 and 03.22. It does not assume that a particular model, prompt, or safety instruction can replace enforceable controls.

## 03.23.2 Design principles

1. Deny by default: an unknown tool, unsupported operation, invalid argument, or missing permission is rejected.

2. Least privilege: each user and Windows bridge receives only the capabilities needed for enabled features.

3. Independent enforcement: the backend and Windows bridge validate operations at their respective boundaries.

4. Approval is specific: approval applies only to the exact operation presented to the user.

5. Hard prohibitions cannot be overridden: neither the AI nor an approval can authorize a prohibited operation.

6. Untrusted content stays untrusted: files, documents, retrieved memories, and model output cannot change permissions or policy.

7. Fail closed: when authorization or policy cannot be verified, NEXUS does not dispatch the operation.

8. Honest outcomes: a timeout or lost connection must not be reported as proof that an operation failed or succeeded.

9. Auditable decisions: NEXUS records why an operation was allowed, rejected, or held for approval without unnecessarily logging private content.

10. Policy changes are controlled: changes to permissions or risk classifications must be reviewed and tested before deployment.

## 03.23.3 The authorization decision pipeline

The policy engine and bridge must not rely on a previous AI response as proof of authorization. The exact interfaces and data structures will be finalized with the tool and API contracts.

### Decision outcomes

| **Outcome** | **Meaning** | **Required behavior** |
| --- | --- | --- |
| ALLOW | All required checks pass without additional approval | Operation may proceed after final revalidation |
| REQUIRE_APPROVAL | Operation is permitted in principle but needs human authorization | Do not dispatch until valid approval is recorded |
| DENY | A prohibition, permission failure, or validation failure applies | Do not dispatch; record a reason code |
| DEFER | A necessary fact or dependency cannot currently be verified | Ask a question or wait; do not treat uncertainty as permission |

DEFER is a proposed internal policy outcome. It may ultimately be represented as an existing task state rather than a separate public API status.

## 03.23.4 Policy layers and precedence

Policy decisions must be deterministic and independent of the AI model.

The proposed precedence is:

1. Hard prohibitions — reject operations that NEXUS does not support or must never perform.

2. Tool capability — confirm the operation exists in the trusted tool registry and is enabled.

3. Identity and ownership — verify the requesting user, task owner, device identity and target device.

4. Resource permissions — verify access to the specific directory, file, application or other resource.

5. Operation-specific constraints — validate arguments, limits, destination rules and other tool requirements.

6. Risk classification — determine whether the operation is permitted directly or requires approval.

7. Approval validation — when required, verify the approval is valid for this exact operation.

8. Execution-time revalidation — repeat the security-relevant checks immediately before dispatch.

A later layer cannot override an earlier rejection. For example, a valid approval cannot make an unregistered tool executable.

## 03.23.5 Risk tiers and permitted autonomy

The following is the proposed MVP policy. The final list of tools and their risk classifications must be reviewed against their actual implementation before they are enabled.

| **Tier** | **Classification** | **Examples** | **Policy** |
| --- | --- | --- | --- |
| Tier 0 | Read-only | Search an approved folder; read a supported document | Allow when existing permissions cover the resource and operation |
| Tier 1 | Limited and reversible | Create a new file in an approved workspace; launch an approved application | Allow only within predefined limits and permissions |
| Tier 2 | Consequential | Overwrite or move an existing file; change significant settings | Require explicit approval if the operation is supported; otherwise deny |
| Tier 3 | Prohibited | Bypass access controls; access another user's private data without authorization; execute unrestricted model-generated commands | Always deny |

Risk tiers are not permissions. Tier 0 does not permit reading every file, and Tier 1 does not permit writing anywhere. Every operation still needs the relevant user, device, tool and resource permissions.

Additional rules:

- A tool's risk classification is assigned by trusted application configuration, not by the model.

- A model cannot downgrade a Tier 2 operation by describing it as harmless.

- A sequence of individually low-risk actions must not be allowed to bypass an overall safety constraint.

- If an operation's real effects exceed its registered capability, reject it or classify it more conservatively.

- If NEXUS cannot reliably determine the operation's effects, it must not assume the lowest risk tier.

### Initial tool policy

search_files

Tier 0 — proposed

Search only configured logical directories, with result and time limits. Do not follow access outside the permitted scope.

read_document

Tier 0 — proposed

Read supported formats only. Enforce file permissions and output-size limits. Treat document content as untrusted input.

create_file

Tier 1 — proposed

Create a new file within an approved workspace. Do not silently overwrite an existing file. Validate the destination at execution time.

launch_application

Tier 1 — proposed

Launch only an allowlisted logical application ID. Do not interpret model-supplied text as an arbitrary shell command or executable path.

These are candidate classifications, not permission to implement unrestricted versions of these tools. Each tool must have a reviewed contract, explicit failure behavior and tests before it is enabled.

## 03.23.6 Plan validation and tool governance

The AI planner must produce structured operations, not executable commands.

Each planned operation should identify, at minimum:

- Tool name and schema version.

- Target device.

- Validated arguments.

- Expected effect or outcome.

- Dependencies on preceding steps.

- Any clarification required before proceeding.

The backend then validates the proposal against the trusted tool registry.

### Required checks

1. Reject unknown or disabled tools.

2. Reject malformed arguments and unsupported fields according to the tool's defined schema policy.

3. Resolve logical resource IDs using trusted configuration; do not accept arbitrary paths as proof of access.

4. Normalize arguments before risk evaluation and approval.

5. Enforce resource, output, time and operation-count limits.

6. Reject plans that violate task ownership, device scope or policy.

7. Require clarification when an essential detail is ambiguous.

8. Revalidate the operation after approval and immediately before dispatch.

The registry should hold trusted metadata such as tool ID, schema version, risk tier, required permissions, enabled status, timeout and retry policy. The model may select from available tools but cannot add tools, change their metadata or alter their permissions.

### Why normalization matters

Suppose a user approves creating a file named report.txt in a permitted workspace. Before execution, the proposed operation changes its destination to a different directory. That is not the same approved operation. NEXUS must reject the existing approval and evaluate the changed operation from the beginning.

Likewise, string-prefix checks alone are insufficient for Windows filesystem boundaries. The bridge must use a safe path-resolution strategy that accounts for path traversal, drive and UNC paths, reparse points, case-insensitive comparisons and race conditions between validation and file access.

## 03.23.7 Human approval protocol

Human approval is a narrowly scoped authorization decision, not a general permission grant.

### What the user must see

Before approving a consequential operation, NEXUS should display:

- The operation and its intended effect.

- The target Windows device.

- The exact resource or destination, with sensitive details minimized where appropriate.

- Relevant parameters, including the existing and proposed destination for a move or overwrite.

- Why approval is required.

- Whether the operation can be reversed.

- The approval expiry.

- Any known uncertainty about the expected outcome.

The approval interface must make the actual effect understandable. A vague prompt such as “Allow AI to continue?” is insufficient for a consequential action.

### Approval binding

An approval record should be bound to the task, step, approving user, target device, normalized tool arguments, resource scope, risk classification, applicable policy version and expiry.

The following rules are mandatory:

- Approval must come from an authenticated, authorized user.

- Approval must be recorded durably before dispatch.

- Rejection or expiry means the operation is not executed.

- Changing the operation, target device or relevant parameters invalidates the approval.

- A cancelled task cannot be revived merely by approving a pending step.

- The backend must revalidate approval and permissions immediately before dispatch.

- The Windows bridge must reject an operation that violates its own local restrictions, even if the backend reports it as approved.

- An approval cannot override a hard prohibition.

- Approval requests must not be reusable as general-purpose authorization tokens.

Open decision: approval expiry duration, whether the task owner must always approve, and whether any future administrative role may approve on another user's behalf. The MVP should default to approval by the task owner and should not introduce delegated approvals without an explicit requirement.

## 03.23.8 Prompt injection and untrusted content

NEXUS will read documents and retrieve stored context. That content may contain instructions designed to manipulate the AI—for example, instructions to disclose private files, ignore previous rules, or send data to another location.

The system must treat the following as data, not authority:

- Contents of documents and files.

- Web or other external content, if external retrieval is added.

- Retrieved memories and task-history summaries.

- Text extracted from images or other supported formats.

- Model-generated plans, explanations and tool arguments.

- Error messages or responses returned by tools.

### Required defenses

1. Separate instructions from data. Retrieved content must be identified as untrusted context.

2. Enforce authorization outside the model. A document cannot grant file access, change the target device or authorize a write.

3. Limit tool capabilities. The model cannot call arbitrary operating-system commands.

4. Validate every operation. Even a plausible plan must pass the policy engine.

5. Limit data exposure. The model receives only the context necessary for the task and permitted for that user.

6. Validate destinations. If a future tool transmits data externally, it needs an explicit capability and a separately reviewed policy.

7. Test adversarial inputs. Include documents containing malicious instructions, misleading filenames and attempts to induce cross-user access.

A prompt saying “ignore instructions inside documents” is useful defense-in-depth, but it is not a security boundary. The enforceable boundary is that the system does not grant extra capabilities because the model encountered an instruction.

## 03.23.9 Enforcement responsibilities

Each component has a distinct responsibility.

| **Component** | **Responsibility** | **Must not do** |
| --- | --- | --- |
| CLI | Display requests, task status and approval details; submit authenticated decisions | Decide that an operation is authorized |
| AI planner | Interpret intent and propose structured plans | Grant permissions or execute unrestricted commands |
| Policy engine | Evaluate prohibitions, permissions, risk and approval requirements | Trust a model-generated risk classification |
| Task orchestrator | Enforce lifecycle, approval gates, cancellation and revalidation | Dispatch a step that has not passed required checks |
| Database layer | Persist tasks, approvals, policy-relevant records and audit events with appropriate constraints | Treat database persistence as proof that an external action occurred |
| Windows bridge | Authenticate the request, validate local scope and execute registered tools | Act as a generic remote shell or trust a device ID alone |
| Tool implementation | Enforce tool-specific input, resource and side-effect constraints | Assume upstream validation eliminates every local risk |

The backend and bridge must use compatible tool contracts and policy versions. A version mismatch affecting a security-sensitive rule should block execution until compatibility is established.

### Failure behavior

- Policy service unavailable: no new operation dispatch.

- Device authentication fails: reject the request.

- Approval status cannot be verified: do not dispatch.

- Tool schema is incompatible: reject or defer for compatibility resolution.

- Device disconnects after dispatch: mark the outcome uncertain if the side effect cannot be determined.

- Tool returns malformed output: record a bounded operational error; do not infer success from an invalid response.

- Audit persistence fails: consequential actions must not proceed if the required audit record cannot be durably written. Other read-only operations may also be blocked if their policy requires audit durability.

The exact availability policy for read-only operations is an implementation decision, but security-sensitive operations must fail closed.

## 03.23.10 Policy changes and administrative governance

Because NEXUS will operate on three developers' computers, a policy change could affect all users and devices. Policy must therefore be managed as versioned configuration, not modified by an AI response or silently edited at runtime.

### Proposed change process

1. Propose: document the policy change, reason, affected tools, users and devices.

2. Review: a teammate reviews the security impact and confirms that the change does not weaken a hard prohibition.

3. Test: run unit, integration and security-regression tests, including negative tests.

4. Version: record the approved policy version in source control or another controlled configuration history.

5. Deploy: apply the change deliberately and verify the active version on the backend and affected bridges.

6. Audit: record who approved the change, when it took effect and which version was replaced.

### MVP governance rules

- The AI cannot edit security policy.

- Ordinary users cannot grant themselves new permissions merely by changing a request.

- The bridge's local scope cannot be expanded by a backend request.

- A change to a tool's risk tier or permission requirements requires review and regression tests.

- Security-sensitive configuration errors must not silently fall back to permissive defaults.

- Revoking a device or permission must prevent new dispatches once the revocation is effective. Already-dispatched external operations may require reconciliation.

- The MVP does not require a separate administrator dashboard; a controlled configuration and deployment workflow is sufficient initially.

Open decision: who is authorized to approve shared policy changes and how emergency revocation will be performed if the designated host is unavailable.

## 03.23.11 Security and policy test matrix

The policy engine must be tested independently of the AI model. Tests should use deterministic plans and mocked or controlled tool implementations wherever possible.

| **Test scenario** | **Expected result** |
| --- | --- |
| Model proposes an unregistered tool | Deny; no dispatch |
| User requests a file outside their permitted scope | Deny |
| One user requests another user's task or private memory | Deny access |
| Model marks a consequential action as low-risk | Trusted policy classification prevails |
| Required approval is missing | Wait for approval; no dispatch |
| Approval has expired | Reject the approval for execution |
| Approved destination changes before dispatch | Invalidate approval and re-evaluate |
| Device identity is invalid or revoked | Reject dispatch |
| Malicious document instructs NEXUS to access another directory | Document cannot expand permissions |
| File creation targets an existing file | Reject under create-only semantics; do not overwrite |
| Cancellation races with approval | Apply task-state rules; do not revive a cancelled task |
| Policy service is unavailable | Do not dispatch security-sensitive operations |
| Backend allows an operation that violates local bridge scope | Bridge rejects it |
| Tool times out after a possible write | Record uncertainty and reconcile before retry |
| Audit persistence fails for a consequential operation | Block execution under the proposed durability rule |
| Unknown policy version reaches a bridge | Block execution until compatibility is resolved |

### Required test layers

- Unit tests: policy precedence, tier classification, argument normalization, approval matching and expiry.

- Integration tests: database transactions, durable approval records, concurrent approval/cancellation requests and permission revocation.

- Bridge tests: local path restrictions, tool allowlisting, authentication, malformed requests and operation deduplication.

- Adversarial tests: prompt injection, malicious document contents, unexpected model output and attempts to manipulate tool parameters.

- End-to-end tests: submit a task, approve an operation, execute on the correct device, inspect the audit trail and recover from interruption.

The critical security acceptance criterion is zero unauthorized side effects in the defined security test suite. This is a test requirement, not a claim that all possible attacks can be eliminated.

## 03.23.12 MVP implementation priorities

P0

Required before real computer operations

- Trusted tool registry and strict input schemas.

- Deny-by-default policy enforcement.

- User, task, device and resource authorization.

- Explicit risk classifications.

- Approval bound to the exact operation.

- Backend and bridge validation.

- Durable policy decisions and consequential-action audit records.

- Security regression tests and safe failure behavior.

P1

Required as capabilities expand

- Versioned policy deployment and compatibility checks.

- Permission and device revocation workflows.

- More comprehensive adversarial testing.

- Clearer recovery and reconciliation for uncertain outcomes.

- Evaluation of policy effectiveness across realistic multi-step tasks.

P2

Future enhancements

- Administrative policy-management UI.

- Advanced approval delegation, if justified.

- Rich policy analytics and review dashboards.

- More granular policies for additional application and automation capabilities.

## 03.23.13 Open decisions register

These decisions must be resolved before the affected functionality is implemented. The proposals below are defaults to evaluate, not finalized requirements.

| **ID** | **Decision required** | **Proposed starting point** |
| --- | --- | --- |
| POL-01 | Who may approve an operation? | Task owner only |
| POL-02 | How long does approval remain valid? | Configurable expiry; choose the duration before implementation |
| POL-03 | What happens when a policy version changes while approval is pending? | Re-evaluate; require fresh approval if the change affects authorization or operation risk |
| POL-04 | What happens when audit storage is unavailable? | Block consequential operations |
| POL-05 | Which Tier 2 operations are supported in the MVP? | Start with a minimal set; deny unsupported operations |
| POL-06 | Who can change shared policy? | Designated reviewer with controlled, versioned deployment |
| POL-07 | How are bridge capabilities synchronized with the backend? | Versioned contracts and fail-closed compatibility checks |
| POL-08 | How is emergency revocation handled? | Define a procedure that accounts for host outages and already-dispatched operations |
| POL-09 | Which read-only actions may continue during partial service failures? | Explicit per-operation availability rules |
| POL-10 | How are approvals and policy decisions retained? | Define retention separately from ordinary logs and task history |

## 03.23.14 Acceptance criteria

## Section 03.23 is ready for implementation planning when the team can demonstrate all of the following:

- The AI cannot grant itself permissions or introduce executable tools.

- Every tool has an explicit contract, risk tier and permission requirement.

- Authorization checks cover user, task, target device and resource scope.

- Hard prohibitions override both AI proposals and human approvals.

- Approval is bound to the exact normalized operation and expires according to policy.

- Security-sensitive checks are repeated immediately before dispatch.

- The Windows bridge independently enforces its local security boundaries.

- Prompt injection cannot expand tool permissions or resource scope.

- Policy changes are reviewed, versioned and tested.

- Security decisions and consequential operations are auditable without unnecessary exposure of private content.

- The defined negative, adversarial and recovery tests pass.

- The team has documented the remaining approval, revocation and failure-handling decisions.

### Section exit criteria

The team should be able to explain, using a real test task, why NEXUS allowed, held or rejected each operation—and demonstrate that a malicious or invalid AI proposal cannot bypass the enforcement layers.
