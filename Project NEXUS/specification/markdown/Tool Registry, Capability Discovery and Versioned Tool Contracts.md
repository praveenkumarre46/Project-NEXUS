## 03.31.1 Purpose

NEXUS needs a controlled way to discover what it can do on a user's Windows computer, determine which operations are appropriate for a request, and execute those operations safely.

The AI planner must not invent tools, create new capabilities dynamically or assume that every registered tool is available on every device.

For example, a user might ask:

Find the design documents in my project folder, summarize the relevant one, and save a summary to my workspace.

NEXUS may need to use three capabilities:

1. Search files in a permitted directory.

2. Read a supported document.

3. Create a new file in an approved workspace.

Each capability has different input requirements, permissions, risks, timeouts and verification rules. The planner should choose from these registered capabilities rather than generate arbitrary commands.

Core design rule: the tool registry defines what NEXUS can attempt; the policy engine decides whether a particular operation is allowed; the Windows bridge independently enforces the local execution boundary.

## 03.31.02 Design objectives

The registry must provide:

- A single authoritative definition of supported tools and their schemas.

- Explicit tool IDs, schema versions, risk classifications and required permissions.

- Capability discovery based on the target device's actual configuration.

- Input and output validation at appropriate trust boundaries.

- Tool-specific timeouts, retry rules and verification requirements.

- Compatibility checks between the backend and Windows bridge.

- Controlled enablement, disablement and version migration.

- Testable contracts that do not require a live AI model.

- Clear separation between a tool's technical capability and authorization to use it.

The registry is not a list of arbitrary executable commands. It is a controlled catalogue of reviewed application capabilities.

## 03.31.03 Three separate concepts

NEXUS must distinguish three related concepts that are easy to confuse.

1. Tool definition

Describes the tool's stable identity, schema, behavior, risk category, limits, retry semantics and verification requirements.

Example: search_files version 1.

2. Device capability

Describes whether a registered device has a compatible bridge and the local configuration required to support that tool.

Example: the Windows bridge supports search_files and has a configured project directory.

3. Operation authorization

Determines whether the authenticated user may execute a particular tool with particular arguments on the selected device, under the current policy and approval state.

Example: the user can search the configured project directory but cannot search another user's private workspace.

A registered tool may be unavailable on a particular device. A device may support a tool that a particular user is not authorized to use. Neither condition should be inferred from the existence of a tool definition alone.

## 03.31.04 Registry architecture

The proposed architecture has four layers.

Tool catalogue

Reviewed definitions, versions, schemas and execution policies

Capability resolver

Filters by target device, supported version, configuration and current availability

Planner-facing tool descriptions

Provides the model with a bounded, validated list of possible operations

Execution-time enforcement

Validates the proposed operation, applies policy and approval, then dispatches to the bridge

### Authoritative ownership

- The backend owns the authoritative tool catalogue and application-level policy.

- The bridge implements only the tools included in its reviewed and installed tool set.

- The bridge reports its supported tool and schema versions.

- The planner receives only capabilities relevant to the current request and target device.

- The policy engine makes authorization decisions independently of the planner.

- The bridge validates incoming requests again before local execution.

Capability discovery is advisory. A tool shown as available can still become unavailable before execution, so the dispatch path must recheck current conditions.

## 03.31.05 Tool definition contract

Every tool must have a versioned definition. The following fields are proposed as the minimum contract.

| **Field** | **Purpose** |
| --- | --- |
| tool_name | Stable machine-readable tool identifier |
| schema_version | Version of the input/output contract |
| display_name | Human-readable name |
| description | Clear description of what the tool does and does not do |
| input_schema | Required fields, types, constraints and unknown-field behavior |
| output_schema | Structured result fields and size constraints |
| risk_tier | Proposed risk classification, reviewed by the application |
| required_permissions | Permission categories needed to attempt the operation |
| resource_scope | Resources the tool can access, such as configured directory IDs |
| timeout_policy | Dispatch and execution limits |
| retry_policy | Whether and under what conditions retry is allowed |
| verification_policy | How success is established |
| enabled | Whether the tool is available for use |
| implementation_version | Identifies the installed implementation for diagnostics and compatibility |

The registry must not allow model output to change a tool's schema, risk tier, permissions, timeout or retry policy.

