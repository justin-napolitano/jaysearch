---
id: "20260319-local-git-hook-automation-codex-01-execplan"
title: "Automate deterministic local runtime updates through versioned git hooks"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260319-local-git-hook-automation-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/codex-orchestrator-contract.md
  - docs/commands.md
  - .githooks/post-merge
  - .githooks/post-checkout
  - .githooks/pre-push
  - bin/auto-reconcile-main
  - bin/install-local-git-hooks
  - bin/run-governed-pre-push-checks
  - pyproject.toml
  - spec/agent-capability-policy.yaml
  - spec/protected-surfaces.schema.yaml
  - spec/workflow.yaml
  - src/platform_tools/auto_reconcile_main.py
  - src/platform_tools/install_local_git_hooks.py
  - src/platform_tools/reconcile_remaining_work_merge.py
  - src/platform_tools/run_governed_pre_push_checks.py
  - tests/test_auto_reconcile_main.py
  - tests/test_install_local_git_hooks.py
  - tests/test_reconcile_pending_merge_completions.py
  - tests/test_reconcile_remaining_work_merge.py
  - tests/test_run_governed_pre_push_checks.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-git-hook-automation"
initiative_node_id: "initiative-local-git-hook-automation"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-local-git-hook-automation-codex-01-20260319"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260319-local-git-hook-automation-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260319-local-git-hook-automation-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Version local git-hook entrypoints in-repo instead of relying on manual command chains"
    priority: "P1"
  - title: "Automatically run deterministic reconciliation after merges and branch switches to canonical integration branches"
    priority: "P1"
  - title: "Automatically run safe governed checks before push on governed branches"
    priority: "P1"
depends_on:
  - "20260319-post-merge-graph-reconciliation-automation-codex-01-execplan"
---

# Purpose / Big Picture

Reduce routine manual runtime maintenance by wiring deterministic local automation into versioned git hooks that call repo-owned commands instead of bespoke developer shell habits.

## Progress

- [ ] define which local hooks may mutate canonical state versus only validate
- [ ] add a repeatable hook installer that makes the local setup explicit
- [ ] automate post-merge and branch-switch reconciliation for canonical branches
- [ ] automate governed pre-push checks for governed branches

## Surprises & Discoveries

- git hooks are local-only by default, so the repo needs versioned hook bodies plus an installer rather than assuming contributors hand-wire them correctly
- hooks should fail safely and visibly; they must not become hidden authority or silently write ambiguous state

## Decision Log

- keep hook logic versioned in the repo under `.githooks/` and invoke repo-owned scripts from there
- prefer post-merge and post-checkout for deterministic local reconciliation, and pre-push for safe validation
- avoid commit-time mutation hooks that could surprise operators or rewrite staged content

## Outcomes & Retrospective

- expected outcome: routine local merges, pulls, and pushes automatically trigger the deterministic commands that currently require manual invocation
- expected retrospective question: whether some of these hooks should later be optional profiles by repo role

## Context and Orientation

- GitHub Actions are not available in the target environment, so local git hooks are the practical automation surface
- canonical authority remains local repo artifacts and referees; hooks only invoke versioned deterministic commands
- the main target is to eliminate repetitive manual reconciliation and pre-push validation runs

## Plan of Work

1. define a versioned local-hook model in workflow/runtime docs
2. add repo-owned scripts for post-merge reconciliation and governed pre-push checks
3. install versioned hooks through one deterministic installer
4. document which hooks mutate state and which are validation-only

## Concrete Steps

1. add `.githooks/` entrypoints for `post-merge`, `post-checkout`, and `pre-push`
2. add `bin/install-local-git-hooks` to configure `core.hooksPath`
3. add `bin/auto-reconcile-main` and related wrappers that safely no-op outside eligible branches
4. update workflow/orchestrator docs so the local automation contract is explicit and machine-readable

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260319-local-git-hook-automation-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- hook installer should produce a reproducible local hooks setup that runs only repo-owned scripts

## Idempotence and Recovery

- repeated hook invocations must be no-ops when no governed state transition is pending
- hooks must fail with clear output and non-destructive behavior when branch mapping or canonical state is ambiguous

## Artifacts and Notes

- local automation should cover the highest-friction manual steps first:
  - post-merge reconciliation on canonical branches
  - branch-switch reconciliation to `main` and initiative branches
  - pre-push governed checks on draft, implementation, and initiative branches

## Interfaces and Dependencies

- depends on `rwg-030` because hooks should call the deterministic post-merge reconciliation runtime instead of re-implementing its logic
- likely touches workflow policy, orchestrator docs, and new hook entrypoint scripts
