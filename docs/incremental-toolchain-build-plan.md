# Incremental Toolchain Build Plan

## Objective

Build the future toolchain by wrapping, orchestrating, and decomposing the existing capabilities in this repository rather than replacing everything up front.

The immediate goal is not a perfect final architecture. The immediate goal is a working orchestration substrate that can drive real research workflows while revealing the right seams for later extraction and simplification.

## Current Reality

This repository already contains meaningful pieces of the future system:

- question intake and canonicalization
- research request materialization
- research execution loop orchestration
- planner sessions and graph building
- planner scoring and graph-quality surfaces
- remaining-work graph machinery
- implementation orchestration
- governance validation and policy checks

Those are not yet the final separated tools, but they are strong enough to use as the first operating substrate.

## Core Build Strategy

Build in this order:

1. use existing tools as black-box capabilities
2. wrap them with explicit packet contracts
3. orchestrate them through a shared DAG runner
4. observe where responsibilities are mixed
5. extract constituent tools only where operational friction proves the boundary
6. improve the extracted tools
7. build missing tools only after the runner and contracts justify them

All future planner and implementation slices must route through the node-based project model:

- `docs/node-based-project-plan-v1.md`

This prevents drift back into generic selected scopes or linear prose plans.

This is an extraction-and-hardening strategy, not a greenfield rewrite.

## What Already Exists And How To Reuse It

### Existing Question Capability

Use:

- `src/platform_tools/research_questions.py`
- `src/platform_tools/intake_research_question.py`

Current value:

- canonical question payload handling
- backlog logging
- question artifact storage

Near-term role:

- become the first operational `question-tool` surface

### Existing Research Capability

Use:

- `src/platform_tools/materialize_research_request_from_question.py`
- `src/platform_tools/run_research_capability.py`
- `src/platform_tools/run_research_improvement_loop.py`

Current value:

- request materialization
- external researcher-harness invocation
- ranked follow-up preparation
- promotion packet generation

Near-term role:

- become the first operational `research-tool` surface

### Existing Planner Capability

Use:

- `src/platform_tools/planner_runtime.py`
- `src/platform_tools/planner_cli.py`
- `src/platform_tools/implementation_orchestrator.py`
- `src/platform_tools/planner_score.py`

Current value:

- session modeling
- graph construction
- move validation and application
- ExecPlan drafting
- implementation orchestration
- first graph scoring model

Near-term role:

- become the first operational `planner-tool` and partial orchestration substrate
- seed the future `plan-quality-score` surface

### Existing Governance Capability

Use:

- `src/platform_tools/governance_check.py`
- existing policy loaders and merge/readiness checks

Current value:

- explicit rule enforcement
- policy validation
- readiness and legality checks

Near-term role:

- become the first operational `governance-tool` surface

## Phase Model

### Phase 0: Inventory And Contract Wrapping

Deliver:

- one inventory of current commands, inputs, outputs, and artifacts
- one contract wrapper per existing capability
- one shared packet base contract

Exit criteria:

- existing question, research, planner, and governance surfaces can be described as tool invocations with typed input and output packets

### Phase 1: Orchestration Runner Around Existing Tools

Deliver:

- `message_envelope`
- workflow DAG node model
- edge semantics
- run lifecycle
- append-only event log
- packet refs and artifact refs

Initial workflow target:

- `question -> research -> planner -> governance`

Exit criteria:

- one multi-step run can be represented and replayed as a DAG over the existing tools

### Phase 2: Operational Observation

Deliver:

- execution logs from real runs
- blocker and failure taxonomy
- mixed-responsibility map

Purpose:

- learn where the current tools are too large or too entangled

Exit criteria:

- the main decomposition seams are observed from runtime friction, not only predicted from design theory

### Phase 3: First Extraction

Likely extraction targets:

- `evidence-search-tool` from research internals or upstream preparation
- `memory-tool` from reusable output curation and retrieval behavior

Exit criteria:

- extracted tools remove real mixed responsibility from the existing research and planner flows

### Phase 4: Planner Hardening

Deliver:

- mandatory problem-node and execution-unit contracts before implementation execution
- mandatory `selected_solution_scope` handoff before planner entry
- cleaner planner packet contracts
- runnable contract from planner to governance
- clearer implementation DAG semantics
- candidate-plan comparison contract
- explicit plan-quality scoring policy integration

Exit criteria:

- no planner path consumes raw research recommendation packets as authoritative selection input
- no implementation path executes a generic selected scope without an execution unit
- planner outputs are machine-runnable and governance does not need to reconstruct missing meaning
- competing valid plans can be ranked consistently for the same selected solution scope

### Phase 5: Governance Simplification

Deliver:

- smaller governance APIs around validated planner and execution packets
- incremental replacement of oversized combined behavior

Exit criteria:

- governance gets simpler because packet boundaries are real, not because rules were deleted blindly

## First Operational DAG

The first DAG should be intentionally small.

Recommended initial nodes:

1. `question_intake`
2. `question_materialization`
3. `research_request_materialization`
4. `research_run`
5. `research_followup_preparation`
6. `selected_solution_scope_materialization`
7. `planner_graph_build`
8. `governance_validation`

This is enough to test:

- packet handoff
- event logging
- blocking behavior
- replayability

It is not yet the final architecture.

However, the true first runner milestone should stop earlier:

1. `question_intake`
2. `question_materialization`
3. `research_request_materialization`
4. `research_run`
5. `research_followup_preparation`

This smaller path should validate packet passing and event logging before planner and governance are introduced.

## Extraction Rules

A new tool should be extracted only when at least one of these is true:

- the existing capability owns more than one distinct responsibility
- the capability needs a different storage model
- the capability needs a different ranking or optimization model
- the capability is reused in multiple workflows with different downstream consumers

This prevents tool proliferation without need.

## Mandatory Research-To-Planner Handoff Rule

The planner must not consume raw `research_recommendation_packet` output as authoritative selected-solution input.

The required sequence is:

1. research emits `research_recommendation_packet`
2. a selection step materializes `selected_solution_scope`
3. planner consumes `selected_solution_scope` through `planning_request_packet`

This prevents dual authority over “the chosen answer.”

## What Not To Do

Do not:

- rewrite governance first
- rebuild planner from scratch first
- build universal memory first

## Plan Comparison Rule

Once planner hardening begins, plan selection should use:

1. `design-iteration-tool`
   reject invalid plans
2. `plan-quality-score`
   compare valid alternatives for the same selected solution scope
3. `planner-tool`
   emit the chosen implementation plan for execution packets
- force every capability into a separate repo before the runner works
- replace existing operational behavior with only document-level concepts

## Next-Step Decision Rule

At any point, the next build step should be chosen by this order:

1. unblock real orchestration flow
2. tighten packet contract
3. simplify mixed-responsibility boundary
4. extract missing tool only if the flow proves the need

This keeps the build grounded in actual payoffs.

## Success Criteria

This build strategy is working if:

- the current tools can already run inside one orchestration substrate
- packet boundaries get cleaner over time
- extracted tools each remove real complexity
- planner and governance become smaller and clearer, not larger
- research workflows become easier to replay, audit, and improve
