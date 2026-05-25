# Evidence Search Tool V1

## Objective

Define a standalone evidence-search API that finds external research, papers, benchmarks, and reference artifacts relevant to a bounded technical problem and returns structured evidence packets for the research tool.

This tool is not the research runtime and not long-term memory.

Its purpose is to:

- search for relevant external research
- normalize paper and source metadata
- extract candidate claims and methods
- return structured evidence packets for candidate generation and evaluation

## Role In The System

The intended split is:

- `evidence-search-tool`
  external retrieval of papers, benchmarks, and references
- `research-tool`
  candidate generation, code synthesis, evaluation, and ranking
- `memory-tool`
  storage and retrieval of internal solved-case records
- `planner-tool`
  DAG generation from a selected solution
- `governance-tool`
  approval and execution controls

The evidence-search tool deals with external knowledge. The memory tool deals with internal reusable knowledge.

## Why This Is Not Overkill

This is the right separation if each tool stays narrow.

Without it, the research tool will absorb:

- paper retrieval
- source normalization
- citation parsing
- claim extraction
- benchmark lookup

That makes the research tool too large again.

The correct pattern is:

1. `evidence-search-tool` finds relevant external evidence
2. `research-tool` uses that evidence to guide candidate generation and evaluation
3. `memory-tool` stores good internal solutions and linked evidence after completion

## Non-Goals

V1 should not become:

- a giant citation graph
- a permanent memory system
- a synthesis engine
- an unrestricted web crawler

It should remain a bounded retrieval and normalization layer.

## Core Use Cases

### Use Case 1: Literature Search

Input:

- bounded problem statement
- keywords
- optional domains or venues

Output:

- ranked paper and source references

### Use Case 2: Evidence Expansion

Input:

- source id or URL

Output:

- normalized metadata
- abstract or extracted text
- candidate claims
- artifact refs

### Use Case 3: Benchmark Retrieval

Input:

- problem class
- metric types

Output:

- relevant benchmarks, datasets, or evaluation references

### Use Case 4: Evidence Packet Assembly

Input:

- retrieved source set

Output:

- structured evidence packet for the research tool

## API Surface

### `search_sources`

Purpose:

- retrieve relevant external sources

Input:

- `query`
- `source_types`
- `filters`
- `top_k`

Output:

- `source_search_results`

### `fetch_source`

Purpose:

- fetch one source and normalize metadata

Input:

- `source_id` or `source_uri`

Output:

- `source_record`

### `extract_claims`

Purpose:

- extract candidate claims, methods, and metrics from one source

Input:

- `source_record`
- `extraction_policy`

Output:

- `claim_record[]`

### `assemble_evidence_packet`

Purpose:

- build the structured evidence packet consumed by the research tool

Input:

- `problem_packet`
- `source_records`
- `claim_records`

Output:

- `evidence_packet`

## Primary Packets

### `source_record`

Minimum fields:

- `source_id`
- `title`
- `authors`
- `published_at`
- `source_type`
- `uri`
- `abstract`
- `artifact_refs`

### `claim_record`

Minimum fields:

- `claim_id`
- `source_id`
- `claim_text`
- `claim_type`
- `evidence_span_refs`
- `metric_refs`

### `evidence_packet`

Minimum fields:

- `problem_id`
- `source_refs`
- `claim_refs`
- `method_refs`
- `benchmark_refs`
- `evidence_summary`

## Retrieval And Ranking

The tool should rank external sources by:

- problem relevance
- source quality
- metric relevance
- methodological similarity
- recency when appropriate

This ranking is for evidence usefulness, not final solution ranking.

## Integration With Research Tool

The research tool should call this tool before candidate generation.

Use:

- `search_sources`
- `fetch_source`
- `extract_claims`
- `assemble_evidence_packet`

Purpose:

- ground candidate generation in existing research
- import known methods and metrics
- reduce redundant exploration
- tie produced solutions back to cited external evidence

The research tool should attach evidence refs to:

- candidate packets
- evaluation packets
- recommendation packets

## Integration With Memory Tool

The memory tool should not store the entire web retrieval stream by default.

After a successful research run, store only:

- curated source refs
- linked claims that materially informed the winning solution
- benchmark refs that remain reusable

That keeps memory small.

## Curation Rule

External evidence becomes memory only after downstream usefulness is demonstrated.

Do not automatically persist every retrieved paper into long-term memory.

## Failure Modes To Avoid

- turning evidence search into memory
- storing all papers forever
- weak sources outranking strong ones
- ungrounded claim extraction
- citation noise overwhelming the actual research task

## V1 Implementation Sequence

1. define source, claim, and evidence packet schemas
2. implement source search
3. implement source fetch and normalization
4. implement claim extraction
5. implement evidence packet assembly
6. integrate with `research-tool`

## V1 Exit Criteria

V1 is successful when:

- a bounded technical problem can retrieve relevant papers or references
- those references can be normalized into structured packets
- the research tool can cite those packets while generating and evaluating candidates
- only useful evidence is promoted into memory later
