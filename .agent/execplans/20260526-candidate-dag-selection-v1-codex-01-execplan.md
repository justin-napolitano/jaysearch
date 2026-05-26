---
id: "20260526-candidate-dag-selection-v1-codex-01"
title: "Candidate DAG Selection V1"
owner: "agent/codex"
created: "2026-05-26T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/candidate-dag-selection-v1.md
  - artifacts/planner/research/candidate-dag-selection-v1-dag.json
  - spec/contracts/candidate-dag-manifest.schema.yaml
  - spec/contracts/candidate-dag-evaluation.schema.yaml
  - spec/contracts/candidate-dag-selection.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/select_candidate_dag.py
  - bin/select-candidate-dag
  - tests/test_candidate_dag_contracts.py
  - tests/test_select_candidate_dag.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "jaysearch-ci"
      command: "bin/run-jaysearch-ci"
      expected_exit: 0
    - name: "candidate-dag-selection-tests"
      command: "uv run pytest tests/test_candidate_dag_contracts.py tests/test_select_candidate_dag.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define candidate DAG manifest/evaluation/selection packets"
    priority: "P0"
  - title: "Implement DAG hard gates"
    priority: "P0"
  - title: "Implement transparent DAG quality scoring"
    priority: "P0"
  - title: "Emit selected DAG packet and report"
    priority: "P0"
  - title: "Preserve invalid DAG blockers"
    priority: "P0"
  - title: "Add selector tests"
    priority: "P0"

depends_on:
  - "20260526-jaysearch-runtime-ci-v1-codex-01"
source_artifacts:
  - docs/candidate-dag-selection-v1.md
  - artifacts/planner/research/candidate-dag-selection-v1-dag.json
  - docs/research-candidate-tree-search-v1.md
  - docs/research-to-selection-validation-v1.md
  - docs/plan-quality-metrics-v1.md
  - docs/plan-quality-score-v1.md
  - docs/current-research-bibliography.md
---

## Objective

Build the first conservative DAG orchestration selection tool.

The tool consumes supplied candidate DAGs, validates hard gates, scores valid candidates, and emits the selected DAG. It does not generate DAGs autonomously.

## Scope

In scope:

- candidate DAG manifest contract
- candidate DAG evaluation contract
- candidate DAG selection contract
- DAG hard gates
- quality scoring using existing plan-quality principles
- selected DAG packet/report
- tests for invalid DAG preservation and selection behavior

Out of scope:

- autonomous DAG generation
- execution-unit materialization from selected DAG
- GitHub merge gate enforcement
- JSON ExecPlan implementation

## Research Basis

- Existing research-to-selection flow validates candidate generation and recommendation before planner/code buildout.
- Existing plan-quality metrics define hard gates before quality scoring.
- AlphaEvolve supports generate/evaluate/select loops when evaluator feedback is explicit.
- SWE-bench supports artifact-grounded software evaluation.
- CRITIC supports tool-grounded critique.
- NetworkX DAG references support explicit acyclicity/topological reasoning.
- JSON Schema supports machine validation of packet contracts.

Implementation decision:

- use NetworkX for DAG mechanics such as acyclicity, topological ordering, and critical path analysis because Jaysearch is becoming graph-native and these primitives will recur across planner, selector, materializer, and orchestration tools
- keep ranking policy local to Jaysearch because plan quality is a product decision, not a generic graph-library decision
- use a hard-gate then multi-criteria scoring model, aligned with plan-quality metrics and multi-criteria decision analysis practice

## Acceptance

- invalid candidate DAGs remain visible with blockers
- cyclic DAGs are rejected before scoring
- valid DAGs receive explicit score breakdowns
- selected DAG is deterministic for the same inputs
- selection packet links manifest, selected DAG, evaluation, evidence, and policy
- Jaysearch CI passes
- design iteration reports no blockers
