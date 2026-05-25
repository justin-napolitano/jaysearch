# Execution ERA Multi Attempt Selection Research V1

## Purpose

Design the first `attempt_selection` stage for the execution ERA loop.

The current loop supports one attempt:

```text
execution_unit -> implementation_attempt -> attempt_evaluation -> solution_artifact -> applied_solution
```

The next loop should support multiple attempts:

```text
execution_unit -> implementation_attempt[] -> attempt_evaluation[] -> attempt_selection -> solution_artifact -> applied_solution
```

## Sources

### AlphaEvolve

Source:

- https://arxiv.org/abs/2506.13131

Relevant claim:

- a generate, evaluate, and select loop over code candidates can improve discovered solutions.

Design implication:

- `implementation_attempt` candidates should remain separate from the selected `solution_artifact`, and selection should be an explicit packet.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- software engineering tasks should be grounded in repository state and concrete patch outcomes.

Design implication:

- selection should prefer attempts with stronger repository-grounded validation evidence, not narrative quality.

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Relevant claim:

- tool-interactive critique is stronger than unsupported self-correction.

Design implication:

- V1 selection must score tool evidence and blockers before considering rationale text.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- simple staged software repair pipelines can be competitive without complex autonomous control.

Design implication:

- V1 selection should be deterministic and bounded instead of using an opaque LLM judge.

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Relevant claim:

- derived artifacts should preserve provenance and source relationships.

Design implication:

- the selected and rejected attempt/evaluation refs must remain visible after selection.

### Mechanism Design Sources

Sources:

- https://www.nobelprize.org/prizes/economic-sciences/2007/maskin/lecture/
- https://www.nobelprize.org/prizes/economic-sciences/2007/myerson/lecture/

Relevant claim:

- outcomes depend on the rules and incentives of the mechanism.

Design implication:

- the selector must define what attempts are rewarded and what cannot be used to game selection.

## Design Decision

Add an `attempt_selection` packet and deterministic selector.

V1 selector policy:

- blocked evaluations are ineligible
- promoted evaluations outrank non-promoted evaluations
- evaluations with command evidence outrank evidence-ref-only evaluations
- evaluations with patch validation evidence outrank unchecked patches
- fewer changed artifact refs wins as a tie-breaker
- more evidence refs wins as a tie-breaker
- lower lexical attempt ref wins as final deterministic tie-breaker

V1 should not use LLM rationale as a scoring input.

## Required Inputs

- one execution unit
- two or more implementation attempts
- one evaluation per attempt

## Required Output

`attempt_selection` packet:

- selected attempt ref
- selected evaluation ref
- rejected attempt refs
- rejected evaluation refs
- score breakdown per candidate
- selection policy ref
- evidence refs
- blockers

## Anti-Cheat Rules

- attempts cannot self-report score
- selector only reads evaluator output and attempt metadata
- blocked evaluations are never eligible
- rationale text is not a scoring input
- patch refs are not enough without evidence
- selection emits rejected refs, not just the winner

## Recommendation

Build selection as a separate tool before wiring it into the smoke runner.

Then extend the runner to generate/evaluate multiple attempts, select one, and feed only the selected attempt/evaluation into `emit_solution_artifact`.
