# Agent Capability Boundaries

## Purpose

This slice defines anti-cheat boundaries for governed work. The goal is not to freeze governance forever; it is to stop an active implementation branch from redefining the rules or exception path that would let it pass itself.

## Capability Model

Capability is evaluated from local repository state:

- actor class
- branch class
- active slice goal area
- changed files since the branch base
- active ExecPlan `changes` field
- active exception registry state

The default governed actor is the active implementation agent on an `impl-execplan/*` branch.

Every new Codex session and every worker session must bootstrap from
repository-local governance state before mutating governed artifacts.
That bootstrap is fail-closed when branch role, active ExecPlan, or
required authority artifacts are ambiguous.

## Protected Surface Categories

- `rule_surface`
  - global rules and governance law
- `referee_surface`
  - local validator and legality commands
- `capability_policy_surface`
  - anti-cheat policy and protected-surface definitions
- `exception_registry`
  - authority-granting exception records
- `canonical_state_surface`
  - graph, ExecPlan, and other canonical in-repo state
- `projection_surface`
  - queue mirrors and provider-board projections

Worker-runtime governance additions:

- worker launchers and worker-runtime modules are treated as governed
  runtime surfaces, not as free-form helper scripts
- worker sessions must execute in isolated checkouts or ephemeral
  container-local clones
- worker sessions must hand off authority through Git-backed artifacts,
  not through durable process memory

## Default Anti-Cheat Rules

- non-governance implementation branches may not change:
  - `rule_surface`
  - `referee_surface`
  - `capability_policy_surface`
  - `exception_registry`
- governance implementation branches may change:
  - `capability_policy_surface`
  - a bounded allow-list of `referee_surface` files needed to enforce governance
- governed agents may never write:
  - `.agent/governance/exceptions.yaml`

## Self-Authorization Denials

The anti-cheat referee blocks these cases explicitly:

- an agent modifies exception records that could authorize itself
- a non-governance branch modifies rule or referee surfaces
- a governance branch modifies referee surfaces outside the bounded anti-cheat allow-list
- a protected-surface path is edited without being declared in the active ExecPlan
- GitHub authority is promoted above projection/evidence roles

## Human Authority

Humans still retain final authority. The anti-cheat model preserves:

- explicit human-authorized exceptions
- separate governance work on dedicated branches
- bounded checker repairs when the active governance slice is legitimately implementing policy

What it removes is silent self-authorization by the governed agent on the branch being judged.
