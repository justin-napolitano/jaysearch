# Codex Prompt - Execute Governance Dual-Mode Loader

Generated: 2026-03-05

You are Codex operating in a repository where the governance/platform roadmap is merged, and the next implementation target is dual-mode governance loading.

Execute strictly through:

- `20260305-governance-dual-mode-loader-codex-01-execplan`

## Intent

Implement a deterministic governance loader so the engine supports:

1. Standalone mode (self-contained local governance).
2. Managed mode (external governance baseline + local codex overlays).

Managed mode must never weaken baseline controls.

## Rules

1. Work only through ExecPlans present in `.agent/execplans/`.
2. Do not modify `.agent/AGENTS.md` or `.agent/PLANS.md`.
3. Keep canonical logic in `src/platform_tools/*`.
4. Keep `bin/*` as operator entrypoints.
5. Deterministic JSON outputs and stable exit codes are mandatory.
6. All execution must occur on a dedicated non-`main` branch.

## Required Implementation Outcomes

- Runtime mode contract exists (`standalone`, `managed`) with explicit governance source handling.
- Governance loader normalizes local + external policy into deterministic effective policy.
- Merge rules enforce non-weakening in managed mode.
- Existing validators consume effective policy instead of hardcoded local-only assumptions.
- Deterministic regression coverage exists for both modes.

## Required Validation Commands

Run and report:

- `bin/execplan-validate .agent/execplans/*.md`
- `bin/sync-todos`
- `bin/repo-health-check`
- `bin/execplan-test`
- `bin/run-local-ci`

## Required Output

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

If deterministic merge/precedence behavior is not fully enforced, stop and report blocker details before proceeding.
