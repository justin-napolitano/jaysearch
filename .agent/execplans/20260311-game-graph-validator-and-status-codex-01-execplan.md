---
id: "20260311-game-graph-validator-and-status-codex-01-execplan"
title: "Implement game-graph validation and active-game status surfaces"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-game-graph-validator-and-status-codex-01-execplan.md
  - bin/game-graph-check
  - bin/game-status
  - src/platform_tools/game_graph_check.py
  - src/platform_tools/game_status.py
  - artifacts/planner/research/game-graph.json
  - spec/games.schema.yaml
  - tests/test_game_graph_check.py
  - tests/test_game_status.py
  - bin/game-graph-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-game-graph-validator-and-status-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-game-graph-validator-and-status-codex-01-execplan.md"
      expected_exit: 0
    - name: "game-graph-smoke-test"
      command: "bin/game-graph-smoke-test"
      expected_exit: 0
tasks:
  - title: "Implement game-graph structural validator"
    priority: "P1"
  - title: "Implement active-game status reporting"
    priority: "P1"
  - title: "Add focused tests for game-graph validation"
    priority: "P1"
  - title: "Add focused tests for game status output"
    priority: "P1"
  - title: "Add smoke coverage for game-aware orchestration surfaces"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Implement the validator and status surfaces for the nested game hierarchy so Codex can ask which game or subgame is active and whether the canonical game graph is structurally sound.

This slice should produce one validator command, one status command, focused tests, and a smoke path that proves the game-aware status layer is callable.

## Progress

- [ ] Implement game-graph validator
- [ ] Implement game-status command
- [ ] Add focused tests
- [ ] Add smoke coverage

## Surprises & Discoveries

- the game graph may need minor normalization once a real validator exists
- active-game status may need to define fallback behavior when a branch has no explicit game marker

## Decision Log

- 2026-03-11 / agent-codex-01 / The game graph should have its own validator rather than relying on JSON syntax checks alone.

## Outcomes & Retrospective

On completion, this slice should leave the nested-game hierarchy machine-checkable and expose the active game/subgame through a stable status command.

## Context and Orientation

This is the second ready slice in the queued execution backlog. It is parallel-safe against output hardening because its primary conflict domain is `game-graph`, not `planner-cli` or `orchestrator-status`.

## Plan of Work

1. Implement structural validation for the canonical game graph.
2. Implement active-game status reporting.
3. Add focused tests.
4. Add one smoke path for the new commands.

## Concrete Steps

1. Add `src/platform_tools/game_graph_check.py`.
2. Add `src/platform_tools/game_status.py`.
3. Add `bin/game-graph-check` and `bin/game-status`.
4. Add focused tests and `bin/game-graph-smoke-test`.
5. Run:
   - `bin/execplan-validate .agent/execplans/20260311-game-graph-validator-and-status-codex-01-execplan.md`
   - `bin/game-graph-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- game-graph structural validation is deterministic
- active-game status is machine-readable
- focused tests cover both commands
- the smoke script passes

## Idempotence and Recovery

This slice should be safe to rerun if the validator and status outputs are deterministic and the smoke path does not create disposable merge-blocking artifacts.

## Artifacts and Notes

Expected artifacts:

- `bin/game-graph-check`
- `bin/game-status`
- focused tests
- `bin/game-graph-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `docs/games/README.md`
- `docs/games/game-inheritance.md`
- `artifacts/planner/research/game-graph.json`
