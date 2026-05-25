# Memory Tool V1

## Objective

Define a standalone memory API that stores reusable solved-case information and returns ranked reusable records to other tools.

This tool is not a planner, not a governance engine, and not a research runtime.

Its purpose is to:

- store reusable records
- retrieve similar prior records
- expand linked artifacts and evidence
- rank likely reuse candidates for a new task

## Role In The System

The intended tool boundaries are:

- `research-tool`
  Generates and evaluates candidate solutions
- `memory-tool`
  Stores and retrieves prior reusable knowledge
- `planner-tool`
  Builds scoped DAGs from selected solutions
- `governance-tool`
  Applies approval, validation, and execution controls

The memory tool is a support layer for the others. It is never the source of final authority.

## Boundary With Evidence Search

The memory tool stores curated internal reusable records.

The evidence-search tool retrieves external papers, benchmarks, and references.

Only evidence that materially contributed to a useful solution should be curated into memory later as linked references. Memory should not become a dump of all external search results.

## Non-Goals

V1 should not become:

- a giant universal graph
- a chat transcript archive
- hidden runtime state
- an autonomous reasoning engine
- a canonical workflow tracker

V1 is a retrieval system for curated reusable records.

## Admission Policy

Memory should be default-deny for long-term storage.

Only admit records that are likely to be reusable:

- solved problems
- high-value rejected alternatives with clear lessons
- reusable code artifacts
- reusable evaluation harnesses
- reusable planner fragments
- curated linked evidence that materially informed a useful solution

Do not automatically admit:

- all intermediate candidate variants
- all exploratory failures
- raw chat transcripts
- every external source retrieved during evidence search
- giant run-state blobs

If retrieval quality degrades because of volume, curation policy should tighten before storage volume expands.

## Core Use Cases

### Use Case 1: Similar Problem Search

Input:

- new problem statement
- constraints
- repo or code context

Output:

- ranked prior `problem_record` entries
- linked `solution_record` entries

### Use Case 2: Reusable Solution Search

Input:

- current technical problem
- desired artifact type
- constraints

Output:

- ranked reusable `solution_record` entries
- linked code, prompts, schemas, or harnesses

### Use Case 3: Artifact Expansion

Input:

- record id

Output:

- related artifacts
- related evaluations
- provenance links

### Use Case 4: Reuse Ranking

Input:

- current problem packet
- retrieved candidate records

Output:

- ranked reusable candidates
- explanation of ranking factors

## API Surface

V1 should stay small.

### `store_record`

Purpose:

- persist one typed memory record

Input:

- `record_type`
- `record`

Output:

- `record_id`
- `status`
- `version`

### `get_record`

Purpose:

- fetch one stored record by id

Input:

- `record_id`

Output:

- `record_type`
- `record`
- `linked_record_ids`

### `search_records`

Purpose:

- retrieve candidate records using lexical, metadata, and optional semantic matching

Input:

- `query`
- `record_types`
- `filters`
- `top_k`

Output:

- `matches`
- `search_metadata`

### `link_records`

Purpose:

- create lightweight reusable relationships between records

Input:

- `from_id`
- `to_id`
- `relation`
- `weight`

Output:

- `link_id`
- `status`

### `get_related_records`

Purpose:

- expand a record into linked reusable context

Input:

- `record_id`
- `relation_filters`
- `depth`

Output:

- `records`
- `edges`

### `rank_reusable_candidates`

Purpose:

- re-rank retrieved memory candidates for the current problem

Input:

- `current_problem_packet`
- `candidate_record_ids` or `candidate_records`
- `ranking_policy`

Output:

- `ranked_candidates`
- `ranking_explanations`

## Record Types

### `problem_record`

Purpose:

- normalized representation of a previously solved or investigated problem

Minimum fields:

- `problem_id`
- `title`
- `summary`
- `constraints`
- `context_tags`
- `fingerprint`
- `status`
- `created_at`

### `solution_record`

Purpose:

- reusable solution pattern or winning candidate

Minimum fields:

- `solution_id`
- `problem_id`
- `summary`
- `approach_type`
- `artifact_refs`
- `evaluation_refs`
- `reusability_tags`
- `adaptation_notes`
- `status`

### `artifact_record`

Purpose:

- reusable concrete object such as code, prompt, schema, DAG fragment, or evaluation harness

Minimum fields:

- `artifact_id`
- `artifact_type`
- `path_or_uri`
- `symbol_refs`
- `language`
- `inputs`
- `outputs`

