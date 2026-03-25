---
id: "20260323-governed-super-agent-harness-planning-spike-codex-01-execplan"
title: "Plan a governed super-agent harness for isolated git workers and graph-driven parallel execution"
owner: "agent/codex-01"
created: "2026-03-23T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260323-governed-super-agent-harness-planning-spike-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/governed-super-agent-harness"
initiative_node_id: "initiative-governed-super-agent-harness"
graph_registration:
  node_id: "rwg-037"
  queue_position: 37
  goal_area: "integration"
  conflict_domains:
    - "super-agent-harness"
    - "research-governance"
  expected_artifacts:
    - ".agent/execplans/20260323-governed-super-agent-harness-planning-spike-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
  implementation_branch: "impl-execplan/20260323-governed-super-agent-harness-planning-spike-codex-01-20260323"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260323-governed-super-agent-harness-planning-spike-codex-01-20260323"
draft_created: "2026-03-23T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260323-governed-super-agent-harness-planning-spike-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define the boundary between the governed platform kernel and an isolated-worker runtime harness"
    priority: "P1"
  - title: "Define the minimum worker contract: isolated filesystem, unique branch, bounded scope, and auditable reconciliation"
    priority: "P1"
  - title: "Define how graph traversal, worker leasing, and task dispatch stay deterministic under parallel execution"
    priority: "P1"
  - title: "Consolidate overlapping orchestrator, managed-repo, and runtime ideas into a bounded follow-on slice map"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Capture the governed-super-agent-harness direction as canonical planning work so the repo can evolve toward a practical multi-worker runtime without losing the stronger graph, validation, Git-backed auditability, and human-authority guarantees already present here.

## Progress

- [ ] define the kernel versus harness boundary explicitly
- [ ] define the minimum useful first release as isolated git-backed workers rather than a broad agent platform
- [ ] define how worker sessions, branches, worktrees or clones, and outputs materialize auditable local artifacts
- [ ] define the scheduler boundary for graph traversal, worker dispatch, worker leasing, and merge or reconcile handoff
- [ ] break the initiative into narrow follow-on ExecPlans with explicit dependency order and clear write-scope separation
- [x] prove the concept with a basic local worker runtime and an Azure job payload renderer without attempting full orchestration integration yet

## Surprises & Discoveries

- this repository is already stronger than generic agent runtimes on governance, canonical local state, and merge-gated execution
- the immediate missing capability is not a richer chat surface; it is a safe way to let many workers operate on one repo without sharing one checkout
- the right first harness is a git-native worker runtime that allocates isolated filesystems and branches, then reconciles back through existing graph and ExecPlan law
- several older planning slices already describe parts of this shape; the missing work is to consolidate them under one worker-first architecture instead of leaving the design scattered
- a small MVP now exists as `governed-worker`, which can prepare local isolated workspaces, run bounded task commands, optionally commit or push, and render an Azure Container Apps Job payload for ephemeral execution
- the first local smoke attempt against this repo hit sandbox limits on `.git` ref writes, which confirms the runtime shape is appropriate but full end-to-end worktree execution needs a normal writable git environment outside this session sandbox

## Decision Log

- treat this as an initiative-level planning spike before implementation
- preserve the current planner, graph, ExecPlan, and merge-governance model as the kernel
- treat the first useful harness as a governed isolated-worker system rather than a full productized agent platform
- require each worker to execute in its own repo clone or git worktree with a unique branch and explicit task lease
- require important runtime decisions, outputs, and state transitions to reconcile back into explicit local artifacts instead of remaining session-local memory
- absorb overlapping direction from earlier orchestrator-contract and managed-repo planning into this initiative instead of spawning another top-level runtime architecture track
- allow bounded prototyping of the worker runtime inside the planning spike when the code is directly in service of architecture validation and remains clearly below full orchestration scope

## Outcomes & Retrospective

- expected outcome: a concrete architecture and follow-on slice map for a governed worker harness that can traverse the graph with multiple agents safely
- expected retrospective question: whether the proposed worker-first harness is thin enough to preserve current platform strengths while still making parallel execution materially easier

## Context and Orientation

