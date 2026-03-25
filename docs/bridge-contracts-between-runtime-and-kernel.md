# Bridge Contracts Between Runtime and Kernel

## Purpose

This document defines the critical missing layer between a future agent runtime and the governed kernel already present in this repository.

Without this bridge, the runtime will either be too weak to matter or too powerful to trust.

## Bridge Role

The bridge exists to answer one question:

How does useful runtime behavior become durable governed state without letting runtime convenience become authority?

## Bridge Responsibilities

The bridge should define:

- which runtime outputs are ephemeral
- which runtime outputs must be materialized
- how runtime actions map to artifact updates
- how runtime observations become graph evidence
- how draft plan content is created from runtime sessions
- where human approval is required

## Categories of Runtime Output

### Ephemeral

May remain transient:

- intermediate thoughts
- temporary tool traces
- convenience summaries
- local UI state

### Materialized

Must become durable when important:

- architecture decisions
- accepted research findings
- planned work items
- graph state changes
- validation evidence
- merge-readiness evidence

## Recommended Bridge Contracts

### 1. Session-to-Artifact Contract

If a runtime session produces a decision or durable finding, it must be written into a governed artifact class.

Examples:

- research document
- ExecPlan draft
- graph evidence field
- audit log artifact

### 2. Tool-to-Evidence Contract

Important tool outputs must be referenceable and attributable.

Examples:

- command report
- generated file
- search result summary with source
- validation result

### 3. Handoff-to-Accountability Contract

Subagent or delegated work should preserve:

- who asked
- what scope was assigned
- what outputs were produced
- whether results were accepted or discarded

### 4. Runtime-to-Graph Contract

The runtime should not mutate the graph directly by implication.

Allowed pattern:

- runtime produces proposed action
- bridge validates legality
- kernel applies action through a governed path

### 5. UI-to-Kernel Contract

UI or chat actions may initiate workflows, but they should not create hidden state transitions.

Every meaningful mutation should resolve into:

- an artifact update
- a graph move
- a logged event

## Negative Rules

The bridge should explicitly forbid:

- memory-only decisions becoming authoritative
- implicit graph mutation from chat activity
- subagent output silently becoming accepted plan content
- service-layer convenience state replacing kernel truth

## Implication

Choosing a runtime before defining the bridge is premature.

The bridge is the thing that makes a runtime safe for this repository.
