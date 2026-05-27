# Research Candidate To DAG Adapter V1

## Purpose

Convert ranked research candidates into candidate DAG artifacts that the existing DAG selector and execution-unit materializer can consume.

This avoids a parallel candidate-generation system. The adapter reuses the existing research loop:

```text
research_problem_packet
  -> research_hypothesis_packet[]
  -> candidate_search_tree_packet
  -> research_candidate_packet[]
  -> research_evaluation_packet[]
  -> research_recommendation_packet
  -> candidate_dag_manifest + candidate_dag[]
```

## Runtime Contract

CLI:

```bash
bin/materialize-candidate-dags-from-research \
  --root . \
  --research-recommendation-path <research-recommendation.packet.json> \
  --candidate <research-candidate.packet.json> \
  --evidence-packet-path <evidence.packet.json>
```

Inputs:

- `research_recommendation_packet`
- `research_candidate_packet[]`
- optional `evidence_packet`

Outputs:

- `candidate-dag-manifest.packet.json`
- one `*.candidate-dag.json` per ranked candidate, capped by V1 `max_dags`
- `candidate-dag-adapter.report.json`

## DAG Projection

Each research candidate becomes a bounded implementation DAG with stable surface nodes:

- `contract_surface`
- `runtime_surface`
- `validation_surface`
- `documentation_surface`
- `handoff_surface`

Each node preserves:

- source research candidate ref
- owned changes from candidate intent fields
- expected outputs
- acceptance checks
- validation command
- evidence refs
- non-goals
- risk level

## Selection Boundary

The adapter does not select the winning DAG. It emits a `candidate_dag_manifest` and delegates selection to `select-candidate-dag`.

Non-promoted research candidates may still be emitted as visible candidate DAGs with blockers, so downstream selection can preserve rejected alternatives without treating them as eligible.

## Non-Claims

V1 does not perform live web research, LLM synthesis, patch application, or production execution. It only projects existing research candidate intent into graph artifacts.
