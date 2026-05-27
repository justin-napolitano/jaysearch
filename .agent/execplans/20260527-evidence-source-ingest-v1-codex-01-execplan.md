---
id: "20260527-evidence-source-ingest-v1-codex-01"
title: "Evidence Source Ingest V1"
owner: "agent/codex"
created: "2026-05-27T00:00:00Z"
status: draft
base_branch: main
initiative_branch: "initiative/evidence-source-ingest-v1"
initiative_node_id: "initiative-evidence-source-ingest-v1"
changes:
  - .agent/execplans/20260527-evidence-source-ingest-v1-codex-01-execplan.md
  - docs/evidence-source-ingest-v1.md
  - artifacts/planner/research/evidence-source-ingest-v1-dag.json
approve_policy: codeowners
reviewers:
  - "github:jna31a"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "jaysearch-evidence-source-ingest-v1"
  queue_position: 73
  implementation_branch: "impl-execplan/evidence-source-ingest-v1"
  goal_area: "research-runtime"
  integration_mode: "via_initiative"
  conflict_domains:
    - "research-runtime"
    - "evidence-ingest"
    - "demo-runtime"
  expected_artifacts:
    - .agent/execplans/20260527-evidence-source-ingest-v1-codex-01-execplan.md
    - docs/evidence-source-ingest-v1.md
    - artifacts/planner/research/evidence-source-ingest-v1-dag.json
    - spec/contracts/packet-schema-registry.yaml
    - src/platform_tools/ingest_evidence_sources.py
    - bin/ingest-evidence-sources
    - tests/test_ingest_evidence_sources.py

validation:
  tests:
    - name: "execplan_validate"
      command: "bin/execplan-validate .agent/execplans/20260527-evidence-source-ingest-v1-codex-01-execplan.md"
      expected_exit: 0
    - name: "design_review"
      command: "bin/design-iteration --root ."
      expected_exit: 0
    - name: "pre_push"
      command: "bin/run-governed-pre-push-checks --root ."
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260527-evidence-source-ingest-v1-codex-01-execplan.md"
      expected_exit: 0

tasks:
  - title: "Define bounded URL evidence ingestion contracts"
    priority: "P0"
  - title: "Implement URL source record and claim record materialization"
    priority: "P0"
  - title: "Assemble evidence packet for existing research candidate loop"
    priority: "P0"
  - title: "Wire a smoke path from question plus URLs into research recommendation"
    priority: "P1"

depends_on:
  - "20260527-research-candidate-to-dag-adapter-v1-codex-01"
  - "20260527-question-to-dag-demo-v1-codex-01"
  - "20260521-research-candidate-tree-search-v1-codex-01"
  - "20260521-research-candidate-evaluation-v1-codex-01"
  - "20260521-research-recommendation-v1-codex-01"
source_artifacts:
  - docs/evidence-search-tool-v1.md
  - docs/research-tool-v1.md
  - docs/design-iteration-tool-v1.md
  - docs/current-research-bibliography.md
  - docs/question-to-dag-demo-v1.md
  - src/platform_tools/run_jaysearch_question_dag_demo.py
  - src/platform_tools/materialize_research_candidate_tree.py
  - src/platform_tools/materialize_research_evaluations.py
  - src/platform_tools/materialize_research_recommendation.py
---

## Objective

Create the build plan for bounded URL-based evidence ingestion so a user can ask a question, provide or discover URLs, and turn those sources into evidence packets consumable by the existing Jaysearch research candidate/evaluation/recommendation loop.

## Context and Orientation

Jaysearch can already move from a question-shaped problem into research candidates, scored evaluations, recommendations, candidate DAGs, and execution units. The missing upstream boundary is fresh external evidence ingestion.

The target V1 flow is:

```text
question
  -> explicit source URL set
  -> source_record[]
  -> claim_record[]
  -> evidence_packet
  -> research_problem_packet
  -> research_candidate_packet[]
  -> research_evaluation_packet[]
  -> research_recommendation_packet
```

