## 04.02.1 Purpose

Before selecting NEXUS's AI model, runtime or final deployment topology, the team must establish what the designated computer can actually support.

The current confirmed information is:

- Target computers run Windows 11.

- Development uses Ubuntu on WSL 2.

- The backend uses Python and FastAPI, with PostgreSQL.

- AI inference is intended to run locally on a designated team computer.

- The designated computer has been reported to have 16 GB of RAM and an AMD dedicated GPU.

- The exact GPU model, dedicated VRAM, available system memory under load and inference compatibility remain unknown.

That is enough to plan the assessment, but not enough to select a model or promise GPU acceleration.

This section defines how to gather the missing facts, test realistic workloads and make a defensible host decision.

## 04.02.2 Define the workload before choosing hardware

NEXUS has several workloads with different resource requirements.

| **Workload** | **Main resources** | **What to measure** |
| --- | --- | --- |
| FastAPI backend | CPU, RAM, network | API latency, concurrent requests, memory |
| PostgreSQL | RAM, CPU, disk | Query latency, connection pressure, storage |
| Local language model | RAM, CPU or GPU, VRAM | Model load time, inference latency, memory |
| Document processing | CPU, RAM, disk | Extraction time, peak memory, file-size limits |
| Memory retrieval | Database, CPU and possibly GPU | Search latency and retrieval quality |
| Three Windows bridges | Network, backend workers | Dispatch delay, reconnect behavior, concurrent operations |

The key question is not whether the machine can run any one component. It is whether the combined workload remains reliable while three developers use NEXUS.

### Proposed host topology

Designated team computer

FastAPI · PostgreSQL · Local AI runtime

Windows PC A

CLI + native bridge

Windows PC B

CLI + native bridge

Windows PC C

CLI + native bridge

Initial topology to validate, not a confirmed hardware capacity claim.

If the host cannot sustain this combined workload, the team should first reduce model size, concurrency or context limits. Moving inference to a second machine is an alternative if suitable hardware is available; it should not be the default solution without evidence.

## 04.02.03 Hardware inventory

Collect the following information from the proposed inference host before evaluating models.

### A. Windows hardware inventory

Run these commands in Windows PowerShell, not Ubuntu:

# Windows version

Get-ComputerInfo |

Select-Object WindowsProductName, WindowsVersion, OsBuildNumber

# Processor

Get-CimInstance Win32_Processor |

Select-Object Name, NumberOfCores, NumberOfLogicalProcessors

# Installed system memory

Get-CimInstance Win32_ComputerSystem |

Select-Object TotalPhysicalMemory

# Graphics adapters

Get-CimInstance Win32_VideoController |

Select-Object Name, DriverVersion, AdapterRAM

# Available disk space

Get-PSDrive -PSProvider FileSystem |

Select-Object Name, Used, Free

The AdapterRAM value is not guaranteed to accurately represent dedicated VRAM on every graphics driver. Confirm the GPU model and memory using Task Manager → Performance → GPU or the GPU vendor's supported diagnostic utility.

Record these details:

- Windows edition and build.

- CPU model, core count and logical processor count.

- Installed RAM and typical available RAM.

- Exact AMD GPU model.

- Dedicated VRAM and shared GPU memory.

- Graphics driver version.

- Free disk space and disk type, if known.

- Whether the computer must remain available for other work.

### B. WSL 2 and development environment

Run these commands in Ubuntu on WSL 2:

# Distribution and kernel

cat /etc/os-release

uname -a

# CPU visible to Ubuntu

nproc

lscpu

# Memory visible to Ubuntu

free -h

# Filesystem space

df -h

# Python version

python3 --version

These commands help characterize the Linux development environment, but they do not establish that an AI runtime can use the Windows AMD GPU through WSL 2.

Also inspect any WSL resource limits already configured on the Windows machine. The available RAM inside WSL may be constrained independently of the installed physical memory.

Important: the backend's deployment environment and the native Windows bridge are separate runtime concerns. Windows filesystem access and application launching should remain with the Windows-side bridge, even if FastAPI and PostgreSQL run in WSL or containers.

## 04.02.04 Establish a baseline before loading a model

First measure the host while it is idle, then while running the backend and database.

Record:

| **Measurement** | **Baseline 1** | **Baseline 2** |
| --- | --- | --- |
| Available system RAM | TBD | TBD |
| CPU utilization | TBD | TBD |
| GPU utilization | TBD | TBD |
| Dedicated VRAM usage | TBD | TBD |
| Free disk space | TBD | TBD |
| FastAPI response latency | TBD | TBD |
| PostgreSQL query latency | TBD | TBD |

Baseline 1 is the host at rest. Baseline 2 is the host running the basic NEXUS backend and PostgreSQL with a small representative test workload.

Do not infer that PostgreSQL is slow or that GPU acceleration is necessary from these measurements alone. They establish a comparison point for later tests.

## 04.02.05 Local inference feasibility assessment

