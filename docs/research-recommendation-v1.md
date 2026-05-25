# Research Recommendation V1

## Objective

Define the evaluation-backed recommendation layer for `research-tool`.

This layer consumes:

- `research_problem_packet`
- `candidate_search_tree_packet`
- `research_candidate_packet[]`
- `research_evaluation_packet[]`
- `candidate_evaluation_summary_packet`

It emits:

- `ranked_candidate_packet[]`
- `research_recommendation_packet`

## Why This Layer Exists

Recommendation is the last research-owned step before selection and planning.

It must not be a plausibility summary.

It should be a traceable decision over evaluated candidates.

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

This design is grounded in:

- `Self-Refine`, because iterative feedback improves outputs when feedback is explicit: https://arxiv.org/abs/2303.17651
- `Reflexion`, because feedback and retained context improve agent decisions: https://arxiv.org/abs/2303.11366
- `CRITIC`, because tool-assisted critique improves correction over unsupported introspection: https://arxiv.org/abs/2305.11738
- `SWE-bench`, because software candidates should be evaluated against task-grounded evidence rather than plausibility alone: https://arxiv.org/abs/2310.06770

The design consequence is:

- recommendation must consume evaluation records
- recommendation must preserve rejected alternatives
- recommendation must explain why the winner beat the alternatives

## Hard Boundary

This layer must not:

- choose final build scope
- generate implementation DAGs
- execute code
- perform governance

It only recommends a candidate.

Final selection still belongs to:

- human gate
- governance-assisted selection gate
- runner-configured selection policy

## Ranking Inputs

Each ranked candidate should use:

- evaluation total score
- promotion status
- failures and warnings
- evidence refs
- feasibility priors
- candidate family
- source hypothesis
- implementation intent

V1 should not rank candidates that lack evaluation records.

## Ranking Rule

V1 should:

1. load all candidate packets
2. load all evaluation packets
3. reject candidates without evaluation records
4. rank promoted candidates first
5. sort by evaluation total score
6. include blocked candidates after promoted candidates for traceability
7. emit the recommended candidate as the top promoted candidate

If no candidates are promoted, the recommendation should block instead of recommending.

## `ranked_candidate_packet` Tightening

Minimum fields:

- `candidate_id`
- `problem_id`
- `rank`
- `total_score`
- `score_breakdown`
- `strengths`
- `weaknesses`
- `promotion_status`
- `evaluation_ref`
- `evidence_refs`
- `source_hypothesis_id`
- `implementation_intent`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `expected_changes`
- `non_goals`
- `handoff_requirements`
- `planner_entry_notes`

## `research_recommendation_packet` Tightening

Required fields:

- all `packet_base` fields
- `problem_id`
- `candidate_search_tree_ref`
- `evaluation_summary_ref`
- `evaluation_refs`
- `ranked_candidates`
- `recommended_candidate_id`
- `recommendation_reason`
- `winner_evidence_refs`
- `rejected_candidate_summaries`
- `open_questions`
- `artifact_refs`
- `evidence_refs`

## Acceptance

V1 is successful when:

- recommendation cannot be emitted without evaluation records
- every ranked candidate has an evaluation ref
- every ranked candidate preserves implementation intent from the source candidate
- rejected candidates remain visible
- planner receives a stronger research output
- `selected_solution_scope` remains the authoritative post-research selection contract
