# Design Iteration Tool DAG And Paths

## Objective

Define the explicit DAG, operating modes, and implementation paths for `design-iteration-tool v1` using critique-loop research as guidance.

This document turns the design-iteration tool from a conceptual capability into a concrete, orchestratable workflow.

## Research Basis

The recommended design is informed by:

- `Self-Refine`
  iterative feedback can improve outputs, but the loop is still model-centric
- `Reflexion`
  feedback plus episodic memory improves later behavior
- `CRITIC`
  tool-interactive critique is stronger than pure self-critique
- `Can Large Language Models Really Improve by Self-critiquing Their Own Plans?`
  self-critique alone is not reliably enough for planning-quality improvement

Design implication:

- do not build the iteration tool as a pure introspection loop
- build it as a tool-assisted critique loop over explicit contracts, DAGs, packets, and prior findings
- use external research references when they materially strengthen or falsify a critique

## Core Design Rule

The iteration tool should critique artifacts, not vibes.

Its preferred inputs are:

- contract specs
- packet schemas
- DAG models
- prior findings
- workflow outputs
- failure packets
- observed drift indicators
- evidence packets or source refs when relevant

It should not primarily rely on free-form self-reflection over prose.

## V1 Operating Modes

### `contract_review`

Purpose:

- find missing, contradictory, or drift-prone contracts

Primary artifacts:

- `docs/core-contract-spec-v1.md`
- tool specs

### `dag_review`

Purpose:

- find execution-model contradictions, missing node semantics, and graph drift risks

Primary artifacts:

- workflow DAG specs
- implementation DAG specs

### `separation_review`

Purpose:

- identify mixed responsibilities and extraction candidates

Primary artifacts:

- build plan
- tool boundaries
- runtime logs

### `run_review`

Purpose:

- critique real observed workflows after the runner exists

Primary artifacts:

- event logs
- failure packets
- blocked runs
- packet traces

## V1 DAG

The initial design-iteration workflow should be represented as a DAG.

### Node 1: `ingest_design_context`

Type:

- `tool_invocation`

Input:

- `design_context_packet`

Output:

- normalized context refs

Purpose:

- load the artifact set under review

### Node 2: `load_contract_artifacts`

Type:

- `artifact_check`

Input:

- contract refs from context

Output:

- contract artifact set

Purpose:

- assemble the shared contract state

### Node 3: `retrieve_relevant_research_evidence`

Type:

- `tool_invocation`

Input:

- `design_context_packet`

Output:

- evidence refs for the critique

Purpose:

- ground critique in relevant external research when available

### Node 4: `load_dag_artifacts`

Type:

- `artifact_check`

Input:

- DAG refs from context

Output:

- workflow and implementation DAG artifact set

Purpose:

- assemble graph-state inputs for critique

### Node 5: `run_contract_consistency_checks`

Type:

- `tool_invocation`

Input:

- contract artifact set

Output:

- contract finding candidates

Purpose:

- detect duplicate authority, missing transforms, optional-field drift, and versioning gaps

### Node 6: `run_dag_consistency_checks`

Type:

- `tool_invocation`

Input:

- DAG artifact set

Output:

- DAG finding candidates

Purpose:

- detect missing node semantics, edge ambiguity, and workflow/implementation graph mismatch

### Node 7: `compare_tool_boundaries_against_contracts`

Type:

- `tool_invocation`

Input:

- contract findings
- DAG findings
- tool boundary specs

Output:

- boundary finding candidates

Purpose:

- detect overloaded tools, duplicate responsibilities, and hidden orchestration logic

### Node 8: `rank_real_findings`

Type:

- `tool_invocation`

Input:

- all finding candidates

Output:

- `design_findings_packet`

Purpose:

- separate real drift findings from cosmetic issues
- require evidence refs when external research materially bears on the finding

### Node 9: `group_findings_into_gaps`

Type:

- `tool_invocation`

Input:

- `design_findings_packet`

Output:

- `design_gap_packet[]`

Purpose:

- convert findings into bounded problem areas

### Node 10: `emit_next_question_candidates`

Type:

- `tool_invocation`

Input:

- `design_gap_packet[]`

Output:

- `next_question_candidate_packet[]`

