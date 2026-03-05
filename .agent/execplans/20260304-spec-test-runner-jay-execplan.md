---
id: spec-test-runner-20260304
title: Implement ExecPlan spec test runner
owner: "github:jay.napolitano"
created: "2026-03-04T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260304-spec-test-runner-jay-execplan.md
  - tools/spec_test_runner.py
  - bin/execplan-test
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"

draft_by: "github:jay.napolitano"
draft_branch: draft-execplan/spec-test-runner-jay-20260304
draft_created: "2026-03-04T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

tasks:
  - title: Parse validation blocks from ExecPlans
    priority: P1
  - title: Execute tests with expected exit assertions
    priority: P1
  - title: Emit deterministic pass/fail summary
    priority: P1
  - title: Return non-zero on failing tests
    priority: P1
  - title: Implement execplan-test CLI
    priority: P1

validation:
  tests:
    - name: execplan_spec_tests
      command: bin/execplan-test
      expected_exit: 0

depends_on:
  - repo-health-engine-20260304
---

# Purpose / Big Picture

Run validation tests embedded in ExecPlans.

Outputs created:

- `bin/execplan-test`
- `tools/spec_test_runner.py`

## Progress

- [ ] Create ExecPlan draft
- [ ] Implement `tools/spec_test_runner.py`
- [ ] Implement `bin/execplan-test`
- [ ] Validate deterministic output and exit behavior
- [ ] Human finalize via signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: test runner reads `validation.tests` from ExecPlan frontmatter and enforces `expected_exit` deterministically.

Rationale: aligns execution directly with plan-defined acceptance tests.

Date/Author: 2026-03-04 / github:jay.napolitano

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

ExecPlans can define validation tests in frontmatter, for example:

    validation:
      tests:
        - name: lint
          command: bin/execplan-validate
          expected_exit: 0

The platform needs a runner that executes those tests consistently and reports deterministic results.

## Plan of Work

1. Implement validation block parser.
2. Execute declared commands in deterministic order.
3. Compare actual vs expected exit codes.
4. Print stable pass/fail report and exit non-zero on failure.
5. Expose via `bin/execplan-test`.

## Concrete Steps

1. Implement `tools/spec_test_runner.py` to parse `validation.tests` from ExecPlans.
2. Execute tests in deterministic order (stable plan order, stable test order).
3. Record per-test result (`PASS`/`FAIL`) and expected/actual exit codes.
4. Implement `bin/execplan-test` wrapper.
5. Run `bin/execplan-test` and verify behavior on passing and failing cases.

Expected execution behavior:

- `bin/execplan-test`

Expected output example:

    Running ExecPlan tests
    ----------------------
    execplan_lint: PASS
    repo_health: PASS

    All tests passed

## Validation and Acceptance

Plan is accepted when:

- ExecPlan validation tests run successfully through `bin/execplan-test`.
- Failing tests return non-zero exit.
- Results are printed in deterministic format.
- Identical inputs produce identical output ordering.

## Idempotence and Recovery

Runner is read-only and safe to rerun. On failure, reported failing test names and commands guide fixes; rerun requires no cleanup.

## Artifacts and Notes

- Test run summaries
- Optional machine-readable test report artifact if implemented

## Interfaces and Dependencies

Interfaces:

- `tools/spec_test_runner.py`
- `bin/execplan-test`

Dependencies:

- ExecPlan files with `validation.tests`
- `repo-health-engine-20260304`
