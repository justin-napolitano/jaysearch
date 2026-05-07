# Researcher Self-Improvement Loop

## Objective

Define how the researcher capability should critically review its own harness without creating uncontrolled self-modification.

## Principle

Self-critique is allowed.
Self-authorization is not.

## Loop

1. Execute one bounded research iteration.
2. Produce normal research outputs.
3. Produce a harness-review artifact when methodological weaknesses are found.
4. Classify the weakness as one of:
   - contract gap
   - artifact gap
   - protocol gap
   - evaluation gap
5. Route the proposed improvement back through governed review.

## Required Self-Review Outputs

- what part of the harness was weak
- what evidence exposed the weakness
- proposed correction
- risk if left unresolved
- whether the change belongs in:
  - researcher repo
  - platform repo
  - target repo research package

## Guardrails

- the researcher may recommend changes to the platform contract
- the researcher may not apply those changes automatically
- platform-level contract changes require normal governed review in the platform repo

## Desired Outcome

The system becomes self-improving through explicit review artifacts, not through hidden behavioral drift.
