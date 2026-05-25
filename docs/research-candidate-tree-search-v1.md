# Research Candidate Tree Search V1

## Objective

Define a bounded tree-search layer for candidate generation inside `research-tool`.

This layer consumes:

- `research_problem_packet`
- `research_hypothesis_packet[]`
- optional `evidence_packet`

It emits:

- `candidate_search_tree_packet`
- `candidate_expansion_decision_packet[]`
- `research_candidate_packet[]`

## Why Tree Search

The research system should not jump directly from a problem to a single smart answer.

It should:

- branch from hypotheses
- generate candidate families
- attach evidence
- keep expansion decisions explicit
- preserve the path that led to each candidate

This creates a reviewable search structure before evaluation and ranking.

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

This design follows the same evidence-backed pattern used by the design-review automation layer:

- iterative refinement can improve outputs when feedback is explicit
- feedback and retained context improve downstream decisions
- tool-assisted critique is stronger than unsupported self-reflection

Relevant sources:

- `Self-Refine`: https://arxiv.org/abs/2303.17651
- `Reflexion`: https://arxiv.org/abs/2303.11366
- `CRITIC`: https://arxiv.org/abs/2305.11738

The design consequence is:

- tree search should record why branches were expanded or pruned
- evidence should be attached to candidate paths
- later evaluation should score candidates from observed results, not model preference alone

## Hard Boundary

This slice must not become:

- full empirical evaluation
- final ranking
- planning
- governance
- open-ended autonomous search

It only creates a bounded candidate tree and initial candidate packets.

## Search Model

V1 should use bounded breadth-first expansion over hypotheses.

Default limits:

- max depth: `2`
- max candidates per hypothesis: `2`
- max total candidates: `8`

The tree should start with:

- one root node for the research problem
- one child node per hypothesis
- one or more candidate nodes under each hypothesis

## Candidate Families

Candidate family should normally inherit from the source hypothesis family:

- `baseline_reference`
- `reuse_direct`
- `reuse_hybrid`
- `novel_synthesized`

The system may emit more than one candidate per hypothesis when:

- evidence supports multiple implementation paths
- feasibility is uncertain
- the branch is high priority

## Evidence Attachment

Evidence should be carried forward as refs, not re-searched here.

Allowed inputs:

- `evidence_packet`
- `research_hypothesis_packet.evidence_refs`
- problem-level references

The candidate tree should record:

- evidence refs used for each branch
- unsupported branches
- branches requiring later evidence search

## Feasibility

V1 should not attempt full feasibility evaluation.

It should emit feasibility priors:

- `expected_complexity`
- `dependency_risk`
- `implementation_risk`
- `evidence_strength`

Later evaluation and ranking can replace priors with observed metrics.

## New Packets

### `candidate_search_tree_packet`

Purpose:

- machine-readable representation of the bounded candidate generation tree

Required fields:

- all `packet_base` fields
- `problem_id`
- `root_node_id`
- `tree_nodes`
- `tree_edges`
- `search_policy`
- `candidate_packet_refs`

### `candidate_expansion_decision_packet`

Purpose:

- record why a hypothesis or candidate branch was expanded, pruned, or deferred

Required fields:

- all `packet_base` fields
- `decision_id`
- `problem_id`
- `source_node_id`
- `decision`
- `reason`
- `evidence_refs`
- `resulting_node_refs`

## Research Candidate Packet Implications

Candidate packets should include:

- `candidate_id`
- `problem_id`
- `source_hypothesis_id`
- `candidate_family`
- `approach_summary`
- `implementation_intent`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `expected_changes`
- `non_goals`
- `handoff_requirements`
- `planner_entry_notes`
- `assumptions`
- `proposed_changes`
- `artifact_refs`
- `source_type`
- `evidence_refs`
- `feasibility_priors`

`implementation_intent` should include:

- `summary`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `handoff_requirements`

Generic candidate-family labels are not enough. A candidate must state what downstream contracts, runtime paths, docs, validations, and handoff requirements it expects to affect.

## Acceptance

V1 is successful when:

- one research problem plus hypotheses produces a bounded candidate search tree
- every candidate traces to a hypothesis
- candidate family diversity is preserved
- every candidate includes implementation-specific intent
- expansion decisions are recorded
- output is machine-readable and ready for evaluation
