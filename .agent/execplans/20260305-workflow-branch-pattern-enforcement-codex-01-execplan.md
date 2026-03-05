---
id: 20260305-workflow-branch-pattern-enforcement-codex-01-execplan
title: Enforce workflow-specific branch patterns and clean command docs
owner: "agent/codex-01"
created: "2026-03-05T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260305-workflow-branch-pattern-enforcement-codex-01-execplan.md
  - prompts/20260305-execute-workflow-branch-pattern-enforcement-codex-01.md
  - spec/ruleset.yaml
  - spec/workflow.yaml
  - policy/execplans.md
  - policy/game-rules.md
  - src/platform_tools/branch_policy.py
  - src/platform_tools/execplan_lint.py
  - src/platform_tools/repo_health.py
  - docs/commands.md
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/workflow-branch-pattern-enforcement-codex-01-20260305"
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
    - name: run_local_ci
      command: bin/run-local-ci
      expected_exit: 0

tasks:
  - title: Enforce workflow-specific branch patterns in branch policy evaluator
    priority: P1
  - title: Expose branch-pattern violations in execplan lint report
    priority: P1
  - title: Expose branch-pattern violations in repository health report
    priority: P1
  - title: Add deterministic rule metadata for workflow branch patterns
    priority: P1
  - title: Remove or replace ambiguous git execfinal command documentation
    priority: P2

depends_on:
  - 20260305-universal-branching-governance-codex-01-execplan
---

# Purpose / Big Picture

Close the remaining governance gap by enforcing workflow-specific branch naming patterns (not just non-main), and remove ambiguous command documentation that reduces operator clarity.

After completion, branch compliance checks will deterministically validate expected branch formats per workflow, and command docs will only contain supported entries.

## Progress

- [ ] Create ExecPlan draft
- [ ] Add workflow branch-pattern rule metadata
- [ ] Implement branch-pattern enforcement in validators
- [ ] Clean up ambiguous command documentation
- [ ] Run deterministic validation commands
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: branch policy checks should validate workflow-specific patterns, not only protected-branch exclusions.

Rationale: stronger auditability and earlier operator feedback.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

Hostile review identified two follow-up risks:

- branch policy currently treats all non-main branches as compliant;
- command reference includes `git execfinal`, which is ambiguous and not clearly supported.

This plan resolves both with deterministic enforcement and documentation cleanup.

## Plan of Work

1. Extend rules metadata with explicit workflow branch patterns.
2. Enhance branch policy evaluation to validate active branch against these patterns.
3. Surface violations in lint/health reports with stable error codes.
4. Remove or replace ambiguous command docs entry.

## Concrete Steps

1. Update `spec/ruleset.yaml` and `spec/workflow.yaml` with workflow-specific branch pattern rules.
2. Update `src/platform_tools/branch_policy.py` evaluation logic.
3. Ensure `src/platform_tools/execplan_lint.py` and `src/platform_tools/repo_health.py` report pattern failures deterministically.
4. Update `docs/commands.md` to remove or clarify `git execfinal`.
5. Run:
   - `bin/execplan-validate .agent/execplans/*.md`
   - `bin/repo-health-check`
   - `bin/run-local-ci`

## Validation and Acceptance

Plan is accepted when:

- workflow-specific branch pattern checks are enforced in machine-readable reports;
- branch mismatch produces deterministic failure output;
- docs command list has no ambiguous unsupported command entries;
- all required validation commands pass on compliant branch.

## Idempotence and Recovery

Changes are safe to reapply. If branch checks fail, switch to a compliant branch name and rerun validations.

## Artifacts and Notes

Expected artifacts:

- JSON lint report with branch-pattern check details
- JSON repo health report with branch-pattern check details
- updated command reference

## Interfaces and Dependencies

Interfaces:

- `spec/ruleset.yaml`
- `spec/workflow.yaml`
- `policy/execplans.md`
- `policy/game-rules.md`
- `src/platform_tools/branch_policy.py`
- `src/platform_tools/execplan_lint.py`
- `src/platform_tools/repo_health.py`
- `docs/commands.md`

Dependencies:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- `20260305-universal-branching-governance-codex-01-execplan`