The team should evaluate runtime and model combinations only after the hardware inventory is complete.

### Evaluation stages

1. Runtime compatibility

2. Confirm that the candidate runtime supports the exact GPU, driver, operating system and deployment mode. Check whether the runtime can actually enumerate and use the GPU.

3. Model loading

4. Load one candidate model and record cold-start time, peak system memory, GPU memory use and any loading failures.

5. Representative planning request

6. Use a fixed NEXUS request that requires a structured multi-step plan. Record input size, output size, latency and schema validity.

7. Repeated inference

8. Repeat the same requests under warm conditions to measure typical latency and variability.

9. Combined workload

10. Run inference while FastAPI, PostgreSQL and document processing are active. Observe memory pressure, latency and errors.

11. Three-user simulation

12. Simulate concurrent requests from three users. Determine whether the runtime queues requests, handles concurrency or causes resource contention.

13. Fallback behavior

14. If the GPU path fails or is too slow, assess whether a CPU configuration can still provide acceptable behavior for the initial supported workload.

The benchmark must record the model identifier and version, quantization where applicable, runtime version, driver details, context configuration, test inputs and observed results. Otherwise, the result may not be reproducible.

## 04.02.06 Compare deployment options

After collecting evidence, compare the following topologies.

| **Option** | **Description** | **Select when** |
| --- | --- | --- |
| A. Combined host | FastAPI, PostgreSQL and AI runtime on the designated computer | The combined workload passes memory, latency and concurrency tests |
| B. Split inference | FastAPI and PostgreSQL remain together; AI inference runs on another available computer | Inference creates resource contention or needs different hardware |
| C. CPU-first host | Backend, database and a suitably small model use CPU resources | GPU support is unavailable or unreliable and CPU performance meets the agreed requirements |

These options are not equivalent in cost or complexity. A split deployment introduces another network dependency and failure boundary. A CPU-first deployment may simplify hardware compatibility but could increase planning latency.

No option should be selected just because it works for a single short request.

## 04.02.07 Define acceptance thresholds

Before running the final benchmark, the team should agree on measurable thresholds. The earlier architecture proposal included an API read target of p95 below 500 ms and task acceptance below one second. These are candidate targets, not yet approved requirements.

The host-readiness assessment should establish:

- API: agreed p95 latency under the representative workload.

- Task acceptance: durable persistence before success is reported to the CLI.

- Inference: a maximum acceptable planning latency for the supported request class.

- Memory: sufficient headroom to avoid sustained swapping or out-of-memory failures.

- Concurrency: three concurrent users can submit and inspect tasks without data leakage or lost task state.

- Recovery: the host can restart and reconcile interrupted operations without blindly repeating uncertain side effects.

- Availability: the team understands what happens when the designated computer is asleep, offline or being used for another workload.

Do not set arbitrary VRAM or RAM cutoffs before measuring the actual runtime/model combinations. A model that fits into memory can still be too slow, and a fast single-user model can still behave poorly under concurrency.

## 04.02.08 Decision record template

Once the assessment is complete, save a report in the NEXUS repository, for example docs/architecture/host-readiness.md.

# NEXUS Host Readiness Report

## 1. Host inventory

- Windows version:

- CPU:

- Installed RAM:

- AMD GPU:

- Dedicated VRAM:

- Driver version:

- Available disk space:

## 2. Deployment environment

- WSL 2 distribution:

- WSL resource limits:

- Backend deployment mode:

- PostgreSQL version:

- Network connectivity results:

## 3. Inference benchmark

- Runtime and version:

- Model and version:

- Quantization:

- GPU acceleration verified:

- Cold-start latency:

- Warm inference latency:

- Peak system RAM:

- Peak GPU memory:

- Three-user test results:

- CPU fallback results:

## 4. Combined workload

- API latency:

- Task acceptance latency:

- Database latency:

- Resource pressure:

- Errors and failures:

## 5. Decision

- Selected topology:

- Evidence supporting the selection:

- Known limitations:

- Fallback plan:

- Revisit conditions:

## 6. Approval

- Developer 1:

- Developer 2:

- Developer 3:

- Decision date:

## 04.02.09 Definition of done

- The designated host's hardware and operating environment are documented.

- The AMD GPU model and dedicated VRAM are verified.

- WSL 2 resource limits and deployment boundaries are understood.

- At least one candidate inference configuration has been tested, or the blocker is explicitly recorded.

- Backend and database baseline measurements are recorded.

- The combined workload and three-user behavior are measured.

- GPU and CPU fallback behavior are understood.

- A deployment topology is selected with evidence and documented limitations.

- The team has agreed on measurable performance thresholds.

Section exit criterion: NEXUS has a validated hardware and inference deployment plan rather than an assumption that the designated computer can run every service simultaneously.

## Next step

Before selecting a model, gather the actual host information. The most useful first output is:

- CPU model

- Installed RAM

- Exact AMD GPU model and dedicated VRAM

- Windows version

- Whether the designated host is also the machine running WSL 2
