---
id: "20260310-planner-move-engine-and-contract-reconciliation-codex-01-execplan"
title: "Implement planner move execution and contract reconciliation runtime"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-planner-move-engine-and-contract-reconciliation-codex-01-execplan.md
  - bin/planner
  - src/platform_tools/planner_cli.py
  - src/platform_tools/planner_runtime.py
  - tests/test_planner_cli.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-planner-move-engine-and-contract-reconciliation-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-planner-move-engine-and-contract-reconciliation-codex-01-execplan.md"
      expected_exit: 0
    - name: "planner-pytest"
      command: "uv run pytest tests/test_planner_cli.py"
      expected_exit: 0

tasks:
  - title: "Implement planner move application against transition rules"
    priority: "P1"
  - title: "Implement illegal transition rejection and evidence enforcement"
    priority: "P1"
  - title: "Implement contract draft generation from canonical graph state"
    priority: "P1"
  - title: "Implement contract import reconciliation runtime"
    priority: "P1"
  - title: "Expand graph views for ready, blocked, review, validated, and recovery states"
    priority: "P1"
  - title: "Add focused tests for move legality and contract reconciliation"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
  - "20260310-planner-runtime-foundation-codex-01-execplan"
---

# Purpose / Big Picture

Implement the first real move engine for the planner game so canonical graph state can change through legal, evidence-backed moves instead of only static graph generation. This slice also introduces contract drafting from canonical graph state and explicit contract import reconciliation so the planner-to-contract loop becomes executable rather than purely specified.

This plan does not implement provider sync, scoring execution, or full multi-role orchestration. It focuses on making the planner game operational: legal moves, referee-aware validation, contract projection, and explicit reconciliation.

## Progress

- [ ] Add move application runtime
- [ ] Add move validation and illegal-transition rejection
- [ ] Add richer graph state views
- [ ] Add contract draft generation
- [ ] Add contract import reconciliation
- [ ] Add focused tests
- [ ] Run targeted validation

## Surprises & Discoveries

- Some move semantics may force refinement of graph-node evidence requirements.
- Contract drafting may reveal missing canonical fields that were acceptable in the foundation slice but are insufficient for projection.
- Reconciliation may surface authority edge cases that need stronger operator/referee boundaries.

## Decision Log

- 2026-03-10 / agent-codex-01 / Move application will be rejected unless the transition is legal under `spec/game-transitions.yaml`.
- 2026-03-10 / agent-codex-01 / Contract drafting will refuse to run when readiness conditions are not met.
- 2026-03-10 / agent-codex-01 / Contract import will remain explicit reconciliation only and will not introduce markdown authority.

## Outcomes & Retrospective

Expected outcomes:

- working planner move application path
- legal transition enforcement with evidence requirements
- stronger graph views aligned with the game states
- working draft ExecPlan projection from canonical graph state
- working reconciliation report generation for contract import
- focused tests proving illegal transitions are rejected and legal ones succeed

## Context and Orientation

The prior implementation slice created session persistence, graph persistence, graph validation, research provenance validation, and the initial `bin/planner` shell. The design package already defines the game model, transition rules, contract import schema, and projection rules. This plan makes those design contracts executable.

Primary governing inputs:

- `spec/game-transitions.yaml`
- `spec/task-graph.schema.yaml`
- `spec/planner-contract-import.yaml`
- `docs/planner-execplan-projection.md`
- `examples/execplan-template.md`

## Plan of Work

1. Implement move application on canonical graph nodes using the formal transition spec.
2. Implement move validation and evidence checks so illegal moves are rejected deterministically.
3. Expand graph inspection commands to reflect the shared board states more usefully.
4. Implement draft ExecPlan projection from canonical graph state.
5. Implement explicit import reconciliation from edited ExecPlan drafts back into canonical state.
6. Add focused tests and validate.

## Concrete Steps

1. Extend `src/platform_tools/planner_runtime.py` with move application and move validation functions.
2. Extend `src/platform_tools/planner_cli.py` with:
   - `bin/planner move apply`
   - `bin/planner move validate`
   - `bin/planner contract draft-execplan`
   - `bin/planner contract import-execplan`
3. Add graph views for:
   - `ready`
   - `blocked`
   - `in_review`
   - `validated`
   - `recovery_required`
4. Implement contract drafting using canonical graph state and the existing ExecPlan template and governance rules.
5. Implement reconciliation report generation that conforms to `spec/planner-contract-import.yaml`.
6. Add tests for:
   - legal move success
   - illegal move rejection
   - missing evidence rejection
   - contract draft success/failure
   - contract import reconciliation output
7. Run `bin/execplan-validate` and `uv run pytest tests/test_planner_cli.py`.

## Validation and Acceptance

Acceptance criteria:

- illegal transitions are rejected deterministically
- required evidence is enforced for referee-required moves
- graph state changes are persisted with provenance
- `bin/planner contract draft-execplan` produces a valid draft only when readiness conditions are met
- `bin/planner contract import-execplan` emits a reconciliation report conforming to the contract-import spec
- focused tests pass

## Idempotence and Recovery

- move validation commands should be read-only
- move application should record explicit graph updates and fail cleanly on illegal transitions
- contract drafting should be reproducible from the same canonical graph state
- reconciliation should never silently mutate canonical state without a recorded report

## Artifacts and Notes

- `src/platform_tools/planner_runtime.py`
- `src/platform_tools/planner_cli.py`
- `tests/test_planner_cli.py`
- `artifacts/planner/imports/`

## Interfaces and Dependencies

- `spec/game-transitions.yaml`
- `spec/task-graph.schema.yaml`
- `spec/planner-contract-import.yaml`
- `docs/planner-execplan-projection.md`
- `examples/execplan-template.md`
