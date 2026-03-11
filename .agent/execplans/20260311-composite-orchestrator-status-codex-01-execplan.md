---
id: "20260311-composite-orchestrator-status-codex-01-execplan"
title: "Implement the composite orchestrator status surface"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-composite-orchestrator-status-codex-01-execplan.md
  - bin/orchestrator-status
  - src/platform_tools/orchestrator_status.py
  - bin/planner
  - bin/citation-check
  - bin/planner-score
  - bin/rule-graph-check
  - bin/merge-readiness-check
  - tests/test_orchestrator_status.py
  - bin/orchestrator-status-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-composite-orchestrator-status-codex-01-execplan.md"
      expected_exit: 0
    - name: "orchestrator-status-smoke-test"
      command: "bin/orchestrator-status-smoke-test"
      expected_exit: 0
tasks:
  - title: "Aggregate planner, rule, citation, score, and merge-readiness surfaces"
    priority: "P1"
  - title: "Expose ready work, blockers, and authority constraints"
    priority: "P1"
  - title: "Produce machine-readable next-action recommendations"
    priority: "P1"
  - title: "Add focused tests and smoke coverage"
    priority: "P1"
depends_on:
  - "20260311-machine-readable-output-hardening-codex-01-execplan"
---

# Purpose / Big Picture

Implement the composite orchestrator status command that exposes ready work, blockers, required validations, authority constraints, and recommended next actions in one machine-readable surface.

This slice is blocked on machine-readable output hardening because it should consume stable command contracts rather than normalize inconsistent outputs internally.

## Progress

- [x] Implement orchestrator-status command
- [x] Aggregate readiness, rule, citation, and score surfaces
- [x] Expose blockers and next actions
- [x] Add focused tests and smoke coverage

## Surprises & Discoveries

- status aggregation may expose gaps in one or more existing machine-readable contracts
- next-action recommendations may need a small policy layer rather than simple sorting
- merge-readiness aggregation must avoid recursively executing the orchestrator-status smoke test, so the status surface uses a non-recursive merge-readiness summary path
- the remaining-work graph needed to be the canonical source for ready and blocked slices, with reference artifacts filtered out of executable work lists

## Decision Log

- 2026-03-11 / agent-codex-01 / Composite orchestrator status should consume stable command contracts rather than normalize inconsistent outputs internally.
- 2026-03-11 / agent-codex-01 / The orchestrator status surface should summarize merge readiness without re-running plan validations so smoke-test validation does not recurse through itself.

## Outcomes & Retrospective

On completion, this slice should provide one machine-readable command that tells Codex what is ready, what is blocked, and what should happen next.

The implemented status surface now identifies the active slice from the canonical remaining-work graph, reports authority constraints and blockers, and recommends the next orchestration action in a deterministic JSON envelope.

## Context and Orientation

This slice is intentionally blocked on machine-readable output hardening because it should aggregate stable contracts rather than patch around unstable ones.

## Plan of Work

1. Implement the composite status runtime.
2. Aggregate readiness, rule, citation, score, and merge-readiness surfaces.
3. Add focused tests.
4. Add a smoke path for the full status command.

## Concrete Steps

1. Add `src/platform_tools/orchestrator_status.py`.
2. Add `bin/orchestrator-status`.
3. Integrate the existing validator and readiness commands.
4. Add tests and `bin/orchestrator-status-smoke-test`.
5. Run:
   - `bin/execplan-validate .agent/execplans/20260311-composite-orchestrator-status-codex-01-execplan.md`
   - `bin/orchestrator-status-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- the status command is fully machine-readable
- blockers and next actions are explicit
- the smoke script passes

## Idempotence and Recovery

This slice should be safe to rerun if the aggregated status output is deterministic and the smoke script does not create disposable artifacts.

## Artifacts and Notes

Expected artifacts:

- `bin/orchestrator-status`
- `src/platform_tools/orchestrator_status.py`
- focused tests
- `bin/orchestrator-status-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `docs/codex-orchestrator-contract.md`
- `docs/merge-readiness-contract.md`
- `bin/merge-readiness-check`
