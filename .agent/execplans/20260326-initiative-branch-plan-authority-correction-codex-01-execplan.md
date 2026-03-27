---
id: "20260326-initiative-branch-plan-authority-correction-codex-01-execplan"
title: "Correct the workflow so initiative branches may carry authoritative in-flight ExecPlans until initiative completion"
owner: "agent/codex-01"
created: "2026-03-26T00:00:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260326-initiative-branch-plan-authority-correction-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/codex-orchestrator-contract.md
  - docs/execplans.md
  - docs/merge-readiness-contract.md
  - docs/queued-execplans.md
  - spec/governance.yaml
  - spec/workflow.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-043"
  queue_position: 43
  goal_area: "governance"
  implementation_branch: "impl-execplan/20260326-initiative-branch-plan-authority-pr-mergeback-clarification"
  conflict_domains:
    - "governance"
    - "workflow"
    - "documentation"
  expected_artifacts:
    - ".agent/execplans/20260326-initiative-branch-plan-authority-correction-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/codex-orchestrator-contract.md"
    - "docs/execplans.md"
    - "docs/merge-readiness-contract.md"
    - "docs/queued-execplans.md"
    - "spec/governance.yaml"
    - "spec/workflow.yaml"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260326-initiative-branch-plan-authority-correction-codex-01-20260326"
draft_created: "2026-03-26T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260326-initiative-branch-plan-authority-correction-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260326-initiative-branch-plan-authority-correction-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define initiative-branch plan authority so the active initiative branch may carry the authoritative in-flight ExecPlan until the initiative is complete"
    priority: "P1"
  - title: "Demote draft-execplan branches from mandatory authoritative planning location to optional review/edit branches for plan changes"
    priority: "P1"
  - title: "Clarify that merge to main records canonical historical finalization and completion, but is not a prerequisite for every in-flight implementation slice inside an active initiative"
    priority: "P1"
  - title: "Preserve deterministic validation and human authority while removing the requirement to land partial planning state on main before initiative execution can proceed"
    priority: "P1"
depends_on:
  - "20260319-managed-repo-orchestration-codex-01-execplan"
  - "20260326-local-orchestration-contract-surface-codex-01-execplan"
---

# Purpose / Big Picture

Correct the workflow model so the active initiative branch may carry the authoritative in-flight ExecPlan and supporting planning state until the initiative itself is complete. The current written rules push draft-plan finalization to `main` too early for the intended working style, which creates pressure to merge incomplete planning state before implementation and initiative integration are actually done.

## Progress

- [ ] define authoritative in-flight planning semantics for initiative branches
- [ ] define the revised role of `draft-execplan/*` branches as optional review/edit branches rather than the only lawful planning location
- [ ] define how implementation slices may proceed under initiative-branch plan authority without requiring pre-implementation merge-to-main finalization
- [ ] preserve human authority, deterministic validation, and final historical finalization semantics

## Surprises & Discoveries

- the current workflow is internally consistent, but it optimizes for early mainline plan finalization rather than for keeping one initiative branch as the living home of in-flight planning and implementation state
- the managed-repo and local-orchestration direction both fit better with initiative-local authoritative planning than with repeated draft-to-main plan merges
- this is not just a branch naming preference; it is a governance correction that affects workflow, finalization semantics, and merge-readiness interpretation

## Decision Log

- the initiative branch should be allowed to carry the authoritative in-flight ExecPlan for that initiative while the initiative is active
- `draft-execplan/*` branches should remain useful for isolated drafting or review, but they should not be the only lawful planning location
- implementation slices should be allowed to execute under initiative-branch plan authority when deterministic validation and authority boundaries are satisfied
- implementation slices should normally integrate back into the initiative branch by PR rather than by local cherry-pick so worker execution remains reviewable and machine-auditable
- canonical append-only worker audit logs should merge with governed work, while live worker lease directories should remain operational runtime state unless a slice explicitly promotes them
- merge to `main` should remain authoritative for completed historical finalization, but it should not be a prerequisite for every intermediate planning update inside an active initiative
- the correction must fail closed if initiative-to-plan mapping is ambiguous

## Outcomes & Retrospective

- expected outcome: one governance correction package that makes the intended initiative-branch working model explicit and lawful without weakening validation or human authority

## Context and Orientation

- the current docs and specs require draft-plan PR review and signed finalization on `main` before governed implementation execution proceeds
- the intended operating model for current work is different: keep the initiative branch as the home of the living plan and integrate implementation slices there until the initiative is complete
- without an explicit correction, implementation would either violate the written workflow or force premature planning merges to `main`

## Plan of Work

1. revise workflow semantics so initiative branches may hold authoritative in-flight ExecPlans
2. clarify the role of draft branches for plan editing and review without making them mandatory for every planning update
3. revise finalization semantics to distinguish:
   - in-flight initiative authority
   - historical finalization and completion on `main`
4. align orchestrator and merge-readiness docs to the corrected model
5. preserve fail-closed checks for ambiguous initiative mapping, missing validation, and human-only authority boundaries

## Concrete Steps

1. update `spec/workflow.yaml`
2. update `spec/governance.yaml`
3. update `docs/execplans.md`
4. update `docs/codex-orchestrator-contract.md`
5. update `docs/merge-readiness-contract.md`
6. register and validate the planning slice

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260326-initiative-branch-plan-authority-correction-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the corrected workflow must make it possible to explain exactly where authoritative in-flight plan state lives during an active initiative without appealing to unwritten operator preference
- the corrected workflow must preserve deterministic validation, fail-closed ambiguity handling, and human-only authority for final historical approval/completion events

## Idempotence and Recovery

- this slice is governance planning only; reruns are safe as long as the intended workflow correction is recorded explicitly rather than inferred from branch habits
- if the correction proves too broad, follow-on slices should separate workflow semantics from merge-readiness semantics rather than silently mixing them

## Artifacts and Notes

- this slice exists because the current written workflow does not match the intended operating model for initiative-local planning and execution
- the correction should prefer one authoritative living plan per initiative rather than forcing partial plan history onto `main` before the initiative is complete

## Interfaces and Dependencies

- this correction touches the relationship between branch roles, finalization semantics, merge readiness, and orchestrator stop conditions
- the resulting model should remain compatible with managed-repo orchestration and the local-orchestration runtime direction
