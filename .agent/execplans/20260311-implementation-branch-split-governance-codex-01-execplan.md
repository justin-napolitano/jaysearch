---
id: "20260311-implementation-branch-split-governance-codex-01-execplan"
title: "Require separate implementation branches for parallel ExecPlan workflows"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-implementation-branch-split-governance-codex-01-execplan.md
  - docs/governance.md
  - docs/agent-game-rules-v1.md
  - spec/workflow.yaml
  - spec/ruleset.yaml
  - policy/game-rules.md
  - .agent/AGENTS.md
  - .agent/PLANS.md
  - docs/agents.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-queued-execplans-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-implementation-branch-split-governance-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define implementation-branch requirement for parallel ExecPlan execution"
    priority: "P1"
  - title: "Add canonical branch-pattern language for implementation branches"
    priority: "P1"
  - title: "Clarify queue branches as optional integration branches rather than implementation branches"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Require each parallel ExecPlan workflow to execute on its own implementation branch so draft-plan branches, implementation branches, and optional queue branches remain distinct and auditable.

This change should tighten governance around parallel work without forbidding deliberate queue or integration branches.

## Progress

- [ ] Draft governing rule changes
- [ ] Update canonical branch-pattern specs
- [ ] Update governance and agent docs
- [ ] Validate the governing ExecPlan

## Surprises & Discoveries

- the current governance docs distinguish protected vs non-protected branches, but they do not yet distinguish draft-plan branches from implementation branches
- queue branches are useful for stacked integration, but they should not be treated as the canonical execution branch for an individual ExecPlan slice

## Decision Log

- 2026-03-11 / agent-codex-01 / A governing ExecPlan is required before changing governance-controlled branch policy files.

## Outcomes & Retrospective

On completion, the repository should explicitly require one implementation branch per active ExecPlan workflow while allowing optional queue branches for deliberate stacking.

## Context and Orientation

Recent parallel slice execution showed that draft-plan branches can remain empty while implementation work accumulates on a shared queue branch. That weakens provenance and makes per-slice merge handling ambiguous.

## Plan of Work

1. Add canonical policy language for implementation branches.
2. Distinguish draft-plan branches from implementation branches.
3. Clarify queue branches as integration-only branches.
4. Update agent-facing governance docs to reflect the split.

## Concrete Steps

1. Update `spec/workflow.yaml` and `spec/ruleset.yaml`.
2. Update `docs/governance.md` and `docs/agent-game-rules-v1.md`.
3. Update `policy/game-rules.md`, `.agent/AGENTS.md`, `.agent/PLANS.md`, and `docs/agents.md`.
4. Run `bin/execplan-validate .agent/execplans/20260311-implementation-branch-split-governance-codex-01-execplan.md`.

## Validation and Acceptance

Acceptance criteria:

- branch policy distinguishes draft, implementation, and optional queue branches
- parallel ExecPlan workflows require distinct implementation branches
- docs and canonical specs agree on the branch split model

## Idempotence and Recovery

This governing slice should be safe to rerun if it changes only policy text and canonical branch-pattern metadata without mutating runtime state.

## Artifacts and Notes

Expected artifacts:

- updated governance and agent policy docs
- updated workflow and ruleset branch metadata

## Interfaces and Dependencies

Primary dependencies:

- `docs/governance.md`
- `docs/agent-game-rules-v1.md`
- `spec/workflow.yaml`
- `spec/ruleset.yaml`
