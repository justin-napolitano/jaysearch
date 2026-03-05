# Codex Prompt - MultiAgent Platform Hostile Review

Generated: 2026-03-05

You are Codex operating inside a repository that implements a plan-driven development platform.

Your task is to perform a rigorous hostile review of the repository and then propose remaining work strictly through ExecPlans.

Before final output, verify consistency with:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- `spec/*`
- `policy/*`
- `docs/*`

Do not invent architecture outside existing repository contracts.

## Review Scope

Review these areas:

1. Governance correctness
2. ExecPlan completeness
3. Validation determinism
4. Security exposure
5. Agent workflow integrity
6. Repository structure
7. Missing or inconsistent ExecPlans

For every issue include:

- file path
- explanation
- suggested fix

## Execution Rules

1. All implementation work must originate from an ExecPlan.
2. Agents may draft but not finalize authoritative changes.
3. Humans finalize with SSH-signed commits.
4. Do not modify `.agent/AGENTS.md` or `.agent/PLANS.md` unless covered by an approved governance ExecPlan.
5. Canonical plan key format is `YYYYMMDD-<plan-name>-<owner>-execplan`.
6. Canonical logic location is `src/platform_tools/*`.

## Platform Plan Set to Verify

- `20260304-docs-governance-bootstrap-jay-execplan`
- `20260304-platform-validator-jay-execplan`
- `20260304-todo-automation-jay-execplan`
- `20260304-repo-health-engine-jay-execplan`
- `20260304-spec-test-runner-jay-execplan`

## Required Output

### 1) JSON report

{
  "issues": [],
  "missing_execplans": [],
  "security_findings": [],
  "recommended_fixes": []
}

### 2) Human summary

Maximum 12 lines including:

- top architectural risks
- missing platform components
- recommended next ExecPlan

## Stop Rule

If governance/spec conflicts are found, stop execution work and report exact conflicts first.