Risk classification is not a property the model gets to choose. It must be assigned through the application's reviewed configuration and checked by the execution workflow.

### Illustrative definition

# Illustrative pseudocode, not a complete implementation.ToolDefinition(    tool_name="search_files",    schema_version=1,    risk_tier="read_only",    required_permissions=["files.search"],    timeout_policy="bounded_search",    retry_policy="safe_read_retry",    verification_policy="validate_scoped_results",    enabled=True,)

The real implementation should use typed models and validated configuration. The string values above are examples, not a finalized enum or permissions vocabulary.

## 03.31.06 Initial tool catalogue

The initial registry should remain small enough that the team can review and test every capability thoroughly.

search_files

Read-only

Searches within configured directory IDs. Supports bounded queries, result counts and execution time. Must not expose arbitrary filesystem paths or bypass directory scope.

read_document

Read-only

Extracts bounded content from supported file formats. Must validate file type, file size and access scope. Document content is untrusted input, not an instruction to change permissions.

create_file

Limited write

Creates a new file in an approved workspace. Must reject existing destinations by default, validate path components and enforce output limits. An uncertain result requires reconciliation before retry.

launch_application

Limited action

Launches a locally configured, approved application ID. Must not accept arbitrary executable paths or shell commands. A successful launch does not prove that a later task inside the application succeeded.

These four tools are proposed MVP candidates, consistent with the earlier sections. Their final schemas, supported document formats, permission names, resource limits and verification procedures still need to be agreed before implementation.

## 03.31.07 Input and output schema validation

Validation must occur at more than one boundary.

Backend validation

- Check that the tool exists and is enabled.

- Validate the model's proposed arguments against the registered input schema.

- Reject unsupported fields and invalid values according to the schema policy.

- Resolve logical resource IDs and enforce application-level constraints.

- Apply authorization, risk and approval rules.

- Enforce request-size and resource limits.

Bridge validation

- Verify protocol and tool-schema compatibility.

- Validate the request again against the installed implementation.

- Resolve local directory IDs to configured paths.

- Enforce local filesystem and application restrictions.

- Reject malformed, oversized, conflicting or unauthorized operations.

- Validate outputs before returning them to the backend.

Backend validation and bridge validation are not redundant. The backend prevents invalid requests from entering execution, while the bridge protects the local computer if the backend sends an invalid request or its state is stale.

### Unknown fields and schema changes

The default should be strict validation for tool inputs. An unknown field must not silently acquire meaning or broaden a tool's behavior.

For schema evolution:

- Additive optional fields may be compatible if their semantics are safe and explicitly defined.

- Changes to required fields, argument meaning or security behavior require deliberate versioning.

- The backend must not dispatch a schema version the target bridge cannot support.

- Unsupported versions must return a stable compatibility error.

- The bridge must never guess how to interpret an unfamiliar schema.

## 03.31.08 Capability discovery for each Windows device

NEXUS needs a way to know which tools each bridge can actually support.

When a bridge starts or reconnects, it should report a capability manifest containing:

- Device identity and bridge protocol version.

- Installed tool names and supported schema versions.

- Tool implementation version, where relevant.

- Required local configuration status.

- Capability status and any safe diagnostic reason for unavailability.

The backend should compare this manifest with its authoritative registry. The manifest is evidence of installed capabilities, not permission to introduce new ones.

### Proposed capability states

| **State** | **Meaning** |
| --- | --- |
| AVAILABLE | Compatible tool is installed and required configuration is present |
| UNAVAILABLE | Tool cannot currently execute, for example because a required directory is not configured |
| INCOMPATIBLE | Installed tool or protocol version is unsupported |
| DISABLED | Tool has been explicitly disabled by authorized configuration |
| UNKNOWN | Capability status cannot currently be established |

These are proposed values; exact names can be finalized with the bridge contract.

A capability may become unavailable after discovery—for example, a directory may become inaccessible or an application may be removed. The bridge must check the actual condition at execution time.

### Example

Developer A's Windows bridge has an approved workspace and supports all four initial tools. Developer B's bridge supports search and document reading, but has not configured a writable workspace.

NEXUS should offer file creation on A's device only if all other authorization and policy checks pass. It should not assume B's capability is available just because the backend registry contains create_file.

