# Research Tool V1 Ranking And Search

## Objective

Define the concrete search policy, ranking model, promotion thresholds, and stopping criteria for `research-tool v1`.

This document turns the research tool from a conceptual pipeline into an implementable empirical loop.

## Scope

This spec applies only to `research-tool v1`.

It assumes:

- bounded technical problems
- `3` to `5` initial candidates
- explicit evaluations
- evidence-backed ranking

It does not try to define a general-purpose search algorithm for all future problem classes.

## Applicability Gate

This ranking and search policy is valid only for bounded technical problems with explicit evaluation criteria.

It should not be used as-is for:

- broad product strategy
- large ambiguous architecture programs without measurable criteria
- organization-wide portfolio prioritization

If the problem cannot be reduced to explicit candidate evaluation, it should be reframed or routed to a different process before using this ranker.

## Core Principle

Candidate ranking must be based primarily on observed evidence from evaluation, not on model preference alone.

The search policy must favor:

- correctness first
- bounded exploration
- efficient reuse when viable
- selective expansion of promising branches

## Search Model

V1 should use a bounded best-first empirical search loop.

### Search Stages

1. retrieve reusable prior records from memory
2. generate explicit hypothesis branches
3. run bounded candidate tree search
4. evaluate all initial candidates
5. rank all evaluated candidates
6. expand only the most promising candidates if budget remains
7. re-evaluate expanded candidates
8. re-rank the pool
9. stop when the stopping rule fires

### Search State

The runtime should track:

- `problem_id`
- `run_id`
- `candidate_pool`
- `candidate_search_tree`
- `expansion_decisions`
- `evaluated_candidate_ids`
- `expansion_count`
- `remaining_budget`
- `best_candidate_id`
- `best_score`
- `score_history`

### Initial Candidate Count

Recommended default:

- minimum: `3`
- target: `4`
- maximum: `5`

The system should not create large initial candidate populations in V1.

## Candidate Classes

Each candidate should be classified to encourage diversity.

Initial candidate classes:

- `reuse_direct`
  Adapt mostly from retrieved memory artifacts
- `reuse_hybrid`
  Combine retrieved artifacts with new synthesis
- `novel_synthesized`
  Freshly synthesized solution with minimal reuse
- `baseline_reference`
  Existing or simple baseline approach for comparison

The initial set should include at least two distinct classes when possible.

## Evaluation Gates

Before detailed ranking, each candidate should pass basic validity and evaluation checks.

### Required Validity Checks

- artifact generation completed
- output format valid
- required files or symbols present
- no immediate contract violation

Candidates that fail validity checks should remain in the pool but receive strong penalties and should not be expanded unless the pool is too sparse.

### Evaluation Packet Requirement

No candidate should be eligible for recommendation unless it has a linked `research_evaluation_packet`.

V1 evaluation can be static and contract-level, but it must still record:

- traceability
- evidence support
- feasibility priors
- artifact readiness
- blocking failures

## Recommendation Gate

Recommendation must run after candidate evaluation.

Required inputs:

- `research_candidate_packet[]`
- `research_evaluation_packet[]`
- `candidate_evaluation_summary_packet`

The ranker should:

- rank promoted candidates first
- sort promoted candidates by evaluation total score
- retain blocked candidates as rejected alternatives
- block recommendation if no candidate is promoted

## Ranking Dimensions

V1 should rank candidates on explicit dimensions.

### Positive Dimensions

- `task_fit`
  How well the candidate addresses the stated problem
- `correctness`
  How well the candidate passes required checks
- `feasibility`
  How practical the candidate is to use or adapt
- `performance`
  Runtime or benchmark quality where relevant
- `artifact_quality`
  Completeness, cleanliness, and usability of produced artifacts
- `reuse_advantage`
  Value gained from reusing known-good prior work

### Negative Dimensions

- `adaptation_cost`
  Estimated effort needed to apply the candidate to the current problem
- `risk_penalty`
  Likelihood of hidden breakage, fragility, or invalid assumptions
- `failure_penalty`
  Penalty derived from failed evaluations or contract violations

## Recommended Default Weights

These weights are for V1 and should be configurable.

- `task_fit`: `0.20`
- `correctness`: `0.25`
- `feasibility`: `0.15`
- `performance`: `0.10`
- `artifact_quality`: `0.10`
- `reuse_advantage`: `0.10`
- `adaptation_cost`: `-0.05`
- `risk_penalty`: `-0.03`
- `failure_penalty`: `-0.12`

This weighting intentionally prioritizes correctness and practical usability over novelty.

## Score Normalization

Each dimension should be normalized to `0.0` through `1.0` before weighting.

Penalty dimensions should also be normalized to `0.0` through `1.0`, then multiplied by their negative weights.

### Examples

- `correctness`
  fraction of required checks passed
- `performance`
  relative improvement against baseline or normalized benchmark score
- `artifact_quality`
  fraction of required artifact outputs present and valid
- `failure_penalty`
  scaled severity of failures, not raw failure count only

## Total Score Formula

The V1 total score should be:

`total_score = sum(weight_i * normalized_dimension_i)`

Expanded explicitly:

`total_score =`
`0.20 * task_fit`
`+ 0.25 * correctness`
`+ 0.15 * feasibility`
`+ 0.10 * performance`
`+ 0.10 * artifact_quality`
`+ 0.10 * reuse_advantage`
`- 0.05 * adaptation_cost`
`- 0.03 * risk_penalty`
`- 0.12 * failure_penalty`

