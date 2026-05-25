# Research Hypothesis Branching V1

## Objective

Add a first bounded branching layer inside `research-tool` so one `research_problem_packet` can produce multiple explicit hypothesis branches before candidate generation.

This is the first concrete improvement slice for the research system.

## Why This Slice Is First

Hypothesis branching is upstream of:

- candidate family diversity
- evaluation comparability
- recommendation traceability

If research still starts from one flattened problem interpretation, the system will keep producing narrow and weakly differentiated candidate sets.

## Hard Boundary

This slice must not become:

- full research execution
- planner logic
- evidence search
- governance

It only does:

- branch the research problem into explicit bounded hypotheses
- preserve traceability back to the source problem and evidence

## New Packet

### `research_hypothesis_packet`

Purpose:

- one explicit research branch derived from a `research_problem_packet`

Required fields:

- all `packet_base` fields
- `hypothesis_id`
- `problem_id`
- `hypothesis_family`
- `hypothesis_statement`
- `approach_outline`
- `evaluation_focus`
- `evidence_refs`
- `branch_rank`
- `prune_conditions`

Recommended optional fields:

- `source_question_refs`
- `source_problem_ref`
- `risk_notes`
- `expected_advantages`
- `expected_tradeoffs`

## Initial Hypothesis Families

V1 should support a small fixed family set:

- `reuse_direct`
- `reuse_hybrid`
- `novel_synthesized`
- `baseline_reference`

The brancher should emit at least:

- `baseline_reference`
- one non-baseline branch

when the problem has enough information to support that.

## Branching Rules

The brancher should:

1. preserve the original `problem_id`
2. derive stable `hypothesis_id`s
3. keep each hypothesis materially distinct
4. map evidence and constraints into each branch
5. define what would cause the branch to be pruned later

V1 does not need to score hypotheses deeply. It only needs to materialize a bounded and explicit branch set.

## Minimum V1 Output

For a normal bounded technical problem, the brancher should target:

- minimum: `2` branches
- default: `3` branches
- maximum: `4` branches

The brancher should not emit large branch populations in V1.

## Example Flow

`research_problem_packet`
-> `materialize_research_hypotheses`
-> `research_hypothesis_packet[]`
-> candidate generation per surviving branch

## Acceptance

V1 is successful when:

- one `research_problem_packet` can produce explicit branches
- each branch is typed and traceable
- the output is machine-readable
- the output is bounded enough for later candidate generation
