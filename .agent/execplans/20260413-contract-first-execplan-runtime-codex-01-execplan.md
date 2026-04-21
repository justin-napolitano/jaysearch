---
id: "20260413-contract-first-execplan-runtime-codex-01-execplan"
title: "Hard-cut runtime and bootstrap surfaces to the contract-first planning model"
owner: "agent/codex-01"
created: "2026-04-13T00:00:00Z"
status: draft
base_branch: "initiative/contract-first-planning"
changes:
  - .agent/execplans/20260413-contract-first-execplan-runtime-codex-01-execplan.md
  - .agent/AGENTS.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - bin/port-execplan
  - docs/agent-game-rules-v1.md
  - docs/agents.md
  - docs/governance.md
  - docs/planner-execplan-projection.md
  - docs/queued-execplans.md
  - pyproject.toml
  - src/platform_tools/game_status.py
  - src/platform_tools/register_remaining_work_node.py
  - src/platform_tools/policy_compliance_check.py
  - src/platform_tools/reconcile_remaining_work_transition.py
  - src/platform_tools/run_governed_pre_push_checks.py
  - src/platform_tools/state_transition_legality.py
  - src/platform_tools/planner_runtime.py
  - src/platform_tools/bootstrap_managed_repo.py
  - tests/test_bootstrap_managed_repo.py
  - src/platform_tools/port_execplan.py
  - tests/test_policy_compliance_check.py
  - tests/test_planner_cli.py
  - tests/test_port_execplan.py
  - tests/test_reconcile_remaining_work_merge.py
  - tests/test_reconcile_remaining_work_transition.py
  - tests/test_run_governed_pre_push_checks.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/contract-first-planning"
initiative_node_id: "initiative-contract-first-planning"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260413-contract-first-execplan-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260413-contract-first-execplan-runtime-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Fail closed on initiative branches in governed pre-push checks so authoritative planning branches cannot bypass ExecPlan validation"
    priority: "P1"
  - title: "Replace draft-first planner-generated ExecPlans with initiative-first contract-first artifacts"
    priority: "P1"
  - title: "Update managed-repo bootstrap defaults so new repos seed the initiative-first planning flow"
    priority: "P1"
  - title: "Remove stale agent guidance that still instructs draft-branch planning"
    priority: "P1"
depends_on:
  - "95c8581"
---

## Outcomes & Retrospective

This slice closes the highest-risk gaps left by the initiative-level policy change: enforcement, generation, bootstrap, and agent guidance must all agree on the same planning model before more implementation work proceeds.

## Context and Orientation

The hostile review found four concrete mismatches that make the current contract-first shift incomplete in practice:

1. `src/platform_tools/run_governed_pre_push_checks.py` still skips ExecPlan validation on `initiative/*`.
2. `src/platform_tools/planner_runtime.py` still generates `draft-execplan/*` plans with verbose legacy sections.
3. `src/platform_tools/bootstrap_managed_repo.py` still bootstraps the old draft-first workflow into new repos.
4. `.agent/AGENTS.md` still tells agents to propose plans on draft branches.

This branch is the first implementation slice under `initiative/contract-first-planning`, so it should hard-cut those runtime and bootstrap mismatches rather than layering compatibility on top.

## Plan of Work

1. Extend governed pre-push enforcement so initiative branches with authoritative plans are linted and blocked the same way implementation branches are.
2. Rewrite planner-generated ExecPlans to emit the thinner contract-first template and stop manufacturing draft-branch metadata as the default planning path.
3. Update managed-repo bootstrap outputs so freshly spawned repos learn the initiative-first planning flow immediately.
4. Correct the agent bootstrap instructions so new sessions do not regress back to draft-first behavior.
5. Keep migration tooling and downstream cleanup in later implementation slices rather than widening this branch beyond the hostile-review blockers.

## Validation and Acceptance

The branch is acceptable when:

- governed pre-push checks fail on malformed or missing initiative-branch ExecPlans
- planner-generated plans no longer default to `draft-execplan/*` or legacy section headings
- managed-repo bootstrap output reflects initiative-first planning by default
- agent-facing bootstrap guidance no longer instructs draft-first planning
- focused tests for the touched runtime, planner, and bootstrap surfaces pass

## Artifacts and Notes

Planned follow-on slices after this branch:

- migration tool to port old prose-heavy ExecPlans into the contract-first shape
- bootstrap/template propagation and cleanup across remaining docs/examples/fixtures
- final enforcement tightening once the porting tool exists
