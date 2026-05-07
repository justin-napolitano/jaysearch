id: ADR-0003
title: Researcher Capability Is External and Self-Critical
status: proposed
date: 2026-05-07
deciders:
  - justin-napolitano
  - agent/codex-01

## Context

The platform now needs a governed research capability. That capability should be reusable across multiple repos and projects, which argues for a separate researcher repo rather than embedding the full engine in the platform repo. At the same time, the researcher should be able to identify weaknesses in its own harness and suggest improvements.

Without an explicit architectural decision, the platform risks either over-centralizing the researcher implementation or allowing uncontrolled self-modification of governance and runtime contracts.

## Decision

The researcher capability will be implemented outside the platform repo and orchestrated through platform-defined contracts.

The researcher capability may critique its own harness and emit self-improvement proposals, but those proposals must be surfaced as governed review artifacts. The capability may not silently modify platform governance or self-authorize contract changes.

## Consequences

Positive:

- the researcher engine becomes reusable and independently evolvable
- the platform repo stays focused on governance and orchestration
- self-improvement becomes explicit and auditable

Negative:

- an additional repo and integration layer must be maintained
- self-improvement proposals add review overhead instead of applying immediately
