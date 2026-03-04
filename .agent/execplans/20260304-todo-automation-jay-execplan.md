---
id: todo-automation-20260304
title: Implement automatic TODO generation from ExecPlans
owner: "github:jay.napolitano"
created: "2026-03-04T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260304-todo-automation-jay-execplan.md
  - tools/generate_todos.py
  - bin/sync-todos
  - TODO.md
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "github:jay.napolitano"
draft_branch: draft-execplan/todo-automation-jay-20260304
draft_created: "2026-03-04T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

tasks:
  - title: Parse ExecPlan tasks
    priority: P1
  - title: Generate deterministic TODO entries
    priority: P1
  - title: Prevent duplicate TODO entries
    priority: P1
  - title: Link TODO entries to ExecPlan IDs
    priority: P1
  - title: Implement CLI wrappers
    priority: P1

validation:
  tests:
    - name: sync_todos
      command: bin/sync-todos
      expected_exit: 0

depends_on:
  - platform-validator-20260304
---

# Purpose / Big Picture

Implement automatic TODO generation from ExecPlans.

Outputs created by this plan:

- `tools/generate_todos.py`
- `bin/sync-todos`

## Progress

- [ ] Create ExecPlan draft
- [ ] Implement `tools/generate_todos.py`
- [ ] Implement `bin/sync-todos`
- [ ] Validate deterministic TODO generation
- [ ] Human finalize via signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: TODO generation must be deterministic and idempotent.

Rationale: repeated runs must not churn `TODO.md` or create duplicates.

Date/Author: 2026-03-04 / github:jay.napolitano

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

This repository tracks work through ExecPlans and `TODO.md`. Tasks may be declared in ExecPlan frontmatter under `tasks`. This plan adds tooling to transform those tasks into normalized TODO entries with stable linking to ExecPlan IDs.

## Plan of Work

1. Parse ExecPlan files under `.agent/execplans/`.
2. Extract tasks and normalize fields.
3. Generate deterministic TODO entries in `TODO.md`.
4. Suppress duplicates by stable key (plan id + task title).
5. Provide operator CLIs (`uv run generate-todos`, `bin/sync-todos`).

## Concrete Steps

1. Implement `tools/generate_todos.py` parser and renderer.
2. Update or create TODO sections in `TODO.md` without duplicates.
3. Implement `bin/sync-todos` wrapper invoking the generator.
4. Run:
   - `uv run generate-todos`
   - `bin/sync-todos`
5. Verify output is stable across consecutive runs with no input changes.

Expected command behavior:

- `uv run generate-todos`
- `bin/sync-todos`

Expected output example:

- `Generated 3 TODO items`
- `Linked to platform-validator-20260304`

## Validation and Acceptance

Plan is accepted when:

- `TODO.md` is populated from ExecPlan tasks.
- `bin/sync-todos` produces deterministic results for identical inputs.
- Duplicate tasks are not created across repeated runs.
- TODO entries include source ExecPlan IDs.

## Idempotence and Recovery

Running the generator multiple times with unchanged ExecPlans must produce the same `TODO.md`. If malformed plan data is detected, tool exits non-zero and reports machine-readable errors.

## Artifacts and Notes

- `TODO.md` updates
- Generator logs from `uv run generate-todos`
- Sync logs from `bin/sync-todos`

## Interfaces and Dependencies

Interfaces:

- `tools/generate_todos.py`
- `bin/sync-todos`
- `TODO.md`

Dependencies:

- `.agent/PLANS.md`
- existing ExecPlan files under `.agent/execplans/`
- `platform-validator-20260304`
