# Research, Planning, And Governance Improvements V1

## Objective

Capture the broad improvements the platform should make to `research`, `planner`, and `governance` rather than forcing upstream `design/question` work to adapt to weak downstream systems.

The core design law is:

- improve downstream system quality first
- then let upstream orchestration rely on stronger contracts and runtime behavior

## Why This Matters

The platform now has a real upstream bridge:

- `research_question_packet`
- `evidence_packet`
- `question_to_research_problem_transform`
- `research_problem_packet`

That means upstream work is now strong enough to expose real weaknesses downstream.

The wrong move would be:

- bending question/design packets around current research/planner/governance limitations

The right move is:

- use the stronger upstream bridge to diagnose and improve downstream systems

## Research Improvements

### Problem

The current research design is still too recommendation-shaped and not enough experiment-shaped.

It is good at:

- bounded problem intake
- candidate generation
- evaluation and ranking framing

It is still weak on:

- explicit hypothesis branching
- evidence typing and normalization depth
- candidate family diversity
- evaluation traceability
- recommendation traceability back to rejected options

### Direction

Research should behave more like:

`problem -> hypotheses -> candidate families -> evaluations -> recommendation`

not:

`problem -> smart answer`

### Recommended Improvements

1. `Hypothesis-aware decomposition`
   One `research_problem_packet` should be able to produce multiple bounded sub-hypotheses or strategy branches.

2. `Typed evidence intake`
   Evidence should be classified at least into:
   - method evidence
   - benchmark evidence
   - implementation evidence
   - caution/risk evidence

3. `Candidate family diversity`
   Candidate generation should ensure materially different families:
   - `reuse_direct`
   - `reuse_hybrid`
   - `novel_synthesized`
   - `baseline_reference`

4. `Evaluation-first recommendations`
   Recommendations should only be emitted after explicit evaluation packets exist for all promoted candidates.

5. `Recommendation traceability`
   A `research_recommendation_packet` should be able to explain:
   - why the winner won
   - why alternates lost
   - what evidence influenced the choice
   - what open questions remain

### Near-Term Research Goal

Strengthen research so planner receives:

- better scoped recommended solutions
- clearer risks
- stronger evaluation evidence
- more than one credible alternative when appropriate

## Planning Improvements

### Problem

Planning is now structurally sound, but it still risks becoming a one-shot DAG emitter instead of a plan-search and plan-comparison system.

### Direction

Planner should become:

- alternative plan generator
- node/edge refactoring engine
- plan scoring consumer

not just:

- graph writer

### Recommended Improvements

1. `Alternative plan generation by default`
   For a meaningful scope, planner should generate at least two structurally distinct candidate plans.

2. `Node boundedness enforcement`
   Nodes should remain small enough to:
   - own
   - validate
   - govern
   - parallelize safely

3. `Dependency justification`
   Dependencies should not exist silently.
   The system should be able to explain why one node depends on another.

4. `Conflict-domain-aware parallelism`
   Parallel work should be justified by:
   - owned changes
   - conflict domains
   - validation boundaries

5. `Plan refactorability`
   The planner should support:
   - split node
   - merge node
   - reorder legal edges
   - re-score after mutation

### Near-Term Planning Goal

Strengthen planner so governance receives:

- cleaner execution-ready plans
- clearer approvals
- more defensible runnable slices

## Governance Improvements

### Problem

Governance is directionally right, but it must become sharper without getting larger.

The main risk is bureaucratic reconstruction:

- inferring missing planner semantics
- inferring missing research authority
- acting as a hidden execution tool

### Direction

Governance should stay:

- minimal
- explicit
- state-transition-focused
- evidence-of-completion-focused

### Recommended Improvements

1. `More specific gates`
   Governance blockers should point to the nearest responsible fix target:
   - selection problem
   - planning problem
   - execution materialization problem
   - evidence problem

2. `Approval semantics from policy`
   Approvals should come from policy and packet contracts, not warning-only interpretation.

3. `Legal transition ownership`
   Governance should own state legality:
   - runnable
   - blocked
   - completed
   - merge-ready

4. `Structured completion evidence`
   Completion should rely on explicit evidence contracts rather than generic “done” markers.

5. `Anti-bureaucracy rule`
   Governance must not reconstruct missing planner or research meaning.

### Near-Term Governance Goal

Make governance a sharper gate on cleaner planner output, not a compensating system for weak planner semantics.

## Recommended Order

If we improve downstream systems intentionally, the recommended order is:

1. `research`
2. `planner`
3. `governance`

Reason:

- weak research poisons planner and governance inputs
- planner quality can improve only after research emits better recommendation structures
- governance is easiest to sharpen once planner outputs are stronger

## Immediate Next Slice

The next best bounded section is:

- build a `research-system improvement plan`

That plan should target:

- hypothesis branching
- typed evidence intake
- candidate family diversity
- evaluation traceability
- recommendation traceability

Only after that should we start broad planner/governance hardening work again.
