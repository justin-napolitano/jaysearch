id: ADR-0001
title: Graph Is Canonical and ExecPlan Is a Contract Projection
status: proposed
date: 2026-03-10
deciders:
  - justin-napolitano
  - agent/codex-01

## Context

The repository already uses ExecPlans, governed prompts, and workflow validators. That is sufficient for contract enforcement, but it is not sufficient for canonical planning state. A planner control plane needs durable local planning artifacts, dependency-aware task structure, and downstream sync capability without allowing external systems or markdown contracts to become workflow authorities.

Without an explicit architectural decision, the platform risks collapsing back into prose-first planning, hidden conversational state, or external-tool-driven workflow semantics.

## Decision

The planner control plane will treat local canonical graph state as the source of truth for planning and execution readiness.

Planner session artifacts will be durable local records used to derive and refresh graph state.

ExecPlans will be treated as governed contract projections rendered from canonical planner state when readiness criteria are met. ExecPlans are not the planner system itself.

External project-management systems such as GitHub Projects, Jira, and Microsoft Lists will be treated as downstream projections. They may receive selected task data and may support selective pullback later, but unresolved conflicts default to local canonical state.

## Consequences

Positive:

- planning state becomes explicit, local, and auditable
- provider integrations become adapters rather than architectural dependencies
- ExecPlans remain useful as human-reviewable execution contracts
- hidden chat-state authority is reduced

Negative:

- the platform must maintain both canonical machine-readable artifacts and rendered markdown contracts
- projection and sync logic must preserve provenance carefully
- implementation work must define graph validation and projection boundaries precisely
