---
id: 20261022-health-check-nonlaunch-codex-01-execplan
title: Keep public API health checks from launching workers
owner: agent/codex-01
created: 2026-10-22T15:35:00Z
status: draft
base_branch: main
initiative_branch: initiative/unified-brand-20261022
initiative_node_id: initiative-unified-brand-20261022
approve_policy: codeowners
reviewers: [github:justin-napolitano]
changes:
  - src/platform_tools/public_orchestration_api_check.py
  - tests/test_public_orchestration_api_check.py
---

## Outcomes & Retrospective

Narrow prerequisite bug fix authorized by rollout coordinator. No auth, policy, worker-launch implementation, or schema changes.

## Context and Orientation

Health checking calls start-next-worker with push_mode=staging; a ready contract starts coordinator bootstrap, which repeats the health checker indefinitely. The same checker already exercises run-worker-contract's nonlaunch path using push_mode=github without a remote: the existing required-remote guard blocks before coordinator launch.

## Plan of Work

Use that same existing fail-closed nonlaunch path for start-next-worker in the health checker. Retain all response/schema validations. Add regression using a ready contract and real start-next-worker/run-worker-contract, with a coordinator sentinel that fails if launched. Test both healthy and invalid API schema responses using existing tests, then bootstrap.

## Validation and Acceptance

Focused public/control API checker tests, bootstrap/lease output and diff check. The health checker must return promptly without worker launches, recursion, filesystem isolation, pushes or task execution. This fix validates blocked execution response contracts; functional worker execution tests remain unchanged.

## Artifacts and Notes

Recovery is a focused revert. No new dry-run interface needed; use the already validated missing-remote guard. Do not weaken bootstrap or remove a checker.
