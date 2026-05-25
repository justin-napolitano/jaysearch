# Research Tool V1

## Objective

Define a standalone research API that can take a bounded technical problem, generate multiple candidate solutions, evaluate them empirically, and emit a ranked recommendation packet for downstream tools.

This tool is not a planner and not a governance engine.

Its job is to:

- understand a bounded problem packet
- retrieve relevant external evidence and papers
- retrieve relevant prior reusable records from memory
- generate multiple candidate approaches
- synthesize candidate artifacts
- run bounded evaluations
- rank the candidates using explicit scoring
- emit a recommendation packet

## Tool Boundary

The intended tool split is:

- `evidence-search-tool`
  external research retrieval and evidence normalization
- `memory-tool`
  retrieval and reusable record storage
- `research-tool`
  candidate generation, evaluation, and ranking
- `planner-tool`
  DAG generation from a selected solution
- `governance-tool`
  approval, validation, and execution control

The research tool should produce evidence and recommendations. It should not decide final execution authority.

## Hard Boundary

The research tool must not absorb evidence retrieval as an internal hidden subsystem.

For V1 and beyond:

- external literature and benchmark retrieval belong to `evidence-search-tool`
- reusable internal solved-case retrieval belong to `memory-tool`
- candidate generation, evaluation, and ranking belong to `research-tool`

If research begins directly owning paper search, source normalization, or persistent solved-case storage, the boundary has failed and the tool is becoming too large again.

## V1 Use Case

V1 should support one narrow class of work:

- compare bounded implementation strategies for a technical problem
- generate a small number of candidate solutions
- evaluate them with explicit checks
- recommend the strongest candidate

Examples of good V1 problems:

- compare two to five design approaches for a subsystem
- compare implementation patterns for a feature
- compare reusable prior solutions against new synthesized approaches

Examples of bad V1 problems:

- open-ended product ideation
- broad business strategy
- unlimited autonomous project execution
- organization-wide planning

## Non-Goals

V1 should not become:

- a giant general-purpose agent swarm
- a hidden orchestration runtime
- a planner
- a governance workflow engine
- a long-term memory system

It should stay tightly scoped to empirical solution search and evaluation.

## End-To-End Flow

1. accept `research_problem_packet`
2. normalize and validate the problem
3. call `evidence-search-tool` for relevant external papers, benchmarks, and methods
4. call `memory-tool` for similar prior problems and reusable artifacts
5. materialize explicit research hypotheses
6. run bounded candidate tree search
7. synthesize or reference candidate artifacts
8. run bounded evaluations for each candidate
9. aggregate metrics and failures
10. rank candidates using explicit scoring
11. emit `research_recommendation_packet`
12. optionally store winning results back into memory

The evidence-search step should be the default path for bounded technical research problems unless the workflow explicitly declares that no external evidence retrieval is needed.

## API Surface

V1 should remain small.

### `define_problem`

Purpose:

- validate and normalize a bounded problem packet

Input:

- `research_problem_packet`

Output:

- `normalized_problem_packet`
- `validation_results`

### `generate_candidates`

Purpose:

- create a bounded set of candidate solution approaches

Input:

- `normalized_problem_packet`
- `research_hypothesis_packet[]`
- `retrieved_memory_context`
- `generation_policy`

Output:

- `research_candidate_packet[]`
- `candidate_search_tree_packet`
- `candidate_expansion_decision_packet[]`

### `evaluate_candidates`

Purpose:

- run explicit evaluations for each candidate

Input:

- `normalized_problem_packet`
- `candidate_search_tree_packet`
- `research_candidate_packet[]`
- `evaluation_policy`

Output:

- `research_evaluation_packet[]`
- `candidate_evaluation_summary_packet`

### `rank_candidates`

Purpose:

- score and rank candidate solutions based on observed evidence

Input:

- `normalized_problem_packet`
- `research_candidate_packet[]`
- `research_evaluation_packet[]`
- `candidate_evaluation_summary_packet`
- `ranking_policy`

Output:

- `ranked_candidate_packet[]`
- `recommended_candidate_id`