If a request targets B's device and requires file creation, NEXUS should explain the missing capability or request the necessary local configuration. It must not silently redirect the operation to A's computer.

## 03.31.09 How the AI planner receives tools

The planner should receive a bounded description of the tools relevant to the current request and target device.

That description should include:

- Tool name and schema version.

- Intended purpose and limitations.

- Required input fields and constraints.

- Output shape.

- Relevant resource IDs that the user is allowed to select.

- Tool-specific limits that affect planning.

It should not receive secrets, local credentials or unrestricted private configuration.

### Planner workflow

1. Resolve the authenticated user and explicit target device.

2. Retrieve compatible tools for that device.

3. Filter tools based on relevant permissions and capability availability.

4. Provide the remaining tool descriptions to the model.

5. Receive a structured plan.

6. Validate every proposed tool and argument against the authoritative registry.

7. Run policy and approval checks.

8. Dispatch only eligible operations.

The planner's tool list is a planning aid, not an authorization token. A model may still propose an unknown or unavailable tool; NEXUS must reject it safely.

### Clarification behavior

If no registered tool can complete a required step, the planner should ask for clarification or explain the unsupported capability rather than inventing a new one.

For example, read_document may extract text from a supported document, but that does not automatically mean NEXUS can edit the document's layout or manipulate its user interface. Such capabilities require their own reviewed tool contracts.

## 03.31.10 Tool registration and change control

Tools should be added through a reviewed engineering process, not by allowing the model to register capabilities at runtime.

Proposed lifecycle:

1

Define intended behavior and scope

2

Specify typed input/output schemas

3

Assign risk, permissions and local restrictions

4

Define timeouts, retries and verification

5

Implement backend and Windows bridge support

6

Add unit, contract, security and recovery tests

7

Review and approve the tool definition

8

Enable for a controlled test environment

9

Release and monitor; disable if unsafe

### Enablement and rollback

- Tool definitions should be version controlled and reviewed.

- Enabling a tool on the backend must not automatically enable it on every device.

- A tool may be disabled globally or for a particular device through authorized configuration.

- Disablement must prevent new dispatches.

- In-flight operations must follow their existing execution and reconciliation rules; disabling a tool does not prove an operation stopped.

- Schema upgrades must account for active tasks and bridge compatibility.

- Rollback must not silently reinterpret an already dispatched operation under a different schema.

A registry change that affects risk classification, permissions or execution semantics should receive security review and corresponding regression tests.

## 03.31.11 Timeouts, retries and verification metadata

Every tool must declare its execution behavior before it can be enabled for real operations.

| **Tool** | **Timeout considerations** | **Retry considerations** | **Verification considerations** |
| --- | --- | --- | --- |
| search_files | Bound directory traversal and result count | Retry permitted within budget | Validate results remain within allowed scope |
| read_document | Bound file size and extraction duration | Retry if read remains authorized and safe | Validate extraction status and output limits |
| create_file | Bound content size and filesystem operation time | Reconcile before retrying uncertain writes | Confirm destination and expected file outcome |
| launch_application | Bound launch wait and process checks | Avoid blind repeated launches | Report launch evidence without claiming the entire application task succeeded |

The registry should reference named, validated policies or structured settings rather than accept arbitrary model-generated timeout and retry values.

A tool cannot become safe merely by having a short timeout. The timeout must be paired with correct handling of uncertain outcomes.

## 03.31.12 Registry persistence and implementation choice

The authoritative registry could be represented through version-controlled definitions loaded at startup, database-backed configuration, or a combination of both.

For the initial MVP, a version-controlled catalogue with validated startup loading is a reasonable starting proposal because the team has a small, known tool set and needs clear review history.

Device capability status and user permissions should remain separate from the immutable tool definition.

A possible separation is:

- Tool definitions: reviewed code/configuration, schemas, versions and execution metadata.

- Device capability records: installed versions, configuration status, heartbeat and compatibility.

- Policy configuration: authorized users, scopes, restrictions and approval requirements.

- Execution records: operation IDs, attempts, results and recovery status.

Do not create a dynamic tool-registration database solely because the registry exists. Add that complexity only if there is a real need for runtime administration or a larger tool ecosystem.

