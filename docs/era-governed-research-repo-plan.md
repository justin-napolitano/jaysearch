# ERA Governed Research Repo Plan

## Objective

Create a new repository dedicated to an ERA-style empirical research runtime that stays subordinate to the existing governance harness and hands selected solutions to a planner that can materialize a canonical DAG of implementation work.

This plan assumes three distinct systems with explicit handoffs:

- `platform-template-bootstrap`
  Governance harness and planning authority
- `era-research-runtime`
  Empirical search, code synthesis, evaluation, and ranking
- `planner`
  DAG generation after a solution is selected

## Why A Separate Repo

The ERA runtime needs freedom to explore candidate implementations, run experiments, and emit ranked evidence without becoming the canonical source of truth for planning or governance.

Keeping it in a dedicated repo gives us:

- cleaner runtime boundaries
- separate iteration speed for search and evaluation code
- fewer accidental authority leaks into governance state
- a clear contract between research output and implementation planning

## Operating Model

1. A governed `research_problem` is authored with business context, technical objective, constraints, and evaluation rules.
2. The ERA runtime generates multiple candidate approaches and implementation variants.
3. The ERA runtime evaluates those variants using bounded empirical checks.
4. The ERA runtime emits a structured `research_run` with ranked candidates and evidence.
5. The governance harness applies a promotion gate and records the selected direction as `selected_solution_scope`.
6. The planner consumes only `selected_solution_scope` and generates the implementation DAG.

The planner does not consume raw search-state artifacts directly.

## Business-Case Contract

Every `research_problem` should force explicit business framing:

- `business_case_id`
- `decision_type`
- `business_objective`
- `expected_value`
- `cost_of_delay`
- `adoption_constraints`
- `operational_constraints`
- `decision_deadline`
- `evidence_required_for_approval`

Every ranked candidate should carry business-aware scoring alongside technical scoring:

- `impact`
- `feasibility`
- `rigor`
- `time_to_value`
- `operational_cost`
- `reversibility`
- `governance_fit`
- `business_alignment`

## New Repo Scope

Repository name recommendation:

- `era-research-runtime`

Initial repo responsibilities:

- define runtime contracts for problem intake, candidate generation, evaluation, and ranking
- implement a bounded empirical search loop
- synthesize code candidates or patches
- run repeatable evaluation pipelines
- emit evidence-rich structured outputs for the governance harness

Initial repo non-goals:

- no canonical planning authority
- no direct mutation of governed queue state
- no merge-readiness or branch-governance ownership
- no broad multi-agent swarm before evaluation contracts are stable

## Proposed Repo Layout

```text
era-research-runtime/
  README.md
  docs/
    architecture.md
    evaluation-model.md
    problem-types.md
  spec/
    research-problem.schema.yaml
    research-run.schema.yaml
    selected-solution-scope.schema.yaml
    evaluation-result.schema.yaml
  src/era_runtime/
    cli.py
    problem_intake.py
    search/
    synthesis/
    evaluation/
    ranking/
    packaging/
    integrations/
  tests/
  examples/
    research-problems/
    research-runs/
```

## Required Contracts

### `research_problem`

Canonical input to the ERA runtime.

Minimum fields:

- `problem_id`
- `title`
- `business_case`
- `target_repo`
- `technical_goal`
- `constraints`
- `success_metrics`
- `evaluation_protocol`
- `search_budget`
- `promotion_gate`

### `research_run`

Structured output from one empirical search run.

Minimum fields:

- `run_id`
- `problem_id`
- `search_strategy`
- `candidate_set`
- `experiments`
- `ranked_candidates`
- `recommended_candidate_id`
- `confidence`
- `open_questions`
- `artifact_paths`

### `selected_solution_scope`

Governed handoff from research into planning.

Minimum fields:

- `selection_id`
- `problem_id`
- `selected_candidate_id`
- `why_selected`
- `business_case_alignment`
- `in_scope`
- `out_of_scope`
- `assumptions`
- `risks`
- `acceptance_checks`

## Delivery Phases

### Phase 1: Contracts And Bootstrap

Deliver:

- repo scaffold
- schema set
- CLI skeleton
- example problems and runs
- architecture and evaluation docs

Exit criteria:

- can validate a `research_problem`
- can emit a stub `research_run`
- governance harness can parse the output contract

### Phase 2: Minimal ERA Loop

Deliver:

- candidate generation for one problem class
- bounded search policy
- code or patch synthesis
- evaluation execution
- ranking and packaging

Exit criteria:

- one end-to-end run can compare at least three candidates
- output contains scored evidence, not only prose

### Phase 3: Governance Integration

Deliver:

- adapter from `research_run` into governed promotion logic
- `selected_solution_scope` generation
- explicit promotion-failure reporting

Exit criteria:

- platform harness can gate, accept, or defer a research recommendation deterministically

### Phase 4: Planner Handoff

Deliver:

- planner input package derived from `selected_solution_scope`
- DAG materialization rules
- acceptance criteria projection into work nodes

Exit criteria:

- one selected candidate can produce a scoped implementation DAG

### Phase 5: Hardening

Deliver:

- reusable evaluation suites
- replayable runs
- cost controls
- failure taxonomy
- run history and comparison reports

Exit criteria:

- repeated runs are attributable, comparable, and cheap enough to use routinely

## First Pilot Use Case

The first supported use case should be narrow and measurable:

- compare candidate designs for a governed agent-runtime or research-harness subsystem
- synthesize small bounded implementations
- run tests and quality checks
- rank candidates on technical and business value

Do not start with unconstrained open-ended product ideation.

## Decision Gates

Gate 1: `problem_ready`

- business case is explicit
- evaluation protocol is bounded
- success metrics are machine-checkable where possible

Gate 2: `research_run_usable`

- at least one candidate has empirical evidence
- ranking is structured
- open uncertainties are explicit

Gate 3: `promotion_ready`

- recommended candidate passes governance thresholds
- scope can be bounded
- no unresolved contract blocker prevents planning

Gate 4: `planning_ready`

- selected solution has clear in-scope and out-of-scope boundaries
- planner inputs are complete enough to generate a DAG

## Immediate Next Moves

1. Approve the repo boundary and repo name.
2. Start the new repo with Phase 1 only.
3. Make the first pilot problem class architecture-comparison or bounded implementation optimization.
4. Keep planner integration downstream of human or governed selection.

## Notes

This plan intentionally separates:

- empirical search authority
- governance authority
- planning authority

That separation is the main design guardrail for building a better version without creating an ungovernable agent runtime.