### `emit_recommendation`

Purpose:

- package the final ranked output for downstream tools

Input:

- `normalized_problem_packet`
- `ranked_candidate_packet[]`
- `recommended_candidate_id`

Output:

- `research_recommendation_packet`

## Primary Packets

### `research_problem_packet`

Purpose:

- canonical input contract for one research task

Minimum fields:

- `problem_id`
- `title`
- `goal`
- `problem_statement`
- `constraints`
- `repo_context`
- `artifact_targets`
- `evaluation_criteria`
- `search_budget`
- `output_requirements`

Recommended optional fields:

- `language`
- `runtime_environment`
- `allowed_tools`
- `disallowed_tools`
- `baseline_artifact_refs`
- `reference_implementations`

### `research_hypothesis_packet`

Purpose:

- one explicit research branch derived from a canonical research problem

Minimum fields:

- `hypothesis_id`
- `problem_id`
- `hypothesis_family`
- `hypothesis_statement`
- `approach_outline`
- `evaluation_focus`
- `evidence_refs`
- `branch_rank`
- `prune_conditions`

### `research_candidate_packet`

Purpose:

- one candidate solution approach

Minimum fields:

- `candidate_id`
- `problem_id`
- `source_hypothesis_id`
- `candidate_family`
- `approach_summary`
- `assumptions`
- `proposed_changes`
- `artifact_refs`
- `source_type`
- `evidence_refs`
- `feasibility_priors`

Recommended optional fields:

- `derived_from_memory_record_ids`
- `novelty_level`
- `risk_notes`

### `candidate_search_tree_packet`

Purpose:

- representation of the bounded candidate search tree

Minimum fields:

- `problem_id`
- `root_node_id`
- `tree_nodes`
- `tree_edges`
- `search_policy`
- `candidate_packet_refs`

### `candidate_expansion_decision_packet`

Purpose:

- one recorded expansion, prune, or defer decision during candidate search

Minimum fields:

- `decision_id`
- `problem_id`
- `source_node_id`
- `decision`
- `reason`
- `evidence_refs`
- `resulting_node_refs`

### `research_evaluation_packet`

Purpose:

- one candidate’s evaluation record

Minimum fields:

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

Recommended optional fields:

- `execution_time_ms`
- `resource_cost`
- `stability_summary`

### `candidate_evaluation_summary_packet`

Purpose:

- summary of candidate evaluation results for one search tree

Minimum fields:

- `problem_id`
- `candidate_search_tree_ref`
- `evaluation_packet_refs`
- `promoted_candidate_ids`
- `blocked_candidate_ids`
- `evaluation_policy`

### `ranked_candidate_packet`

Purpose:

- ranked representation of one candidate with explicit scoring breakdown

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

### `research_recommendation_packet`

Purpose:

- downstream handoff from research into planner or governance

Minimum fields:

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

## Downstream Handoff Rule

`research_recommendation_packet` is not itself the authoritative build-selection contract.

It must be followed by a selection step that produces:

- `selected_solution_scope`

Downstream planner entry should consume the selected-solution contract, not the raw recommendation packet directly.

Recommendation must be evaluation-backed:

- every ranked candidate must reference a `research_evaluation_packet`
- the recommendation must reference a `candidate_evaluation_summary_packet`
- no promoted recommendation should be emitted when all candidates are blocked

## Candidate Generation Model

V1 should generate a small bounded set of candidates.

Recommended default:

- `3` to `5` candidates

Candidate sources may include:

- adapted prior solutions from memory
- direct synthesized solutions
- hybrid solutions that combine retrieved artifacts and new code

Candidate generation should force diversity across:

- architecture choice
- implementation strategy
- reuse vs new build posture

Avoid generating many superficial variants of the same idea.

## Evaluation Model

V1 evaluations must be explicit and bounded.

Allowed evaluation methods:

- unit or integration tests
- static checks
- benchmark or timing checks
- contract validation
- artifact completeness checks
- comparison against baseline metrics

Each problem packet should specify the evaluation criteria.

Example criteria:

- test pass rate
- runtime performance
- implementation completeness
- code footprint
- error rate
- schema compliance

