# Research System Improvement Plan V1

## Objective

Define the next bounded build section for improving `research-tool` so it produces stronger inputs for planner and governance.

This plan is about improving the research system itself, not about adapting upstream inputs to current research limitations.

## Why Research Is Next

The platform now has:

- a live upstream handoff from `research_question_packet` and `evidence_packet`
- a materialized `research_problem_packet`
- a downstream planning and governance path

That means the weakest remaining link is the internal quality of the research system.

If research stays too shallow, planner and governance will receive:

- over-compressed recommendations
- weakly differentiated alternatives
- poor evaluation traceability
- insufficient justification for downstream scope selection

## Improvement Goals

V1 of the improvement plan should focus on five upgrades.

### 1. Hypothesis Branching

One research problem should support multiple explicit strategy branches.

Desired output:

- `research_hypothesis_packet[]`

Questions:

- how many branches should be allowed by default?
- what makes two branches materially distinct?
- when should a branch be pruned?

### 2. Typed Evidence Intake

Evidence should stop being one flat bundle.

Desired typing:

- `method_evidence`
- `benchmark_evidence`
- `implementation_evidence`
- `risk_evidence`

Questions:

- does the existing `evidence_packet` need subtyping or extension?
- should research normalize evidence further before candidate generation?

### 3. Candidate Family Diversity

Research should generate multiple candidate families, not minor variations.

Desired families:

- `reuse_direct`
- `reuse_hybrid`
- `novel_synthesized`
- `baseline_reference`

Questions:

- what policy enforces family diversity?
- how many families are required before ranking begins?

### 4. Evaluation Traceability

Every promoted candidate should have explicit evaluation support.

Desired property:

- no recommendation without linked evaluation records

Questions:

- what minimum evaluation record fields should be mandatory?
- when is evaluation evidence strong enough to rank?

### 5. Recommendation Traceability

Recommendations should be inspectable.

Desired property:

- winner, losers, and rationale all remain explicit

Questions:

- what exactly should `research_recommendation_packet` explain?
- how should rejected alternatives be summarized?

## Proposed Work Sequence

1. `review current research design against these goals`
2. `define missing contracts`
3. `define bounded runtime slices`
4. `implement one small improvement slice at a time`

## First Planned Slice

The first concrete improvement slice should be:

- `research hypothesis branching v1`

Reason:

- it is upstream of candidate diversity
- it improves evaluation comparability
- it sharpens recommendation quality

## Acceptance Standard

We should consider the research system ready for broader runtime integration when it can:

- materialize one research problem into explicit hypothesis branches
- generate candidates across distinct families
- emit evaluations per promoted candidate
- emit a traceable recommendation packet for planner
