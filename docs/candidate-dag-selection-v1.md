# Candidate DAG Selection V1

## Objective

Create the first graph-level ERA loop for planning.

V1 should not autonomously generate DAGs. It should consume supplied candidate DAG artifacts, validate hard gates, score valid DAGs, select one, and emit a machine-readable selection packet.

This mirrors the implementation-side strategy already used for candidate patches:

```text
candidate_dag_manifest
  -> candidate_dag[]
  -> dag_evaluation[]
  -> candidate_dag_selection
  -> selected_dag_ref
```

## Research Basis

Local sources:

- `docs/research-candidate-tree-search-v1.md`
- `docs/research-to-selection-validation-v1.md`
- `docs/plan-quality-metrics-v1.md`
- `docs/plan-quality-score-v1.md`
- `docs/candidate-patch-manifest-research-v1.md`
- `docs/candidate-generation-request-result-v1.md`
- `spec/plan-quality-scoring.yaml`

External sources:

- AlphaEvolve: generate/evaluate/select loops are useful when candidate diversity is paired with evaluators: https://arxiv.org/abs/2506.13131
- SWE-bench: software work should be grounded in concrete repository tasks and artifacts: https://arxiv.org/abs/2310.06770
- CRITIC: tool-grounded critique is stronger than unsupported self-correction: https://arxiv.org/abs/2305.11738
- NetworkX DAG algorithms: DAG validation and topological ordering are first-class graph operations: https://networkx.org/documentation/stable/reference/algorithms/dag.html
- JSON Schema: candidate DAG and selection packets should be machine-validated object contracts: https://json-schema.org/understanding-json-schema/reference/object
- W3C PROV-DM: DAG selection should preserve provenance from problem, evidence, candidate DAG, evaluation, and selector: https://www.w3.org/TR/prov-dm/

## Design Decision

Build candidate DAG selection before candidate DAG generation.

Do:

- ingest 2-5 supplied candidate DAG JSON files
- validate each DAG for hard-gate eligibility
- score eligible DAGs using plan-quality metrics
- preserve invalid DAGs with blockers
- select the highest-quality valid DAG
- emit `candidate_dag_selection` with evidence and score breakdowns

Do not:

- generate new DAGs
- mutate candidate DAG files
- materialize execution units
- claim implementation readiness
- select invalid DAGs because they look promising

## Hard Gates

A candidate DAG is ineligible if:

- graph has cycles
- node ids are missing or duplicated
- edge endpoints reference missing nodes
- executable nodes lack validation targets
- owned surfaces are ambiguous
- evidence refs are missing for high-risk nodes
- output contracts are not stated for buildable nodes

These are binary gates. Invalid DAGs do not enter quality ranking.

## Quality Dimensions

Use the existing plan-quality vocabulary:

- boundedness
- dependency efficiency
- parallelism safety
- validation completeness
- scope isolation
- recovery containment
- evidence and assumption clarity
- critical path burden

V1 should use transparent score fields rather than a hidden scalar-only score.

## Packet Concepts

### `candidate_dag_manifest`

Purpose:

- list candidate DAG refs for the same source problem or selected scope

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `manifest_id`
- `source_problem_ref`
- `source_execplan_ref`
- `candidate_dag_refs`
- `selection_policy_ref`
- `evidence_refs`
- `blockers`

### `candidate_dag_evaluation`

Purpose:

- record hard-gate and quality evaluation for one DAG

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `evaluation_id`
- `candidate_dag_ref`
- `hard_gate_status`
- `hard_gate_blockers`
- `score_breakdown`
- `critical_path_summary`
- `evidence_refs`
- `promotion_status`

### `candidate_dag_selection`

Purpose:

- select one candidate DAG among evaluated alternatives

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `selection_id`
- `source_manifest_ref`
- `selected_dag_ref`
- `selected_evaluation_ref`
- `rejected_dag_refs`
- `selection_policy`
- `score_summary`
- `evidence_refs`
- `blockers`

## V1 Runtime Shape

Proposed command:

- `bin/select-candidate-dag`

Inputs:

- `--manifest-path`
- optional `--plan-quality-policy-path`
- optional `--output-root`

Outputs:

- `candidate-dag-evaluation-*.packet.json`
- `candidate-dag-selection.packet.json`
- `candidate-dag-selection.report.json`

## Relationship To ExecPlans

ExecPlans remain the work contract. DAGs remain the execution structure.

The future JSON ExecPlan packet should point at selected DAG refs:

```json
{
  "execplan_id": "example",
  "dag_refs": ["artifacts/planner/research/selected-dag.json"]
}
```

Candidate DAG selection should not replace ExecPlans. It chooses the graph that an ExecPlan can authorize.

## Relationship To Research Loop

The existing research loop already supports:

- question to research problem
- hypotheses
- candidate tree
- evaluation
- recommendation
- selected solution scope

Candidate DAG selection starts after that. It takes one selected strategy/scope and chooses the best graph-shaped decomposition.

## Acceptance

V1 is acceptable when:

- supplied candidate DAGs can be ingested
- invalid DAGs remain visible with blockers
- valid DAGs are ranked by explicit quality dimensions
- one selected DAG is emitted
- selection packet links source manifest, selected DAG, evaluation, evidence, and policy
- Jaysearch CI passes
- design iteration reports no blockers

## Critical Non-Goal

Do not build autonomous DAG generation in this slice.

Generation should be a later producer that emits the same candidate DAG manifest contract.
