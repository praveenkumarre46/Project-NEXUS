# Phase 0 — Foundation & Environment

> **Status:** DRAFT for team review · **Weeks:** 1 · **Primary owners (rotation table):** BE = Dev A, WB = Dev B, AI = Dev C
> **Parent plan:** [`00-phase-plan.md`](00-phase-plan.md) · **Tracker:** [`tracker.md`](tracker.md) · **Diagrams:** [`architecture.md`](architecture.md)

## How to read this document

- Every step has: **Intent → Owner → How (exact actions) → Verify → Evidence → Learning → Status**.
- **Source** = which of the 66 documents the requirement comes from.
- **[Docs]** = stated in the documentation. **[Suggestion]** = my recommendation, *not* in the documents — the team must accept or change it. **[Verify]** = general tooling knowledge I could not check against your machines; confirm it works before relying on it.
- Commands are examples for the standard tools. If a command's output differs from what is described, stop and ask — do not improvise around it.
- Developers: **Dev A, Dev B, Dev C** (replace with names). Where the docs say Developer 1/2/3, the mapping is Dev 1 = A, Dev 2 = B, Dev 3 = C.
- No time estimates are given, per project rules. The schedule fixes this phase at Week 1; the exit criteria decide when it is done.

---

## 1. Goal and scope

**Goal [Docs, 04.28.06 / 04.05.01]:** after P0, every developer can clone the repository, create the Python environment, reach a local PostgreSQL, run the (still trivial) test suite, and the team knows the real facts about the designated host and the LAN.

**What P0 is *not*:** no FastAPI app, no schema, no bridge, no AI features. Those start in P1+. P0 must not "design more architecture documents" (04.28.06) — it produces an environment and a *draft* of shared agreements.

### Week 1 checklist from the docs (04.28.06) and where each is covered

| # | Docs checklist item | Docs owner | Covered by |
|---|---|---|---|
| 1 | Create shared Git repository and agreed directory structure | All three | Steps 2, 3 |
| 2 | Establish branching, PR review and coding standards | All three | Steps 4, 5 |
| 3 | Verify Python, WSL 2, PostgreSQL and test environment setup | Dev 1 (A) | Steps 6, 7, 8, 9 |
| 4 | Inventory designated host hardware, AMD GPU and available memory | Dev 3 (C) | Step 10 |
| 5 | Test LAN connectivity from another Windows computer | Dev 1 + 2 (A+B) | Step 11 |
| 6 | Define the first bridge tool contract and file-search scope | Dev 2 + 1 (B+A) | Step 13 |
| 7 | Define the planner interface and deterministic test fixtures | Dev 3 + 1 (C+A) | Step 13 |
| 8 | Agree task lifecycle, IDs and stable error format | All three | Step 13 |

### Additions beyond the docs

| Addition | Why | Needs team OK |
|---|---|---|
| Step 12 — local-model **smoke test** (not the full benchmark) | Docs schedule model validation in Week 7 (04.28.03). Your AMD GPU/runtime compatibility is unverified (04.02.01); learning early that it fails changes the product. | Yes |
| Step 14 — decision records (ADRs) for what P0 decides | Docs require decisions to be recorded (04.27.04 closure rules) | No (docs already require it) |

---

## 2. Decisions this phase must settle

These are *open* in the docs. Record each in `docs/decisions/` (Step 14). Do not treat any as decided until recorded.

| ID | Decision | Docs position | Settled in step |
|---|---|---|---|
| D-01 | Python version (one supported version for backend and CLI) | "One supported version", not yet chosen (04.05.03) | 7 |
| D-02 | Dependency manager / lock approach | "Lock file if the manager supports one" (04.05.03) | 7 |
| D-03 | PostgreSQL: native in WSL vs Docker Compose | "Local or containerized"; Compose is a *candidate* (04.05.02/03) | 8 |
| D-04 | Formatter, linter, type checker, test library — pick once | "Selected once and documented" (04.04.06) | 5 |
| D-05 | WSL networking mode (NAT vs mirrored) | "Validate on the actual machines" (3.7.5) | 11 |
| D-06 | Provisional host topology: Option A (one team computer) vs B | Option A is provisional default (3.7.6) | 10, 11, 12 |
| D-07 | Where the repo stores the specification and roadmap files | Not in docs | 3 |
| D-08 | Repository host = GitHub private, free plan | **Confirmed by you** | 2 |

---

## 3. Prerequisites — Step 0

### Step 0 — Team facts and accounts

