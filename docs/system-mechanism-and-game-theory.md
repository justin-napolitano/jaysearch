# System Mechanism And Game Theory

## Objective

Define the mechanism-design principles for the tool ecosystem so that:

- incentives are aligned with measured outcomes
- cheating is either visible or unprofitable
- clever shortcuts are allowed only when they improve real results
- every important decision is replayable and contestable

This document is theoretical scaffolding for the system design. It should shape the tool contracts before implementation hardens.

## Core Principle

The system should not reward plausible-looking work.

It should reward only:

- measured improvement
- reusable value
- valid evidence
- executable plans
- legal state transitions

A shortcut is acceptable only when it improves the scored objective under audit.

## Framing

This is a mechanism-design problem more than a pure software architecture problem.

Each tool is an agent with:

- information
- action space
- objective
- output contract
- possible gaming strategies

The system must be designed so that the best local strategy is usually compatible with the global objective.

## Global Objective

The global objective is not “maximize activity.”

The real system objective is:

- find better solutions faster
- build them with less waste
- preserve reproducibility and auditability
- prevent low-value or misleading work from propagating

In compressed form:

`global_utility = outcome_quality + buildability + reuse_value + auditability - wasted_work - misleading_work`

## Design Targets

The system should aim for:

- incentive compatibility
- auditability
- bounded execution cost
- replayability
- resistance to Goodhart effects
- stable decomposition across tools

It probably cannot be globally optimal in a formal sense. The practical goal is robust improvement under adversarial pressure and iterative use.

## Agent Model

### Evidence Search Tool

Information:

- external papers
- websites
- benchmarks
- metadata

Action space:

- search
- filter
- rank
- extract claims

Local objective:

- maximize relevance and evidence usefulness

Gaming risk:

- flood the system with noisy but superficially relevant sources
- over-rank flashy or recent sources without methodological value

### Memory Tool

Information:

- prior solved problems
- reusable solutions
- evaluation records
- reusable artifacts

Action space:

- store
- search
- rank
- expand linked records

Local objective:

- maximize future reuse value

Gaming risk:

- over-store low-signal records
- over-rank stale or overly general records

### Research Tool

Information:

- problem packet
- evidence packet
- memory context
- evaluation results

Action space:

- generate candidates
- synthesize artifacts
- evaluate
- rank
- recommend

Local objective:

- maximize empirical solution quality under budget

Gaming risk:

- generate plausible but weak candidates
- overfit to easy metrics
- suppress hard comparisons

### Planner Tool

Information:

- selected solutions
- constraints
- target artifacts

Action space:

- decompose work
- define nodes
- define edges
- emit execution packets

Local objective:

- maximize buildability and execution clarity

Gaming risk:

- emit elegant but non-runnable graphs
- invent excess dependencies
- hide ambiguity in large nodes

### Governance Tool

Information:

- graph packets
- execution packets
- validation evidence
- transition requests

Action space:

- validate
- block
- allow
- record transition
- decide readiness

Local objective:

- maximize legal, auditable execution quality

Gaming risk:

- become bureaucratic theater
- silently infer missing structure
- over-block useful work

### Orchestration Runner

Information:

- run state
- packet refs
- tool outputs
- event history

Action space:

- dispatch
- retry
- block
- record events

Local objective:

- maximize successful workflow completion with clear observability

Gaming risk:

- swallow failures
- hide complexity in orchestration logic
- become the real owner of domain behavior

## Utility Layers

The system should have multiple utility layers.

### Global Utility

Measures:

- quality of final selected solution
- quality of implementation outcome
- reuse gained
- cost and time efficiency
- auditability and replayability

### Tool Utility

Each tool should optimize a narrow, local utility.

Examples:

- evidence quality for evidence search
- retrieval usefulness for memory
- empirical candidate quality for research
- DAG buildability for planner
- legality and merge readiness for governance

### Constraint Utility

Some constraints override utility gains.

Examples:

- invalid artifacts
- unverifiable evidence
- illegal state transitions
- missing completion criteria

These should fail closed.

## Hard Constraints

These are not negotiable optimization targets.

- packets must be valid
- evidence must be attributable
- planner outputs must be machine-readable
- governance transitions must be explicit
- runs must be replayable
- no hidden authority may silently override canonical contracts

If a shortcut violates a hard constraint, it is a cheat even if it appears efficient.

## Soft Optimization Targets

These may trade off against each other:

- time to answer
- compute cost
- amount of reuse
- novelty of candidate generation
- planner granularity
- governance strictness

These are legitimate optimization surfaces.

## Allowed Shortcuts

A shortcut is allowed when:

- it improves a measured downstream outcome
- it is replayable
- it preserves required evidence
- it does not violate hard constraints

Examples:

