---
id: "20260527-research-candidate-to-dag-adapter-v1-codex-01"
title: "Research Candidate To Candidate DAG Adapter V1"
owner: "agent/codex"
created: "2026-05-27T00:00:00Z"
status: draft
base_branch: main
initiative_branch: "initiative/research-candidate-to-dag-adapter-v1"
initiative_node_id: "initiative-research-candidate-to-dag-adapter-v1"
changes:
  - .agent/execplans/20260527-research-candidate-to-dag-adapter-v1-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/research-candidate-to-dag-adapter-v1.md
  - src/platform_tools/materialize_candidate_dags_from_research.py
  - bin/materialize-candidate-dags-from-research
  - src/platform_tools/run_jaysearch_question_dag_demo.py
  - tests/test_materialize_candidate_dags_from_research.py
  - tests/test_run_jaysearch_question_dag_demo.py
  - src/platform_tools/run_jaysearch_ci.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-072"
  queue_position: 72
  implementation_branch: "impl-execplan/research-candidate-to-dag-adapter-v1"
  goal_area: "research-runtime"
  integration_mode: "via_initiative"
  conflict_domains:
    - "research-runtime"
    - "planner-runtime"
    - "candidate-dag"
    - "demo-runtime"
  expected_artifacts:
    - .agent/execplans/20260527-research-candidate-to-dag-adapter-v1-codex-01-execplan.md
    - artifacts/governance/board-action-events.jsonl
    - artifacts/planner/research/remaining-work-graph.json
    - bin/materialize-candidate-dags-from-research
    - docs/queued-execplans.md
    - docs/research-candidate-to-dag-adapter-v1.md
    - docs/question-dag-demo.html
    - docs/question-to-dag-demo-v1.md
    - src/platform_tools/materialize_candidate_dags_from_research.py
    - src/platform_tools/run_jaysearch_ci.py
    - src/platform_tools/run_jaysearch_question_dag_demo.py
    - tests/test_materialize_candidate_dags_from_research.py
    - tests/test_run_jaysearch_question_dag_demo.py

validation:
  tests:
    - name: "candidate-dag-adapter-tests"
      command: "uv run pytest tests/test_materialize_candidate_dags_from_research.py tests/test_run_jaysearch_question_dag_demo.py"
      expected_exit: 0
    - name: "jaysearch-ci"
      command: "bin/run-jaysearch-ci"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260527-research-candidate-to-dag-adapter-v1-codex-01-execplan.md"
      expected_exit: 0

tasks:
  - title: "Define research candidate to DAG adapter contract"
    priority: "P0"
  - title: "Implement adapter CLI and runtime"
    priority: "P0"
  - title: "Wire question-to-DAG demo through research candidate generation"
    priority: "P0"
  - title: "Add focused tests and Jaysearch CI coverage"
    priority: "P0"

depends_on:
  - "20260521-research-candidate-tree-search-v1-codex-01"
  - "20260521-research-candidate-evaluation-v1-codex-01"
  - "20260521-research-recommendation-v1-codex-01"
  - "20260526-candidate-dag-selection-v1-codex-01"
  - "20260526-selected-dag-execution-units-v1-codex-01"
  - "20260527-question-to-dag-demo-v1-codex-01"
source_artifacts:
  - docs/research-candidate-tree-search-v1.md
  - docs/research-candidate-evaluation-v1.md
  - docs/research-recommendation-v1.md
  - docs/candidate-dag-selection-v1.md
  - docs/selected-dag-execution-units-v1.md
  - docs/question-to-dag-demo-v1.md
  - src/platform_tools/materialize_research_candidate_tree.py
  - src/platform_tools/materialize_research_evaluations.py
  - src/platform_tools/materialize_research_recommendation.py
  - src/platform_tools/select_candidate_dag.py
  - src/platform_tools/materialize_selected_dag_execution_units.py
---

## Objective

Replace the question-to-DAG demo's internal fixture DAG writer with a governed adapter that turns evaluated research candidates into candidate DAG artifacts.

## Context and Orientation

Jaysearch already has the upstream research candidate loop and downstream candidate DAG selector. The missing bridge is an adapter from ranked research candidate intent into DAG artifacts the selector and execution-unit materializer can consume.

The target flow is:

```text
research_question_packet
  -> evidence_packet
  -> research_problem_packet
  -> research_hypothesis_packet[]
  -> candidate_search_tree_packet
  -> research_candidate_packet[]
  -> research_evaluation_packet[]
  -> research_recommendation_packet
  -> candidate_dag_manifest + candidate_dag[]
  -> candidate_dag_selection
  -> dag_execution_unit_manifest + execution_unit[]
```

## Scope

Build `materialize-candidate-dags-from-research`.

Inputs:

- `--research-recommendation-path`
- one or more `--candidate`
- optional `--evidence-packet-path`
- optional `--output-root`

