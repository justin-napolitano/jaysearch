---
id: "20260311-machine-readable-output-hardening-codex-01-execplan"
title: "Harden machine-readable outputs for orchestrator-facing commands"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-machine-readable-output-hardening-codex-01-execplan.md
  - bin/planner
  - bin/citation-check
  - bin/planner-score
  - bin/rule-graph-check
  - src/platform_tools/planner_cli.py
  - src/platform_tools/citation_check.py
  - src/platform_tools/planner_score.py
  - src/platform_tools/rule_graph_check.py
  - tests/test_planner_cli.py
  - tests/test_citation_check.py
  - tests/test_planner_score.py
  - tests/test_rule_graph_check.py
  - bin/orchestrator-output-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-machine-readable-output-hardening-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-machine-readable-output-hardening-codex-01-execplan.md"
      expected_exit: 0
    - name: "orchestrator-output-smoke-test"
      command: "bin/orchestrator-output-smoke-test"
      expected_exit: 0
tasks:
  - title: "Normalize planner JSON output contract"
    priority: "P1"
  - title: "Normalize citation-check JSON output contract"
    priority: "P1"
  - title: "Normalize planner-score JSON output contract"
    priority: "P1"
  - title: "Normalize rule-graph-check JSON output contract"
    priority: "P1"
  - title: "Add smoke coverage for orchestrator-facing outputs"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Harden the machine-readable outputs for the orchestrator-facing command set so later orchestration work does not depend on inconsistent JSON shapes or prose parsing.

This slice should normalize the output contracts for `bin/planner`, `bin/citation-check`, `bin/planner-score`, and `bin/rule-graph-check`, then add one smoke path that proves those contracts remain callable and stable.

## Progress

- [ ] Normalize planner output contract
- [ ] Normalize citation-check output contract
- [ ] Normalize planner-score output contract
- [ ] Normalize rule-graph-check output contract
- [ ] Add smoke coverage

## Surprises & Discoveries

- output shapes may already be close enough that this slice is mostly normalization and test hardening
- some commands may need explicit `--json` support even if they already print JSON today

## Decision Log

- 2026-03-11 / agent-codex-01 / Orchestrator-facing commands must prefer stable machine-readable outputs over ad hoc human formatting.

## Outcomes & Retrospective

On completion, this slice should leave the key orchestration commands with stable JSON surfaces and one smoke test that verifies they can be consumed together.

## Context and Orientation

This is the first ready slice in the queued execution backlog. It should precede the composite orchestrator status command because the status layer should consume stable command contracts rather than normalize inconsistent outputs internally.

## Plan of Work

1. Review current JSON output behavior across the four commands.
2. Normalize shared top-level fields where appropriate.
3. Add or tighten focused tests.
4. Add a smoke script that exercises the primary orchestrator-facing output path.

## Concrete Steps

1. Update the relevant command implementations and wrappers.
2. Preserve non-zero exits on failure.
3. Add tests for the normalized JSON shape.
4. Add `bin/orchestrator-output-smoke-test`.
5. Run:
   - `bin/execplan-validate .agent/execplans/20260311-machine-readable-output-hardening-codex-01-execplan.md`
   - `bin/orchestrator-output-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- all four commands emit stable machine-readable output
- focused tests cover the normalized contract
- the smoke script passes

## Idempotence and Recovery

This slice should be safe to rerun if the output normalization is deterministic and the smoke test does not leave disposable artifacts.

## Artifacts and Notes

Expected artifacts:

- normalized command output implementations
- focused tests
- `bin/orchestrator-output-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `docs/codex-orchestrator-contract.md`
- `docs/codex-orchestrator-execution-loop.md`
