---
id: "20260311-implementation-branch-split-governance-codex-01-execplan"
title: "Require separate implementation branches for parallel ExecPlan workflows"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: approved
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
finalized_by: "github:justin-napolitano"
finalized_at: "2026-03-11T00:00:00Z"
finalized_in_pr: "50"
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
  - title: "Capture follow-on one-command human finalization automation"
    priority: "P2"
depends_on: []
---

# Purpose / Big Picture

Require each parallel ExecPlan workflow to execute on its own implementation branch so draft-plan branches, implementation branches, and optional queue branches remain distinct and auditable.

This change should tighten governance around parallel work without forbidding deliberate queue or integration branches.

## Progress

- [x] Draft governing rule changes
- [x] Update canonical branch-pattern specs
- [x] Update governance and agent docs
- [x] Validate the governing ExecPlan

## Surprises & Discoveries

- the current governance docs distinguish protected vs non-protected branches, but they do not yet distinguish draft-plan branches from implementation branches
- queue branches are useful for stacked integration, but they should not be treated as the canonical execution branch for an individual ExecPlan slice
- human finalization remains too manual; the better follow-on is a deterministic `finalize-execplan` flow that derives metadata from repo history and keeps the human at the signing boundary
- signed merge commits on `main` are a better finalization authority signal than intermediate implementation commits because they capture the human acceptance event directly

## Decision Log

- 2026-03-11 / agent-codex-01 / A governing ExecPlan is required before changing governance-controlled branch policy files.
- 2026-03-11 / agent-codex-01 / The governance switch should also record a follow-on design target for one-command human finalization driven by commit history and signer identity.
- 2026-03-11 / agent-codex-01 / Governed ExecPlan finalization should standardize on signed merge commits rather than intermediate commits as the canonical authority event.

## Outcomes & Retrospective

On completion, the repository should explicitly require one implementation branch per active ExecPlan workflow while allowing optional queue branches for deliberate stacking.

This slice should also leave a clear follow-on governance/runtime direction: automate ExecPlan finalization preparation, derive finalization metadata from commit history where possible, and preserve human authority through a single signed finalization command.

The implemented policy now treats signed merge commits on `main` as the preferred authority boundary for governed ExecPlan finalization.

## Context and Orientation

Recent parallel slice execution showed that draft-plan branches can remain empty while implementation work accumulates on a shared queue branch. That weakens provenance and makes per-slice merge handling ambiguous.

## Plan of Work

1. Add canonical policy language for implementation branches.
2. Distinguish draft-plan branches from implementation branches.
3. Clarify queue branches as integration-only branches.
4. Update agent-facing governance docs to reflect the split.
5. Record the follow-on `bin/finalize-execplan` automation target as the preferred path for future human finalization.

## Concrete Steps

1. Update `spec/workflow.yaml` and `spec/ruleset.yaml`.
2. Update `docs/governance.md` and `docs/agent-game-rules-v1.md`.
3. Update `policy/game-rules.md`, `.agent/AGENTS.md`, `.agent/PLANS.md`, and `docs/agents.md`.
4. Add plan language that positions deterministic one-command finalization as a follow-on governed improvement.
5. Run `bin/execplan-validate .agent/execplans/20260311-implementation-branch-split-governance-codex-01-execplan.md`.

## Validation and Acceptance

Acceptance criteria:

- branch policy distinguishes draft, implementation, and optional queue branches
- parallel ExecPlan workflows require distinct implementation branches
- docs and canonical specs agree on the branch split model
- the plan explicitly records one-command human finalization as the preferred follow-on automation path

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