The implementation should keep the weights configurable in a ranking policy object.

## Dimension Computation Guidance

### `task_fit`

Derived from:

- coverage of requested artifact targets
- relevance to stated goal
- alignment with problem constraints

### `correctness`

Derived from:

- required tests passed
- contract validation passed
- required outputs present

### `feasibility`

Derived from:

- implementation practicality
- dependency burden
- environment compatibility

### `performance`

Derived from:

- benchmark results
- runtime efficiency
- resource efficiency where relevant

### `artifact_quality`

Derived from:

- completeness
- structure
- schema compliance
- clarity of produced artifacts

### `reuse_advantage`

Derived from:

- amount of proven reusable material
- linked evaluation strength from memory
- reduction in fresh implementation load

### `adaptation_cost`

Derived from:

- estimated modification complexity
- amount of glue code or translation required
- mismatch between stored solution and current environment

### `risk_penalty`

Derived from:

- weak assumptions
- fragile dependencies
- poor evidence coverage
- hidden coupling signals

### `failure_penalty`

Derived from:

- severity-weighted failed checks
- invalid artifacts
- contract violations

## Tie-Breaking Rules

If two candidates have very similar total scores, break ties in this order:

1. higher `correctness`
2. lower `failure_penalty`
3. lower `adaptation_cost`
4. higher `reuse_advantage`
5. deterministic `candidate_id` ordering

This prevents arbitrary rank instability.

## Expansion Policy

V1 should expand only a small number of candidates after initial ranking.

### Default Expansion Rule

After the first full evaluation pass:

- sort candidates by `total_score`
- keep top `2`
- expand only candidates that:
  - pass minimum correctness threshold
  - do not have critical contract failures
  - are within the top `2`

### Expansion Types

Allowed V1 expansion actions:

- refine artifact generation
- adapt retrieved reusable artifacts more precisely
- simplify over-complex candidates
- repair failed evaluation targets

Do not branch into many speculative variants.

### Maximum Expansion Count

Recommended default:

- `2` total expansion rounds

This keeps search bounded.

## Promotion Thresholds

The research tool may mark a candidate as `recommended`, but downstream tools still make final approval decisions.

### Minimum Thresholds

A candidate is recommendable only if:

- `correctness >= 0.70`
- `task_fit >= 0.60`
- `total_score >= 0.65`
- `failure_penalty <= 0.30`
- required evidence refs are present
- no critical contract failure exists

These are V1 defaults and should be configurable.

## Candidate Disposition States

Every candidate should end in one of these states:

- `recommended`
- `viable_not_top_ranked`
- `needs_more_research`
- `failed_evaluation`
- `rejected`

The disposition should be machine-readable.

## Stopping Criteria

Stop the search when any of these are true:

### Budget Stop

- candidate generation budget exhausted
- evaluation budget exhausted
- expansion budget exhausted

### Improvement Stop

- no candidate improves the best score by at least `0.03` after an expansion round

### Quality Stop

- one candidate clearly exceeds recommendation thresholds and no remaining branch is likely to beat it within budget

### Failure Stop

- all remaining branches fail required validity or correctness gates

## Ranking Output Contract

The ranker should emit for each candidate:

- `candidate_id`
- `rank`
- `total_score`
- `score_breakdown`
- `evaluation_refs`
- `top_failures`
- `disposition`
- `expansion_eligible`

And for the overall run:

- `recommended_candidate_id`
- `recommended_score`
- `ranking_policy_id`
- `stop_reason`

## Memory-Aware Reuse Logic

When retrieved memory candidates are present, they should not automatically outrank novel candidates.

Reuse should help only when:

- prior evidence is strong
- constraints match closely
- adaptation cost is low enough

This avoids blindly preferring old solutions.

## Ranking Policy Packet

The runtime should accept a `ranking_policy` packet with:

- `policy_id`
- `dimension_weights`
- `minimum_thresholds`
- `tie_break_order`
- `expansion_top_n`
- `max_expansion_rounds`
- `minimum_improvement_delta`

This makes the implementation configurable without changing code every time.

## Observability Requirements

The runtime should record:

- per-candidate normalized dimensions
- total score per evaluation round
- expansion decisions
- stop reason
- recommendation reason

If ranking decisions cannot be reconstructed from artifacts, the system is too opaque.

## Recommended V1 Defaults

- `initial_candidate_count = 4`
- `expansion_top_n = 2`
- `max_expansion_rounds = 2`
- `minimum_improvement_delta = 0.03`
- `recommendation_total_score_threshold = 0.65`
- `recommendation_correctness_threshold = 0.70`
- `recommendation_task_fit_threshold = 0.60`

## Implementation Sequence

1. define ranking policy schema
2. define score normalization helpers
3. implement dimension calculators
4. implement total score calculator
5. implement tie-breaking rules
6. implement expansion selector
7. implement stop-rule evaluator
8. emit machine-readable ranking artifacts

## V1 Exit Criteria

This spec is implemented successfully when:

- the runtime can score all candidates deterministically
- expansion decisions are explainable and bounded
- recommendation thresholds are machine-checkable
- stop reasons are explicit
- ranking can be replayed from stored artifacts