- direct reuse of a prior validated solution
- skipping weak candidate branches early
- using a simpler DAG when it preserves buildability

## Unacceptable Cheats

A cheat is unacceptable when it improves the appearance of success without improving the scored outcome.

Examples:

- citing irrelevant papers to appear grounded
- retrieving stale memory because it looks reusable
- optimizing only for easy evaluation metrics
- emitting large plan nodes that avoid explicit dependencies
- inferring missing governance structure instead of blocking
- hiding failed tool invocations in orchestration

## Goodhart Risk Surfaces

The system is exposed to Goodhart effects anywhere a proxy metric becomes the real target.

Main risk surfaces:

- evidence count replacing evidence quality
- reuse count replacing reuse usefulness
- candidate score replacing real implementation value
- graph complexity replacing buildability
- governance pass count replacing actual safety

The response is not “avoid metrics.” The response is:

- use multiple metrics
- keep metrics inspectable
- attach evidence to scores
- penalize proxy gaming

## Anti-Goodhart Design Rules

1. no single score should determine all outcomes
2. every major score should have a visible breakdown
3. every promoted output should carry evidence refs
4. failures should remain visible, not be silently dropped
5. low-cost adversarial review should be possible

## Observation Layer

The system can only reward what it can observe.

Observable artifacts should include:

- evidence packets
- evaluation packets
- ranking artifacts
- graph packets
- governance decisions
- orchestration event logs

If an important quality cannot be observed, it must not be a primary reward target yet.

## Audit Layer

Every important decision should be reconstructible from artifacts.

Audit requirements:

- why a source was ranked highly
- why a solution was recommended
- why a node was declared ready or blocked
- why a merge or completion decision was made
- why a run retried, blocked, or failed

If a decision cannot be replayed, the mechanism is too weak.

## Reward Model

The system should reward:

- better final recommendations
- stronger reusable artifacts
- cleaner executable DAGs
- lower rework
- lower invalid-output rate

The system should not reward:

- more messages
- more records
- more papers
- more candidate branches
- more plan nodes

Activity is not value.

## Penalty Model

The system should penalize:

- invalid packets
- unverifiable claims
- failed evaluations
- stale or noisy retrieval
- DAG ambiguity
- illegal transitions
- hidden logic in orchestration

Penalties should be explicit in scoring or blocking behavior where possible.

## Equilibrium Goal

The target equilibrium is:

- evidence search returns fewer, stronger sources
- memory stores fewer, more reusable records
- research generates fewer, stronger candidates
- planner emits smaller, more executable graphs
- governance blocks only what truly lacks prerequisites
- orchestration remains thin and observable

This is a sparse, high-signal equilibrium rather than a maximal-activity system.

## Adversarial Evaluation Questions

The system should be tested with questions like:

### Evidence Search

- Can the tool inflate quality by returning many weak sources?
- Can recent but irrelevant papers outrank older stronger ones?

### Memory

- Can the tool dominate retrieval with stale popular records?
- Can it overfit similarity while ignoring adaptation cost?

### Research

- Can the tool win by exploiting an easy metric while producing weak artifacts?
- Can it avoid hard comparisons and still recommend itself?

### Planner

- Can the planner hide uncertainty in huge nodes?
- Can it make all work appear sequential to avoid explicit parallel reasoning?

### Governance

- Can governance pass incomplete work by reconstructing missing details itself?
- Can governance block useful work by inflating policy complexity?

### Orchestration

- Can the runner appear successful while hiding failed steps?
- Can retries or reordering silently distort run meaning?

## Tool-Specific Mechanism Rules

### Evidence Search Rule

Reward relevance and evidence strength, not source volume.

### Memory Rule

Reward reusable retrieval hits, not record count.

### Research Rule

Reward evidence-backed candidate quality, not prose plausibility.

### Planner Rule

Reward runnable decomposition, not plan complexity.

### Governance Rule

Reward correct legality decisions, not maximal strictness.

### Orchestration Rule

Reward transparent workflow completion, not hidden automation cleverness.

## Design Implications

This mechanism design implies:

- every tool needs explicit local utility
- every handoff needs typed packets
- every score needs evidence
- every blocker needs a machine-readable reason
- every shortcut must survive replay

These are architecture requirements, not just evaluation niceties.

## Implementation Consequences

Before major build-out, the design should define:

1. shared packet schemas
2. scoring breakdown fields
3. blocker and failure taxonomies
4. replayable event contracts
5. curation and admission policies

Without those, the system will drift toward opaque local optimization.

## V1 Success Criteria

The mechanism is working if:

- tools cannot improve measured outcomes by hiding evidence
- tools cannot win by increasing low-value activity
- reuse beats fresh generation only when it truly helps
- planner outputs are simpler and more executable over time
- governance remains smaller while staying reliable
- orchestration remains thin and replayable
