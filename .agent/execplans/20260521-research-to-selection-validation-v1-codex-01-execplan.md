---
id: "20260521-research-to-selection-validation-v1-codex-01"
title: "Research To Selection Validation V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/research-to-selection-validation-v1.md
  - artifacts/planner/research/research-to-selection-validation-v1-dag.json
  - src/platform_tools/validate_research_to_selection_flow.py
  - tests/test_validate_research_to_selection_flow.py
  - bin/validate-research-to-selection-flow
  - pyproject.toml
  - .agent/execplans/20260521-research-to-selection-validation-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/research-to-selection-validation-v1"
initiative_node_id: "initiative-research-to-selection-validation-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "validation-runner"
      command: "uv run pytest tests/test_validate_research_to_selection_flow.py"
      expected_exit: 0
    - name: "research-runtime-regression"
      command: "uv run pytest tests/test_materialize_research_hypotheses.py tests/test_materialize_research_candidate_tree.py tests/test_materialize_research_evaluations.py tests/test_materialize_research_recommendation.py tests/test_materialize_selected_solution_scope.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define bounded validation scope"
    priority: "P0"
  - title: "Create validation DAG"
    priority: "P0"
  - title: "Implement research-to-selection validation runner"
    priority: "P0"
  - title: "Add positive and blocking tests"
    priority: "P0"
  - title: "Run validator against canonical seed packets"
    priority: "P1"

depends_on:
  - "20260521-recommendation-selection-gate-v1-codex-01"
---

## Outcomes & Retrospective

This slice creates a full-chain validation runner for the currently implemented research-to-selection path.

## Research Basis

The validator is backed by CRITIC, SWE-bench, W3C PROV, and Self-Refine as summarized in `docs/current-research-bibliography.md`.

## Plan of Work

Phase 1 defines the validation boundary. Phase 2 implements the runner. Phase 3 runs it against canonical seed packets and records what remains unvalidated before planner/code scopes.

## Validation and Acceptance

Acceptance means the runner emits a validation report with packet refs, step reports, blockers, and explicit not-yet-validated planner/code scopes.
