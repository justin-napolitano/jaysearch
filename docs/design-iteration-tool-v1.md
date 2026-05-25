# Design Iteration Tool V1

## Objective

Define a standalone design-iteration API that reviews the current system state, identifies drift risks and design gaps, and emits the next bounded set of questions and problem areas to investigate.

This tool is not evidence search, not solution research, and not planning.

Its purpose is to:

- review the current design and contract state
- reference relevant external research and prior internal evidence during critique
- identify contradictions, drift risks, and missing contracts
- identify unresolved decisions and weak assumptions
- emit structured findings and next-question candidates

## Role In The System

The intended split is:

- `design-iteration-tool`
  finds design errors, drift risks, missing contracts, and next-step problem areas
- `question-tool`
  converts context and findings into bounded research questions
- `evidence-search-tool`
  retrieves external evidence
- `memory-tool`
  stores and retrieves reusable internal knowledge
- `research-tool`
  evaluates solution candidates
- `planner-tool`
  builds implementation DAGs
- `governance-tool`
  enforces execution legality
- `orchestration-runner`
  coordinates workflows

The design-iteration tool is the critique and reframing layer.

It should be critique-with-evidence, not critique-by-opinion.

## Core Principle

Before building more, the system should be able to critique itself structurally.

The design-iteration tool should answer:

- what is missing
- what is drifting
- what is contradictory
- what needs a stronger contract
- what question should be asked next

This makes design refinement operational rather than ad hoc.

## V1 Use Case

V1 should support:

- review of current tool specs, contracts, and workflow assumptions
- extraction of design findings
- grouping of design gaps into bounded next-problem areas
- emission of question candidates for downstream question tooling

## Non-Goals

V1 should not become:

- a universal architecture engine
- a replacement for the question tool
- a planner
- a governance authority

It should stay focused on critique, gap detection, and next-step problem framing.

## End-To-End Flow

1. accept `design_context_packet`
2. retrieve relevant external and internal evidence for the design context
3. analyze current contracts, docs, workflow assumptions, and evidence
4. emit `design_findings_packet`
5. group findings into `design_gap_packet[]`
6. emit `next_question_candidate_packet[]`

## API Surface

### `review_design_state`

Purpose:

- review current design context for contradictions, weak boundaries, and drift risks

Input:

- `design_context_packet`

Output:

- `design_findings_packet`

### `group_design_gaps`

Purpose:

- cluster findings into bounded problem areas worth solving

Input:

- `design_findings_packet`

Output:

- `design_gap_packet[]`

### `emit_next_question_candidates`

Purpose:

- produce bounded question candidates from the design gaps

Input:

- `design_gap_packet[]`

Output:

- `next_question_candidate_packet[]`

## Primary Packets

### `design_context_packet`

Purpose:

- canonical design-iteration input

Minimum fields:

- `context_id`
- `system_scope`
- `artifact_refs`
- `assumptions`
- `active_contract_refs`
- `active_workflow_refs`

Recommended optional fields:

- `known_failures`
- `known_blockers`
- `open_decisions`
- `recent_findings`
- `evidence_refs`

### `design_findings_packet`

Purpose:

- structured output of design review

Minimum fields:

- `context_id`
- `findings`
- `drift_risks`
- `missing_contracts`
- `contradictions`
- `recommended_focus_areas`
- `evidence_refs`

### `design_gap_packet`

Purpose:

- one bounded design problem area derived from findings

Minimum fields:

- `gap_id`
- `title`
- `problem_statement`
- `why_it_matters`
- `affected_contracts`
- `drift_risk_level`

### `next_question_candidate_packet`

Purpose:

- candidate question output for downstream question-tool ranking and emission

Minimum fields:

- `question_id`
- `source_gap_id`
- `question_text`
- `decision_target`
- `why_now`
- `expected_downstream_change`

## Finding Types

V1 should support a small set of finding categories.

- `missing_contract`
- `duplicate_authority`
- `underspecified_boundary`
- `optional_field_causes_drift`
- `workflow_gap`
- `graph_semantics_gap`
- `versioning_gap`
- `overloaded_tool`
- `premature_abstraction`

## What Counts As A Real Finding

The design-iteration tool should prioritize only findings that materially increase drift risk.

A real finding is one that can cause:

- two tools to evolve the same concept differently
- a handoff packet to be interpreted differently by different tools
- orchestration and tool logic to diverge
- governance to reconstruct missing plan meaning
- planner to depend on undocumented research semantics

Minor wording issues are not the main purpose of this tool.

## Gap Grouping Rules

The tool should group findings into bounded problem sets, not just list many isolated defects.

Good grouped gap examples:

- missing research-to-planner selection contract
- planner-to-governance runnable contract incomplete
- packet versioning authority undefined

Bad grouped gap examples:

- architecture feels messy
- docs need cleanup
- too many concepts

## Integration With Question Tool

The question tool should consume:

- `next_question_candidate_packet[]`

The question tool may then:

- refine
- rank
- reject weak candidates
- emit final `research_question_packet[]`

This keeps critique and question ranking related but distinct.

## Integration With Memory Tool

The design-iteration tool may retrieve:

- prior design findings
- prior resolved gaps
- prior question templates

It should not automatically store every review cycle unless the outputs are curated and reusable.

## Integration With Evidence Search Tool

The design-iteration tool should call evidence retrieval when critique would benefit from external grounding.

Use:

- prior research on iterative refinement
- prior research on orchestration and contract governance
- benchmark references for workflow reliability

The design-iteration tool should attach explicit evidence refs to findings whenever external research materially supports a critique.

## Integration With Research Tool

The design-iteration tool does not directly generate solution candidates.

It may, however, trigger the creation of research questions that the research tool later consumes.

## Failure Modes To Avoid

- turning every small issue into a first-class finding
- generating gaps too broad to solve
- replacing the question tool
- producing critique without downstream actionability
- using prose-only findings without machine-readable fields
- making unsupported claims without evidence refs when external research is available

## V1 Implementation Sequence

1. define design context, findings, gap, and next-question schemas
2. define finding taxonomy
3. define real-finding filter rules
4. define gap grouping rules
5. integrate with question-tool

## V1 Exit Criteria

V1 is successful when:

- a current design state can be reviewed into structured findings
- real drift risks are separated from cosmetic issues
- findings can be grouped into bounded design gaps
- question candidates can be emitted for downstream research