- DeerFlow is strongest as a batteries-included runtime harness: skills, tools, subagents, memory, sandboxed execution, gateway APIs, and a UI
- this repository is strongest as a governed kernel: canonical graph state, explicit legal moves, deterministic validation, merge-readiness, Git-backed execution, and human-only authority boundaries
- the immediate user need is narrower than a full harness product: allocate many workers against one git project without shared-filesystem corruption
- the planning problem is to combine those strengths without introducing hidden authority, hidden session state, merge ambiguity, or non-reconcilable runtime behavior
- the likely first user-facing surface is a basic worker-launch skill or command that creates isolated workspaces, assigns bounded graph work, and reports results back to canonical artifacts

## Plan of Work

1. define the architecture in three layers: kernel, worker harness, and optional gateway
2. identify the minimum contracts required for the first useful release: isolated workspace allocation, branch allocation, task leasing, and deterministic reconciliation
3. define how worker outputs become governed evidence and canonical state instead of informal operator memory
4. consolidate overlapping older planning work into this initiative and split the rest into bounded follow-on slices

## Concrete Steps

1. write the architecture contract for `kernel`, `worker-harness`, and `gateway` responsibilities
2. specify the first runtime capability families around isolated workspace provisioning:
   - repo clone versus `git worktree` backend
   - worker identity and lease records
   - graph node or ExecPlan assignment
   - per-worker branch naming and base-ref selection
   - validation, push, and merge-handoff contract
3. define artifact and reconciliation rules for worker leases, session transcripts, task state, generated outputs, and graph-facing decisions
4. define what the basic operator surface looks like:
   - a local skill
   - a platform command
   - or both, with one thin wrapper over the same runtime contract
5. identify which capabilities remain local-first and which may later project to external interfaces such as chat channels or a web UI
6. draft follow-on ExecPlans for the first implementable slices once the architecture is stable

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260323-governed-super-agent-harness-planning-spike-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes after the node is registered
- the resulting plan must make the kernel-versus-worker-harness split explicit and actionable
- the resulting plan must show how several workers can operate on one repo without sharing one filesystem or one branch
- follow-on work should be decomposed into multiple bounded slices rather than one large runtime rewrite
- the first operator surface should be narrow enough to implement as a basic local skill or command before any broader gateway work begins

## Idempotence and Recovery

- rerunning validation should be safe as long as the ExecPlan, queue mirror, and graph registration remain aligned
- if the harness scope proves too broad, the initiative can stay planning-only until narrower follow-on ExecPlans are drafted and sequenced
- if worker orchestration requirements exceed what one shared local repo can safely support, the design should prefer separate clones or worktrees over looser shared-state coordination
- if DeerFlow-inspired features conflict with existing governance invariants, the invariant wins and the runtime design must adapt rather than bypass the kernel

## Artifacts and Notes

- comparison source used for planning: `https://github.com/bytedance/deer-flow`
- intended future model: governed platform kernel plus a worker-first runtime harness, not a wholesale transplant of a generic agent framework
- overlapping concerns being consolidated here include parts of the earlier orchestrator-contract direction, managed-repo runtime targeting, terminal-first runtime posture, and the open DeerFlow-inspired harness research
- current MVP artifacts:
  1. `src/platform_tools/governed_worker.py`
  2. `bin/governed-worker`
  3. `tests/test_governed_worker.py`
  4. `docs/governed-worker-runtime.md`
- current MVP capabilities:
  1. local isolated workspace preparation using `clone` or `worktree`
  2. ephemeral run flow with task execution, optional commit, optional push, optional PR, and cleanup
  3. Azure Container Apps Job payload rendering for a finite-lived worker that clones, works, commits, pushes, opens a PR, and exits
- current MVP validation:
  1. `uv run pytest -q tests/test_governed_worker.py` passes
  2. live local `worktree` smoke execution inside this Codex session was blocked by sandbox restrictions on writing `.git` refs, so full interactive repo-level smoke validation remains follow-on operator work
- proposed bounded follow-on slices after this planning spike:
  1. worker workspace backend and lease registry
  2. graph-aware dispatch and branch allocation
  3. basic skill or CLI surface for launching and monitoring workers
  4. merge-handoff, validation, and completion reconciliation for worker-produced branches
  5. optional remote or UI gateway after the local-first runtime is stable
- this slice is intentionally a planning spike and should not silently expand into runtime implementation

## Interfaces and Dependencies

- this initiative will likely touch planner contracts, orchestrator contracts, managed-repo runtime targeting, future runtime packages, and any eventual API or UI surfaces
- the planning spike currently depends only on existing kernel capabilities already present in this repository
- follow-on slices should isolate write scopes across workspace provisioning, worker state and leasing, graph dispatch, tool or skill loading, and any user-facing gateway surfaces
