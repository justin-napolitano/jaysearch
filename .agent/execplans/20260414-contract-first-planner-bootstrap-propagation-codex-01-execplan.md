---
id: "20260414-contract-first-planner-bootstrap-propagation-codex-01-execplan"
title: "Propagate contract-first planning through planner and bootstrap surfaces"
owner: "agent/codex-01"
created: "2026-04-14T15:54:17Z"
status: draft
base_branch: "initiative/contract-first-planning"
initiative_branch: "initiative/contract-first-planning"
initiative_node_id: "initiative-contract-first-planning"
changes:
  - .agent/execplans/20260414-contract-first-planner-bootstrap-propagation-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - src/platform_tools/planner_cli.py
  - src/platform_tools/bootstrap_managed_repo.py
  - docs/planner-cli-contract.md
  - docs/prompts.md
  - spec/workflow.yaml
  - bin/planner-smoke-test
  - tests/test_planner_cli.py
  - tests/test_bootstrap_managed_repo.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-056"
  queue_position: 56
  implementation_branch: "impl-execplan/contract-first-planner-bootstrap-propagation"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "workflow"
    - "planner-runtime"
    - "bootstrap"
  expected_artifacts:
    - ".agent/execplans/20260414-contract-first-planner-bootstrap-propagation-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "src/platform_tools/planner_cli.py"
    - "src/platform_tools/bootstrap_managed_repo.py"
    - "docs/planner-cli-contract.md"
    - "tests/test_planner_cli.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260414-contract-first-planner-bootstrap-propagation-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260414-contract-first-planner-bootstrap-propagation-codex-01-execplan.md"
      expected_exit: 0
    - name: "planner-bootstrap"
      command: "uv run pytest tests/test_planner_cli.py tests/test_bootstrap_managed_repo.py"
      expected_exit: 0
tasks:
  - title: "Propagate contract-first planner command naming"
    priority: "P1"
  - title: "Update bootstrapped workflow guidance and smoke tests"
    priority: "P1"
depends_on:
  - "20260413-contract-first-execplan-runtime-codex-01-execplan"
  - "20260414-contract-first-execplan-consumer-cleanup-codex-01-execplan"
---

## Outcomes & Retrospective

Planner and bootstrap surfaces should default to the contract-first planning model without teaching draft-first command names or examples.

## Context and Orientation

The remaining confusion is concentrated in planner CLI naming, managed-repo bootstrap guidance, and smoke-test fixtures that still advertise `contract draft-execplan` or draft-first examples.

## Plan of Work

Rename or alias the planner contract surface toward `execplan`, update bootstrapped workflow/spec language to initiative-first planning, and align smoke tests and planner-facing docs to the newer model.

## Validation and Acceptance

`execplan-validate` must pass for this plan, and planner/bootstrap tests must confirm the generated guidance no longer defaults to `draft-execplan` workflows where the contract-first model is intended.

## Artifacts and Notes

This slice should not attempt bulk migration of historical archived ExecPlans; it should change the active generator, bootstrap, and validation-facing surfaces only.
