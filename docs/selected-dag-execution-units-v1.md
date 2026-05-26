# Selected DAG Execution Units V1

## Objective

Bridge planning selection into implementation execution.

Jaysearch can now select the best supplied candidate DAG. V1 must convert the selected DAG into buildable execution-unit packets without generating new plans or changing the selected DAG.

```text
candidate_dag_selection
  -> selected_dag_ref
  -> dag_execution_unit_manifest
  -> execution_unit[]
  -> implementation_attempt[]
```

## Research Basis

Local sources:

- `docs/candidate-dag-selection-v1.md`
- `docs/node-based-project-plan-v1.md`
- `docs/problem-node-execution-unit-contract-v1.md`
- `docs/single-workflow-node-era-prebuild-review-v1.md`
- `docs/plan-quality-metrics-v1.md`
- `spec/contracts/execution-unit.schema.yaml`

External sources:

- NetworkX DAG algorithms support acyclicity checks, topological ordering, generation layering, and longest-path analysis: https://networkx.org/documentation/stable/reference/algorithms/dag.html
- JSON Schema object contracts support required fields for machine-readable packets: https://json-schema.org/understanding-json-schema/reference/object
- W3C PROV-DM defines provenance as descriptions of entities, activities, and agents involved in producing data or things: https://www.w3.org/TR/prov-dm/
- Multi-criteria decision analysis is useful when alternatives need transparent scoring across multiple criteria: https://www.epa.gov/risk/multi-criteria-integrated-resource-assessment-mira

## Design Decision

Build a selected-DAG materializer before autonomous DAG generation.

The selector answers: which graph should we use?

The materializer answers: what execution units can the implementation loop actually build?

This avoids a drift-prone gap where the system can rank DAGs but cannot execute the selected DAG in a governed way.

## V1 Scope

Do:

- consume a `candidate_dag_selection` packet
- load `selected_dag_ref`
- validate that the selection has no blockers
- validate the selected DAG is still acyclic
- materialize one execution unit for each buildable DAG node
- preserve dependency edges between execution units
- emit a `dag_execution_unit_manifest`
- preserve non-buildable nodes as manifest metadata instead of silently dropping them
- fail closed when selected DAG nodes lack owned changes or validation targets

Do not:

- generate candidate DAGs
- re-score the selected DAG
- mutate the selected DAG
- run implementation attempts
- infer hidden scope not present in the DAG
- bypass existing execution-unit readiness requirements

## Buildable Node Rules

A DAG node is buildable when it has:

- a stable `node_id`
- `owned_changes` or `owned_surfaces`
- `expected_outputs`
- `validation_commands`, `validation_refs`, `validation_targets`, or `acceptance_checks`
- enough goal/intent text to form an implementation intent

Nodes that are documentation, contract, runtime, or validation nodes can all be buildable if they meet those rules.

## Output Contract

`dag_execution_unit_manifest` records the bridge from graph to executable work.

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `manifest_id`
- `source_selection_ref`
- `selected_dag_ref`
- `execution_unit_refs`
- `execution_dependencies`
- `non_buildable_node_refs`
- `topological_layers`
- `evidence_refs`
- `blockers`

The manifest does not replace individual `execution_unit` packets. It groups them and preserves dependency structure.

## Runtime Shape

Proposed command:

- `bin/materialize-selected-dag-execution-units`

Inputs:

- `--selection-path`
- optional `--output-root`
- optional `--target-state`

Outputs:

- `execution-unit-*.packet.json`
- `dag-execution-unit-manifest.packet.json`
- `dag-execution-unit-materialization.report.json`

## Critical Checks

The command must block if:

- selection packet type is not `candidate_dag_selection`
- selection has blockers
- `selected_dag_ref` is missing or unreadable
- selected DAG has cycles
- selected DAG has missing or duplicate node ids
- edges point to missing nodes
- a buildable-looking node lacks owned changes
- a buildable-looking node lacks validation targets
- no execution units can be emitted

## Dependency Semantics

Candidate DAG edges use:

```json
{
  "from_node_id": "implement-runtime",
  "to_node_id": "define-contract",
  "relation": "depends_on"
}
```

The materialized execution dependency should preserve that meaning:

```json
{
  "from_execution_unit_ref": "execution-unit:implement-runtime",
  "to_execution_unit_ref": "execution-unit:define-contract",
  "relation": "depends_on"
}
```

This keeps topological execution possible without reversing edge meaning.

## Acceptance

V1 is acceptable when:

- a valid selected DAG emits execution-unit packets
- the manifest preserves dependency edges
- cyclic or blocked selections fail closed
- invalid node scope is reported as blockers
- generated execution units pass existing readiness validation
- tests cover valid materialization and blocked cases
- Jaysearch CI passes
- design iteration reports no blockers

## Critical Non-Goal

Do not improve candidate generation in this slice.

This bridge should make the existing selected DAG executable. Better DAG generation can come later and target the same manifest contract.