## Search Policy

V1 should not be a full unconstrained swarm. It should be a bounded empirical search loop.

Recommended V1 search policy:

- retrieve reusable context from memory
- generate initial candidate set
- evaluate all candidates once
- expand only the top `N` candidates if budget remains
- stop when no material improvement appears or budget is exhausted

This is a simplified best-first search posture. It is enough for V1 without building a large general tree-search engine immediately.

## Ranking Model

Ranking must be explicit and based on observed evidence, not only model preference.

V1 ranking dimensions should be:

- `task_fit`
- `correctness`
- `feasibility`
- `performance`
- `artifact_quality`
- `adaptation_cost`
- `risk_penalty`

Conceptual scoring shape:

`total_score = task_fit + correctness + feasibility + performance + artifact_quality - adaptation_cost - risk_penalty`

The exact weights should be configurable through `ranking_policy`.

## Ranking Output Requirements

Every ranked candidate should include:

- numeric total score
- per-dimension score breakdown
- key evaluation evidence refs
- top failure modes
- whether the candidate is promotable for downstream use

The system should never emit only prose like “candidate A seems best.”

## Promotion Rule

The research tool should emit a recommendation, not a final approval.

Its internal promotion rule should only identify whether a candidate is strong enough to recommend.

Suggested V1 criteria:

- required evaluations completed
- minimum correctness threshold met
- minimum total score met
- no critical contract failure
- evidence refs present

That output becomes input for planner or governance, depending on the workflow.

## Stopping Rule

Stop research when one of these is true:

- search budget exhausted
- maximum candidate expansions reached
- no material score improvement after `N` expansions
- all remaining candidates fail required evaluation gates

This keeps the tool bounded.

## Integration With Memory Tool

The research tool should call memory in two places.

### Before Candidate Generation

Use:

- `search_records`
- `rank_reusable_candidates`
- `get_related_records`

Purpose:

- find similar solved problems
- import reusable solution artifacts
- reduce unnecessary new code generation

### After Recommendation

Use:

- `store_record`
- `link_records`

Purpose:

- preserve strong winning candidates
- preserve reusable evaluations
- preserve reusable generated artifacts

## Integration With Evidence Search Tool

The research tool should call evidence search before candidate generation and optionally during evaluation design.

### Before Candidate Generation

Use:

- `search_sources`
- `fetch_source`
- `extract_claims`
- `assemble_evidence_packet`

Purpose:

- ground the candidate set in relevant papers and prior methods
- import benchmark ideas and known evaluation criteria
- link proposed candidates to cited external evidence

### During Recommendation Emission

The recommendation packet should include:

- source refs
- claim refs
- benchmark refs

This keeps the generated code and ranking tied to explicit empirical or literature evidence.

The evidence-search integration is not optional by default for research problems that can benefit from external methods, papers, or benchmark references.

## Integration With Planner Tool

The planner should receive only:

- selected candidate data
- supporting artifacts
- explicit constraints
- open questions

The planner should not receive raw internal search state unless explicitly needed.

## Integration With Governance Tool

The governance tool may consume:

- recommendation packet
- evidence refs
- evaluation summaries

The governance tool should independently decide what is allowed to proceed.

## Failure Modes To Avoid

- generating candidates without diversity
- ranking without empirical evidence
- evaluating too many low-value branches
- mixing planner logic into research logic
- mixing governance rules into research scoring
- storing raw exploratory noise as reusable truth

## V1 Implementation Sequence

1. define problem, candidate, evaluation, ranked-candidate, and recommendation schemas
2. implement problem normalization
3. implement memory retrieval adapter
4. implement bounded candidate generation
5. implement evaluation runner
6. implement ranking engine
7. implement recommendation emitter
8. store winning outputs back into memory

## V1 Exit Criteria

V1 is successful when:

- one bounded technical problem can be processed end-to-end
- at least `3` candidates are compared
- candidates are ranked using explicit evidence-backed scoring
- the output packet is clean enough for planner or governance consumption
- memory retrieval measurably reduces duplicate work or code generation