- **Intent:** collect the facts later steps need so nobody is blocked mid-phase.
- **Owner:** All three. **Source:** 04.02.01, 3.7.2.
- **How:**
  1. Each developer writes down (in a shared note for now; moved into the repo in Step 14): GitHub username, which Windows 11 PC they use, whether WSL 2 is already installed, and whether their PC has an AMD or other GPU.
  2. Agree **which PC is the designated host** (runs FastAPI + PostgreSQL + model runtime in the docs' Option A). The docs' open question: *is the designated host also the machine running WSL 2?* (04.02 "Next step"). Answer it explicitly.
  3. Agree the names that replace Dev A/B/C and the calendar start date.
  4. Confirm each PC has a Windows administrator account available (needed for WSL install and firewall rules).
- **Verify:** a table with 3 rows (developer, GitHub user, PC, role in host topology) exists.
- **Evidence:** `docs/roadmap/team.md` (created in Step 14).
- **Learning:** none.
- **Status:** `[ ] pending`

---

## 4. Steps

### Step 1 — Learning block 1: Git, GitHub and pull requests

- **Intent:** everyone is beginner/intermediate (your answer). Merge-conflict and branching mistakes are the most likely early blocker, so learn this *before* touching the repo.
- **Owner:** All three. **Source:** 04.04.03 (branching model).
- **How:** each developer completes and then explains to a teammate:
  1. What a commit, branch, remote and pull request are.
  2. The commands: `git clone`, `git status`, `git add`, `git commit`, `git switch -c <branch>`, `git push -u origin <branch>`, `git pull`, `git merge`, and how to resolve a conflict.
  3. How to open, review and merge a pull request on GitHub.
  4. The docs' branch names: `main`, `feat/<name>`, `fix/<name>`, `docs/<name>`, `test/<name>`.
- **Practice exercise (throwaway repo, not NEXUS):** Dev A creates `git-practice`; each developer makes a branch, edits the *same line* of the same file, and the three resolve the resulting conflict through pull requests. Delete the repo afterward.
- **Verify:** each developer has opened one PR and resolved one conflict in the practice repo.
- **Learning resources:** the Pro Git book (git-scm.com) and the GitHub Docs pull-request guides (docs.github.com). [Verify] links before sharing.
- **Evidence:** screenshot or link to the closed practice PRs.
- **Status:** `[ ] pending`

### Step 2 — Create the GitHub repository

- **Intent:** one shared source of truth. **Owner:** Dev A (BE) creates; all verify access.
- **Source:** 04.04.02; D-08 confirmed by you (GitHub, private, free plan).
- **How:**
  1. On GitHub create a **private** repository named `nexus` (the docs' layout root is `nexus/`). Initialize with no files if you will push a prepared skeleton, or with a README if you prefer to clone first — pick one and tell the team.
  2. Settings → Collaborators: add Dev B and Dev C with **Write** access.
  3. Settings → General → Pull Requests: enable "Automatically delete head branches" and keep "Allow squash merging" on. (Optional [Suggestion]: disable merge commits to keep history simple — decide as a team.)
  4. **Branch protection on `main`:** the docs want "at least one other developer reviews" and "automated checks pass" (04.04.03). **[Verify]** — on GitHub's free plan, *private* repositories may not offer enforced branch protection / rulesets. Open Settings → Branches and check. If it is not available:
     - Record that in D-08's decision record as a known limitation.
     - Enforce the rules by team agreement + the PR template (Step 4): *nobody pushes directly to `main`; nobody merges their own PR without one approval.*
  5. Never commit secrets: confirm "Secret scanning" / push protection availability on the plan **[Verify]**; if unavailable, rely on `.gitignore` and review.
- **Verify:** all three can clone the empty/initial repo and push a branch (not `main`).
- **Evidence:** repo URL; screenshot of Settings → Branches (what is/isn't enforceable).
- **Learning:** GitHub Docs → "About protected branches" **[Verify]** availability for your plan.
- **Status:** `[ ] pending`

### Step 3 — Repository skeleton

- **Intent:** the agreed directory structure exists so parallel work from P1 lands in the right places. **Owner:** Dev A with B and C reviewing.
- **Source:** 04.04.02 (and 3.8.2). The docs say *"not a claim that every file needs to exist on day one"* and *"avoid creating empty abstractions"* — so create **directories and a short README per area, not Python modules**.
- **How:**
  1. In WSL (after Step 6) clone to the documented WSL location, e.g. `~/projects/nexus` — **not** under `/mnt/c/...` (04.05.04 says "documented WSL filesystem location"; this keeps Linux file semantics).
  2. Create this layout (names are from 04.04.02):
     ```text
     nexus/
     ├── apps/            (api/ cli/ windows_bridge/)
     ├── nexus_core/      (domain/ services/ execution/ tools/ ai/ memory/ security/
     │                     infrastructure/{database,model_adapters,bridge_transport}/ observability/)
     ├── migrations/
     ├── contracts/       (api/ bridge/ tools/ events/)
     ├── tests/           (unit/ integration/ contract/ security/ reliability/ end_to_end/)
     ├── deploy/          (config/)
     ├── scripts/
     ├── docs/            (architecture/ decisions/ testing/ operations/)
     ├── .env.example
     ├── .gitignore
     ├── pyproject.toml
     └── README.md
     ```
  3. Git does not track empty directories. Put a one-line `README.md` (what belongs here, copied from the structure rules in 04.04.02) into each folder instead of an empty file. Example for `contracts/`: *"Reviewed interface definitions and examples used by multiple components."*
  4. Do **not** create `.py` modules yet (`tasks.py`, `orchestrator.py`, …). They appear in P1+ when there is a concrete consumer (04.04.02, last rule).
  5. **D-07 — where do specification and roadmap files live?** [Suggestion]: copy this `roadmap/` folder to `docs/roadmap/` and the `.docx` files to `docs/specification/` so everything is versioned in git as you asked. Binary `.docx` files diff poorly in git — record that trade-off in the decision record.
  6. Add the dependency-direction rules from 04.04.06 to `docs/architecture/dependency-rules.md` (domain ← services ← infrastructure; API/CLI call services; planner produces proposals only; bridge does its own validation; CLI never writes directly to PostgreSQL).
  7. Commit on branch `docs/repo-skeleton`, open a PR, get one review, merge.
- **Verify:** a fresh clone shows the layout; every folder has a README; no `.py` files other than any placeholder in Step 7.
- **Evidence:** merged PR link.
- **Learning:** why Python packages need `__init__.py` (read later in Step 7); the idea of dependency direction.
- **Status:** `[ ] pending`

### Step 4 — Branching, pull-request and review rules

- **Intent:** write down the process once so reviews are consistent. **Owner:** All three, drafted by Dev A.
- **Source:** 04.04.03, 04.04.09.
- **How:**
  1. Create `CONTRIBUTING.md` containing, from the docs: branch names (`main`, `feat/`, `fix/`, `docs/`, `test/`), *short-lived branches only*, merge requirements (small change; checks pass; ≥1 other reviewer; security-sensitive changes cross-reviewed; contract/migration changes coordinated; up to date with `main`).
  2. Create `.github/pull_request_template.md` with the docs' PR checklist: problem solved · requirement or decision referenced · interface/DB changes · tests added/updated · security & failure-handling implications · config/migration changes · known limitations. Add the line *"If this changes a shared contract, list affected consumers"* (04.04.03).
  3. Add the 9-step team loop (plan → contract → implement → test locally → review → integrate → verify → document → demonstrate) from 04.04.09 to `CONTRIBUTING.md`.
  4. Agree the **daily sync** questions (04.04.09): what contract changed · what is blocked · what merged and passed · is anyone on an outdated schema · any assumption found false · next demonstrable end-to-end result.
  5. Add rotation rules from [`00-phase-plan.md`](00-phase-plan.md) §3: previous owner pairs with new owner at hand-off; security-sensitive code reviewed by a non-author.
- **Verify:** open a trivial PR on `docs/contributing`; the template appears automatically; a teammate approves.
- **Evidence:** merged PR.
- **Learning:** how to give a useful code review (what to look for: correctness, tests, security, readability).
- **Status:** `[ ] pending`

### Step 5 — Coding standards and tool selection (D-04)

- **Intent:** pick one formatter/linter/type-checker/test tool *once* (04.04.06: "consistency matters more than adopting a large collection of tools"). **Owner:** All three.
- **Source:** 04.04.06.
- **How:**
  1. Write `docs/architecture/coding-standards.md` containing the docs' Python standards verbatim in spirit: shared Python version · type hints on public interfaces and domain contracts · validate external input at boundaries · typed stable error codes (not exception text) · one responsibility per function/module · async only where beneficial (CPU-heavy work does not become non-blocking just by `async def`) · explicit timeouts on network calls and external processes · no hidden global state for users/devices/ownership/permissions · no secrets or machine-specific paths in source.
  2. **Choose tools.** The docs name no tools. [Suggestion] (common, beginner-friendly, widely documented): **pytest** for tests; **Ruff** for lint + format (one tool instead of two); **mypy** for type checking. Alternatives are acceptable — the requirement is *one* of each, written in the decision record. [Verify] each installs on your chosen Python version.
  3. Decide strictness: start type checking on `nexus_core/domain` and public interfaces only, not the whole codebase [Suggestion].
- **Verify:** `docs/decisions/ADR-004-tooling.md` (Step 14) states the chosen tools and why.
- **Evidence:** merged PR with the standards file.
- **Learning:** Python type hints; what a linter catches; how pytest discovers tests.
- **Status:** `[ ] pending`

### Step 6 — WSL 2 + Ubuntu on every developer PC

- **Intent:** the Linux-side backend development environment. **Owner:** each developer on their own PC; Dev A verifies the designated host.
- **Source:** 04.05.02, 04.02.03 B, 3.7.5.
- **How:**
  1. Open **PowerShell (Administrator)**. Check state: `wsl --status` and `wsl --list --verbose`. **[Verify]** The VERSION column for your Ubuntu distro must be `2`.
  2. If not installed: `wsl --install -d Ubuntu` then restart if asked, and create the Linux username/password. **[Verify]** the exact distro name with `wsl --list --online`.
  3. If a distro is VERSION 1: `wsl --set-version <DistroName> 2`.
  4. Inside Ubuntu run the docs' characterisation commands and **save the output**:
     ```bash
     cat /etc/os-release
     uname -a
     nproc
     lscpu
     free -h
     df -h
     python3 --version
     ```
  5. Check for WSL resource limits: on Windows look for `%UserProfile%\.wslconfig`. The docs warn RAM inside WSL "may be constrained independently of installed physical memory" (04.02.03 B). Record whether the file exists and its contents. Do **not** change it yet unless a later step needs it.
  6. Update packages: `sudo apt update && sudo apt upgrade -y`.
  7. Install base tools: `sudo apt install -y git build-essential curl` **[Verify]** package names on your Ubuntu release.
  8. Configure git: `git config --global user.name "Your Name"`, `git config --global user.email "you@example.com"`. Set up authentication to GitHub (HTTPS token or SSH key — follow GitHub Docs **[Verify]**); never paste tokens in shared chats or commit them.
  9. Clone: `mkdir -p ~/projects && cd ~/projects && git clone <repo-url> nexus`.
- **Verify:** `git status` shows a clean tree in `~/projects/nexus`; `python3 --version` prints a version (record it).
- **Evidence:** each developer's saved command output pasted to `docs/operations/dev-environments/<name>.md`.
- **Learning:** what WSL 2 is (a lightweight VM), how Linux paths differ from Windows paths, why the repo lives inside the Linux filesystem.
- **Status:** `[ ] pending` (track per developer in the tracker)

### Step 7 — Python environment and `pyproject.toml` (D-01, D-02)

- **Intent:** a reproducible Python setup that never touches Ubuntu's system Python. **Owner:** Dev A leads; each developer repeats on their own PC.
- **Source:** 04.05.03 (version matrix, dependency rules), 04.05.04 steps 3–4.
- **How:**
  1. **D-01 — choose the Python version.** The docs require "one supported version for backend and CLI". Check what `python3 --version` shows on all PCs. [Suggestion] pick the highest version that (a) all three can install and (b) the libraries you plan to use support — **[Verify]** against FastAPI/Pydantic/SQLAlchemy release notes before pinning. Record it in the version matrix (below).
  2. Install venv support if needed: `sudo apt install -y python3-venv python3-pip` **[Verify]**.
  3. Create the environment *inside the repo folder, but git-ignored*:
     ```bash
     cd ~/projects/nexus
     python3 -m venv .venv
     source .venv/bin/activate
     python --version
     which python        # must point inside .venv
     ```
     Never run `pip install` outside an activated venv (04.05.04: "do not install project packages into Ubuntu's system Python").
  4. **D-02 — dependency manager.** The docs require direct dependencies declared in project configuration, a lock/equivalent, runtime vs dev dependencies separated, no unpinned production dependencies. Options: (a) plain `venv` + `pip` with `pyproject.toml` and a pinned requirements/constraints file; (b) a manager that produces a lock file (e.g. `uv`, `poetry`, `pip-tools`). [Suggestion] for beginners: **(a)**, because it needs no extra tool to learn. Record the choice and the exact "how to update a dependency" procedure.
  5. Create `pyproject.toml` with: project name/version, the chosen Python requirement, and a **dev** dependency group containing only the Step 5 tools (pytest, ruff, mypy or the team's choices). **Do not add FastAPI/SQLAlchemy/Alembic/Pydantic yet** — P1 adds them with a recorded decision (the docs mark SQLAlchemy/Alembic/Pydantic as *candidates*, not final).
  6. Install and **pin** versions per the chosen D-02 approach; commit the lock/pinned file.
  7. Add a trivial passing test so the pipeline is proven end-to-end: `tests/unit/test_environment.py` asserting `sys.version_info[:2]` equals the pinned version. Run `pytest`, `ruff check .`, `ruff format --check .`, `mypy` (as chosen).
  8. Maintain the **version matrix** in `docs/operations/version-matrix.md` with the docs' rows: Windows · WSL 2/Ubuntu · Python · PostgreSQL · FastAPI & related packages · SQLAlchemy & Alembic · Git · Docker/Docker Compose · AI runtime & model. Fill what is known; mark the rest "open — decided in P1 / P4".
  9. Rule from the docs: nobody upgrades core dependencies individually; changes go through a reviewed PR (04.05.03).
- **Verify:** from a fresh clone another developer runs the documented commands and gets all-green checks.
- **Evidence:** merged PR + second developer's confirmation in the PR.
- **Learning:** what a virtual environment is; `pyproject.toml` basics; what "pinning" means and why unpinned dependencies are risky; running pytest.
- **Status:** `[ ] pending`

### Step 8 — PostgreSQL (D-03) and separate databases

- **Intent:** a local PostgreSQL every developer can reach, with development and test databases separate. **Owner:** Dev A leads; each developer repeats.
- **Source:** 04.05.02, 04.05.06, 3.7 (do not expose to LAN).
- **How:**
  1. **D-03 — decide:** native PostgreSQL inside WSL **or** Docker Compose. Both are valid in the docs; Compose is a "candidate" and its role (standard vs optional) must be confirmed (04.05.03). Compare on: setup difficulty for beginners, behaviour after WSL restart, memory use on the 16 GB host. [Suggestion]: choose whichever *all three* can get working first; record the other as a fallback.
  2. **Path A — native in WSL** **[Verify]** commands:
     ```bash
     sudo apt install -y postgresql postgresql-client
     sudo service postgresql start            # or systemctl if systemd is enabled in WSL
     sudo -u postgres psql -c "SELECT version();"
     ```
  3. **Path B — Docker Compose:** install Docker per Docker's current instructions for WSL 2 **[Verify]**; create `deploy/docker-compose.yml` that runs one PostgreSQL service bound to `127.0.0.1` only, with a named volume, and credentials read from environment variables (never hard-coded). Start with `docker compose up -d`.
  4. Create **three logically separate uses** (04.05.06): a **developer** database, an **automated test** database, and (later, P6) a **shared integration** database. In P0 create the first two:
     ```sql
     CREATE ROLE nexus_dev LOGIN PASSWORD '<local secret>';
     CREATE ROLE nexus_test LOGIN PASSWORD '<different local secret>';
     CREATE DATABASE nexus_dev  OWNER nexus_dev;
     CREATE DATABASE nexus_test OWNER nexus_test;
     ```
     Use *different* credentials per database so a test run cannot touch dev data by accident.
  5. **Do not expose PostgreSQL to the LAN** (04.05.02 rule 5): confirm it listens on localhost only — `ss -ltnp | grep 5432` must show `127.0.0.1`/`::1`, not `0.0.0.0`. Leave `listen_addresses` at its localhost default.
  6. Connect from Python-agnostic tool first: `psql "postgresql://nexus_dev:...@localhost:5432/nexus_dev" -c "SELECT 1;"`.
  7. Write down the *startup checks* the docs want implemented later (04.05.06): verify host + database name, environment name, that the target is not a protected shared database, current schema version, dependency availability — "if the environment cannot be established safely, the operation should fail rather than guess." These become code in P1; capture them now as an issue/ADR note.
- **Verify:** each developer can `SELECT 1` against both databases; the port is not reachable from another PC (re-checked in Step 11).
- **Evidence:** pasted `SELECT version();` output in the developer environment file; D-03 record.
- **Learning:** what a database, role and connection string are; why test DBs are separate; why SQLite cannot substitute for PostgreSQL here (04.05.06: row locking, unique constraints, concurrent state transitions need real PostgreSQL).
- **Status:** `[ ] pending`

### Step 9 — Configuration and secrets skeleton

- **Intent:** the pattern for config/secrets exists before any code needs it. **Owner:** Dev A.
- **Source:** 04.05.05.
- **How:**
  1. Create `.gitignore` covering: `.env`, any `.env.*` except `.env.example`, `.venv/`, `__pycache__/`, `*.pyc`, tool caches (`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`), logs, local data/artifacts, Windows bridge local config files that contain credentials. The docs: "never commit live credentials, signing keys, private device credentials or real user data."
  2. Create `.env.example` with **placeholders and non-secret defaults only**. Organise by the docs' categories — Application · Database · Authentication · AI · Windows bridge · Security policy · Diagnostics. For P0 only the first, second and last categories have content; the others get a comment `# defined in P1/P4`. Setting names below are *proposals* for the team to rename:
     ```dotenv
     # Application
     NEXUS_ENV=development
     # Database
     DATABASE_URL=postgresql://nexus_dev:CHANGE_ME@localhost:5432/nexus_dev
     TEST_DATABASE_URL=postgresql://nexus_test:CHANGE_ME@localhost:5432/nexus_test
     # Diagnostics
     LOG_LEVEL=INFO
     # Authentication: defined in P1
     # AI: defined in P4
     # Windows bridge / Security policy: defined in P1-P3 (bridge config lives on the Windows PC, not here)
     ```
  3. Each developer: `cp .env.example .env` then edit locally. `.env` must never be committed — verify with `git status`.
  4. Start `docs/operations/configuration-reference.md`: for each setting list its type, default, security implications and whether restart is required (04.05.05).
  5. Remember: Windows directory paths belong in the **bridge's** config mapped to logical directory IDs, never in backend `.env` (04.05.05). Note that in the reference.
- **Verify:** `git status` after `cp` shows `.env` untracked-but-ignored; `git check-ignore -v .env` prints the matching rule.
- **Evidence:** merged PR; no secrets in `git log -p`.
- **Learning:** environment variables; why secrets stay out of source; what `.gitignore` does and does not undo (a file once committed stays in history).
- **Status:** `[ ] pending`

### Step 10 — Hardware inventory of the designated host (Dev C leads)

- **Intent:** replace "16 GB RAM and an AMD GPU" with measured facts (PC-09). **Owner:** Dev C; Dev A assists on the WSL side.
- **Source:** 04.02.03, 04.02.04, 04.02.08.
- **How:**
  1. On the **designated host**, open Windows PowerShell (not Ubuntu) and run, saving all output:
     ```powershell
     Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber
     Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
     Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
     Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM
     Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free
     ```
  2. **Do not trust `AdapterRAM` for VRAM** (docs warning). Confirm GPU model and dedicated VRAM via Task Manager → Performance → GPU, or the GPU vendor's diagnostic tool. Record dedicated vs shared GPU memory.
  3. Run the WSL commands from Step 6 on the host; record the WSL-visible RAM and any `.wslconfig` limits.
  4. Record: Windows edition and build · CPU model, cores, logical processors · installed and typical available RAM · exact AMD GPU model · dedicated and shared VRAM · driver version · free disk and disk type if known · **whether the host must remain available for other work** (the docs list this explicitly).
  5. **Baseline 1 — idle:** with nothing special running, record CPU %, RAM used/available, GPU memory in use, disk activity. The docs' baseline table (04.02.04) is authoritative for *which* metrics; [Suggestion] if you cannot read it, use these four.
  6. **Baseline 2 — backend + database:** the FastAPI app does not exist yet. In P0 record Baseline 2 with **PostgreSQL running and the Step 8 test connection active**; repeat the full Baseline 2 (backend + PostgreSQL + small workload) at the end of P2 once an API exists. Mark this in the tracker as a carried-over item.
  7. Fill `docs/architecture/host-readiness.md` using the docs' template (04.02.08), sections 1 and 2 now; 3–6 in P4 and later.
  8. The docs do not set VRAM/RAM cutoffs "before measuring" (04.02.07) — **do not invent thresholds here.**
- **Verify:** every field in template sections 1–2 is filled with a measured value or an explicit "unknown + why".
- **Evidence:** `docs/architecture/host-readiness.md` (merged).
- **Learning:** what VRAM vs system RAM is; how to read Task Manager; what WSL's memory limit means.
- **Status:** `[ ] pending`

### Step 11 — LAN connectivity test (Dev A + Dev B)

- **Intent:** prove a second Windows computer can reach a service on the host *before* building on that assumption (PC-02). **Owner:** Dev A + Dev B. **Source:** 3.7.5, 3.7.4.
- **How (follow the docs' order — local first, then LAN):**
  1. **Throwaway service only.** Do not use NEXUS code. In WSL on the host:
     ```bash
     mkdir -p /tmp/lan-test && cd /tmp/lan-test && echo ok > index.html
     python3 -m http.server 8000 --bind 0.0.0.0
     ```
     (It serves one file; stop it with Ctrl+C when done.)
  2. **Local Windows → WSL:** on the same PC open PowerShell: `curl.exe http://localhost:8000/` **[Verify]** and expect `ok`. If it fails, record the exact error.
  3. **Understand your WSL networking mode (D-05).** Microsoft documents NAT as the default, with *mirrored* networking available on Windows 11 (docs 3.7.5). Check which one is in use **[Verify]**: in WSL `hostname -I`; compare with the Windows IPv4 address from `ipconfig`. If addresses differ you are in NAT mode.
  4. **Second computer → host:** find the host's LAN IP (`ipconfig` on the host). From the second PC: `curl.exe http://<host-ip>:8000/`.
  5. If step 4 fails, work through causes **one change at a time, recording each**:
     a. Windows Defender Firewall inbound rule for TCP 8000. Example, run as Administrator, scoped to the local subnet and a single port **[Verify]**:
        `New-NetFirewallRule -DisplayName "NEXUS lan-test" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -RemoteAddress LocalSubnet`
     b. NAT mode: Windows must forward the port to WSL (e.g. `netsh interface portproxy` rules) **[Verify]**, *or* switch to mirrored networking by adding `networkingMode=mirrored` under `[wsl2]` in `%UserProfile%\.wslconfig` and running `wsl --shutdown` **[Verify]**. The docs say "do not change networking merely because one configuration is theoretically convenient" — change only after recording that the simple path failed.
  6. **Remove what you added:** delete the temporary firewall rule (`Remove-NetFirewallRule -DisplayName "NEXUS lan-test"`) and any portproxy rule, stop the server. Permanent rules are created deliberately in P6 with the real ports.
  7. **Resilience observations (docs 3.7.5 list):** note what happens after `wsl --shutdown` and restart, after the host sleeps/wakes, and after the host's network changes. Observe and record — do not solve here.
  8. **Confirm PostgreSQL is *not* reachable** from the second PC: attempt `Test-NetConnection <host-ip> -Port 5432` from it. Expected: failure.
  9. Treat "same LAN" as **untrusted** (docs 3.7.4: "we must not assume local network means trusted"). TLS/auth design is P1+; this step only proves reachability.
- **Verify:** a table of attempts (what, from where, result, fix) with a conclusion: *reachable / reachable only with X / not reachable*.
- **Evidence:** `docs/architecture/lan-connectivity.md`; D-05 record (NAT vs mirrored, with measured results).
- **Learning:** IP addresses and ports; NAT; what a firewall inbound rule does; why you scope a rule to LocalSubnet and one port.
- **Status:** `[ ] pending`

### Step 12 — Local-model smoke test (proposed addition; Dev C)

- **Intent:** early yes/no on whether *any* local model runs usefully on this AMD host. This is a **smoke test, not the Week-7 benchmark**, and the docs forbid choosing a model without that benchmark (04.02.05, 04.27.04). **Owner:** Dev C.
- **Source:** 04.02.05 (evaluation stages 1–2 and fallback), 04.03 benchmark plan; Ollama is only a *candidate* (3.7.6).
- **Needs team OK:** this moves a small part of Week-7 work earlier. If the team declines, skip and leave Week 7 as in the docs.
- **How:**
  1. Use the exact GPU model from Step 10. Read the **runtime vendor's own supported-hardware documentation** for that GPU and operating system **[Verify]** — the docs state "do not assume NVIDIA CUDA compatibility" and that AMD acceleration "must be validated for the exact OS, runtime, driver and model combination". I have not verified support for your GPU; this step is how you find out.
  2. Install one candidate runtime on the host following its official instructions (e.g. Ollama is the docs' named candidate; any other is allowed if recorded). Record runtime **version**.
  3. Pull **one small model** only. Record model identifier/version and quantization, as the docs require for reproducibility.
  4. Ask the runtime to list devices / show whether the GPU is in use **[Verify]** and record the answer — do not infer GPU use from speed alone.
  5. Send one fixed, simple prompt (write it into `docs/testing/model-smoke-prompt.md` so it is reproducible) and record: cold-start time, response time, peak RAM, peak GPU memory, any load errors.
  6. Force CPU-only if the runtime allows **[Verify]** and repeat, to learn whether the docs' CPU fallback is plausible.
  7. Write a conclusion with exactly one of: **GPU works** · **CPU only works** · **blocked (reason)**. Do not select a final model, runtime or thresholds.
  8. Uninstall nothing; leave it for P4. Keep it out of the backend's test suite (docs: model runtime stays optional for tests, 04.05.02 rule 4).
- **Verify:** the result table is complete and reproducible by another person.
- **Evidence:** `docs/architecture/host-readiness.md` section 3 (partial, labelled "smoke test only").
- **Learning:** what a quantized model is; what a runtime does; why GPU support depends on driver + runtime + model.
- **Status:** `[ ] pending (optional — needs team OK)`

### Step 13 — Draft shared agreements (v0, not frozen)

- **Intent:** satisfy Week-1 items 6–8 with *drafts* that P1 will formalise and freeze at Gate 1. The docs say "do not spend the first two weeks designing more architecture documents" (04.28.06), so each draft is **one page**.
- **Owners:** see sub-steps. **Source:** 04.04.04 (contract approval process), 04.04.10 (first slice), 04.05.08 (fixtures), Product Vision 1.6 B.
- **13a — Task lifecycle, IDs, error format (All three).**
  - Start from what the docs state: tasks need explicit states for **pending, running, waiting for approval, succeeded, failed and cancelled** (Product Vision 1.6 B); tasks carry **durable task IDs** (04.27.03); the CLI submits a **unique client request ID** for duplicate protection (04.04.10); errors are **typed, stable codes**, not exception text (04.04.06).
  - Write `docs/architecture/draft-task-lifecycle.md` listing: proposed states, which transitions are legal, ID formats, error-code naming convention, and **open questions**. The docs say the exact state machine and legal transitions are *deferred* (3.6; formalised in the Task State Machine document) — mark every unknown as open rather than guessing.
- **13b — First bridge tool contract and file-search scope (Dev B + Dev A).**
  - The first slice uses a registered **`search_files`** tool against a configured directory on an explicitly selected device (04.04.10). Draft one page with: request fields, response fields, bounded results (the bridge returns a *bounded* structured result), rejection cases, and the **logical directory ID** concept (bridge maps IDs to local paths; backend never sends raw paths — 04.05.05).
  - Carry over the docs' bridge rejection list (04.05.07): unknown tools · unsupported protocol versions · invalid/revoked credentials · wrong target device · unconfigured directory ID · paths escaping the scope · operations exceeding limits.
  - Use the contract approval checklist (04.04.04): schemas, required/optional fields, validation & failure behaviour, version-compatibility rules, valid/invalid examples, contract tests, producer/consumer review, freeze. P0 completes the first two items; P1 completes the rest.
- **13c — Planner interface and deterministic fixtures (Dev C + Dev A).**
  - The first slice needs **no live model** (04.04.10) — a mock planner returns a predetermined proposal. Draft the planner interface: input = user request + permitted context; output = structured plan **or** clarification request (04.05.08, Application Structure 3.8.3).
  - List the fixture names the docs require (04.05.08): valid plans · malformed model output · unknown tools · missing/invalid arguments · clarification requests · unauthorized device targets · approval-required operations · model timeouts/unavailability · plans containing malicious or irrelevant document instructions. Only *list* them in P0; build them in P1–P3.
  - Keep two claims separate (docs): "deterministic contract tests passed" ≠ "real-model evaluation passed".
- **Verify:** three one-page drafts exist, each with an **Open questions** section; each is reviewed by the other developers.
- **Evidence:** merged PRs; links in the tracker.
- **Learning:** what an API contract is; JSON; what "idempotent" means (preview for P2/P3).
- **Status:** `[ ] pending`

### Step 14 — Decision records and team document

- **Intent:** record decisions so they are not "buried in prose" (04.27.01). **Owner:** Dev A with all signing off.
- **Source:** 04.27.02 (status definitions), 04.27.04 (closure rules).
- **How:**
  1. Create `docs/decisions/` and a template `ADR-000-template.md` with: ID · Title · Status (**Confirmed / Provisional / Open / Blocked / Deferred** — the docs' five values) · Context · Options considered · Decision · Evidence · Consequences/limitations · Owner · Date · Revisit condition.
  2. Write ADRs for: ADR-001 repo host (GitHub, private, free plan; branch-protection limits found in Step 2) · ADR-002 Python version · ADR-003 dependency management · ADR-004 tooling · ADR-005 PostgreSQL mode · ADR-006 WSL networking mode · ADR-007 provisional host topology (Option A, citing Steps 10–12 evidence) · ADR-008 docs/roadmap storage location.
  3. A decision is **Provisional** until its evidence exists (04.27.04). Only mark **Confirmed** when the owner has gathered evidence, alternatives are documented, affected docs/tests updated.
  4. Write `docs/roadmap/team.md` from Step 0.
  5. Copy `roadmap/` into the repo per D-07 and keep the tracker current from now on.
- **Verify:** all eight ADRs exist with a status; none say "decided" without evidence.
- **Evidence:** merged PR.
- **Learning:** why teams keep decision records.
- **Status:** `[ ] pending`

### Step 15 — Clean-clone verification (the P0 acceptance test)

- **Intent:** prove the setup is reproducible by someone other than its author (04.05.09: "validated by someone other than their author"). **Owner:** the developer who did *not* write `docs/setup.md` runs it.
- **How:**
  1. Dev A writes `docs/setup.md` with the exact commands and expected outputs from Steps 6–9, plus a **Troubleshooting** section listing every problem hit and its fix.
  2. Dev B, on a clean WSL clone (delete `~/projects/nexus` and the `.venv` first), follows `docs/setup.md` **literally**, with no help from Dev A. Every place Dev B needs to ask a question is a documentation bug — fix the doc.
  3. Repeat with Dev C (it is a different PC, so it tests different assumptions).
  4. Run the subset of the docs' 19-item onboarding checklist (04.05.09) that applies to P0: *Fresh clone works from the documented location · Python environment installs from the committed dependency specification · Formatting and unit tests run successfully · PostgreSQL connects · Test database is isolated · No secrets required from another developer · No live credentials or local data committed · A second developer can reproduce the setup · Troubleshooting and cleanup instructions are documented.* The items for the API, migrations, bridge and AI belong to later phases.
- **Verify:** both developers complete the setup without outside help.
- **Evidence:** signed-off checklist in the tracker; fixes merged.
- **Status:** `[ ] pending`

### Step 16 — Phase review and hand-off to P1

- **Intent:** close P0 honestly and prepare P1. **Owner:** All three.
- **How:**
  1. Run the **P0 exit checklist** (§5). Anything not met is carried over explicitly, with an owner — not silently dropped.
  2. Update the tracker; update risks (especially hardware/LAN findings).
  3. **Rotation hand-off (P0 → P1):** P1 owners are BE = Dev B, WB = Dev C, AI = Dev A. Each previous owner spends the start of P1 pairing with the new owner and walks through what they built (Dev A → Dev B on repo/DB/config; Dev B → Dev C on LAN/bridge-related findings; Dev C → Dev A on hardware/model findings).
  4. Update open-decision table: PC-02 and PC-09 should now have evidence; PC-01 (does NEXUS need to work disconnected from the backend?) is assigned to P1.
  5. Hold a short retrospective: what slowed us down, what to change.
  6. **Ask me to detail P1.** I will read the P1 source documents first (API Contract Freeze, Database Architecture, Task State Machine, Authentication design) before writing it, and will flag anything the documents leave unspecified.
- **Status:** `[ ] pending`

---

## 5. P0 exit criteria

P0 is done only when **all** are true. This list is derived from 04.05.10, 04.02.09, 04.04.12 and the Week-1 checklist (04.28.06).

- [ ] Shared GitHub repo exists with the agreed directory structure (README per folder).
- [ ] Branching, PR template, review rules and coding standards are merged.
- [ ] Tooling choices (D-04) recorded.
- [ ] All three developers can clone, create the venv, install pinned dev dependencies and run the checks green.
- [ ] Python version and dependency approach recorded; version matrix started.
- [ ] PostgreSQL runs for all three; **dev and test databases are separate** with different credentials.
- [ ] PostgreSQL is **not** reachable from another PC.
- [ ] `.env.example` and `.gitignore` committed; no secrets committed; configuration reference started.
- [ ] Designated host's hardware, OS, **exact GPU model and VRAM**, WSL limits documented (or marked unknown with a reason).
- [ ] LAN reachability from a second Windows computer tested; result and networking mode recorded.
- [ ] Task lifecycle / IDs / error-format draft, `search_files` contract draft and planner-interface draft exist, each with open questions listed.
- [ ] ADRs written for D-01…D-08 with honest statuses.
- [ ] Clean-clone setup validated by a developer who did not write the instructions.
- [ ] (If accepted) local-model smoke test result recorded.
- [ ] Carried-over items listed in the tracker with owners.

> **Not part of P0 exit** (docs list them later): API running, migrations applied, bridge enrolled, first end-to-end search. These are P1/P2 (Gate 1 and Gate 2).

---

## 6. Risks specific to P0

| Risk | Why it matters | Mitigation in this phase |
|---|---|---|
| WSL 2 not installable / virtualization disabled on some PC | Blocks the backend environment | Step 6 checks `wsl --status` first; record BIOS/virtualization requirement if hit **[Verify]** |
| WSL networking prevents LAN access | Blocks the shared-backend topology | Step 11 tests early; fallback modes recorded in D-05 |
| AMD GPU not usable by any candidate runtime | May force CPU-only AI, changing the product | Step 12 smoke test; docs' CPU fallback (04.02.05) |
| Free-plan private repo cannot enforce branch protection | Rules rely on discipline | Step 2 records the limit; PR template + team agreement |
| Docker/WSL memory pressure on a 16 GB host | PostgreSQL + WSL + model compete | Step 10 baselines; D-03 compares native vs Compose |
| Setup instructions only work for their author | Violates onboarding acceptance | Step 15 requires a different developer |
| Beginners lose time on Git conflicts | Slows every later phase | Step 1 practice exercise |

---

## 7. Learning plan summary

| Topic | Step | Needed because |
|---|---|---|
| Git, branches, PRs, conflicts | 1, 4 | Every later step |
| Linux basics on WSL; paths | 6 | Backend dev environment |
| Python venv, `pyproject.toml`, pinning, pytest | 7 | Reproducibility |
| PostgreSQL basics; roles; connection strings | 8 | Task persistence in P1 |
| Environment variables; secrets hygiene | 9 | Security rule: no secrets in git |
| Hardware metrics; VRAM | 10 | Model feasibility |
| Networking: IP, ports, NAT, firewall | 11 | Shared-backend topology |
| What an LLM runtime/quantization is | 12 | P4 |
| API contracts; JSON; idempotency (preview) | 13 | P1–P3 |
| Writing decision records | 14 | Governance (04.27) |

---

## 8. What I could not verify (so you know)

- I have **not** run any command on your machines. All commands are standard-tool examples and are marked **[Verify]** where syntax, package names or availability may differ.
- I did not open the docs' baseline-metrics table (04.02.04 table 2), the CI table (04.04.05) or the 5-row risk-tier table (Product Vision 1.4); where I used my own list I labelled it **[Suggestion]**.
- GitHub free-plan feature limits (branch protection, secret scanning on private repos) are stated as things to **check**, not facts.
- GPU/runtime compatibility is genuinely unknown until Step 12.
