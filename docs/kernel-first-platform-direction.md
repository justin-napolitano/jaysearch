# Kernel-First Platform Direction

## Purpose

This document captures the emerging strategic direction for the repository:

build a standard kernel layer that works extremely well with Git and GitHub, and make runtimes above it pluggable.

## Thesis

The long-term value of this repository is probably not one specific agent runtime.

The long-term value is a kernel that:

- works cleanly with Git
- works cleanly with GitHub
- preserves canonical local state
- exposes explicit contracts
- can host multiple runtime or UX layers without giving them authority

## Why This Direction Is Attractive

### 1. Tool Agnosticism

If the kernel is strong enough, different runtimes can come and go:

- DeerFlow-like local harness
- Microsoft Agent Framework runtime
- LangGraph-based workflows
- OpenAI Agents SDK-based services
- future internal tools

The kernel survives framework churn.

### 2. Git and GitHub Are Durable Substrates

Git and GitHub already provide:

- versioned artifacts
- branches
- PR review surfaces
- merge events
- commit identity
- audit trail
- broad developer familiarity

That makes them a much stronger base layer than any one framework’s internal state model.

### 3. Governance Fits Naturally There

This repository’s existing strengths already align with Git/GitHub:

- merge-backed completion evidence
- branch policy
- PR review and handoff
- artifact-based planning
- projection to GitHub boards

That suggests the kernel should lean harder into these substrates rather than abstract away from them.

## What the Kernel Should Probably Standardize

### Canonical Artifact Classes

- research notes
- ExecPlans
- graph state
- validation reports
- reconciliation reports
- board projection metadata

### Canonical Events

- plan drafted
- plan finalized
- graph node registered
- graph state transitioned
- validation passed or failed
- merge evidence reconciled

### Canonical Bridges

- runtime session to artifact
- artifact to graph
- graph to board projection
- merge event to completion reconciliation

## What the Kernel Should Avoid

- coupling itself to one framework’s internal workflow model
- storing critical truth in non-versioned service state
- making UI/session state part of canonical authority
- requiring one runtime for all developer workflows

## Role of DeerFlow-Like Tools

DeerFlow-like tools fit well above this kernel.

They can provide:

- local developer ergonomics
- search and research
- tool orchestration
- subagent fan-out
- faster execution loops

But they should plug into the kernel through explicit contracts instead of replacing it.

## Role of Microsoft Agent Framework

Microsoft Agent Framework could also fit above this kernel.

It may be a particularly good choice if the organization wants:

- enterprise alignment
- Microsoft ecosystem fit
- broader workflow/session/middleware structure

Again, the key is the same:

it should plug into the kernel, not become the kernel.

## Recommended Direction

Near-term direction:

1. keep strengthening the kernel as the Git/GitHub-native authority layer
2. define bridge contracts clearly
3. evaluate runtimes as replaceable harness layers
4. resist committing the kernel to any one runtime too early

This would make the repository more durable, more portable, and easier to integrate with whichever tool turns out to be best for local development flow.
