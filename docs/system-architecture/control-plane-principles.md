# Control Plane Principles

## Objective

Define the governing principles for a multi-repo orchestration system centered in the platform repo.

## Principles

1. The platform repo is the constitutional layer.
   - It owns policies, contracts, orchestration rules, and capability boundaries.

2. Specialized capabilities live outside the platform repo.
   - Research, domain engines, and experimental runtimes should be implemented in separate repos.

3. Integration is contract-first.
   - Repos interact through versioned schemas, CLI or API contracts, plugin contracts, and declared output destinations.

4. No cross-repo private coupling.
   - One repo must not depend on another repo's internal file layout or internal Python modules.

5. Output mutation is explicit and bounded.
   - A capability may write only to declared output roots and only through validated artifact types.

6. Governance stays local.
   - Each target repo remains the authority for its own artifacts once written.

7. Self-improvement is reviewable.
   - A capability may critique its own harness, but proposed changes must be surfaced as governed artifacts for review.

8. Orchestration is observable.
   - Inputs, outputs, iteration state, and failure reasons must be inspectable without relying on hidden chat context.

## Immediate Consequence

The platform repo should define:

- repo boundary contracts
- capability invocation contracts
- output destination contracts
- self-review and self-improvement rules

before building more runtime code.
