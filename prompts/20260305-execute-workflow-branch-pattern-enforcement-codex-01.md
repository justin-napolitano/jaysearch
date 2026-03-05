# Codex Prompt - Execute Workflow Branch-Pattern Enforcement Plan

Generated: 2026-03-05

You are Codex operating in a plan-governed repository.

Your task is to execute ExecPlan `20260305-workflow-branch-pattern-enforcement-codex-01-execplan`.

## Mandatory Precondition

Before any repository action (read/validate/edit/commit), create/switch to a dedicated branch matching:

`draft-execplan/<plan-id>-<agent>-YYYYMMDD`

Do not run on `main`.

## Scope

1. Add workflow-specific branch pattern rules in `spec/ruleset.yaml` and `spec/workflow.yaml`.
2. Enforce branch pattern compliance in:
   - `src/platform_tools/branch_policy.py`
   - `src/platform_tools/execplan_lint.py`
   - `src/platform_tools/repo_health.py`
3. Remove or clarify ambiguous command entry in `docs/commands.md` (`git execfinal`).

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
  "branch_pattern_findings": [],
  "artifacts": []
}

### Human summary

Maximum 12 lines with:

- what was implemented
- what failed and why
- next blocking item in order

## Stop Rule

If branch does not match required workflow pattern, stop and report mismatch before any file edits.
