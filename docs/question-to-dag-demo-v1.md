# Question To DAG Demo V1

## Objective

Create the interview-ready flow from a user-entered problem/question to a traceable, evidence-backed DAG and execution-unit handoff.

This is the intended demo boundary:

```text
user question
  -> research_question_packet
  -> evidence_packet in bounded fixture mode
  -> research_problem_packet
  -> research_hypothesis_packet[]
  -> research_candidate_packet[]
  -> research_evaluation_packet[]
  -> research_recommendation_packet
  -> candidate DAG manifest
  -> selected DAG
  -> execution units
  -> implementation boundary notice
```

The demo should be honest: development execution and autonomous candidate generation remain future production slices.

## Research Basis

Local sources:

- `docs/question-tool-v1.md`
- `docs/research-tool-v1.md`
- `docs/candidate-dag-selection-v1.md`
- `docs/selected-dag-execution-units-v1.md`
- `docs/jaysearch-demo-runner-v1.md`
- `docs/core-contract-spec-v1.md`

External sources:

- W3C PROV-DM supports explicit provenance links between generated entities, activities, and agents: https://www.w3.org/TR/prov-dm/
- JSON Schema object contracts support required fields for machine-readable packets: https://json-schema.org/understanding-json-schema/reference/object
- NetworkX DAG algorithms support acyclicity, topological ordering, and graph-layer analysis: https://networkx.org/documentation/stable/reference/algorithms/dag.html
- SWE-bench supports grounding software work in concrete repository tasks and artifacts rather than prose-only plans: https://arxiv.org/abs/2310.06770

## Demo Claim

The demo proves:

- Jaysearch can accept an ambiguous problem/question.
- Jaysearch can produce bounded research questions and evidence refs.
- Jaysearch can use the existing question-to-research handoff to materialize a research problem packet.
- Jaysearch can use the existing research candidate loop to generate, evaluate, and recommend candidate approaches.
- Jaysearch can adapt research candidate intent into candidate DAGs that preserve lineage.
- Jaysearch can select a DAG using the existing DAG selector.
- Jaysearch can materialize execution units from the selected DAG.
- Jaysearch can stop at the implementation boundary without overclaiming.

The demo does not prove:

- live autonomous web research
- autonomous code generation
- production-ready implementation execution
- semantic correctness of generated software

## Slice Plan

### Slice 1: CLI Artifact Flow

Build `bin/run-jaysearch-question-dag-demo`.

Inputs:

- `--question`
- optional `--topic`
- optional `--output-root`

Outputs:

- `question.packet.json`
- `evidence.packet.json`
- `research-hypothesis-*.packet.json`
- `research-candidate-*.packet.json`
- `research-evaluation-*.packet.json`
- `research-recommendation.packet.json`
- `candidate-dag-manifest.packet.json`
- `candidate-dag-selection.packet.json`
- `dag-execution-unit-manifest.packet.json`
- `execution-unit-*.packet.json`
- `question-dag-demo.report.json`
- `question-dag-demo-summary.md`

Implementation notes:

- Use bounded fixture evidence first.
- Emit the registered `evidence_packet` contract, with fixture mode recorded as metadata.
- Reuse `orchestrate_question_research_handoff`.
- Reuse the existing research hypothesis, candidate tree, evaluation, and recommendation tools.
- Use `materialize-candidate-dags-from-research` to adapt ranked research candidates into candidate DAGs.
- Preserve lineage refs on every packet.
- Reuse `select_candidate_dag`.
- Reuse `materialize_selected_dag_execution_units`.
- Do not call live web research in V1.

### Slice 2: Presentation UI

Build a small static artifact viewer.

Options:

- Generate `demo.html` inside each run directory.
- Or add a GitHub Pages demo page that explains how to run the command and read artifacts.

Recommended V1:

- Generate `demo.html` inside the run directory.
- Keep GitHub Pages as documentation, not a hosted app.

## Packet Lineage

Every output must preserve:

- `problem_ref`
- `question_ref`
- `evidence_refs`
- `candidate_dag_manifest_ref`
- `selected_dag_ref`
- `dag_execution_unit_manifest_ref`
- `execution_unit_refs`

This lets the presenter answer:

- What question produced this DAG?
- What evidence supports it?
- Why was this graph selected?
- Which execution units came from which DAG nodes?
- Where does implementation begin?

## Harsh Review

- Do not make this a fake chat UI. The demo must produce inspectable packet files.
- Do not perform open-ended web research live in front of the interviewer.
- Do not hide that research is fixture/bounded in V1.
- Do not route directly from question to execution units without a selected DAG.
- Do not collapse lineage into prose summaries.
- Do not build code generation before the question-to-DAG demo is understandable.

## Acceptance

Slice 1 is acceptable when:

- `bin/run-jaysearch-question-dag-demo --question "..."` exits `0`
- the selected DAG has evidence refs and question refs
- execution units preserve selected DAG lineage
- the report states the implementation boundary clearly
- tests cover successful flow and missing question blockers

Slice 2 is acceptable when:

- the run emits a readable `demo.html`
- the UI shows question, evidence, DAG, selection rationale, execution units, and implementation boundary
- the UI uses the same packet artifacts as the CLI flow
