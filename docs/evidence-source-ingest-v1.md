# Evidence Source Ingest V1

## Purpose

Make external source use explicit and replayable.

Jaysearch should let a user ask a design or implementation question, provide or discover URLs, and turn those sources into structured evidence that the research loop can evaluate.

V1 is not a crawler. It is a bounded ingestion boundary.

## Target Flow

```text
question
  -> explicit URL set
  -> source_record[]
  -> claim_record[]
  -> evidence_packet
  -> research candidate generation
  -> research evaluation
  -> research recommendation
  -> candidate DAG generation
```

The retrieval layer does not decide the final answer. It only records sources, extracted claims, limitations, and source acceptance decisions.

## Why This Slice Exists

The current Jaysearch loop can rank research candidates after structured evidence exists. The missing step is turning fresh URLs into that structured evidence.

Without this boundary, Codex can browse and summarize sources, but Jaysearch cannot replay what was fetched, why it mattered, or which candidate depended on which source.

## V1 Input

Required:

- `question`
- one or more explicit `url` values

Optional:

- `source_type`
- `expected_claim_types`
- `acceptance_policy`
- `output_root`
- local fixture text for deterministic tests

Search automation is future work. A user or Codex can provide URLs in V1.

## V1 Output

Run directory:

```text
artifacts/evidence-source-ingest/runs/<run_id>/
  source-record-01.packet.json
  source-record-02.packet.json
  claim-records.packet.json
  evidence.packet.json
  ingest.report.json
```

### `source_record`

Minimum fields:

- `packet_type`
- `packet_version`
- `source_id`
- `question`
- `uri`
- `retrieval_status`
- `source_type`
- `title`
- `summary`
- `accepted`
- `acceptance_reasons`
- `rejection_reasons`
- `retrieved_at`

### `claim_record`

Minimum fields:

- `packet_type`
- `packet_version`
- `claim_id`
- `source_id`
- `claim_text`
- `claim_type`
- `evidence_span_ref`
- `extraction_status`
- `limitations`

### `evidence_packet`

Minimum fields:

- `packet_type`
- `packet_version`
- `evidence_packet_id`
- `question`
- `source_record_refs`
- `accepted_source_refs`
- `rejected_source_refs`
- `claim_record_refs`
- `evidence_summary`
- `limitations`

## Source Ranking

V1 should rank evidence usefulness before the research loop uses it.

Starter dimensions:

- problem relevance
- source authority
- methodological fit
- graph/workflow applicability
- provenance usefulness
- retrieval quality

Ranking is not final solution selection. It only decides whether a source should influence candidate generation and scoring.

## Claim Extraction

V1 claim extraction should be conservative.

Acceptable extraction sources:

- page title and headings
- abstract text
- documentation summary sections
- first relevant paragraphs
- explicit definitions

Do not invent claims from weakly related text. When extraction is uncertain, emit a low-confidence claim or a source limitation instead.

## Relationship To Existing Tools

`evidence-source-ingest-v1` feeds the existing research loop.

```text
ingest-evidence-sources
  -> evidence_packet
  -> materialize-research-candidate-tree
  -> materialize-research-evaluations
  -> materialize-research-recommendation
  -> materialize-candidate-dags-from-research
```

The ingest tool must not replace:

- research candidate generation
- candidate evaluation
- recommendation selection
- candidate DAG generation
- implementation execution

## Example Question

Question:

```text
How should Jaysearch structure workflow graphs and lineage graphs?
```

Example URLs:

- Airflow DAG concepts: `https://airflow.apache.org/docs/apache-airflow/2.10.3/core-concepts/dags.html`
- NetworkX DAG algorithms: `https://networkx.org/documentation/stable/reference/algorithms/dag.html`
- W3C PROV-DM: `https://www.w3.org/TR/prov-dm/`
- Scientific workflow provenance paper: `https://arxiv.org/abs/1311.4610`

Expected use:

- Airflow informs task/DAG dependency structure.
- NetworkX informs traversal, acyclicity, topological order, and ranking implementation.
- W3C PROV-DM informs lineage edges between sources, claims, candidates, artifacts, and agents.
- Scientific workflow literature informs reproducible workflow execution and provenance capture.

## Design Rules

- Persist JSON packets, not browser state.
- Preserve failed and rejected sources.
- Separate retrieval from reasoning.
- Separate evidence ranking from candidate ranking.
- Require every claim used by a candidate to trace back to a source record.
- Keep NetworkX as an analysis engine, not the persisted graph format.

## Future Work

- Add web search query generation from a question.
- Add source search result ranking before URL fetch.
- Add richer claim extraction.
- Add citation-span storage.
- Add direct handoff from evidence packet to question-DAG demo.
- Add a Jaysearch-native work graph that records evidence-source-ingest runs as lineage nodes.
