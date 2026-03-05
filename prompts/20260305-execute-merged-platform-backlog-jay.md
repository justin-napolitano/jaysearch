# Codex Prompt - Execute Merged Platform Backlog

Generated: 2026-03-05

You are Codex operating in a repository where platform planning branches have already been merged to `main`, but implementation remains incomplete.

Your job is to execute the merged platform backlog strictly through existing ExecPlans and produce deterministic evidence.

## Merged history to account for

Merged PR sequence includes:

- #6 `draft-execplan/platform-validator-jay-20260304`
- #7 `draft-execplan/todo-automation-jay-20260304`
- #8 `draft-execplan/repo-health-engine-jay-20260304`
- #9 `draft-execplan/spec-test-runner-jay-20260304`

## Rules

1. Work only through ExecPlans present in `.agent/execplans/`.
2. Do not modify `.agent/AGENTS.md` or `.agent/PLANS.md`.
3. Use canonical logic location `src/platform_tools/*`.
4. Keep `bin/*` as operator entrypoints.
5. Deterministic JSON outputs and stable exit codes are mandatory.

## Required Execution Order

1. `20260304-platform-validator-jay-execplan`
2. `20260304-todo-automation-jay-execplan`
3. `20260304-repo-health-engine-jay-execplan`
4. `20260304-spec-test-runner-jay-execplan`

Do not reorder.

## Expected deliverables by plan

### platform-validator

- `src/platform_tools/execplan_lint.py`
- `src/platform_tools/security_scan.py`
- `src/platform_tools/agent_score.py`
- `src/platform_tools/diff_analyzer.py`
- `bin/execplan-validate`
- `bin/run-local-ci`

### todo-automation

- `src/platform_tools/generate_todos.py`
- `bin/sync-todos`

### repo-health-engine

- `src/platform_tools/repo_health.py`
- `bin/repo-health-check`

### spec-test-runner

- `src/platform_tools/spec_test_runner.py`
- `bin/execplan-test`

## Validation requirements

Run and report:

- `bin/execplan-validate .agent/execplans/*.md`
- `bin/sync-todos`
- `bin/repo-health-check`
- `bin/execplan-test`
- `bin/run-local-ci`

All outputs must be deterministic and machine-readable where applicable.

## Required output

### JSON report

{
  "issues": [],
  "completed_plans": [],
  "remaining_work": [],
  "security_findings": [],
  "artifacts": []
}

### Human summary

Max 12 lines with:

- what executed successfully
- what failed and why
- next blocking item in order

## Stop Rule

If an earlier plan in the sequence is incomplete or non-compliant, stop and do not execute later plans.
