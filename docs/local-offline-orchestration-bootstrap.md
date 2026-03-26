# Local Offline Orchestration Bootstrap

## Objective

Define a practical local-first orchestration posture for this platform repository that minimizes OpenAI token usage, keeps the control loop runnable without internet access, and preserves the existing governance and graph-driven execution model already present in this repo.

## Machine Baseline

The current workstation baseline was gathered from local terminal commands:

- OS: WSL2 on Linux `6.6.87.2-microsoft-standard-WSL2`
- CPU: `Intel Core Ultra 5 135U`
- Logical CPUs: `14`
- Memory: `15 GiB`
- Swap: `4 GiB`
- GPU: none exposed to WSL through `nvidia-smi`
- Installed local tooling: `python3`, `uv`
- Missing local LLM runtimes: `ollama`, `llama.cpp`

This machine should be treated as a CPU-first local orchestration host, not a GPU inference box.

## Recommended Operating Model

Use a small local model as the default planner and orchestrator. Use larger or task-specialized models only when a governed worker contract explicitly needs them.

Recommended split:

1. Local orchestration model
   - responsibility: routing, planning, governance checks, work decomposition, contract drafting, status summarization
   - target size: `3B` to `4B`
   - examples:
     - `SmolLM3-3B`
     - `Qwen2.5-Coder-3B-Instruct`
     - another small instruct model with reliable JSON/tool discipline
2. Task-specific worker model
   - responsibility: implementation, review, research, transformation, code generation
   - selected per worker contract
   - may run locally if lightweight enough
   - may use a network model only when explicitly authorized for that slice
3. Canonical authority
   - remains repo-native machine-readable state in `spec/`, `artifacts/`, `policy/`, and command wrappers in `bin/`
   - the local model is not authority; it is an executor over authority surfaces

## Why This Fits This Repo

This repository already assumes:

- graph-first canonical planning state
- governed command wrappers
- machine-readable orchestration contracts
- explicit worker contracts and runtime artifacts
- token economy as a design constraint

That means the correct next step is not "add a chatbot." The correct next step is to add a local model adapter that can drive the existing contract surface cheaply.

## Runtime Recommendation

Start with `ollama` for bootstrap simplicity.

Reasons:

- fastest path to a working local orchestration loop
- easy local model management
- straightforward HTTP interface from Python
- easier handoff to later sessions than a raw `llama.cpp` bootstrap

Do not optimize for maximum runtime sophistication first. Optimize for a small, stable local planner loop that can be swapped later.

If tighter resource control becomes necessary later, add a second backend adapter for `llama.cpp`.

## Initial Model Recommendation

Default orchestrator candidate order for this machine:

1. `SmolLM3-3B`
   - general orchestration and planning default
2. `Qwen2.5-Coder-3B-Instruct`
   - better if orchestration output is heavily code- and JSON-shaped
3. a future 7B quantized model only if local latency is still acceptable

The orchestrator should be optimized for:

- compact structured output
- deterministic decision points
- policy-aware routing
- low-context incremental control

It should not be optimized for:

- long prose generation
- autonomous coding across large surfaces
- internet-backed search loops

## Proposed Architecture

Add a local orchestration layer without replacing the current repo contract.

### Layer 1: Runtime Adapter

Introduce a small provider interface for local orchestration backends.

Suggested shape:

- `src/platform_tools/local_runtime/adapter.py`
- `src/platform_tools/local_runtime/ollama_adapter.py`
- `src/platform_tools/local_runtime/types.py`

Required capabilities:

- submit prompt
- request structured JSON response
- set model name
- control max tokens / context budget
- detect unavailable runtime cleanly

### Layer 2: Orchestrator Profile

Add a governed local orchestration profile that selects:

- default backend: `ollama`
- default local model
- strict token budget
- internet-disabled mode by default
- allowed command families

Suggested files:

- `spec/local-orchestration.yaml`
- `spec/bootstrap-profiles.yaml` extension

### Layer 3: Router

Add a lightweight policy router that decides:

- can the local model complete this task?
- does this require a specialized coding model?
- does this require internet access?
- should the task be blocked until explicit human approval?

The router should emit a compact decision artifact, not prose only.

### Layer 4: Worker Handoff Contract

When the local orchestrator decides to hand work to another model, it should emit a worker handoff packet with:

- task objective
- owned surfaces
- acceptance criteria
- validations to run
- non-goals
- required evidence refs

This should align to the existing worker-contract posture in the repo.

## Concrete Phase 1 Scope

Phase 1 should be intentionally small.

Build only this:

1. Local runtime adapter for `ollama`
2. One local orchestration config file
3. One CLI smoke command that proves the runtime is reachable
4. One CLI command that asks the local model to classify a task into:
   - local orchestration
   - local coding worker
   - remote coding worker
   - human escalation
5. Tests for:
   - adapter contract
   - config loading
   - classification output shape
   - fail-closed behavior when runtime is missing

Do not build full autonomous execution in the first slice.

## Non-Goals For Phase 1

- no generalized multi-provider abstraction beyond what the first adapter needs
- no internet research mode
- no embedded vector database
- no long-running daemon requirement
- no always-on MCP dependency
- no replacement of current `bin/` command wrappers

## Suggested File Additions

The next implementation slice should likely add:

- `src/platform_tools/local_runtime/__init__.py`
- `src/platform_tools/local_runtime/types.py`
- `src/platform_tools/local_runtime/adapter.py`
- `src/platform_tools/local_runtime/ollama_adapter.py`
- `src/platform_tools/local_runtime/config.py`
- `src/platform_tools/local_runtime/router.py`
- `src/platform_tools/local_runtime/runtime_check.py`
- `bin/local-runtime-check`
- `bin/local-task-router`
- `tests/test_local_runtime_adapter.py`
- `tests/test_local_runtime_router.py`
- `tests/test_local_runtime_check.py`
- `spec/local-orchestration.yaml`

## Proposed Decision Rules

The local orchestrator should default to local handling when all are true:

- task is planning, routing, drafting, summarization, or governance-oriented
- required context is already in repo-local machine-readable artifacts
- no internet dependency exists
- expected output is structured and bounded

The router should hand off when any are true:

- substantial code generation or refactor is needed
- deep repo-wide implementation is needed
- internet research is required
- a domain-specific coding model is materially better suited

The router should escalate to a human when:

- authority boundaries are ambiguous
- policy requires approval
- internet use would violate the current operating mode
- a required local runtime is missing and no approved fallback exists

## First Local Commands To Support

The first two commands should be small and boring:

1. `bin/local-runtime-check`
   - validates local runtime reachability and configured model availability
2. `bin/local-task-router`
   - takes a task description and returns a compact JSON routing decision

If those two commands are stable, they can later be called by the broader orchestrator.

## Risks

- local model may be too weak for ambiguous planning unless prompts are tightly bounded
- CPU-only inference may still be slow if the model size creeps upward
- unbounded prompt design will erase the token-cost advantage
- backend abstraction can become over-engineered too early

## Recommended Rule

Keep the local planner stupid on purpose:

- short prompts
- structured outputs
- deterministic routing
- repo-native canonical state
- no hidden memory

That is the best path to reducing token usage without creating a second uncontrolled platform inside the platform.
