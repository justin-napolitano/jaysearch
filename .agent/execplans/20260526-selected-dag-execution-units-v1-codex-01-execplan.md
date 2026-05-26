---
id: "20260526-selected-dag-execution-units-v1-codex-01"
title: "Selected DAG Execution Units V1"
owner: "agent/codex"
created: "2026-05-26T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/selected-dag-execution-units-v1.md
  - artifacts/planner/research/selected-dag-execution-units-v1-dag.json
  - spec/contracts/dag-execution-unit-manifest.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/materialize_selected_dag_execution_units.py
  - bin/materialize-selected-dag-execution-units
  - src/platform_tools/run_jaysearch_ci.py
  - tests/test_dag_execution_unit_manifest_contracts.py
  - tests/test_materialize_selected_dag_execution_units.py
  - tests/test_run_jaysearch_ci.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "selected-dag-execution-unit-tests"
      command: "uv run pytest tests/test_dag_execution_unit_manifest_contracts.py tests/test_materialize_selected_dag_execution_units.py"
      expected_exit: 0
    - name: "jaysearch-ci"
      command: "bin/run-jaysearch-ci"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define dag_execution_unit_manifest contract"
    priority: "P0"
  - title: "Implement selected DAG materializer"
    priority: "P0"
  - title: "Preserve execution-unit dependencies"
    priority: "P0"
  - title: "Enforce existing execution-unit readiness"
    priority: "P0"
  - title: "Add tests and CI coverage"
    priority: "P0"

depends_on:
  - "20260526-candidate-dag-selection-v1-codex-01"
source_artifacts:
  - docs/selected-dag-execution-units-v1.md
  - artifacts/planner/research/selected-dag-execution-units-v1-dag.json
  - docs/candidate-dag-selection-v1.md
  - docs/problem-node-execution-unit-contract-v1.md
  - spec/contracts/execution-unit.schema.yaml
---

## Objective

Build the bridge from selected planner DAG to executable implementation units.

The current system can select a candidate DAG, but the implementation ERA loop consumes execution-unit-like work contracts. This slice materializes selected DAG nodes into execution units and emits a manifest that preserves graph dependencies.

## Scope

In scope:

- `dag_execution_unit_manifest` contract
- selected-DAG materializer CLI
- execution unit packets emitted from buildable DAG nodes
- dependency preservation between execution units
- fail-closed blockers for invalid selections and underspecified nodes
- Jaysearch CI coverage

Out of scope:

- autonomous DAG generation
- candidate DAG re-scoring
- implementation attempt generation
- merge gate enforcement
- JSON ExecPlan conversion

## Research Basis

- NetworkX documents DAG operations for acyclicity, topological sorting, generation layering, and longest path analysis. This supports using graph primitives for selected-DAG traversal and dependency preservation.
- JSON Schema documents required object properties, supporting explicit machine-readable packet contracts for the manifest.
- W3C PROV-DM frames provenance around entities, activities, and agents, supporting explicit links from selection to DAG to execution units.
- Existing Jaysearch execution-unit contracts already define buildable/evaluable work and should be reused instead of creating a parallel work-unit abstraction.

## Acceptance

- valid selected DAG emits one execution unit per buildable node
- output manifest links selection, DAG, execution units, dependencies, layers, evidence, and blockers
- blocked selections fail without emitting implementation-ready units
- cyclic selected DAGs fail closed
- node-level missing owned surfaces or validation targets are reported
- existing execution-unit readiness policy remains authoritative
- targeted tests pass
- `bin/run-jaysearch-ci` passes
- `bin/design-iteration --root .` reports no blockers
