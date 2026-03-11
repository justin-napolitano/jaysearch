---
id: "20260311-implementation-orchestrator-runtime-codex-01-execplan"
title: "Implement the implementation-phase orchestrator runtime"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-implementation-orchestrator-runtime-codex-01-execplan.md
  - bin/implementation-orchestrator
  - src/platform_tools/implementation_orchestrator.py
  - src/platform_tools/planner_runtime.py
  - src/platform_tools/merge_readiness.py
  - src/platform_tools/game_status.py
  - tests/test_implementation_orchestrator.py
  - bin/implementation-orchestrator-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-implementation-orchestrator-runtime-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-implementation-orchestrator-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "implementation-orchestrator-smoke-test"
      command: "bin/implementation-orchestrator-smoke-test"
      expected_exit: 0
tasks:
  - title: "Implement implementation-phase task selection"
    priority: "P1"
  - title: "Implement legal move execution against the shared board"
    priority: "P1"
  - title: "Integrate merge-readiness and active-game constraints"
    priority: "P1"
  - title: "Add focused tests and smoke coverage"
    priority: "P1"
depends_on:
  - "20260311-composite-orchestrator-status-codex-01-execplan"
  - "20260311-game-graph-validator-and-status-codex-01-execplan"
---

# Purpose / Big Picture

Implement the runtime that executes implementation-phase work using the same governed board, move rules, evidence model, and merge-readiness constraints as the planner phase.

This slice is blocked on both the composite orchestrator status surface and the game-graph validator/status surface.

## Progress

- [x] Implement implementation task selection
- [x] Implement legal move execution
- [x] Integrate merge-readiness and game-state constraints
- [x] Add focused tests and smoke coverage

## Surprises & Discoveries

- implementation task selection may force refinement of active-game or merge-readiness contracts
- stop conditions may need to be stricter than the planner-phase defaults
- the remaining-work graph can lag the branch-local implementation sequence, so the runtime now derives current-slice eligibility from dependency completion instead of trusting the raw node status alone
- move validation depends on `spec/game-transitions.yaml`, so the smoke path seeds the real transition spec rather than bypassing the shared referee logic

## Decision Log

- 2026-03-11 / agent-codex-01 / Implementation orchestration must obey the same governed board and evidence model as the planner phase.
- 2026-03-11 / agent-codex-01 / The implementation runtime should expose deterministic `inspect`, `select`, and `implement` actions instead of a broad autonomous loop so each bounded move remains machine-checkable.
- 2026-03-11 / agent-codex-01 / Current-slice eligibility should be computed from remaining-work dependencies and gating class, even when the canonical backlog artifact still marks the slice as blocked.

## Outcomes & Retrospective

This slice now provides the runtime that selects implementation work, applies legal moves against planner graphs, and stops when merge-readiness or game-state constraints require it.

## Context and Orientation

This slice is blocked on both the composite orchestrator status surface and the game-graph validator/status surface because it needs both queue awareness and active-game awareness.

## Plan of Work

1. Implement the implementation-phase orchestrator runtime.
2. Integrate active-game and merge-readiness constraints.
3. Add focused tests.
4. Add a smoke path for the runtime.

## Concrete Steps

1. Add `src/platform_tools/implementation_orchestrator.py`.
2. Add `bin/implementation-orchestrator`.
3. Reuse the existing planner runtime and merge-readiness logic.
4. Add tests and `bin/implementation-orchestrator-smoke-test`.
5. Run:
   - `bin/execplan-validate .agent/execplans/20260311-implementation-orchestrator-runtime-codex-01-execplan.md`
   - `bin/implementation-orchestrator-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- the implementation orchestrator obeys active game and merge-readiness constraints
- legal moves and stop conditions are deterministic
- the smoke script passes

## Idempotence and Recovery

This slice should be safe to rerun if task selection and move execution remain deterministic and the smoke path does not leave disposable artifacts.

## Artifacts and Notes

Expected artifacts:

- `bin/implementation-orchestrator`
- `src/platform_tools/implementation_orchestrator.py`
- focused tests
- `bin/implementation-orchestrator-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `bin/orchestrator-status`
- `bin/game-status`
- `bin/merge-readiness-check`
