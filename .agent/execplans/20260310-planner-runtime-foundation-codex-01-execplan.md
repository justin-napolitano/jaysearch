---
id: "20260310-planner-runtime-foundation-codex-01-execplan"
title: "Implement the planner runtime foundation"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-planner-runtime-foundation-codex-01-execplan.md
  - artifacts/planner/research/bibliography-graph.json
  - bin/planner
  - pyproject.toml
  - src/platform_tools/planner_cli.py
  - src/platform_tools/planner_runtime.py
  - tests/test_planner_cli.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-planner-control-plane-design-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-planner-runtime-foundation-codex-01-execplan.md"
      expected_exit: 0
    - name: "planner-pytest"
      command: "uv run pytest tests/test_planner_cli.py"
      expected_exit: 0

tasks:
  - title: "Implement planner session persistence primitives"
    priority: "P1"
  - title: "Implement graph build and validation primitives"
    priority: "P1"
  - title: "Implement citation and bibliography validation primitives"
    priority: "P1"
  - title: "Implement initial bin/planner command surface"
    priority: "P1"
  - title: "Add focused tests for the first planner runtime slice"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
---

# Purpose / Big Picture

Implement the first working runtime slice for the planner control plane. This slice establishes local session persistence, canonical graph persistence, graph validation, transition-aware status validation, and citation/bibliography validation. It also introduces the initial `bin/planner` command surface needed to exercise those primitives from the terminal.

This plan does not implement provider sync, scoring execution, or the full interactive planner experience. It provides the minimum governed runtime required to make the design package executable rather than aspirational.

## Progress

- [ ] Add planner runtime module for session and graph persistence
- [ ] Add planner CLI module and `bin/planner` wrapper
- [ ] Add citation and bibliography validation checks
- [ ] Add focused tests
- [ ] Run targeted validation

## Surprises & Discoveries

- Existing repo tooling uses thin shell wrappers and Python modules rather than richer CLI frameworks.
- The implementation slice should stay smaller than the full design package or it will degenerate into scope fraud.

## Decision Log

- 2026-03-10 / agent-codex-01 / First implementation slice excludes provider sync and scoring execution.
- 2026-03-10 / agent-codex-01 / Citation and bibliography validation is included in the initial runtime slice.

## Outcomes & Retrospective

Expected outcomes:

- working `bin/planner` entrypoint
- working session artifact creation
- working graph build and validation
- working bibliography/citation validation
- focused tests that prove the first runtime slice actually works

## Context and Orientation

The design package already defines the planner CLI, game model, graph schema, move transitions, scoring rationale, citation rules, and bibliography graph. This plan implements only the foundational runtime needed to make those contracts executable in a terminal-first workflow.

## Plan of Work

1. Implement local session persistence and artifact creation.
2. Implement graph construction and validation against the current design specs.
3. Implement citation and bibliography validation against the research artifacts.
4. Expose those capabilities via `bin/planner`.
5. Add focused tests and validate.

## Concrete Steps

1. Add `src/platform_tools/planner_runtime.py` with session, graph, and validation functions.
2. Add `src/platform_tools/planner_cli.py` with the initial command surface.
3. Add `bin/planner` as a thin wrapper to the Python module.
4. Register the planner command in `pyproject.toml`.
5. Add focused tests in `tests/test_planner_cli.py`.
6. Run `bin/execplan-validate` and `pytest tests/test_planner_cli.py`.

## Validation and Acceptance

Acceptance criteria:

- `bin/planner session start` creates the required local artifacts.
- `bin/planner graph build` creates a canonical graph artifact.
- `bin/planner graph validate` rejects malformed graphs and accepts valid ones.
- planner validation checks bibliography graph and research documents.
- focused tests pass.

## Idempotence and Recovery

- rerunning session start with the same generated session id should not happen in normal flow; session ids must remain unique
- graph build should be safe to rerun for the same session and should overwrite the derived graph artifact deterministically
- validation commands should be read-only

## Artifacts and Notes

- `artifacts/planner/sessions/`
- `artifacts/planner/graphs/`
- `src/platform_tools/planner_runtime.py`
- `src/platform_tools/planner_cli.py`
- `tests/test_planner_cli.py`

## Interfaces and Dependencies

- `spec/planner-session.yaml`
- `spec/task-graph.schema.yaml`
- `spec/game-transitions.yaml`
- `spec/bibliography-graph.schema.yaml`
- `docs/references.md`
- `docs/research-assumptions.md`
