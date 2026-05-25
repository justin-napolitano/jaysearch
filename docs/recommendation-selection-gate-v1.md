# Recommendation Selection Gate V1

## Objective

Define the handoff gate from `research_recommendation_packet` to `selected_solution_scope`.

This gate is the safety boundary between research and planning.

Research may recommend a candidate. Planner may only consume a selected scope.

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

The gate is informed by:

- `CRITIC`, because critique and correction should be grounded in tools and artifacts, not unsupported introspection
- `SWE-bench`, because software candidates need task-grounded evaluation before downstream execution planning
- W3C PROV, because the selected scope must preserve provenance from recommendation, evidence, and evaluation records
- mechanism-design sources, because the handoff is an incentive boundary: research cannot authorize execution by recommendation alone

## Inputs

Required:

- `research_recommendation_packet`

The recommendation must include:

- `problem_id`
- `recommended_candidate_id`
- `ranked_candidates`
- `evaluation_summary_ref`
- `evaluation_refs`
- selected candidate with `promotion_status = promoted`
- selected candidate with `evaluation_ref`
- selected candidate with `evidence_refs`

Optional operator inputs:

- selected candidate override
- selection reason override
- in-scope entries
- out-of-scope entries
- acceptance checks

## Output

- `selected_solution_scope`

The selected scope must preserve:

- source recommendation ref
- selected candidate id
- selection policy
- evidence refs
- artifact refs
- assumptions
- risks
- acceptance checks

## Hard Boundary

This gate must not:

- generate implementation DAGs
- plan execution slices
- mutate research rankings
- silently select blocked candidates
- allow planner to consume raw recommendations

## Selection Policy

V1 policy id:

- `evaluation_backed_recommendation_gate_v1`

Rules:

1. load the recommendation packet
2. require `packet_type = research_recommendation_packet`
3. require evaluation summary and evaluation refs
4. require ranked candidates
5. find selected candidate from override or recommended candidate
6. require selected candidate to be ranked
7. require selected candidate to be promoted
8. require selected candidate evaluation ref
9. require selected candidate evidence refs
10. emit `selected_solution_scope`

## DAG

Canonical DAG:

- `artifacts/planner/research/recommendation-selection-gate-v1-dag.json`

## Acceptance

The gate is acceptable when:

- unevaluated recommendations block
- missing ranked candidates block
- unpromoted selected candidates block
- selected candidate missing evaluation ref blocks
- a real recommendation packet materializes a selected scope
- `design-iteration` reports no findings
