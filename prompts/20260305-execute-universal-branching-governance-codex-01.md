# Codex Prompt - Execute Universal Branching Governance Plan

Generated: 2026-03-05

You are Codex operating in a repository with plan-driven governance.

Your task is to execute ExecPlan `20260305-universal-branching-governance-codex-01-execplan` and enforce universal branch-first policy deterministically.

## Mandatory Precondition

Before any file changes, create/switch to a dedicated branch matching:

`draft-execplan/<plan-id>-<agent>-YYYYMMDD`

Do not execute this plan on `main`.

## Rules

1. Work only through `.agent/execplans/20260305-universal-branching-governance-codex-01-execplan.md`.
2. Do not modify `.agent/AGENTS.md` or `.agent/PLANS.md`.
3. Canonical logic location is `src/platform_tools/*`.
4. `bin/*` remains operator entrypoints.
5. Outputs must be deterministic and machine-readable where applicable.

## Required Implementation Scope

- Add universal branch constraints in `spec/ruleset.yaml` and `spec/workflow.yaml`.
- Add matching normative policy updates in:
  - `policy/agents.md`
  - `policy/execplans.md`
  - `policy/game-rules.md`
- Add deterministic branch-policy checks in:
  - `src/platform_tools/execplan_lint.py`
  - `src/platform_tools/repo_health.py`
  - `bin/repo-health-check` (surface branch-check result)

## Required Validation Order

1. `bin/execplan-validate .agent/execplans/*.md`
2. `bin/repo-health-check`
3. `bin/run-local-ci`

Do not reorder.

## Required Output

### JSON report

{
  "issues": [],
  "completed_tasks": [],
  "remaining_work": [],
  "branch_policy_findings": [],
  "artifacts": []
}

### Human summary

Max 12 lines with:

- what was implemented
- what failed and why
- next blocking item in order

## Stop Rule

If running on a non-compliant branch, stop immediately and report the branch-policy failure before any edits.
