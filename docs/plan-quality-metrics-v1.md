# Plan Quality Metrics V1

## Objective

Define how the platform should decide which plan is best when multiple candidate
plans exist.

This is not the same as asking whether a plan exists.

A valid plan must first be:

- legal
- buildable
- machine-readable
- auditable

Only then should it compete on quality.

## Core Rule

Do not rank invalid plans against valid ones.

Plan comparison should use a two-stage decision model:

1. `hard gates`
   Plans that fail hard gates are disqualified.
2. `quality scoring`
   Only qualified plans are ranked against each other.

This prevents a flashy but non-runnable graph from beating a boring but valid plan.

## Stage 1: Hard Gates

A plan is disqualified if it fails any of these:

- graph is cyclic where execution ordering requires a DAG
- required contract handoffs are missing
- selected-solution authority is ambiguous
- required runnable contract fields are missing
- required node ids or edge endpoints are missing
- validation targets are absent for executable work
- scope ownership is ambiguous for build nodes
- governance cannot determine runnable state from emitted packets

These are binary gates, not weighted metrics.

## Stage 2: Quality Metrics

Once a plan passes the hard gates, rank it on quality.

### `BDS` Boundedness Score

Question:

- are nodes small enough to execute, review, and recover?

High score:

- nodes have narrow goals
- nodes have explicit outputs
- nodes do not bundle many unrelated changes

Low score:

- giant nodes
- vague work items
- mixed responsibilities inside one node

### `DES` Dependency Efficiency Score

Question:

- does the graph contain only necessary dependencies?

High score:

- minimal required edges
- little fake serialization
- few broad fan-in bottlenecks

Low score:

- dense dependency mesh
- many unnecessary sequencing edges
- dependencies used to hide uncertainty

### `PSS` Parallelism Safety Score

Question:

- how much safe parallel work does the plan expose?

High score:

- many ready or near-ready nodes
- low conflict-domain overlap
- parallel work does not create merge chaos

Low score:

- everything waits on one giant trunk node
- parallelism exists only on paper

### `VCS` Validation Completeness Score

Question:

- does each executable node have explicit validation targets?

High score:

- tests/checks are declared per slice
- acceptance is measurable
- completion evidence is explicit

Low score:

- nodes complete by narrative claim alone

### `SIS` Scope Isolation Score

Question:

- does each node own a clear slice of artifacts or conflict domains?

High score:

- narrow file/domain ownership
- explicit conflict declarations
- low accidental overlap

Low score:

- many nodes touch the same unstable areas
- ownership is inferred rather than declared

### `RCS` Recovery Containment Score

Question:

- if a node fails, how contained is the blast radius?

High score:

- failures isolate to a small subtree
- rollback/adaptation is local
- late-stage plan failure is unlikely to invalidate the whole graph

Low score:

- one failed node collapses most of the plan

### `EAS` Evidence And Assumption Score

Question:

- are key planning assumptions explicit and supported?

High score:

- critical assumptions are stated
- risky nodes reference evidence or design rationale
- open questions are localized

Low score:

- hidden assumptions
- dependencies exist with no stated reason

### `CPS` Critical Path Score

Question:

- how efficient is the critical path relative to plan scope?

High score:

- short critical path
- bottlenecks are intentional
- long chains are justified

Low score:

- deep serialized chains
- late discovery of blocking work

## Suggested Decision Policy

Use lexicographic decision-making:

1. reject plans failing hard gates
2. among valid plans, compare `boundedness`, `dependency efficiency`, and `validation completeness` first
3. break ties with `parallelism`, `scope isolation`, `recovery containment`, `evidence`, and `critical path`

That is better than one flat weighted sum because some dimensions matter more than others.

## Why Not Just Use One Score?

Because a single scalar is easy to game.

A plan can look good numerically by:

- splitting work artificially into tiny nodes
- removing dependencies that are actually needed
- maximizing fake parallelism

So the scoring model should combine:

- hard gates
- weighted metrics
- anti-cheat heuristics

## Anti-Cheat Rules

Do not reward:

- tiny nodes that only move prose around with no execution value
- removal of necessary dependencies to improve parallelism
- fake validation targets
- scope fragmentation that increases integration cost

Reward only:

- structure that improves measured execution outcomes
- lower failure propagation
- clearer verification
- lower ambiguity at handoff boundaries

## Comparison Policy

If two plans solve the same selected solution scope:

- prefer the plan with better hard-gate compliance
- then prefer the plan with better boundedness and validation
- then prefer the plan with lower critical-path burden and safer parallelism

If one plan is less ambitious but far more executable, it should often win.

## V1 Machine-Readable Use

These metrics should be captured in policy so:

- planner-tool can optimize toward them
- design-iteration-tool can critique plans against them
- future plan-ranking tools can compare alternatives consistently

## Bottom Line

The best plan is:

- the highest-quality plan among plans that are already legal and buildable

Not:

- the biggest plan
- the most detailed plan
- the most parallel-looking plan
- the highest raw scalar without gating