Purpose:

- produce bounded next-step research questions

### Node 11: `human_gate_review_findings`

Type:

- `human_gate`

Input:

- findings packet
- gap packets
- next question candidates

Output:

- adjudicated next-step packet set

Purpose:

- keep early iteration grounded before automated critique becomes too authoritative

## Required Edges

The minimum dependency structure should be:

- `load_contract_artifacts depends_on ingest_design_context`
- `retrieve_relevant_research_evidence depends_on ingest_design_context`
- `load_dag_artifacts depends_on ingest_design_context`
- `run_contract_consistency_checks depends_on load_contract_artifacts`
- `run_contract_consistency_checks depends_on retrieve_relevant_research_evidence`
- `run_dag_consistency_checks depends_on load_dag_artifacts`
- `compare_tool_boundaries_against_contracts depends_on run_contract_consistency_checks`
- `compare_tool_boundaries_against_contracts depends_on run_dag_consistency_checks`
- `rank_real_findings depends_on compare_tool_boundaries_against_contracts`
- `group_findings_into_gaps depends_on rank_real_findings`
- `emit_next_question_candidates depends_on group_findings_into_gaps`
- `human_gate_review_findings depends_on emit_next_question_candidates`

## Finding Ranking Rules

The iteration tool should rank findings by drift risk, not by rhetorical severity.

Recommended ranking dimensions:

- `duplicate_authority_risk`
- `contract_gap_severity`
- `workflow_breakage_risk`
- `tool_boundary_leakage`
- `downstream_impact`
- `repair_cost`

Conceptual priority rule:

`real_finding_score = authority_risk + contract_gap + workflow_breakage + downstream_impact + boundary_leakage - repair_cost`

The top findings should be the ones most likely to cause two parts of the system to evolve different meanings of the same thing.

Where external research materially addresses the same class of problem, the finding should carry supporting evidence refs or explicitly note that no strong evidence was found.

## Real-Finding Filter

The iteration tool should reject findings that are:

- wording-only
- cosmetic naming preferences
- abstract concerns with no contract consequence
- implementation detail bikeshedding without architecture impact

This keeps the loop high-signal.

## First Explicit Paths To Accomplish V1

### Path A: Contract Locking Path

Use when:

- core packet semantics are still unstable

Flow:

1. ingest contract docs
2. run contract consistency checks
3. rank findings
4. group gaps
5. emit next contract questions
6. human review

Target outputs:

- locked handoff contracts
- versioning gaps
- missing transforms

### Path B: DAG Sanity Path

Use when:

- orchestration or planner semantics look unstable

Flow:

1. ingest DAG artifacts
2. run DAG consistency checks
3. compare against shared contract semantics
4. rank findings
5. emit graph-focused next questions
6. human review

Target outputs:

- node/edge semantic fixes
- runner/planner graph boundary fixes
- runnable-contract fixes

### Path C: Separation Path

Use when:

- tool responsibilities appear mixed

Flow:

1. ingest tool specs and build plan
2. compare boundaries against contracts
3. rank mixed-responsibility findings
4. group extraction candidates
5. emit next separation questions
6. human review

Target outputs:

- extraction candidates
- anti-drift separation decisions

## Recommended First Use

The first actual use of the iteration tool should be:

- `Path A: Contract Locking Path`

Reason:

- contracts drift first
- downstream tooling cannot be safely separated until shared semantics stabilize
- external critique patterns can strengthen early contract review findings

The second use should be:

- `Path C: Separation Path`

Reason:

- separation decisions are more reliable after contract review than before

## Why This Works Better Than Pure Self-Critique

This design follows the lesson from `CRITIC` and related work:

- critique improves when the model can inspect external artifacts and tool outputs
- feedback loops are stronger when grounded in explicit evidence and checks
- memory helps, but only if it stores useful prior findings instead of everything

So the design-iteration tool should be:

- artifact-grounded
- contract-aware
- DAG-aware
- research-aware when relevant
- human-gated early

not merely introspective.

## Exit Criteria

The iteration-tool design is ready to build when:

- the initial DAG is explicit
- the operating modes are clear
- the real-finding filter is clear
- the first path to execute is obvious
- downstream question generation from findings is explicit