Outputs:

- `candidate-dag-manifest.packet.json`
- one candidate DAG per ranked/promoted research candidate, bounded by a small V1 cap
- adapter report with generated DAG refs, skipped candidate refs, blockers, and lineage refs

The adapter must synthesize DAG nodes from existing `research_candidate_packet` intent fields:

- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `expected_changes`
- `non_goals`
- `handoff_requirements`
- `evidence_refs`
- `feasibility_priors`

## Outcomes & Retrospective

Expected outcome: the question-to-DAG demo becomes research-candidate-derived instead of template-derived, while preserving the current honest implementation boundary.

Retrospective notes will be filled after implementation.

## Plan of Work

1. Add `src/platform_tools/materialize_candidate_dags_from_research.py`.
2. Add `bin/materialize-candidate-dags-from-research`.
3. Validate packet types for `research_recommendation_packet`, `research_candidate_packet`, and optional `evidence_packet`.
4. Select ranked candidates from the recommendation, preserving rejected or skipped candidates in the adapter report.
5. For each eligible candidate, emit a candidate DAG with stable node families:
   - `contract_surface`
   - `runtime_surface`
   - `validation_surface`
   - `documentation_surface`
   - `handoff_surface`
6. Populate each DAG node with concrete `goal`, `owned_changes`, `expected_outputs`, `validation_commands`, `acceptance_checks`, `non_goals`, `evidence_refs`, and `risk_level`.
7. Emit a `candidate_dag_manifest` consumable by the existing `select_candidate_dag`.
8. Update `run_jaysearch_question_dag_demo` so it runs the existing research candidate loop before DAG selection:
   - `materialize_research_hypotheses`
   - `materialize_research_candidate_tree`
   - `materialize_research_evaluations`
   - `materialize_research_recommendation`
   - `materialize_candidate_dags_from_research`
9. Keep the old invalid-cycle demo candidate only if needed as an explicit selector hard-gate fixture; do not let it masquerade as research-derived output.
10. Extend focused tests and Jaysearch CI.

## Validation and Acceptance

- The demo no longer uses `_write_candidate_dags` as its primary source of candidate DAGs.
- Candidate DAG nodes are derived from research candidate implementation intent, not static generic demo text.
- The selected DAG remains consumable by `materialize_selected_dag_execution_units`.
- The demo report includes refs for research hypotheses, candidate tree, research candidates, evaluations, recommendation, candidate DAG manifest, DAG selection, and execution-unit manifest.
- The implementation boundary still explicitly excludes autonomous web research, code synthesis, patch application, and production execution.

Validation commands:

```bash
uv run pytest tests/test_materialize_candidate_dags_from_research.py tests/test_run_jaysearch_question_dag_demo.py
bin/run-jaysearch-ci
bin/design-iteration --root .
bin/policy-compliance-check --execplan-path .agent/execplans/20260527-research-candidate-to-dag-adapter-v1-codex-01-execplan.md
```

## Non-Goals

- Do not add live web research in this slice.
- Do not add autonomous code generation in this slice.
- Do not change `select_candidate_dag` scoring unless a hard blocker appears.
- Do not replace the research candidate/evaluation/recommendation tools.
- Do not introduce a new graph database or external runtime dependency.

## Research and Design Basis

This slice reuses existing Jaysearch contracts rather than inventing a parallel generator:

- `materialize_research_candidate_tree` already emits `research_candidate_packet[]` with implementation intent and feasibility priors.
- `materialize_research_evaluations` already scores candidates and preserves promotion status.
- `materialize_research_recommendation` already ranks candidates and emits a winner plus rejected summaries.
- `select_candidate_dag` already hard-gates DAG validity and ranks eligible candidate DAGs.
- `materialize_selected_dag_execution_units` already converts selected DAG nodes into execution units.

External design basis already referenced by the current demo remains applicable:

- W3C PROV-DM supports explicit provenance and lineage refs.
- JSON Schema required fields support machine-readable packet contracts.
- NetworkX DAG algorithms support acyclicity, topological ordering, and layer analysis.
- SWE-bench supports grounding software work in concrete repository tasks and artifacts.

## Risks

- Research candidates may still be too generic. Mitigation: adapter tests must assert node goals and owned surfaces reflect candidate intent fields.
- DAGs may become over-split. Mitigation: V1 emits bounded surface-family nodes and lets `select_candidate_dag` penalize long critical paths.
- The demo may become harder to explain. Mitigation: demo report must include `step_reports` and concise artifact refs for each stage.

## Artifacts and Notes

Implementation should avoid committing generated run artifacts under `artifacts/demo/` or `artifacts/design-iteration/runs/`.

If this plan is executed from the current feature branch, create a proper `impl-execplan/*` or `draft-execplan/*` branch before relying on branch-governance checks.
