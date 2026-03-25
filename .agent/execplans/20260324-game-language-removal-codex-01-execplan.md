---
id: "20260324-game-language-removal-codex-01-execplan"
title: "Remove game-first platform language from public docs and provider terminology"
owner: "agent/codex-01"
created: "2026-03-24T00:00:00Z"
status: draft
base_branch: initiative/platform-surface-simplification
changes:
  - .agent/execplans/20260324-game-language-removal-codex-01-execplan.md
  - artifacts/governance/initiative-worker-contracts/initiative-platform-surface-simplification.json
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/agent-game-rules-v1.md
  - docs/games/implementation-game.md
  - spec/providers/github-projects.schema.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/platform-surface-simplification"
initiative_node_id: "initiative-platform-surface-simplification"
graph_registration:
  node_id: "rwg-034"
  queue_position: 34
  goal_area: "documentation"
  conflict_domains:
    - "documentation"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260324-game-language-removal-codex-01-execplan.md"
    - "artifacts/governance/initiative-worker-contracts/initiative-platform-surface-simplification.json"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "docs/agent-game-rules-v1.md"
    - "docs/games/implementation-game.md"
    - "spec/providers/github-projects.schema.yaml"
  implementation_branch: "impl-execplan/future-game-language-removal"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260324-game-language-removal-codex-01-20260324"
draft_created: "2026-03-24T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260324-game-language-removal-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Replace game-first user-facing language with execution-model terminology in public docs"
    priority: "P1"
  - title: "Align provider and workflow terminology so validators, transitions, and states remain the public framing"
    priority: "P1"
  - title: "Preserve runtime behavior while narrowing the public vocabulary"
    priority: "P1"
depends_on:
  - "20260319-platform-surface-simplification-codex-01-execplan"
---

# Purpose / Big Picture

Remove game-first platform language from the public documentation and supporting provider terminology so the platform is described in terms of validators, transitions, execution state, and evidence rather than games, subgames, and proof-game framing.

## Progress

- [ ] identify the public docs and provider surfaces that still present game-first framing as the default model
- [ ] replace that language with the simpler execution model introduced by the parent initiative
- [ ] keep internal governance semantics and runtime behavior intact while shrinking the public vocabulary
- [ ] confirm the queue, graph, and worker-contract surfaces all point at this real initiative contract

## Surprises & Discoveries

- the queue and graph already identified this slice, but only as a `future:*` placeholder, which meant worker activation could not lawfully start
- the repo now correctly refuses worker startup unless the graph node, initiative contract, and worker contract all agree on a real ExecPlan id
- some game-language surfaces are still useful internally, so this slice needs to distinguish public wording cleanup from deeper runtime redesign

## Decision Log

- keep this work under `initiative/platform-surface-simplification`
- convert `rwg-034` from a queue placeholder into a real initiative contract before allowing any worker execution
- treat this slice as terminology and public-model cleanup, not as a worker-runtime or orchestration refactor
- keep the current worker branch `impl-execplan/future-game-language-removal` for this slice rather than churning the prepared contract and graph mapping again

## Outcomes & Retrospective

- expected outcome: the public platform story no longer depends on game-first framing where validator, transition, and execution-state language is clearer
- expected retrospective question: which internal governance docs should retain game-oriented vocabulary as implementation detail versus which should also be simplified later

## Context and Orientation

- the parent simplification slice established a smaller public platform model and explicitly deferred terminology cleanup to `rwg-034`
- the current queue entry and graph node already describe this slice as replacing game-first public language with validators, transitions, evidence, and canonical work state
- the worker-contract runtime now requires a real initiative ExecPlan before any worker can start, so this draft is the missing authority layer for that path
- this slice should update public-facing terminology without changing the underlying legality, reconciliation, or lease machinery created by the worker-governance work

## Plan of Work

1. identify the public documents and provider-facing schemas where game-first framing still appears as the default explanation
2. replace that language with execution-model terminology centered on validators, transitions, statuses, and evidence
3. keep internal governance mechanics stable while clarifying which vocabulary remains internal-only
4. validate that graph, queue, and worker-contract references now resolve to this real ExecPlan

## Concrete Steps

1. update the graph and queue mirror so `rwg-034` targets this ExecPlan id instead of `future:game-language-removal`
2. update the prepared worker contract for `rwg-034` so its `execplan_id` and `contract_id` point at this real initiative contract
3. rewrite the selected public doc and schema surfaces to remove game-first framing where the simpler execution model is more accurate
4. run ExecPlan and graph validation, then retry worker-resolution and worker-bootstrap commands

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260324-game-language-removal-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- `bin/next-worker-slice --initiative-branch initiative/platform-surface-simplification` resolves this slice lawfully once the contract and graph references align
- worker bootstrap for `impl-execplan/future-game-language-removal` succeeds only after the initiative contract, worker contract, and graph node all point at the same ExecPlan id
- public docs touched by this slice describe the platform primarily through validators, transitions, execution state, and evidence rather than game-first terminology

## Idempotence and Recovery

- rerunning the graph and queue updates should be safe as long as `rwg-034` continues to point at this ExecPlan id
- if the terminology cleanup proves broader than expected, follow-on wording cleanup should stay in separate slices rather than widening this contract
- if internal-only docs still need game-first language after the public rewrite, that vocabulary may remain as implementation detail rather than forcing broad semantic churn

## Artifacts and Notes

- this slice is the authority layer that was previously missing for `rwg-034`
- the current prepared worker contract remains the execution path for this slice once the contract references are aligned
- owned implementation scope for the prepared worker contract currently includes:
  1. `docs/agent-game-rules-v1.md`
  2. `docs/games/implementation-game.md`
  3. `spec/providers/github-projects.schema.yaml`

## Interfaces and Dependencies

- this slice depends on the completed parent simplification ExecPlan for overall framing
- the graph node, queue mirror, and worker contract must all reconcile to this real ExecPlan id before worker execution is legal
- this work should not modify worker-runtime governance, lease lifecycle, Docker planning, or Azure planning surfaces
