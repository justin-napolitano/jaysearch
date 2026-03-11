---
id: "20260311-remaining-work-graph-codex-01-execplan"
title: "Define the remaining-work graph and parallel execution backlog"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-remaining-work-graph-codex-01-execplan.md
  - docs/remaining-work-graph.md
  - docs/parallel-execution-policy.md
  - docs/queued-execplans.md
  - spec/remaining-work-graph.schema.yaml
  - artifacts/planner/research/remaining-work-graph.json
  - artifacts/planner/research/claim-registry.json
  - artifacts/planner/research/bibliography-graph.json
  - docs/research-assumptions.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-remaining-work-graph-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-remaining-work-graph-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-json-parse"
      command: "python3 -m json.tool artifacts/planner/research/remaining-work-graph.json >/dev/null"
      expected_exit: 0
    - name: "claim-registry-check"
      command: "bin/citation-check"
      expected_exit: 0
tasks:
  - title: "Define canonical remaining-work graph"
    priority: "P1"
  - title: "Define parallel-execution policy and conflict domains"
    priority: "P1"
  - title: "Define queued ExecPlan backlog for next slices"
    priority: "P1"
  - title: "Link remaining-work graph to existing orchestration and governance artifacts"
    priority: "P1"
  - title: "Register remaining-work claims and assumptions"
    priority: "P1"
depends_on:
  - "20260310-codex-orchestrator-contract-codex-01-execplan"
  - "20260310-merge-readiness-engine-codex-01-execplan"
  - "20260311-nested-game-system-design-codex-01-execplan"
---

# Purpose / Big Picture

Define the remaining platform work as a canonical dependency graph rather than a loose backlog. The objective is to make the next implementation slices schedulable by Codex, including safe parallel execution where dependency edges and conflict domains allow it.

This phase is design and artifact definition only. It does not implement the queued runtime work. It defines the backlog graph, execution policy, and initial queued ExecPlan set needed for later chained execution.

## Progress

- [ ] Define canonical remaining-work graph
- [ ] Define parallel-execution policy
- [ ] Define queued ExecPlan backlog
- [ ] Define dependency and conflict edges
- [ ] Link remaining-work graph to existing governance and orchestration artifacts
- [ ] Register claims and assumptions

## Surprises & Discoveries

Expected discoveries to capture during execution:

- some remaining slices are dependency-blocked rather than merely unstarted
- some slices may be executable in parallel only if conflict domains are explicit
- chained execution requires stronger queue semantics than existing phase backlogs provide

## Decision Log

Planned foundational decisions to record during execution:

- 2026-03-11 / agent-codex-01 / Remaining platform work should be modeled as a canonical backlog graph rather than as prose-only backlog lists
- 2026-03-11 / agent-codex-01 / Parallel execution requires both dependency edges and explicit conflict domains
- 2026-03-11 / agent-codex-01 / Not every queued ExecPlan should be auto-runnable; some remain review-gated or human-decision-gated

## Outcomes & Retrospective

On completion, this plan should yield:

- a canonical remaining-work graph artifact
- a written parallel-execution policy
- a queued ExecPlan backlog for the next slices
- explicit graph linkage to orchestration, merge-readiness, and governance artifacts

## Context and Orientation

The repository already contains planner, merge-readiness, rule-graph, scoring, and nested-game design artifacts. What is missing is the canonical graph that orders the remaining implementation work and defines what can run in parallel without collisions.

## Plan of Work

1. Define the remaining-work graph schema and artifact.
2. Define the execution policy for parallel and gated work.
3. Define the next queued ExecPlans as graph nodes with dependencies and conflict domains.
4. Link the graph to existing orchestrator and governance artifacts.
5. Register the research provenance for the new abstraction.

## Concrete Steps

1. Write `docs/remaining-work-graph.md`.
2. Write `docs/parallel-execution-policy.md`.
3. Write `docs/queued-execplans.md`.
4. Write `spec/remaining-work-graph.schema.yaml`.
5. Write `artifacts/planner/research/remaining-work-graph.json`.
6. Update `artifacts/planner/research/claim-registry.json`.
7. Update `artifacts/planner/research/bibliography-graph.json`.
8. Update `docs/research-assumptions.md`.
9. Run:
   - `bin/execplan-validate .agent/execplans/20260311-remaining-work-graph-codex-01-execplan.md`
   - `python3 -m json.tool artifacts/planner/research/remaining-work-graph.json >/dev/null`
   - `bin/citation-check`

## Validation and Acceptance

Acceptance criteria:

- a reviewer can identify the next implementation slices and their dependencies without inference
- parallel-safe work is distinguished from conflict-prone work
- queued ExecPlans are classified by readiness and gating posture
- the graph links back to existing orchestrator and governance artifacts rather than inventing a second authority model

## Idempotence and Recovery

This is a design-and-artifact slice. Reruns are safe if graph nodes, dependencies, and queued slices are updated consistently across docs and research artifacts.

## Artifacts and Notes

Expected artifacts:

- `docs/remaining-work-graph.md`
- `docs/parallel-execution-policy.md`
- `docs/queued-execplans.md`
- `spec/remaining-work-graph.schema.yaml`
- `artifacts/planner/research/remaining-work-graph.json`
- updated research registry artifacts

## Interfaces and Dependencies

Primary dependencies:

- `docs/codex-orchestrator-contract.md`
- `docs/merge-readiness-contract.md`
- `docs/codex-orchestrator-phase-2-backlog.md`
- `docs/planner-phase-2-backlog.md`
- `artifacts/planner/research/rule-graph.json`
- `artifacts/planner/research/claim-registry.json`
- `artifacts/planner/research/bibliography-graph.json`
