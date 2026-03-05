---
id: 20260305-universal-branching-governance-codex-01-execplan
title: Enforce universal branch-first execution governance
owner: "agent/codex-01"
created: "2026-03-05T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260305-universal-branching-governance-codex-01-execplan.md
  - prompts/20260305-execute-universal-branching-governance-codex-01.md
  - spec/ruleset.yaml
  - spec/workflow.yaml
  - policy/agents.md
  - policy/execplans.md
  - policy/game-rules.md
  - src/platform_tools/execplan_lint.py
  - src/platform_tools/repo_health.py
  - bin/repo-health-check
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/universal-branching-governance-codex-01-20260305"
draft_created: "2026-03-05T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: execplan_validate
      command: bin/execplan-validate .agent/execplans/*.md
      expected_exit: 0
    - name: repo_health_check
      command: bin/repo-health-check
      expected_exit: 0

tasks:
  - title: Require unique non-main branch for every execution run
    priority: P1
  - title: Define hostile-review branch contract and artifact paths
    priority: P1
  - title: Add deterministic branch-policy checks to validators
    priority: P1
  - title: Add deterministic failure semantics for branch-policy violations
    priority: P1
  - title: Publish operator guidance for branch-first workflow
    priority: P2

depends_on:
  - 20260305-multiagent-review-prompt-jay-execplan
---

# Purpose / Big Picture

Establish universal branch-first governance so all repository actions are executed on dedicated branches and never directly on `main`.

After completion, branch policy violations become deterministic validation failures with machine-readable evidence.

## Progress

- [ ] Create ExecPlan draft
- [ ] Add branch-first rules to canonical spec/policy files
- [ ] Add validator checks for branch policy compliance
- [ ] Add deterministic evidence outputs for branch checks
- [ ] Run deterministic validation commands
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: branch-first execution is universal and not limited to ExecPlan implementation or hostile review.

Rationale: prevents unreviewed direct commits to protected flows and makes audit trails deterministic.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

Current governance enforces branching for ExecPlan implementation and hostile review workflows, but not all repository actions. This gap permits ambiguous execution context and reduces auditability.

This plan introduces universal branch requirements, deterministic checks, and explicit failure semantics.

## Plan of Work

1. Update canonical rules in `spec/ruleset.yaml` and `spec/workflow.yaml`.
2. Mirror normative policy statements in `policy/*`.
3. Implement branch compliance checks in validator/health tooling.
4. Ensure machine-readable outputs include branch violations.
5. Validate deterministic behavior through existing command interfaces.

## Concrete Steps

1. Add universal branch constraints to `spec/ruleset.yaml` and `spec/workflow.yaml`.
2. Update `policy/agents.md`, `policy/execplans.md`, and `policy/game-rules.md`.
3. Extend `src/platform_tools/execplan_lint.py` and `src/platform_tools/repo_health.py` to report branch-policy failures deterministically.
4. Ensure `bin/repo-health-check` surfaces branch-policy status in JSON output and stable exit codes.
5. Run:
   - `bin/execplan-validate .agent/execplans/*.md`
   - `bin/repo-health-check`
   - `bin/run-local-ci`

## Validation and Acceptance

Plan is accepted when:

- universal branch-first rules are present in canonical spec/policy files;
- branch-policy violations are surfaced as deterministic machine-readable errors;
- `bin/repo-health-check` fails when execution branch is non-compliant;
- repeated runs with unchanged state produce stable output and exit codes.

## Idempotence and Recovery

Rule and validator updates are safe to reapply. If violations occur, switch to a compliant branch and rerun checks without cleanup operations.

## Artifacts and Notes

Artifacts expected:

- JSON validator output showing branch-policy check status
- JSON repository health output with branch-compliance section
- CI evidence from `bin/run-local-ci`

## Interfaces and Dependencies

Interfaces:

- `spec/ruleset.yaml`
- `spec/workflow.yaml`
- `policy/agents.md`
- `policy/execplans.md`
- `policy/game-rules.md`
- `src/platform_tools/execplan_lint.py`
- `src/platform_tools/repo_health.py`
- `bin/repo-health-check`

Dependencies:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- existing deterministic validator command surfaces
