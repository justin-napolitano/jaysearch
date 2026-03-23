# Kernel vs Dev Harness Separation

## Purpose

This document captures a critical architectural distinction for the future of this repository:

- governance, reporting, auditing, and canonical work-state control are one system
- local developer execution ergonomics are a different system

Keeping those concerns separate is likely the difference between a useful governed platform and an overgrown agent runtime that quietly becomes its own authority source.

## Thesis

This repository should treat the governed platform kernel and the local development harness as separate layers with different responsibilities.

The kernel should own truth.

The dev harness should own convenience.

The bridge between them should be explicit.

## Kernel Responsibilities

The kernel is the authoritative layer.

It should own:

- canonical local artifacts
- remaining-work graph authority
- ExecPlan authority
- validation and merge-readiness
- human approval boundaries
- board projection and audit evidence
- deterministic reconciliation rules

It should not depend on:

- chat session memory
- hidden runtime state
- UI-local state
- tool-specific execution traces unless they are explicitly reconciled into durable artifacts

## Dev Harness Responsibilities

The dev harness is the execution-convenience layer.

It should own:

- local developer UX
- skill and tool loading
- search and research helpers
- subagent delegation
- sandboxed execution
- fast iteration loops
- optional UI or local service surfaces

It should not own:

- canonical work-state truth
- approval authority
- merge legality
- final audit semantics

## Why DeerFlow Is Attractive Here

DeerFlow is appealing as a local-dev harness pattern because it emphasizes runtime convenience:

- integrated tooling
- subagents
- memory
- sandboxing
- developer-friendly workflow surfaces

Those are valuable for actual development flow.

They are not, by themselves, a sufficient authority model for this repository’s governed state.

That makes DeerFlow a strong reference for the harness layer, not for the kernel.

## Why the Separation Matters

If the same runtime owns both convenience and authority, several things go wrong quickly:

- session memory becomes de facto truth
- subagent output becomes accepted state without reconciliation
- local UI or service interactions mutate state outside governed paths
- auditability degrades because runtime convenience artifacts start substituting for canonical evidence

The more ergonomic the runtime becomes, the more tempting this drift is.

That is exactly why the separation should be designed early.

## Recommended Three-Layer Model

### 1. Kernel

The current repository is already close to this layer.

It owns:

- graph
- ExecPlans
- validators
- merge-readiness
- governance rules
- provider projection

### 2. Dev Harness

This is the DeerFlow-like or framework-backed runtime.

It may eventually use:

- Microsoft Agent Framework
- LangGraph
- OpenAI Agents SDK
- DeerFlow-inspired patterns

Its job is to help produce work efficiently, not to define whether the work is canonical.

### 3. Bridge

This is the most important missing layer.

It defines:

- which runtime outputs are ephemeral
- which runtime outputs must be materialized as artifacts
- how session results reconcile into graph state
- how agent findings become draft ExecPlan content, research notes, or validation evidence
- where human confirmation is required

## Practical Rules

The following rules appear durable regardless of framework choice:

1. Session memory is convenience, not authority.
2. Subagent output is draft material until reconciled.
3. Tool execution logs are not canonical unless explicitly referenced by governed artifacts.
4. UI and chat surfaces may initiate actions, but they must not bypass local reconciliation rules.
5. Merge and approval decisions stay in the kernel.

## Framework Implication

This separation changes how frameworks should be evaluated.

The question is not:

"Which framework should replace this repository?"

The question is:

"Which framework is the best dev harness beneath an explicit bridge and above a governed kernel?"

That is why DeerFlow can still be a good influence even if the underlying runtime substrate ends up being Microsoft Agent Framework, LangGraph, or OpenAI Agents SDK.

## Recommendation

Near-term recommendation:

- keep researching the dev harness as a separate concern
- do not collapse governance and local dev flow into one architecture prematurely
- define the bridge contracts before choosing a full harness implementation

This keeps the repo honest while still allowing fast, modern local development ergonomics later.
