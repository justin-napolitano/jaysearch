# Codex Orchestrator Execution Loop

## Objective

The orchestrator execution loop defines how Codex should move through governed work without inventing hidden state or skipping required validations.

The loop is sequential, deterministic, and referee-constrained.

## Loop Stages

1. Inspect

Codex reads:

- canonical graph state
- rule graph status
- citation and scoring status where relevant
- active ExecPlan state
- branch and merge-readiness state

Required outputs from this stage:

- ready work candidates
- blocked work candidates
- missing evidence
- required validations

2. Select

Codex selects the next unit of work only if:

- it is ready under the graph
- no blocking rule prevents execution
- required authority is available
- the selected work fits inside the active ExecPlan scope

If multiple candidates are ready, selection should prefer:

- highest-priority work
- smallest reviewable unit
- work with the clearest validation path

3. Execute

Codex performs one bounded unit of work by:

- applying a legal move
- updating governed artifacts
- producing implementation changes when in implementation phase
- recording evidence links and provenance

Execution must not silently expand scope.

4. Validate

Codex runs the required validators and smoke tests for the active slice. A claimed state transition is not complete until its required validation path passes.

5. Review

Codex performs hostile review against:

- graph state consistency
- rule compliance
- citation/inference compliance where applicable
- smoke-test and merge-readiness obligations

6. Recover or Escalate

If validation or review fails, Codex must either:

- recover through a legal remediation move, or
- escalate when the failure crosses an authority or policy boundary

7. Merge Check

Codex checks whether the branch is merge-ready under the merge-readiness contract. If not, the loop returns to inspect with the unresolved blockers made explicit.

## Loop Invariants

The loop must preserve:

- no hidden state
- no skipped validators
- no unsupported readiness claims
- no human-authority bypass
- no mutation outside governed paths

## Failure Modes

The loop should treat these as hard failures:

- missing canonical artifact required for the next move
- illegal transition attempt
- failed smoke test
- failed citation or rule validation when required
- dirty generated artifacts at merge-check time
- unresolved merge blocker requiring human policy decision

## Implementation Consequences

A later runtime implementation should support:

- machine-readable inspect and merge-check commands
- deterministic next-step reporting
- explicit blocker and stop-condition reporting
- reusable hostile-review and validation phases

## Research Framing

This execution loop is a design inference informed by formal transition modeling and inspection literature already registered in `docs/references.md`.
