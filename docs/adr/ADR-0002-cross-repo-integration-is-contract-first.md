id: ADR-0002
title: Cross-Repo Integration Is Contract-First
status: proposed
date: 2026-05-07
deciders:
  - justin-napolitano
  - agent/codex-01

## Context

The platform is evolving from a single governed repo template into a system that will orchestrate specialized external capabilities. Without an explicit architectural rule, capability repos could begin to depend on the platform repo's private internals or on target repos' private layouts. That would turn orchestration into cross-repo entanglement and make replacement, testing, and governance harder.

## Decision

Cross-repo integration will be contract-first.

Repos may interact only through explicit public surfaces such as:

- versioned schemas
- CLI or API contracts
- plugin contracts
- declared output destination roots

Private source-tree imports and undocumented folder-layout assumptions are not valid integration mechanisms.

## Consequences

Positive:

- repos stay independently testable and replaceable
- orchestration remains reviewable and auditable
- target repos can remain mostly self-contained

Negative:

- more contract definition work is required up front
- integration must be validated explicitly rather than improvised
