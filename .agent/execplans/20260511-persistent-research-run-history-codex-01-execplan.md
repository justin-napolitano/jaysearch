---
id: "20260511-persistent-research-run-history-codex-01-execplan"
title: "Persist and query research improvement loop run history"
owner: "agent/codex-01"
created: "2026-05-11T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260511-persistent-research-run-history-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/get-research-run-history"
  - "docs/commands.md"
  - "docs/public-orchestration-api.md"
  - "docs/queued-execplans.md"
  - "spec/public-orchestration-api.schema.yaml"
  - "src/platform_tools/get_research_run_history.py"
  - "src/platform_tools/run_research_improvement_loop.py"
  - "tests/test_get_research_run_history.py"
  - "tests/test_run_research_improvement_loop.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-068"
  queue_position: 68
  implementation_branch: "impl-execplan/20260511-persistent-research-run-history-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "research-runtime"
    - "capability-contracts"
  expected_artifacts:
    - ".agent/execplans/20260511-persistent-research-run-history-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/get-research-run-history"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/get_research_run_history.py"
    - "src/platform_tools/run_research_improvement_loop.py"
    - "tests/test_get_research_run_history.py"
    - "tests/test_run_research_improvement_loop.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260511-persistent-research-run-history-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260511-persistent-research-run-history-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_get_research_run_history.py tests/test_run_research_improvement_loop.py"
      expected_exit: 0
tasks:
  - title: "Persist canonical run-history records for completed research improvement loops"
    priority: "P1"
  - title: "Add a query command over the research loop history ledger"
    priority: "P1"
  - title: "Expose history paths through the public orchestration contract"
    priority: "P1"
depends_on:
  - "20260507-external-handoff-and-loop-runner-codex-01-execplan"
  - "20260511-supervised-loop-smoke-run-codex-01-execplan"
---

## Outcomes & Retrospective

Completed research loops should leave canonical, queryable history inside the platform repo rather than only per-run output trees or temporary smoke-test directories.

## Context and Orientation

The loop runner already produces reviewable per-run artifacts, but they are tied to the selected output root. This slice adds a durable control-plane ledger and a read-side query command so the platform can reason over prior runs.

## Plan of Work

Persist a compact run summary into canonical governance artifacts on each successful loop execution, add a query façade over that ledger, and extend the public orchestration contract accordingly.

## Validation and Acceptance

This slice is accepted when successful loop runs write canonical history artifacts, the query command returns filtered history records, and the updated public orchestration contract plus focused tests pass.

## Artifacts and Notes

This slice intentionally records successful loop summaries only. It does not attempt to become a full event-sourcing runtime for every intermediate step or failed draft.
