# Local Offline Orchestration Bootstrap Prompt

Use this repository's existing orchestration and governance posture. Do not invent a parallel framework. Build the smallest implementation slice necessary to support a local-first orchestration loop that can run without internet access.

## Context

This repo already contains:

- graph-driven planning and governance
- governed command wrappers in `bin/`
- machine-readable contract surfaces in `spec/`
- worker and orchestration runtime concepts

The goal is to reduce OpenAI token usage by running the orchestration layer locally. Actual implementation work may still be handed off to a model chosen for that task.

The terminal remains the operator UI. The local model is a cheap router/planner inside that terminal workflow, not a replacement for the governed command surface.

## Machine Constraints

Assume the host baseline is:

- WSL2
- `Intel Core Ultra 5 135U`
- `14` logical CPUs
- `15 GiB` RAM
- `4 GiB` swap
- no GPU exposed in WSL

Design for CPU-first local inference.

## Desired Outcome

Implement a phase-1 local orchestration bootstrap with:

1. a small local runtime adapter
2. `ollama` as the initial backend
3. one governed runtime-check command
4. one governed task-router command
5. compact structured JSON outputs
6. tests that fail closed when the runtime is absent
7. explicit routing between local planner, planning worker, execution worker, remote worker, and human escalation

## Constraints

- do not replace existing platform contracts
- do not add internet-dependent behavior
- do not build a full autonomous framework in one slice
- do not optimize for prose-heavy chat UX
- do optimize for bounded structured outputs and routing decisions
- do treat planning workers and execution workers as distinct roles

## Required Reading

Read and align with:

- `docs/codex-orchestrator-contract.md`
- `docs/graph-runtime-contracts-and-token-economy.md`
- `docs/local-offline-orchestration-bootstrap.md`

## Expected Additions

Target additions should likely include:

- `src/platform_tools/local_runtime/`
- `bin/local-runtime-check`
- `bin/local-task-router`
- `spec/local-orchestration.yaml`
- focused tests for adapter, router, and runtime check

## Deliverable Standard

The implementation should:

- stay narrow
- be policy-driven where practical
- emit stable machine-readable output
- be easy to extend later to additional local or remote backends
- preserve the terminal as the primary operator interface
- keep repo-owned APIs as authority rather than large markdown or prompt surfaces

Do not stop at analysis. Implement the phase-1 slice, run relevant tests, and summarize the resulting contract surface.
