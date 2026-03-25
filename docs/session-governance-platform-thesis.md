# Session Governance Platform Thesis

## Purpose

This document states the likely core thesis of the platform more directly than the generic “agent framework” framing.

## Thesis

The main problem this platform is solving is:

- governance of session-based work
- auditability of planning and execution
- orchestration of work through explicit graphs and plans
- reviewability across agent and human handoffs
- preservation of durable Git and GitHub-native evidence

This is not primarily a generic AI assistant platform.

It is a session governance platform with explicit orchestration and audit requirements.

## Core Objects

The platform revolves around a small number of durable objects:

- sessions
- plans
- graph state
- validation evidence
- review findings
- merge/finalization evidence

Those objects should remain explicit and inspectable.

## Why Sessions Matter

Modern agentic work often happens through sessions:

- planning sessions
- research sessions
- implementation sessions
- review sessions
- reconciliation sessions

Without governance, those sessions become opaque.

Without durable state, they become hard to resume, audit, or challenge.

The platform exists to stop that from happening.

## Why Graphs and Plans Matter

Sessions are useful, but they are not enough.

Graphs and plans provide:

- durable structure
- dependency awareness
- legality and readiness checks
- explicit handoff surfaces
- machine-checkable orchestration

Sessions are activity.

Graphs and plans are controlled state.

## Why Auditability Matters

If session-based work cannot be reconstructed, it cannot be trusted.

Auditability requires:

- explicit artifacts
- explicit evidence
- explicit transitions
- explicit authority boundaries

This is especially important once work spans:

- multiple agents
- multiple sessions
- multiple branches
- multiple humans

## Why Hostile Review Matters

Hostile review is not an add-on.

It is one of the key controls that keeps this kind of system honest.

Its purpose is to ask:

- what is unsupported?
- what is ambiguous?
- what drifted from canonical state?
- what relied on hidden memory?
- what should be blocked before merge or approval?

In this platform, hostile review is a referee mechanism.

It should remain central.

## Platform Shape

The platform now looks less like a generic framework and more like this:

### Kernel

Owns:

- plans
- graph state
- validation
- hostile review
- merge-readiness
- audit evidence
- human authority boundaries

### Session Orchestration Layer

Owns:

- planning session flow
- execution session flow
- review session flow
- session resumption and traceability
- controlled movement between graph and plan states

### Dev Harness

Owns:

- local execution convenience
- tool loading
- search
- subagents
- DeerFlow-like developer ergonomics

The dev harness is useful, but it is not the core thesis.

## Git and GitHub Role

Git and GitHub are not incidental implementation details.

They are part of the durable substrate:

- versioned artifacts
- branches
- PRs
- merges
- review evidence
- identity and authorship
- audit trail

That makes them a strong base for a governance platform.

## What This Means Strategically

The strongest long-term direction is probably:

- standard kernel for governed session orchestration
- explicit graph and plan control
- strong hostile-review and audit surfaces
- Git/GitHub-native durability
- pluggable local runtimes above the kernel

That is a stronger thesis than “build an agent framework.”

## Recommendation

Use this thesis as the main filter for future design choices.

Questions to ask:

- does this improve session governance?
- does this improve auditability?
- does this improve graph/plan orchestration?
- does this preserve hostile review and human authority?
- does this strengthen the Git/GitHub-native kernel?

If not, it is probably peripheral.
