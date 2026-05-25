---
id: "20260521-research-recommendation-v1-codex-01"
title: "Research Recommendation V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - pyproject.toml
  - docs/research-recommendation-v1.md
  - docs/research-tool-v1.md
  - docs/research-tool-v1-ranking-and-search.md
  - docs/core-contract-spec-v1.md
  - spec/contracts/packet-schema-registry.yaml
  - artifacts/planner/research/research-recommendation-v1-dag.json
  - bin/materialize-research-recommendation
  - src/platform_tools/materialize_research_recommendation.py
  - tests/test_materialize_research_recommendation.py
  - .agent/execplans/20260521-research-recommendation-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/research-recommendation-v1"
initiative_node_id: "initiative-research-recommendation-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "design-review"
      command: "run design-iteration after adding recommendation contracts and DAG"
      expected_exit: 0
    - name: "recommendation-runtime"
      command: "uv run pytest tests/test_materialize_research_recommendation.py"
      expected_exit: 0

tasks:
  - title: "Define evaluation-backed recommendation spec"
    priority: "P0"
  - title: "Tighten research_recommendation_packet contract"
    priority: "P0"
  - title: "Tighten ranked_candidate_packet contract"
    priority: "P0"
  - title: "Create bounded recommendation DAG"
    priority: "P0"
  - title: "Implement recommendation runtime materializer"
    priority: "P1"

depends_on:
  - "20260521-research-candidate-evaluation-v1-codex-01"
---

## Outcomes & Retrospective

This slice makes research recommendation evaluation-backed. It prevents recommendation packets from bypassing candidate evaluation records.

## Research Basis

The plan uses:

- `Self-Refine` for explicit feedback loops
- `Reflexion` for feedback plus retained context
- `CRITIC` for tool-grounded critique
- `SWE-bench` for task-grounded software evaluation expectations

## Plan of Work

Phase 1 tightens the recommendation contracts. Phase 2 defines the recommendation DAG. Phase 3 implements a runtime that ranks evaluated candidates and emits a traceable recommendation packet.

## Validation and Acceptance

Acceptance means:

- recommendation requires evaluation packet refs
- ranked candidates carry evaluation refs
- rejected candidates remain explicit
- raw recommendations still do not authorize planning
- runtime blocks when candidates lack evaluations
- runtime blocks when all candidates are blocked
