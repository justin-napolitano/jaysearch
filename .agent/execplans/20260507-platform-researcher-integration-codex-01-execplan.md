---
id: "20260507-platform-researcher-integration-codex-01-execplan"
title: "Add the first platform command for invoking the external researcher capability"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - .agent/execplans/20260507-platform-researcher-integration-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - bin/run-research-capability
  - docs/commands.md
  - docs/public-orchestration-api.md
  - docs/system-architecture/platform-researcher-interface.md
  - spec/public-orchestration-api.schema.yaml
  - src/platform_tools/run_research_capability.py
  - tests/test_run_research_capability.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-059"
  queue_position: 59
  implementation_branch: "impl-execplan/20260507-platform-researcher-integration-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-platform-researcher-integration-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "bin/run-research-capability"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/run_research_capability.py"
    - "tests/test_run_research_capability.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-platform-researcher-integration-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-platform-researcher-integration-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_run_research_capability.py"
      expected_exit: 0
tasks:
  - title: "Add a platform command that invokes the external researcher repo through its CLI contract"
    priority: "P1"
  - title: "Expose the command through the versioned public orchestration API catalog"
    priority: "P1"
  - title: "Document the operator-facing command and validate the machine-readable response surface"
    priority: "P1"
depends_on:
  - "20260507-researcher-repo-architecture-codex-01-execplan"
---

## Outcomes & Retrospective

The platform should be able to invoke one bounded researcher run through a stable command surface rather than relying only on documentation.

## Context and Orientation

The previous slice defined the external researcher repo and its contract surface. The next step is to expose one real platform command that can call the external runtime, validate its result shape, and return a versioned orchestration envelope.

## Plan of Work

Implement a thin `run-research-capability` command in the platform repo, wire it into the public orchestration API catalog, and add focused tests around request validation, subprocess execution, and response projection.

## Validation and Acceptance

This slice is accepted when the platform repo contains a documented, tested command that invokes the external researcher CLI contract and returns a stable machine-oriented response.

## Artifacts and Notes

This slice adds the first real platform-owned invocation surface for the external researcher capability but intentionally stops short of deeper plugin routing or managed-repo automation.
