# Phase 0 (Foundation & Environment) Implementation Plan

## Top-Level Overview

Source of truth: [`roadmap/phase-0-foundation.md`](../roadmap/phase-0-foundation.md) (Steps 0–16) and [`roadmap/tracker.md`](../roadmap/tracker.md) §2 (P0-00 … P0-16c). Cross-check notes: [`spec-crosscheck-findings.md`](../reports/spec-crosscheck-findings.md).

Goal: every developer can clone the repository, create the Python environment, reach a local PostgreSQL, run the trivial test suite, and the team knows the real facts about the designated host and the LAN. Phase 0 produces an environment and **draft** agreements. It builds no FastAPI app, schema, bridge or AI feature.

Decisions settled here: D-01 to D-08 (ADR-001 to ADR-008). Owners: BE = Dev A, WB = Dev B, AI = Dev C.

Environment note: the product targets WSL 2 and native Windows. Steps 6, 8, 10, 11, 12 must run on the real developer PCs and the designated host, not on a macOS workspace.

---

## Sub-Tasks

### Sub-Task 1: Team facts, accounts and designated host (Step 0)
- **Intent**: Collect the facts later steps depend on, so nobody is blocked mid-phase.
- **Expected Outcomes**:
  - A three-row table: developer name, GitHub user, Windows PC, GPU, WSL status, role in host topology.
  - The designated host is chosen and the question "is the host also the WSL 2 machine?" is answered explicitly.
  - Names replace Dev A/B/C, and a calendar start date is set (the tracker's names and start date are blank today).
  - Each PC has a Windows administrator account available.
- **Todo List**:
  - [ ] Each developer records GitHub user, PC, WSL status and GPU.
  - [ ] Team picks the designated host and answers the WSL-on-host question.
  - [ ] Team agrees names and start date, and fills them in `roadmap/tracker.md`.
  - [ ] Confirm admin access on each PC.
- **Relevant Context**:
  - Roadmap Step 0; tracker P0-00
- **Status**: `[ ] pending`

---

### Sub-Task 2: Git/GitHub learning, repository creation and branch rules (Steps 1, 2, 4)
- **Intent**: Create the shared private repository and the collaboration rules the docs require.
- **Expected Outcomes**:
  - Each developer has completed a practice PR (P0-01a/b/c).
  - A private GitHub repository on the free plan exists with all collaborators (D-08).
  - Branch-protection capability on the free plan is checked and recorded (docs want 1 reviewer plus passing checks).
  - `CONTRIBUTING.md` and a PR template are merged. Branch prefixes are `feat/`, `fix/`, `docs/`, `test/`.
  - Daily-sync questions and rotation rules are agreed.
- **Todo List**:
  - [ ] Complete practice PRs (A, B, C).
  - [ ] Create the private repo and add collaborators.
  - [ ] Check and record branch-protection limits on the free plan.
  - [ ] Merge `CONTRIBUTING.md` and the PR template.
  - [ ] Agree daily-sync questions and rotation rules.
- **Relevant Context**:
  - Roadmap Steps 1, 2, 4; tracker P0-01a…P0-02b, P0-04, P0-04b
  - Specs: 04.04 Repository Structure and Branching
- **Status**: `[ ] pending`

---

### Sub-Task 3: Repository skeleton and dependency-direction rules (Step 3, D-07)
- **Intent**: Create the agreed directory structure so parallel work from Phase 1 lands in the right places, without creating Python modules or empty abstractions.
- **Expected Outcomes**:
  - Layout exactly as in spec 04.04.02:
    - `apps/{api,cli,windows_bridge}`
    - `nexus_core/{domain,services,execution,tools,ai,memory,security,infrastructure/{database,model_adapters,bridge_transport},observability}`
    - `migrations/`, `scripts/`
    - `contracts/{api,bridge,tools,events}`
    - `tests/{unit,integration,contract,security,reliability,end_to_end}`
    - `deploy/config`
    - `docs/{architecture,decisions,testing,operations}`
  - A one-line `README.md` in each folder. No `.py` modules yet.
  - `docs/architecture/dependency-rules.md` with the 04.04.06 rules (domain ← services ← infrastructure; API/CLI call services; planner proposes only; bridge validates on its own; CLI never writes to PostgreSQL).
  - D-07 decided: where the specs and Roadmap live in the repo (the roadmap suggests `docs/roadmap/` and `docs/specification/`).
  - Merged on branch `docs/repo-skeleton` after one review.
- **Todo List**:
  - [ ] Clone to the WSL filesystem, not under `/mnt/c`.
  - [ ] Create the folder tree with a README per folder.
  - [ ] Write `docs/architecture/dependency-rules.md`.
  - [ ] Decide D-07 and copy specs and Roadmap accordingly.
  - [ ] Open the PR, get one review, merge.
- **Relevant Context**:
  - Roadmap Step 3; tracker P0-03, P0-03b
  - Specs: 04.04.02, 04.04.06
- **Status**: `[ ] pending`

---

### Sub-Task 4: Coding standards and tooling (Step 5, D-04)
- **Intent**: Choose formatter, linter, type checker and test library once, and document the coding standards.
- **Expected Outcomes**:
  - D-04 recorded.
  - `docs/architecture/coding-standards.md` merged.
- **Todo List**:
  - [ ] Choose the four tools as a team.
  - [ ] Write the coding-standards document and merge it.
- **Relevant Context**:
  - Roadmap Step 5; tracker P0-05
  - Spec: 04.04.06
- **Status**: `[ ] pending`

---

### Sub-Task 5: WSL 2, Python environment and PostgreSQL on every developer PC (Steps 6, 7, 8, D-01, D-02, D-03)
- **Intent**: Make the development environment reproducible on all three PCs.
- **Expected Outcomes**:
  - WSL 2 with Ubuntu works on all three PCs. Each developer's `.wslconfig` resource limits are checked and recorded (P0-06a–d).
  - D-01 (one Python version) and D-02 (dependency manager and lock approach) decided. `pyproject.toml` and the lock file are committed. Pinned dev dependencies install and the checks run green on all three PCs (P0-07a–e). A version matrix is started in `docs/operations/version-matrix.md`.
  - D-03 decided (native in WSL vs Docker Compose). PostgreSQL runs on each PC with separate dev and test databases and different credentials (P0-08a–d).
  - PostgreSQL is confirmed not reachable from another PC (P0-08e).
  - A trivial baseline test runs under the chosen test library.
- **Todo List**:
  - [ ] Install and verify WSL 2 + Ubuntu (A, B, C). Record `.wslconfig` limits.
  - [ ] Decide D-01 and D-02. Create `pyproject.toml` and the lock file.
  - [ ] Each developer creates the venv, installs pinned dev dependencies and runs the checks.
  - [ ] Decide D-03. Install PostgreSQL and create dev and test databases with separate credentials.
  - [ ] Verify from a second PC that PostgreSQL is unreachable.
  - [ ] Start `docs/operations/version-matrix.md`.
- **Relevant Context**:
  - Roadmap Steps 6, 7, 8; tracker P0-06a…P0-08e
  - Specs: 04.05 Development Environment Bootstrap
- **Status**: `[ ] pending`

---

### Sub-Task 6: Configuration and secrets skeleton (Step 9)
- **Intent**: Set up configuration files so secrets never reach git.
- **Expected Outcomes**:
  - `.gitignore` and `.env.example` committed. No secrets in git history (P0-09b).
  - `docs/operations/configuration-reference.md` started.
- **Todo List**:
  - [ ] Create `.gitignore` and `.env.example`.
  - [ ] Start the configuration reference.
  - [ ] Confirm all three developers see no secrets in git history.
- **Relevant Context**:
  - Roadmap Step 9; tracker P0-09, P0-09b
  - Spec: 03.20 Configuration Management, Secrets and Environment Isolation
- **Status**: `[ ] pending`

---

### Sub-Task 7: Designated-host hardware inventory (Step 10, Dev C leads, D-06)
- **Intent**: Learn the real hardware facts that decide whether local AI is feasible.
- **Expected Outcomes**:
  - A hardware inventory run from Windows PowerShell on the designated host.
  - Exact GPU model and dedicated VRAM confirmed (not taken from `AdapterRAM`).
  - Baseline 1 (idle) and baseline 2 (PostgreSQL running) recorded. The full backend baseline is carried to Phase 2.
  - Sections 1–2 of `docs/architecture/host-readiness.md` filled. Unknowns are marked unknown with a reason.
- **Todo List**:
  - [ ] Run the inventory on the host.
  - [ ] Confirm GPU model and dedicated VRAM.
  - [ ] Record baselines 1 and 2.
  - [ ] Write `docs/architecture/host-readiness.md` sections 1–2.
- **Relevant Context**:
  - Roadmap Step 10; tracker P0-10a…P0-10e
  - Spec: 04.02 Hardware Inventory, Host Readiness and Local AI Feasibility
- **Status**: `[ ] pending`

---

### Sub-Task 8: LAN connectivity test (Step 11, Dev A + Dev B, D-05, D-06)
- **Intent**: Verify that a second Windows PC can reach the designated host, and record the WSL networking mode.
- **Expected Outcomes**:
  - Local Windows → WSL reachability tested. Second PC → host reachability tested.
  - D-05 (NAT vs mirrored) decided with evidence.
  - Temporary firewall and portproxy rules removed.
  - Behaviour on sleep, restart and network change observed and recorded.
  - Result documented in `docs/architecture/lan-connectivity.md`.
- **Todo List**:
  - [ ] Test Windows → WSL.
  - [ ] Test second PC → host.
  - [ ] Record the networking mode (D-05).
  - [ ] Remove temporary rules.
  - [ ] Observe and record sleep, restart and network-change behaviour.
- **Relevant Context**:
  - Roadmap Step 11; tracker P0-11a…P0-11e
  - Specs: 03.22 Deployment Topology, Network Boundaries
- **Status**: `[ ] pending`

---

### Sub-Task 9: Local-model smoke test (Step 12, optional, needs team OK)
- **Intent**: Learn early whether the AMD GPU and runtime combination works. This is not the full benchmark (Phase 4).
- **Expected Outcomes**:
  - The team has accepted or declined the addition.
  - If accepted, one result recorded: GPU works / CPU only / blocked, using `docs/testing/model-smoke-prompt.md`.
- **Todo List**:
  - [ ] Team decision: run the smoke test or defer to Phase 4.
  - [ ] If accepted, run it and record the result.
- **Relevant Context**:
  - Roadmap Step 12; tracker P0-12
  - Spec: 04.03 Local AI Runtime and Model Selection Benchmark Plan
- **Status**: `[ ] pending`

---

### Sub-Task 10: Draft shared agreements, v0 (Step 13)
- **Intent**: Write three draft agreements that Phase 1 will freeze. Each lists its open questions.
- **Expected Outcomes**:
  - Draft task lifecycle, IDs and error format. It follows the 04.08.06 and 03.29 state names (task: `QUEUED, RUNNING, WAITING_FOR_APPROVAL, INTERRUPTED, SUCCEEDED, FAILED, CANCELLED`) and flags D-23 and D-24 as open.
  - Draft `search_files` tool contract and file-search scope.
  - Draft planner interface and a fixture list.
- **Todo List**:
  - [ ] Write `docs/architecture/draft-task-lifecycle.md` (All).
  - [ ] Write `docs/architecture/draft-search-files-contract.md` (B + A).
  - [ ] Write `docs/architecture/draft-planner-interface.md` (C + A).
- **Relevant Context**:
  - Roadmap Step 13; tracker P0-13a/b/c
  - Specs: 04.08, 03.29, 03.30, 03.32
- **Status**: `[ ] pending`

---

### Sub-Task 11: Decision records, team document and setup guide (Steps 14, 15)
- **Intent**: Record the decisions and prove the setup works for someone other than its author.
- **Expected Outcomes**:
  - `docs/decisions/ADR-000-template.md` with ID, Title, Status (Confirmed / Provisional / Open / Blocked / Deferred), Context, Options considered, Decision, Evidence, Consequences, Owner, Date and Revisit condition.
  - ADR-001 to ADR-008, one per decision: repo host (D-08), Python version (D-01), dependency management (D-02), tooling (D-04), PostgreSQL mode (D-03), WSL networking (D-05), provisional host topology (D-06), docs storage location (D-07). None says "decided" without evidence.
  - `docs/roadmap/team.md` written from Step 0.
  - `docs/setup.md` with exact commands, expected output and a troubleshooting section.
  - Clean-clone validation by Dev B and by Dev C, each following the doc literally. Every question they have is fixed in the doc.
- **Todo List**:
  - [ ] Create the ADR template and ADR-001 to ADR-008.
  - [ ] Write `docs/roadmap/team.md`.
  - [ ] Write `docs/setup.md` (Dev A).
  - [ ] Clean-clone validation by Dev B (P0-15b) and Dev C (P0-15c).
  - [ ] Fix every documentation gap they report.
- **Relevant Context**:
  - Roadmap Steps 14, 15; tracker P0-14a, P0-14b, P0-15a/b/c
  - Specs: 04.27 closure rules, 04.05.09 onboarding checklist
- **Status**: `[ ] pending`

---

### Sub-Task 12: Phase review and hand-off to Phase 1 (Step 16)
- **Intent**: Close Phase 0 honestly and prepare Phase 1.
- **Expected Outcomes**:
  - All P0 exit criteria (Roadmap §5) checked. Anything unmet is carried over with an owner.
  - Tracker and risk register updated with hardware and LAN findings.
  - Rotation hand-off done: A→B (repo/DB/config), B→C (LAN/bridge), C→A (hardware/model). Phase 1 owners: BE = Dev B, WB = Dev C, AI = Dev A.
  - PC-02 and PC-09 have evidence. PC-01 is assigned to Phase 1.
  - Retrospective held.
- **Todo List**:
  - [ ] Review the P0 exit checklist (P0-16a).
  - [ ] Do the rotation hand-off (P0-16b).
  - [ ] Hold the retrospective (P0-16c).
  - [ ] Update `roadmap/tracker.md` and the risk register.
- **Relevant Context**:
  - Roadmap Step 16 and §5; tracker P0-16a/b/c and P0 exit criteria
- **Status**: `[ ] pending`
