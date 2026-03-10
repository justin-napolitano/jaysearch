---
id: "20260310-planner-scoring-engine-codex-01-execplan"
title: "Implement planner and implementation scoring engine"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-planner-scoring-engine-codex-01-execplan.md
  - bin/planner-score
  - bin/planner-score-smoke-test
  - pyproject.toml
  - src/platform_tools/planner_score.py
  - tests/test_planner_score.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-planner-scoring-engine-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-planner-scoring-engine-codex-01-execplan.md"
      expected_exit: 0
    - name: "planner-score-pytest"
      command: "uv run pytest tests/test_planner_score.py"
      expected_exit: 0
    - name: "planner-score-smoke-test"
      command: "bin/planner-score-smoke-test"
      expected_exit: 0

tasks:
  - title: "Implement scoring engine for planner and implementation phases"
    priority: "P1"
  - title: "Expose deterministic planner score command"
    priority: "P1"
  - title: "Add focused tests for scoring calculations"
    priority: "P1"
  - title: "Add one-command smoke test for merge readiness"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
  - "20260310-citation-inference-validator-codex-01-execplan"
---

# Purpose / Big Picture

Implement the planner scoring engine defined by `spec/scoring.yaml` so planner and implementation game state can be scored deterministically from canonical graph artifacts. This slice adds a standalone score command and a smoke-test script suitable for merge gating.

## Progress

- [ ] Implement score engine
- [ ] Add planner score CLI
- [ ] Add tests
- [ ] Add smoke test
- [ ] Run validation

## Surprises & Discoveries

- Scoring must remain heuristic and source-informed rather than pretending to be ground truth.
- The runtime currently exposes graph state more directly than higher-order execution evidence, so some scores are necessarily graph-derived proxies in this slice.

## Decision Log

- 2026-03-10 / agent-codex-01 / Scoring will be implemented as a standalone command rather than folded into `bin/planner` in this slice.
- 2026-03-10 / agent-codex-01 / Scores will remain explicit policy calculations over canonical graph state.

## Outcomes & Retrospective

Expected outcomes:

- working score engine for planner and implementation phases
- deterministic JSON score reports
- focused tests and smoke test

## Context and Orientation

The design package already defines the scoring rationale and formulas in `spec/scoring.yaml`. This slice turns those scoring definitions into an executable tool.

## Plan of Work

1. Implement score calculations for planner and implementation phases from graph state.
2. Expose the score engine via a dedicated command.
3. Add focused tests and a smoke test.
4. Validate and prepare for review.

## Concrete Steps

1. Add `src/platform_tools/planner_score.py`.
2. Add `bin/planner-score`.
3. Add `bin/planner-score-smoke-test`.
4. Register the score command in `pyproject.toml`.
5. Add focused tests in `tests/test_planner_score.py`.
6. Run `bin/execplan-validate`, `bin/planner-score-smoke-test`, and `uv run pytest tests/test_planner_score.py`.

## Validation and Acceptance

Acceptance criteria:

- score command emits deterministic JSON
- planner and implementation score sections are both present
- scores remain bounded and explainable
- smoke test passes
- focused tests pass

## Idempotence and Recovery

- scoring is read-only
- same graph input should produce the same score output
- smoke test should be safe to rerun

## Artifacts and Notes

- `src/platform_tools/planner_score.py`
- `tests/test_planner_score.py`
- `bin/planner-score`
- `bin/planner-score-smoke-test`

## Interfaces and Dependencies

- `spec/scoring.yaml`
- `spec/task-graph.schema.yaml`
- `spec/game-transitions.yaml`
- `artifacts/planner/research/bibliography-graph.json`
