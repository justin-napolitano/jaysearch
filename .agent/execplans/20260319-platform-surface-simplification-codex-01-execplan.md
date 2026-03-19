---
id: "20260319-platform-surface-simplification-codex-01-execplan"
title: "Simplify the platform to a small public runtime surface"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: initiative/platform-surface-simplification
changes:
  - .agent/execplans/20260319-platform-surface-simplification-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - README.md
  - docs/commands.md
  - docs/codex-orchestrator-contract.md
  - docs/platform-definition-v1.md
  - spec/workflow.yaml
  - spec/rule-registry.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/platform-surface-simplification"
initiative_node_id: "initiative-platform-surface-simplification"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-platform-surface-simplification-codex-01-20260319"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260319-platform-surface-simplification-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define the minimal public platform surface"
    priority: "P1"
  - title: "Consolidate the public runtime story around graph, transitions, validators, and managed repos"
    priority: "P1"
  - title: "Demote intermediate commands and overlapping narratives from the public model"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Reduce the platform to the smallest public model that is clearly true: work graph, ExecPlans, transition engine, validator suite, board projection, and managed-repo orchestration.

## Progress

- [ ] define the supported public platform surface explicitly
- [ ] identify which docs/specs are canonical versus explanatory
- [ ] remove overlapping public narratives that do not improve execution
- [ ] prepare the follow-on simplification slices for terminology and command-surface cleanup

## Surprises & Discoveries

- the platform has accumulated historical language and intermediate commands while the working core has become much smaller and clearer
- simplification needs to preserve behavior while shrinking the public story, not erase the transition and validation engine underneath it

## Decision Log

- keep the simplification work under `initiative/platform-surface-simplification`
- treat this slice as the parent runtime-consolidation step before the narrower terminology and command-surface follow-ons
- preserve backward-compatible runtime behavior while tightening the supported public model

## Outcomes & Retrospective

- expected outcome: the repo can describe itself accurately in a small number of concepts and commands
- expected retrospective question: which internal commands still deserve to remain user-visible after the public surface is frozen

## Context and Orientation

- the working core today is the graph, workflow, rule registry, reconciler/orchestrator path, managed-repo bootstrap/status, and board projection
- the simplification effort should make that core explicit and demote the rest
- this slice is about consolidation and public-surface definition, not large runtime redesign

## Plan of Work

1. identify the minimal public platform model and command set
2. rewrite the central docs/spec framing around that model
3. mark supporting commands and concepts as internal or follow-on cleanup
4. validate that the graph and ExecPlan flow remain canonical during the simplification

## Concrete Steps

1. update the graph and queue to point `rwg-033` at this real ExecPlan
2. rewrite the central platform docs around the minimal execution model
3. tighten `workflow.yaml` and `rule-registry.yaml` wording so the public story matches runtime truth
4. leave terminology and command demotion details for `rwg-034` through `rwg-036`

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260319-platform-surface-simplification-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- the public platform story is reduced to a small, consistent set of concepts and surfaces

## Idempotence and Recovery

- repeated validation should stay green as long as the graph, queue, and ExecPlan references remain aligned
- if the simplification draft proves too broad, follow-on cleanup stays split into `rwg-034` through `rwg-036`

## Artifacts and Notes

- primary artifacts are central docs/specs, not new runtime families
- the point is to define the surface the platform should defend going forward

## Interfaces and Dependencies

- this slice sets the framing for the follow-on simplification nodes already captured in the graph
- it should stay compatible with initiative-first execution and managed-repo orchestration