### Startup validation

The backend should reject or disable an invalid tool definition when:

- Its schema is malformed.

- Its risk or retry policy is missing.

- Its implementation is unavailable.

- Its schema version is unsupported.

- Required limits are missing or invalid.

- Its declared permissions conflict with the application's supported permission model.

A broken definition must not silently fall back to unrestricted execution.

## 03.31.13 Security and testing requirements

### Security tests

- Unknown tool names are rejected.

- Disabled tools cannot be dispatched.

- A device cannot claim an uninstalled or unsupported capability.

- Unsupported schema versions fail safely.

- Model-supplied arguments cannot expand filesystem scope.

- Tool risk and permissions cannot be changed through model output.

- A tool unavailable on one device is not routed to another device silently.

- A bridge cannot use a valid operation ID to bypass authorization.

- Conflicting reuse of an operation ID is rejected.

- Tool disablement prevents new dispatch without misreporting in-flight results.

### Contract tests

For every tool:

1. Valid input is accepted.

2. Missing required fields are rejected.

3. Invalid types and out-of-range values are rejected.

4. Unknown fields follow the documented strictness policy.

5. Output conforms to the declared schema.

6. Timeouts and error outcomes use stable codes.

7. Retry behavior matches the tool's contract.

8. Verification checks detect incomplete or incorrect results.

9. Backend and bridge agree on schema version and semantics.

### Integration tests

- Start a bridge and verify its capability manifest.

- Disable a tool and verify it is no longer eligible for new execution.

- Change a bridge version and verify compatibility checks.

- Disconnect and reconnect a device with an unresolved operation.

- Introduce an invalid registry definition and verify safe startup behavior.

- Run multiple users against different capability sets and verify isolation.

A tool must not be enabled for the team deployment merely because its happy-path test passes. Its negative, authorization and recovery tests must pass as well.

## 03.31.14 Implementation priorities

P0

Required for MVP

- Versioned tool definitions and strict schemas.

- The four proposed initial tool contracts.

- Separation of tool definitions, device capabilities and permissions.

- Backend validation and independent bridge validation.

- Capability discovery and compatibility checks.

- Explicit timeout, retry and verification policies.

- Reviewed tool enablement and disablement.

- Automated tool contract and security tests.

P1

Add as the tool set grows

- More detailed capability diagnostics.

- Controlled rollout of new tool versions.

- Automated compatibility reporting.

- Additional tool-specific recovery and verification support.

P2

Not required for initial deployment

- Dynamic third-party tool plugins.

- Runtime registration of externally developed tools.

- An administrative tool marketplace or graphical registry editor.

## 03.31.15 Open decisions

| **Decision** | **Current position** |
| --- | --- |
| Tool definition storage | Version-controlled catalogue is the initial proposal |
| Schema technology | Typed validation is required; exact library and format open |
| Risk and permission enums | Align with Sections 03.11 and 03.23 |
| Document formats | Still to be confirmed |
| Capability manifest protocol | Required; exact schema open |
| Tool enablement scope | Global and per-device controls proposed |
| Schema compatibility rules | Must be documented before bridge integration |
| Retry and verification policies | Defined per tool; exact values open |
| Dynamic tool registration | Out of initial scope |
| Tool definition signing or integrity checks | Assess based on packaging and deployment threat model |
| Registry and capability retention | Define alongside persistence and operational-history policies |

## 03.31.16 Definition of done

- Each MVP tool has a reviewed, versioned contract.

- The registry distinguishes tool definitions from device availability and user authorization.

- The planner sees only relevant compatible capabilities.

- Backend and bridge independently validate operations.

- Unknown tools and unsupported schemas fail safely.

- Timeouts, retry behavior and verification are specified per tool.

- Tool changes follow a reviewed enablement and rollback process.

- Security and contract tests pass for both valid and invalid inputs.

- Tool registration cannot be performed by model output.

- Every enabled tool has evidence that its side effects and recovery behavior have been tested.

Recommended engineering decision: start with a small, version-controlled tool catalogue and four reviewed capabilities. Keep the registry authoritative, device capabilities explicit and authorization independent. Expand NEXUS's abilities only when the team can define and test each new tool's complete execution contract.
