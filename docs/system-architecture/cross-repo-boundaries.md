# Cross-Repo Boundaries

## Objective

Define how the platform repo, a separate researcher repo, and target repos may interact.

## Repo Roles

### Platform Repo

Owns:

- orchestration policy
- execution contracts
- plugin entrypoints
- validation policy

Does not own:

- researcher engine internals
- target repo business logic

### Researcher Repo

Owns:

- research runtime
- study-design plugins
- bibliography, evidence, and decision helpers
- evaluation and self-review logic

Does not own:

- target repo governance
- platform repo orchestration policy

### Target Repo

Owns:

- output artifacts after they are written
- repo-local review and merge decisions
- repo-local execution context

## Allowed Integration Surfaces

- versioned artifact schemas
- CLI contracts
- plugin contracts
- API or MCP surfaces if later adopted
- declared output roots

## Disallowed Integration Surfaces

- direct imports from one repo into another repo's private source tree
- implicit writes outside a declared output root
- undocumented assumptions about another repo's folder layout
- silent self-modification of platform governance from a capability runtime

## Destination Contract

Every orchestrated run should declare:

- target repo or root
- output root
- artifact classes allowed
- whether writes are draft-only or execution-authoritative

If any of these are ambiguous, orchestration should fail closed.
