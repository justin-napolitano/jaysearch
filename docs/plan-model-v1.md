# Plan Model V1

## Objective

Define what a `plan` is in this system.

This exists to stop overloading terms like:

- plan
- graph
- node
- edge
- execution slice

Canonical project-level model:

- `docs/node-based-project-plan-v1.md`

The node-based project model is the authority for problem nodes, node options, execution units, readiness states, and anti-drift rules.

## Core Definition

A plan is a machine-readable execution model for delivering a selected solution scope.

A valid plan is not only a graph. It also includes:

- selected scope authority
- node ownership
- dependency structure
- execution contracts
- validation targets
- completion evidence

## Canonical Layers

### `selected_solution_scope`

This is the authority boundary before planning starts.

It says:

- what solution was selected
- what is in scope
- what is out of scope
- what assumptions and risks remain

Planning must not infer or override this authority.

### `problem_node`

This is the project-level unit of manageable problem decomposition.

Problem nodes may be incomplete. They can be researched, expanded into options, ranked, selected, and eventually materialized into execution units.

Planner should rank and expand problem nodes.

Planner and governance must not treat every problem node as directly executable.

### `node_option`

This is one candidate way to solve or advance a problem node.

It carries implementation intent, expected changes, assumptions, risks, evidence refs, and evaluation refs.

### `execution_unit`

This is the buildable and evaluable unit derived from a selected node option.

Only execution units should be handed to implementation/governance as runnable work.

### `implementation_plan`

This is the main plan object.

It represents the bounded build work needed to realize the selected scope.

It contains:

- plan metadata
- plan nodes
- plan edges
- optional execution slices
- plan-level quality metadata

### `execution_slice`

This is the operational unit of execution derived from one or more plan nodes.

It is what downstream tooling can run, validate, govern, and complete.

Execution slices are required before governed execution.

They may be absent on candidate plans that are still being compared, as long as:

- nodes and edges are already machine-readable
- hard-gate validity can still be tested
- the chosen plan is forced into execution-ready form before governance

### `execution_slice_materialization`

This is the downstream planner phase that converts a chosen structural plan into an execution-ready plan.

It is responsible for:

- grouping nodes into runnable units
- defining required inputs and expected outputs
- attaching runnable preconditions
- attaching completion evidence requirements
- emitting governance-facing execution semantics

This phase should happen after plan comparison, not before it.

## Plan

### Definition

A plan is a dependency-structured execution model for delivering a selected scope through bounded, validatable nodes.

### Required properties

- stable plan id
- selected solution scope reference
- graph id
- nodes
- edges
- execution slices when execution-ready
- declared plan purpose
- plan status

### Invariants

- one plan must target one selected solution scope
- plan dependencies must be machine-readable
- plan nodes must be bounded enough to execute and review
- plan execution semantics must not depend on hidden prose
- candidate plans may omit execution slices temporarily, but chosen plans may not
- execution-ready plans must be the result of explicit execution-slice materialization

## Node

### Definition

A node is one bounded implementation problem or execution unit inside a plan.

Project-level problem nodes are defined in `docs/node-based-project-plan-v1.md`.

Implementation-plan nodes should either reference a source `problem_node` or be explicitly derived from an `execution_unit`.

### Good node properties

- stable id
- clear goal
- explicit status
- explicit dependencies
- owned changes or conflict domains
- expected outputs
- validation targets
- completion evidence requirements

### What a node is not

- a vague milestone
- a whole subsystem rewrite
- a narrative paragraph

### Good example

- implement planner packet normalization helpers for selected solution scope intake

### Bad example

- make the planner better

## Edge

### Definition

An edge is a meaningful relationship between nodes that changes execution, safety, or interpretation.

### Primary edge relations

- `depends_on`
- `gated_by`
- `conflicts_with`
- `informed_by`

### Rule

Only keep an edge if execution, legality, or interpretation would change without it.

Do not add decorative edges.

## Execution Slice

### Definition

An execution slice is the governed runnable unit emitted from a plan.

It is the object that downstream orchestration and governance act on.

### Required properties

- stable execution id
- source plan id
- source node refs
- required inputs
- expected outputs
- validation targets
- blocking dependencies
- conflict domains

### Invariant

Governance should be able to determine runnable state from execution slices without reconstructing plan semantics from prose.

Execution slices should map back to `execution_unit` records once the node-based project model is implemented.

## Plan Readiness

Plans move through at least two readiness states.

### `candidate`

This is the structural plan form used for comparison.

It requires:

- machine-readable nodes
- machine-readable edges
- dependency legality
- validation intent

It does not require fully materialized execution slices yet.

### `execution_ready`

This is the downstream plan form used for governance and governed execution.

It requires:

- execution slices
- runnable preconditions
- completion evidence requirements
- governance-facing execution semantics

## Plan Quality

Plans are compared in two stages.

### Stage 1: Hard validity gates

Reject plans that are:

- cyclic where execution requires acyclicity
- missing required handoffs
- missing validation targets
- missing runnable contract fields
- ambiguous in scope ownership

### Stage 2: Quality comparison

Among valid plans, rank by:

- boundedness
- dependency efficiency
- validation completeness
- parallelism safety
- scope isolation
- recovery containment
- evidence and assumption clarity
- critical path efficiency

See:

- [plan-quality-metrics-v1.md](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/docs/plan-quality-metrics-v1.md:1)
- [plan-quality-scoring.yaml](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/spec/plan-quality-scoring.yaml:1)

## Reorganization Rule

Because nodes and edges are explicit, a plan can be reorganized by:

- splitting oversized nodes
- merging fake micro-nodes
- removing unnecessary edges
- adding missing gating or conflict edges
- regrouping execution slices

Reorganization is allowed only if:

- selected solution scope stays unchanged
- hard validity gates still pass
- plan quality improves or remains neutral with lower complexity

## Best Plan

The best plan is:

- the highest-quality plan among plans that already pass hard validity gates for the same selected solution scope

In practice, that usually means:

- compare `candidate` structural plans first
- choose one plan
- materialize execution slices second
- then hand the `execution_ready` plan to governance

Not:

- the most detailed graph
- the largest graph
- the graph with the most parallel-looking nodes

## Relationship To Existing Artifacts

This plan model should align with:

- [task-graph.schema.yaml](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/spec/task-graph.schema.yaml:1)
- [remaining-work-graph.schema.yaml](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/spec/remaining-work-graph.schema.yaml:1)
- [core-contract-spec-v1.md](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/docs/core-contract-spec-v1.md:1)

This file is the semantic definition layer above those machine-readable schemas.
