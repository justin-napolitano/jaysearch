# Codex Prompt - MultiAgent Control Plane MVP Execution

Generated: 2026-03-05

You are Codex operating in a repository that implements an ExecPlan-driven AI engineering platform.

Your objective is to implement the **minimum operational multi-agent control plane** so this template can be reused across future Codex projects.

Follow these constraints exactly:

1. All implementation work must originate from an ExecPlan.
2. Do not modify `.agent/AGENTS.md` or `.agent/PLANS.md`.
3. Use canonical plan identity format: `YYYYMMDD-<plan-name>-<owner>-execplan`.
4. Canonical logic location is `src/platform_tools/*`.
5. `bin/*` are operator entrypoints/wrappers.
6. Outputs must be deterministic and machine-readable.

## Mission

Build a control plane that can:

- enforce rule contracts from `spec/*`
- score agent execution using `spec/scoring.yaml` and `.agent/metrics.yml`
- run deterministic referee checks
- emit auditable run artifacts
- support Planner/Builder/Reviewer/Compliance role workflow

## Required Deliverables

1. Rule loader and contract validator
- parse and validate `spec/execplan.schema.yaml`, `spec/ruleset.yaml`, `spec/workflow.yaml`, `spec/exit-codes.yaml`, `spec/scoring.yaml`

2. Referee engine
- deterministic execution pipeline for:
  - `bin/execplan-validate`
  - `bin/run-local-ci`
  - optional gates when available (`bin/repo-health-check`, `bin/execplan-test`, `bin/sync-todos`)

3. Score engine
- compute session/turn score from `DQ`, `HED`, `VPR`, `SLS`, `BC`
- apply penalties from `spec/scoring.yaml`

4. Evidence and audit output
- produce deterministic JSON reports for each run
- include rule checks, command results, score breakdown, violations

5. Multi-agent turn protocol support
- explicit state transitions for plan turn lifecycle
- enforce allowed/forbidden moves from `spec/ruleset.yaml`

## Execution Steps

1. Audit current platform code and identify placeholders.
2. Create/update an ExecPlan for control-plane implementation.
3. Implement in `src/platform_tools/*` and wire `bin/*` wrappers.
4. Add deterministic tests and fixture-based validations.
5. Run full local referee sequence and capture evidence.
6. Update ExecPlan progress and produce final JSON + concise human summary.

## Required Output

### 1) JSON report

{
  "status": "pass|fail",
  "implemented": [],
  "violations": [],
  "score": {},
  "artifacts": [],
  "next_execplan": ""
}

### 2) Human summary

Max 12 lines with:

- completed deliverables
- remaining blockers
- recommended next ExecPlan

## Stop Rule

If governance/spec conflicts are found, stop implementation and report exact file-level conflicts before continuing.
