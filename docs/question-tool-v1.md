# Question Tool V1

## Objective

Define a standalone question-generation API that takes project context, identifies bounded problems worth researching, ranks those questions, and emits structured question packets for downstream evidence and research tools.

This tool is not evidence search, not research execution, and not planning.

Its purpose is to:

- turn vague project context into strong research questions
- identify multiple bounded subproblems in a large project
- rank which questions are worth pursuing first
- emit machine-readable question packets

## Role In The System

The intended split is:

- `question-tool`
  derive and rank research questions
- `evidence-search-tool`
  retrieve external papers, websites, and benchmarks
- `memory-tool`
  retrieve and store reusable solved-case knowledge
- `research-tool`
  generate and evaluate candidate solutions
- `planner-tool`
  turn selected solutions into implementation DAGs
- `governance-tool`
  control execution legality and readiness
- `orchestration-runner`
  coordinate runs across tools

The question tool is the front door of the system.

## Core Principle

Large projects should not be researched as one giant undefined problem.

They should be decomposed first into bounded questions such as:

- what needs to be decided
- what is uncertain
- what is blocking progress
- what alternative approaches matter

The quality of downstream research depends heavily on the quality of the question set.

## V1 Use Case

V1 should support:

- one project context packet
- derivation of multiple bounded research questions
- ranking of those questions
- emission of question packets ready for evidence search and research

## Non-Goals

V1 should not become:

- a planner
- a full portfolio manager
- a broad business strategy engine
- a giant ontology of all possible question types

It should stay focused on deriving actionable research questions from project context.

## End-To-End Flow

1. accept `project_context_packet`
2. normalize goals, constraints, and ambiguity areas
3. identify candidate question areas
4. turn those into bounded question candidates
5. rank question candidates
6. emit `research_question_packet[]`

## API Surface

### `ingest_project_context`

Purpose:

- validate and normalize project context

Input:

- `project_context_packet`

Output:

- `normalized_project_context_packet`
- `validation_results`

### `derive_question_candidates`

Purpose:

- identify bounded research questions implied by the project context

Input:

- `normalized_project_context_packet`

Output:

- `question_candidate_packet[]`

### `rank_questions`

Purpose:

- rank which questions are most worth investigating first

Input:

- `question_candidate_packet[]`
- `question_ranking_policy`

Output:

- `ranked_question_packet[]`

### `emit_question_packets`

Purpose:

- produce downstream-ready research question packets

Input:

- `ranked_question_packet[]`

Output:

- `research_question_packet[]`

## Primary Packets

### `project_context_packet`

Purpose:

- canonical question-tool input

Minimum fields:

- `project_id`
- `title`
- `project_goal`
- `current_state`
- `constraints`
- `known_unknowns`
- `target_outcomes`

Recommended optional fields:

- `repo_context`
- `stakeholder_context`
- `existing_artifact_refs`
- `timeline_constraints`
- `non_goals`

### `question_candidate_packet`

Purpose:

- one candidate research question

Minimum fields:

- `question_id`
- `project_id`
- `question_text`
- `question_type`
- `problem_area`
- `decision_target`
- `constraints`

### `ranked_question_packet`

Purpose:

- ranked representation of one candidate question

Minimum fields:

- `question_id`
- `rank`
- `priority_score`
- `score_breakdown`
- `why_now`
- `downstream_value`

### `research_question_packet`

Purpose:

- downstream-ready question for evidence-search and research

Minimum fields:

- `question_id`
- `project_id`
- `question_text`
- `question_type`
- `goal`
- `decision_target`
- `decision_consequence`
- `blocked_work_if_unanswered`
- `constraints`
- `evaluation_targets`
- `artifact_targets`

## Question Types

V1 should support a small question taxonomy.

Recommended initial types:

- `architecture_decision`
- `implementation_strategy`
- `evaluation_design`
- `dependency_resolution`
- `performance_optimization`
- `risk_reduction`
- `reuse_discovery`

This is enough to cover most technical work without overcomplicating the front door.

## What Makes A Good Research Question

A strong question should be:

- bounded
- decision-relevant
- answerable with evidence
- likely to change downstream action
- specific enough to evaluate solutions against

A weak question is:

- vague
- too broad
- not tied to a decision
- impossible to evaluate
- only descriptive with no action consequence

## Question Derivation Rules

The tool should derive questions from:

- unresolved decisions
- blocked progress
- major implementation uncertainty
- risk concentration
- places where reuse may reduce work
- high-cost or high-impact technical choices

It should avoid generating questions about everything. More questions are not better.

## Question Ranking Model

Questions should be ranked by expected downstream value.

Recommended ranking dimensions:

- `decision_importance`
- `uncertainty_reduction`
- `downstream_impact`
- `time_sensitivity`
- `researchability`
- `reuse_potential`
- `scope_clarity`

Conceptual scoring shape:

`priority_score = decision_importance + uncertainty_reduction + downstream_impact + time_sensitivity + researchability + reuse_potential + scope_clarity`

Weights should be configurable in `question_ranking_policy`.

## Prioritization Principle

The best question is not necessarily the most interesting question.

The best question is the one whose answer is most likely to:

- unblock important work
- avoid major waste
- produce reusable knowledge
- change what gets built next

## Emission Rule

Only emit downstream question packets for questions that:

- are bounded enough to research
- are tied to an actionable decision
- have enough context to search or evaluate against

Weak questions should be rejected or marked for reframing.

## Integration With Evidence Search Tool

The evidence-search tool consumes:

- `research_question_packet`

The question packet should give evidence search:

- keywords
- problem framing
- constraints
- likely source types
- evaluation targets

## Integration With Research Tool

The research tool consumes:

- `research_question_packet`
- evidence packets
- memory context

The question packet should be specific enough that research can produce bounded candidates rather than vague brainstorming.

## Integration With Memory Tool

The question tool may call memory to:

- retrieve similar prior problem statements
- retrieve reusable prior question forms
- avoid repeatedly asking already-solved questions

Memory should help sharpen questions, not replace question generation.

## Integration With Planner Tool

The planner should not consume raw question packets directly as implementation tasks.

Questions become planner inputs only after:

- evidence search
- research
- selected solutions

This protects the planner from turning uncertainty directly into work nodes.

## Failure Modes To Avoid

- generating too many weak questions
- asking broad philosophical questions instead of build-relevant ones
- ranking novelty over downstream value
- emitting questions too vague for evidence or research tools
- skipping question decomposition and treating the whole project as one question

## V1 Implementation Sequence

1. define project context, question candidate, ranked question, and research question schemas
2. implement project context normalization
3. implement question derivation heuristics
4. implement question ranking policy
5. implement packet emission
6. integrate with evidence-search-tool and research-tool

## V1 Exit Criteria

V1 is successful when:

- one large project context can be decomposed into bounded research questions
- the top-ranked questions are clearly more actionable than the rest
- downstream tools can consume the emitted question packets without manual rewriting
