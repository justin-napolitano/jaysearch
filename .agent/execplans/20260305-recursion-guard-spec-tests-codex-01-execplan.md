---
id: 20260305-recursion-guard-spec-tests-codex-01-execplan
title: Prevent recursive execution between spec-test runner and local CI
owner: agent/codex-01
created: '2026-03-05T00:00:00Z'
status: approved
base_branch: main
changes:
- .agent/execplans/20260305-recursion-guard-spec-tests-codex-01-execplan.md
- src/platform_tools/spec_test_runner.py
- bin/run-local-ci
approve_policy: codeowners
reviewers:
- github:jay.napolitano
draft_by: agent/codex-01
draft_branch: draft-execplan/recursion-guard-spec-tests-codex-01-20260305
draft_created: '2026-03-05T00:00:00Z'
finalized_by: github:jay.napolitano
finalized_at: '2026-03-05T17:20:00Z'
finalized_in_pr: '21'
validation:
  tests:
  - name: execplan_validate
    command: bin/execplan-validate .agent/execplans/*.md
    expected_exit: 0
  - name: execplan_spec_tests
    command: bin/execplan-test
    expected_exit: 0
  - name: run_local_ci
    command: bin/run-local-ci
    expected_exit: 0
tasks:
- title: Add recursion guard for run-local-ci in spec_test_runner
  priority: P1
- title: Preserve deterministic pass/fail/skip semantics
  priority: P1
- title: Validate no timeout loops in execplan-test and run-local-ci
  priority: P1
depends_on:
- 20260305-platform-hostile-review-sweep-codex-01-execplan
---

# Purpose / Big Picture

Fix the blocking recursion path where `bin/execplan-test` and `bin/run-local-ci` can invoke each other indefinitely through ExecPlan-declared tests.

After completion, both commands must terminate deterministically with stable machine-readable output.

## Progress

- [ ] Create ExecPlan draft
- [ ] Implement recursion guard in spec test runner
- [ ] Validate deterministic behavior
- [ ] Human finalize via SSH-signed commit

## Surprises & Discoveries

None yet.

## Decision Log

Decision: recursion prevention should be handled in the test runner at command-dispatch time.

Rationale: this centralizes loop prevention across all plan-declared tests.

Date/Author: 2026-03-05 / agent/codex-01

## Outcomes & Retrospective

(To be completed after finalization.)

## Context and Orientation

A hostile review found that `run-local-ci` runs `execplan-test`, while some ExecPlans include `run-local-ci` as a validation test. This causes reentrant execution and command timeouts.

## Plan of Work

1. Extend recursion guard logic in `spec_test_runner`.
2. Mark reentrant `run-local-ci`/`execplan-test` invocations as `SKIP` under nested execution context.
3. Validate command termination and stable outputs.

## Concrete Steps

1. Update `src/platform_tools/spec_test_runner.py` and `bin/run-local-ci` recursion checks.
2. Run:
   - `bin/execplan-validate .agent/execplans/*.md`
   - `bin/execplan-test`
   - `bin/run-local-ci`
3. Confirm no timeout behavior and deterministic output structure.

## Validation and Acceptance

Plan is accepted when:

- `bin/execplan-test` exits `0` on compliant branch;
- `bin/run-local-ci` exits `0` on compliant branch;
- no recursive timeout behavior occurs;
- skip behavior for protected recursive commands is deterministic.

## Idempotence and Recovery

The fix is deterministic and safe to rerun. If loop behavior remains, extend recursion guards and rerun validation commands.

## Artifacts and Notes

Expected artifacts:

- command outputs from `bin/execplan-test`
- command outputs from `bin/run-local-ci`

## Interfaces and Dependencies

Interfaces:

- `src/platform_tools/spec_test_runner.py`
- `bin/execplan-test`
- `bin/run-local-ci`

Dependencies:

- `20260305-platform-hostile-review-sweep-codex-01-execplan`
