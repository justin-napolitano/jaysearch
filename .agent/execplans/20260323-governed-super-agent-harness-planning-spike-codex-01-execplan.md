---
id: "20260323-governed-super-agent-harness-planning-spike-codex-01-execplan"
title: "Plan a governed super-agent harness that layers DeerFlow-style runtime capabilities on top of the platform kernel"
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
  - title: "Define the boundary between the governed platform kernel and a DeerFlow-style runtime harness"
    priority: "P1"
  - title: "Identify the runtime capability families to add next: skills, tools, memory, sandbox, subagents, gateway, and UI"
    priority: "P1"
  - title: "Define how runtime actions reconcile back into canonical graph and ExecPlan artifacts"
    priority: "P1"
  - title: "Split follow-on work into bounded contracts instead of one oversized implementation branch"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Capture the governed-super-agent-harness direction as canonical planning work so the repo can evolve toward a DeerFlow-style runtime without losing the stronger graph, validation, and human-authority guarantees already present here.

## Progress

- [ ] define the kernel versus harness boundary explicitly
- [ ] identify the minimum runtime capability surface required for a useful first harness release
- [ ] define how runtime sessions, tools, and subagents materialize auditable local artifacts
- [ ] break the initiative into narrow follow-on ExecPlans with explicit dependency order

## Surprises & Discoveries

- this repository is already stronger than DeerFlow on governance, canonical local state, and merge-gated execution
- the main gap is not planning or control-loop rigor; it is the runtime layer that DeerFlow ships out of the box
- the right direction is additive layering, not replacing the existing kernel with a generic agent framework

## Decision Log

- treat this as an initiative-level planning spike before implementation
- preserve the current planner, graph, ExecPlan, and merge-governance model as the kernel
- add DeerFlow-like runtime behavior as a harness layer above the kernel rather than rewriting the kernel around LangGraph-style execution
- require important runtime decisions, outputs, and state transitions to reconcile back into explicit local artifacts instead of remaining session-local memory

## Outcomes & Retrospective

- expected outcome: a concrete architecture and follow-on slice map for a governed super-agent harness
- expected retrospective question: whether the proposed harness boundary is thin enough to preserve current platform strengths while still giving users a substantially better runtime experience

## Context and Orientation

- DeerFlow is strongest as a batteries-included runtime harness: skills, tools, subagents, memory, sandboxed execution, gateway APIs, and a UI
- this repository is strongest as a governed kernel: canonical graph state, explicit legal moves, deterministic validation, merge-readiness, and human-only authority boundaries
- the planning problem is to combine those strengths without introducing hidden authority, hidden session state, or non-reconcilable runtime behavior

## Plan of Work

1. define the architecture in three layers: kernel, harness, and gateway
2. identify the capability contracts required for the harness to feel materially more useful than the current terminal-first control plane
3. define how runtime outputs become governed evidence and canonical state instead of informal operator memory
4. split the initiative into follow-on slices that can be implemented and reviewed independently

## Concrete Steps

1. write the architecture contract for `kernel`, `harness`, and `gateway` responsibilities
2. specify the first runtime capability families: skill loading, tool registry, sandbox abstraction, memory store, subagent orchestration, and service ingress
3. define artifact and reconciliation rules for session transcripts, task state, generated outputs, and graph-facing decisions
4. identify which capabilities should remain local-first and which may project to external interfaces such as chat channels or a web UI
5. draft follow-on ExecPlans for the first implementable slices once the architecture is stable

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260323-governed-super-agent-harness-planning-spike-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes after the node is registered
- the resulting plan must make the kernel-versus-harness split explicit and actionable
- follow-on work should be decomposed into multiple bounded slices rather than one large runtime rewrite

## Idempotence and Recovery

- rerunning validation should be safe as long as the ExecPlan, queue mirror, and graph registration remain aligned
- if the harness scope proves too broad, the initiative can stay planning-only until narrower follow-on ExecPlans are drafted and sequenced
- if DeerFlow-inspired features conflict with existing governance invariants, the invariant wins and the runtime design must adapt rather than bypass the kernel

## Artifacts and Notes

- comparison source used for planning: `https://github.com/bytedance/deer-flow`
- intended future model: governed platform kernel plus a DeerFlow-style runtime harness, not a wholesale transplant
- this slice is intentionally a planning spike and should not silently expand into runtime implementation

## Interfaces and Dependencies

- this initiative will likely touch planner contracts, orchestrator contracts, future runtime packages, and any eventual API or UI surfaces
- the planning spike currently depends only on existing kernel capabilities already present in this repository
- follow-on slices should isolate write scopes across kernel contracts, runtime services, tool/skill loading, and user-facing gateway surfaces