V1 should support manually supplied or Codex-discovered URLs. It should not implement broad crawling.

## Scope

Implement a bounded CLI:

```bash
bin/ingest-evidence-sources \
  --question "How should Jaysearch structure workflow graphs?" \
  --url https://airflow.apache.org/docs/apache-airflow/2.10.3/core-concepts/dags.html \
  --url https://networkx.org/documentation/stable/reference/algorithms/dag.html
```

The CLI should emit a run directory under `artifacts/evidence-source-ingest/runs/<run_id>/` containing:

- `source-record-XX.packet.json`
- `claim-records.packet.json`
- `evidence.packet.json`
- `ingest.report.json`

## Non-Goals

- No unrestricted crawler.
- No autonomous source acceptance without visible acceptance/rejection reasons.
- No final design recommendation inside the ingest tool.
- No replacement of the existing research candidate/evaluation/recommendation tools.
- No hidden browser state as evidence.

## Contract Requirements

`source_record` must include:

- stable `source_id`
- source URL
- retrieval status
- title or fallback title
- source type
- retrieved/extracted text summary
- accepted/rejected status
- acceptance or rejection reasons

`claim_record` must include:

- stable `claim_id`
- `source_id`
- bounded claim text
- claim type
- evidence span or excerpt reference
- confidence or extraction status

`evidence_packet` must include:

- source question
- accepted source refs
- rejected source refs
- claim refs
- evidence summary
- limitations

## Plan of Work

1. Add packet schema registry entries for `source_record`, `claim_record`, and URL-ingest `evidence_packet` if the current registry does not already define equivalent packets.
2. Implement `src/platform_tools/ingest_evidence_sources.py`.
3. Add `bin/ingest-evidence-sources`.
4. Support local/offline deterministic tests by allowing file URLs or injected source text fixtures.
5. Use live HTTP fetch only behind explicit URL inputs and clear retrieval status.
6. Extract simple V1 claims deterministically from headings, abstracts, summaries, or first relevant paragraphs.
7. Emit accepted and rejected sources so source ranking remains inspectable.
8. Add tests for successful ingestion, failed URL handling, accepted/rejected source traceability, and evidence packet assembly.
9. Optionally wire the question-DAG demo to consume a supplied evidence packet in a later slice.

## Validation and Acceptance

Minimum validation for the implementation slice:

```bash
uv run pytest tests/test_ingest_evidence_sources.py
bin/ingest-evidence-sources --root . --question "How should Jaysearch structure workflow graphs?" --url file://<fixture>
bin/run-governed-pre-push-checks --root .
```

Acceptance criteria:

- source ingestion works without broad crawling
- failed sources are preserved with rejection reasons
- source and claim packet IDs are stable enough for replay
- evidence packet can be referenced by the existing research loop
- no candidate is ranked using evidence that lacks traceable source refs

## Evidence Basis

- `docs/evidence-search-tool-v1.md` already defines the intended search/fetch/extract/assemble split.
- W3C PROV-DM supports preserving derivation between source records, claim records, evidence packets, candidates, and recommendations.
- Airflow and NetworkX docs are target example sources for workflow DAG and graph traversal questions.
- The scientific workflow literature motivates combining DAG execution with provenance and reproducibility.

## Open Questions

- Should V1 fetch live URLs directly, or should Codex/browser retrieval write text fixtures that Jaysearch ingests first?
- Should `evidence_packet` be generalized now or kept as `evidence_source_ingest_packet` until the broader contract stabilizes?
- Should source ranking be implemented in this slice or deferred until after traceable ingestion works?

## Artifacts and Notes

The planning artifacts for this slice are:

- `docs/evidence-source-ingest-v1.md`
- `artifacts/planner/research/evidence-source-ingest-v1-dag.json`
- `.agent/execplans/20260527-evidence-source-ingest-v1-codex-01-execplan.md`

## Outcomes & Retrospective

Pending implementation.
