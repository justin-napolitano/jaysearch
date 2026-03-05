# Codex Prompt - Execute Platform Hostile Review Sweep

Generated: 2026-03-05

You are Codex operating in a plan-governed repository.

Your task is to execute ExecPlan `20260305-platform-hostile-review-sweep-codex-01-execplan` and produce a rigorous hostile review of governance, enforcement, auditability, and usability.

## Mandatory Precondition

Before any repository action (read/validate/edit/commit), create/switch to a dedicated branch matching:

`draft-execplan/<plan-id>-<agent>-YYYYMMDD`

Do not run this review on `main`.

## Scope

Review all of the following with adversarial rigor:

1. Branch policy rules and enforcement behavior
2. Commit identity/metadata rules and operator commit path
3. Validator determinism and stable exit-code semantics
4. TODO generation/sync correctness and idempotence
5. Documentation/operator workflow clarity and friction
6. Prompt contracts and stop-rule behavior

## Required Commands

Run and record outputs:

1. `bin/execplan-validate .agent/execplans/*.md`
2. `bin/repo-health-check`
3. `bin/execplan-test`
4. `bin/run-local-ci`

## Required Artifacts

Write deterministic artifacts:

- `artifacts/review/platform-hostile-review-report.json`
- `artifacts/review/platform-hostile-review-summary.md`
- `artifacts/review/platform-hostile-review-evidence.json`

## Required Output

### JSON report

{
  "issues": [],
  "security_findings": [],
  "usability_gaps": [],
  "determinism_risks": [],
  "recommended_fixes": [],
  "artifacts": []
}

### Human summary

Maximum 12 lines with:

- top risks and severity
- what is already strong
- next blocking item to address first

## Stop Rule

If branch policy is violated or governance contracts conflict, stop and report conflicts before proposing implementation changes.
