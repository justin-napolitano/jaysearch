# Research Candidate Evaluation V1

## Objective

Define the first bounded evaluation layer for research candidates.

This layer consumes:

- `research_problem_packet`
- `candidate_search_tree_packet`
- `research_candidate_packet[]`
- optional `evidence_packet`

It emits:

- `research_evaluation_packet[]`
- `candidate_evaluation_summary_packet`

## Why Evaluation Comes Next

The research system now has:

- problem materialization
- hypothesis branching
- candidate tree search

Without evaluation, the system still cannot distinguish:

- plausible candidates
- feasible candidates
- evidence-supported candidates
- candidates ready for recommendation

Candidate evaluation is the gate between search and recommendation.

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

The design is grounded in four research threads.

- `Self-Refine` shows that iterative feedback can improve generated outputs, but the feedback signal must be explicit enough to guide refinement: https://arxiv.org/abs/2303.17651
- `Reflexion` shows that feedback and retained context can improve agent performance across decision and coding tasks: https://arxiv.org/abs/2303.11366
- `CRITIC` shows that tool-interactive critique can improve self-correction compared with unsupported introspection: https://arxiv.org/abs/2305.11738
- `SWE-bench` shows why software candidates need task-grounded evaluation against realistic code issues rather than plausibility-only scoring: https://arxiv.org/abs/2310.06770

Design consequence:

- candidate evaluation should combine structural checks, evidence support, feasibility priors, and executable or artifact-level checks where available
- the evaluator should emit machine-readable records before any recommendation is allowed

## Hard Boundary

This slice must not become:

- candidate generation
- final recommendation
- planner
- governance
- code-writing runtime

It only evaluates candidate packets and records what is known.

## Evaluation Model

V1 uses bounded static and contract-level evaluation.

It does not require full execution of candidate code.

Evaluation dimensions:

- `contract_completeness`
- `traceability`
- `evidence_support`
- `feasibility`
- `artifact_readiness`
- `risk_level`

The output should be explicit about whether a score is:

- observed from artifacts
- inferred from packet content
- missing and therefore penalized

## Evaluation Gates

A candidate should be blocked from recommendation if:

- it does not trace to a source hypothesis
- it has no candidate family
- it has no approach summary
- it has no proposed changes or artifact target
- it has unresolved high-risk feasibility priors and no evidence support

Blocked candidates still receive evaluation packets.

## New Packet

### `candidate_evaluation_summary_packet`

Purpose:

- summarize evaluation results for one candidate search run

Required fields:

- all `packet_base` fields
- `problem_id`
- `candidate_search_tree_ref`
- `evaluation_packet_refs`
- `promoted_candidate_ids`
- `blocked_candidate_ids`
- `evaluation_policy`

## `research_evaluation_packet` Tightening

Required fields should include:

- all `packet_base` fields
- `evaluation_id`
- `problem_id`
- `candidate_id`
- `source_hypothesis_id`
- `evaluation_method`
- `metrics`
- `failures`
- `warnings`
- `artifact_refs`
- `evidence_refs`
- `promotion_status`

## Scoring

V1 should compute a simple normalized score:

- `contract_completeness`: `0.0` to `1.0`
- `traceability`: `0.0` to `1.0`
- `evidence_support`: `0.0` to `1.0`
- `feasibility`: `0.0` to `1.0`
- `artifact_readiness`: `0.0` to `1.0`
- `risk_penalty`: `0.0` to `1.0`

Promotion rule:

- candidate can be promoted if total score is at least `0.65`
- candidate must not have blocking failures

V1 promotion does not mean final recommendation.

It only means the candidate is eligible for ranking and recommendation.

## Acceptance

V1 is successful when:

- every generated candidate receives an evaluation packet
- evaluation records trace back to hypotheses and evidence
- blocked candidates are explicit
- promoted candidates are explicit
- recommendation is impossible without evaluation records