### `evaluation_record`

Purpose:

- empirical evidence for whether a solution worked

Minimum fields:

- `evaluation_id`
- `solution_id`
- `method`
- `metrics`
- `environment`
- `result`
- `notes`

### `plan_fragment_record`

Purpose:

- reusable planning pattern, subgraph, or execution slice

Minimum fields:

- `plan_fragment_id`
- `summary`
- `node_refs`
- `dependency_pattern`
- `artifact_refs`
- `constraints`

### `policy_record`

Purpose:

- reusable governance or approval pattern

Minimum fields:

- `policy_id`
- `summary`
- `policy_type`
- `applicability_tags`
- `artifact_refs`

## Relationship Model

Use lightweight edges, not a monolithic graph document.

Supported initial relations:

- `solves`
- `uses`
- `validated_by`
- `derived_from`
- `similar_to`
- `supersedes`
- `adapted_into`

Each edge should include:

- `from_id`
- `to_id`
- `relation`
- `weight`
- `created_at`

## Storage Model

V1 should use a hybrid local-first model:

1. canonical typed record store
2. lightweight relation index
3. searchable text index
4. optional semantic index behind an abstraction

Recommended first implementation:

- `SQLite` for canonical records and edge tables
- `FTS` for text search
- optional embeddings later

Avoid one giant JSON graph file.

## Retrieval Pipeline

Retrieval should be staged.

### Stage 1: Recall

Find candidate prior records using:

- lexical search
- tags
- constraints
- repo or language filters

### Stage 2: Filter

Drop candidates that do not fit:

- language/runtime constraints
- architecture constraints
- artifact type requirements
- validation quality requirements

### Stage 3: Expand

Load linked:

- solutions
- artifacts
- evaluations
- plan fragments

### Stage 4: Re-Rank

Apply explicit reuse scoring for the current task.

### Stage 5: Return

Return ranked candidates plus provenance and linked artifacts.

## Ranking Model

Do not rank only by semantic similarity.

V1 ranking dimensions should be:

- `problem_similarity`
- `constraint_match`
- `artifact_reusability`
- `prior_success_rate`
- `evidence_strength`
- `adaptation_cost`
- `recency`

Conceptual scoring shape:

`reuse_score = similarity + constraint_match + evidence_strength + success_rate + recency - adaptation_cost`

The exact weights should be configurable.

## Ranking Output Contract

Each ranked candidate should return:

- `record_id`
- `record_type`
- `reuse_score`
- `score_breakdown`
- `matched_constraints`
- `missing_constraints`
- `top_artifact_refs`
- `top_evaluation_refs`
- `adaptation_notes`

## Curation Rules

Only store memory that is likely to be reusable.

Store:

- solved problems
- winning or high-value rejected solutions
- reusable code artifacts
- reusable evaluation harnesses
- reusable planner fragments

Do not store:

- all intermediate thoughts
- every failed draft
- raw chat logs by default
- giant nested runtime blobs

## Integration With Research Tool

The `research-tool` should call memory in two places:

### Before Search

Use:

- `search_records`
- `rank_reusable_candidates`

Purpose:

- see if a similar problem was already solved
- import reusable artifacts before generating new candidates

### After A Good Result

Use:

- `store_record`
- `link_records`

Purpose:

- preserve good solutions, evaluations, and artifacts for future reuse

## Integration With Planner Tool

The `planner-tool` should retrieve:

- reusable plan fragments
- reusable dependency patterns
- reusable artifact bundles

It should not treat memory output as canonical DAG state.

## Integration With Governance Tool

The `governance-tool` may retrieve:

- precedent solutions
- prior evaluation evidence
- reusable policy objects

It should still make fresh approval decisions in the current context.

## Failure Modes To Avoid

- memory becoming hidden authority
- unbounded graph growth
- low-signal records dominating search results
- embeddings replacing explicit filtering
- reused code without linked evaluation evidence
- stale solutions outranking validated recent ones

## V1 Implementation Sequence

1. define record schemas
2. define API request and response packets
3. implement typed storage
4. implement lexical search and metadata filters
5. implement relation expansion
6. implement explicit reuse ranking
7. integrate with `research-tool`

## V1 Exit Criteria

V1 is successful when:

- a new problem can retrieve similar prior solved cases
- retrieved candidates can be ranked for reuse
- linked artifacts and evaluations can be expanded deterministically
- the research tool can store new winning solutions for future reuse
- the system remains small and queryable
