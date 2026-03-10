---
id: "20260310-rule-graph-codex-01-execplan"
title: "Implement canonical rule graph and validator"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-rule-graph-codex-01-execplan.md
  - artifacts/planner/research/rule-graph.json
  - bin/rule-graph-check
  - bin/rule-graph-smoke-test
  - pyproject.toml
  - spec/rule-graph.schema.yaml
  - src/platform_tools/rule_graph_check.py
  - tests/test_rule_graph_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-rule-graph-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-rule-graph-codex-01-execplan.md"
      expected_exit: 0
    - name: "rule-graph-check"
      command: "bin/rule-graph-check"
      expected_exit: 0
    - name: "rule-graph-smoke-test"
      command: "bin/rule-graph-smoke-test"
      expected_exit: 0
    - name: "rule-graph-pytest"
      command: "uv run pytest tests/test_rule_graph_check.py"
      expected_exit: 0

tasks:
  - title: "Define canonical rule graph schema"
    priority: "P1"
  - title: "Build machine-readable rule graph artifact"
    priority: "P1"
  - title: "Implement rule graph validator"
    priority: "P1"
  - title: "Add focused tests and smoke test"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
  - "20260310-citation-inference-validator-codex-01-execplan"
---

# Purpose / Big Picture

Implement a canonical rule graph that makes repository rules machine-readable in the same way the task graph and bibliography graph already do for planning and research provenance. The rule graph should capture rule nodes, the artifacts they apply to, the validators that enforce them, and the merge/readiness conditions they block or require.

This slice exists to eliminate prose-only governance as the last weak link in the platform.

## Progress

- [ ] Add rule graph schema
- [ ] Add initial rule graph artifact
- [ ] Implement rule graph validator
- [ ] Add smoke test and focused tests
- [ ] Run validation

## Surprises & Discoveries

- Rules currently live across docs and spec layers, so the validator must check structural coverage rather than pretend one file is the only source.
- The initial graph should prefer explicit coverage over exhaustive semantic modeling.

## Decision Log

- 2026-03-10 / agent-codex-01 / The rule graph will supplement docs/specs rather than replace them.
- 2026-03-10 / agent-codex-01 / The validator will enforce coverage and linkage, not full natural-language equivalence.

## Outcomes & Retrospective

Expected outcomes:

- canonical rule graph schema
- canonical rule graph artifact
- deterministic rule graph validator
- smoke test and focused tests

## Context and Orientation

The repository already has task graphs, bibliography graphs, and claim registries. Governance rules still span docs and specs without a canonical graph representation. This plan corrects that gap.

## Plan of Work

1. Define the rule graph schema.
2. Encode the current major rules into a canonical graph artifact.
3. Implement a validator that checks graph integrity and artifact coverage.
4. Add smoke/test coverage and validate.

## Concrete Steps

1. Add `spec/rule-graph.schema.yaml`.
2. Add `artifacts/planner/research/rule-graph.json`.
3. Implement `src/platform_tools/rule_graph_check.py`.
4. Add `bin/rule-graph-check`.
5. Add `bin/rule-graph-smoke-test`.
6. Add focused tests in `tests/test_rule_graph_check.py`.
7. Run `bin/execplan-validate`, `bin/rule-graph-check`, `bin/rule-graph-smoke-test`, and `uv run pytest tests/test_rule_graph_check.py`.

## Validation and Acceptance

Acceptance criteria:

- rule graph validator passes on the in-repo rule graph
- validator fails on structurally incomplete rule graphs
- graph includes major merge/readiness rules, validator mappings, and governed artifact coverage
- smoke test passes
- focused tests pass

## Idempotence and Recovery

- validator is read-only
- rule graph edits should be deterministic and reviewable
- the smoke test should be rerunnable without mutating the canonical graph

## Artifacts and Notes

- `artifacts/planner/research/rule-graph.json`
- `spec/rule-graph.schema.yaml`
- `src/platform_tools/rule_graph_check.py`
- `tests/test_rule_graph_check.py`

## Interfaces and Dependencies

- `docs/agent-game-rules-v1.md`
- `docs/governance.md`
- `spec/governance.yaml`
- `spec/ruleset.yaml`
- `spec/workflow.yaml`
