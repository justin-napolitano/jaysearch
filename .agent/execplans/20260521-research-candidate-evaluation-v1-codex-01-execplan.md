---
id: "20260521-research-candidate-evaluation-v1-codex-01"
title: "Research Candidate Evaluation V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/research-candidate-evaluation-v1.md
  - docs/research-tool-v1.md
  - docs/research-tool-v1-ranking-and-search.md
  - docs/core-contract-spec-v1.md
  - spec/contracts/packet-schema-registry.yaml
  - artifacts/planner/research/research-candidate-evaluation-v1-dag.json
  - .agent/execplans/20260521-research-candidate-evaluation-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/research-candidate-evaluation-v1"
initiative_node_id: "initiative-research-candidate-evaluation-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "design-review"
      command: "run design-iteration after adding candidate evaluation contracts and DAG"
      expected_exit: 0

tasks:
  - title: "Define research candidate evaluation spec"
    priority: "P0"
  - title: "Tighten research_evaluation_packet contract"
    priority: "P0"
  - title: "Define candidate_evaluation_summary_packet"
    priority: "P0"
  - title: "Create bounded evaluation DAG"
    priority: "P0"
  - title: "Prepare runtime implementation slice"
    priority: "P1"

depends_on:
  - "20260521-research-candidate-tree-search-v1-codex-01"
---

## Outcomes & Retrospective

This slice defines the first evaluation layer after candidate tree search. It keeps evaluation bounded to static, contract, traceability, evidence, and feasibility checks before full empirical execution exists.

## Research Basis

The plan is grounded in:

- `Self-Refine`: iterative feedback improves outputs when feedback is explicit
- `Reflexion`: feedback and retained context improve agent decisions
- `CRITIC`: tool-assisted critique improves self-correction over unsupported introspection
- `SWE-bench`: software work needs task-grounded evaluation rather than plausibility-only scoring

## Plan of Work

Phase 1 locks the evaluation contract. Phase 2 defines the evaluation DAG. Phase 3 prepares the runtime build that will consume candidate packets and emit evaluation records.

## Validation and Acceptance

Acceptance means:

- every candidate has a required evaluation record before recommendation
- promotion and blocking status are explicit
- evaluation outputs are machine-readable and traceable
