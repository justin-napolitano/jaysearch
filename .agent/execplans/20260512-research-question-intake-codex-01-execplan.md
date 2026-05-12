---
id: "20260512-research-question-intake-codex-01-execplan"
title: "Add governed research question intake and backlog commands"
owner: "agent/codex-01"
created: "2026-05-12T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260512-research-question-intake-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/get-research-question-backlog"
  - "bin/intake-research-question"
  - "bin/materialize-research-request-from-question"
  - "docs/commands.md"
  - "docs/public-orchestration-api.md"
  - "docs/queued-execplans.md"
  - "spec/public-orchestration-api.schema.yaml"
  - "src/platform_tools/get_research_question_backlog.py"
  - "src/platform_tools/intake_research_question.py"
  - "src/platform_tools/materialize_research_request_from_question.py"
  - "src/platform_tools/research_questions.py"
  - "src/platform_tools/run_research_improvement_loop.py"
  - "tests/test_research_question_intake.py"
  - "tests/test_run_research_improvement_loop.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-071"
  queue_position: 71
  implementation_branch: "impl-execplan/20260512-research-question-intake-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "research-runtime"
    - "capability-contracts"
  expected_artifacts:
    - ".agent/execplans/20260512-research-question-intake-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/get-research-question-backlog"
    - "bin/intake-research-question"
    - "bin/materialize-research-request-from-question"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/get_research_question_backlog.py"
    - "src/platform_tools/intake_research_question.py"
    - "src/platform_tools/materialize_research_request_from_question.py"
    - "src/platform_tools/research_questions.py"
    - "src/platform_tools/run_research_improvement_loop.py"
    - "tests/test_research_question_intake.py"
    - "tests/test_run_research_improvement_loop.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260512-research-question-intake-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260512-research-question-intake-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_research_question_intake.py tests/test_run_research_improvement_loop.py"
      expected_exit: 0
tasks:
  - title: "Add canonical research question artifact intake and append-only backlog ledger"
    priority: "P1"
  - title: "Add a query command over the research question backlog"
    priority: "P1"
  - title: "Materialize bounded researcher requests from canonical question artifacts"
    priority: "P1"
  - title: "Allow the supervised loop to start from question artifacts"
    priority: "P1"
depends_on:
  - "20260511-persistent-research-run-history-codex-01-execplan"
  - "20260512-candidate-conflict-detection-codex-01-execplan"
---

## Outcomes & Retrospective

The supervised loop should start from governed durable research questions instead of requiring hand-authored request JSON as the first operator step.

## Context and Orientation

The platform already persists run history and can promote ranked candidates, but it still lacks a durable intake surface for the questions that seed those runs. This slice adds a canonical question artifact, a backlog ledger, a query command, and a bridge from governed question artifacts into bounded `researcher-harness` requests.

## Plan of Work

Add durable question storage and backlog querying, add request materialization from canonical question artifacts, and extend the loop runner so it can start from `--question-path` without a manually prepared request file.

## Validation and Acceptance

This slice is accepted when a bounded question artifact can be ingested, queried, converted into a valid researcher request, and used as the starting point for the supervised research loop under focused tests.

## Artifacts and Notes

This slice intentionally keeps question state append-only and query-oriented. It does not yet add question lifecycle mutation commands beyond intake.
