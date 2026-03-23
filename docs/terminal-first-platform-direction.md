# Terminal-First Platform Direction

## Purpose

This document records a deliberate product decision:

the user experience for this platform should remain terminal-first.

This is not a temporary limitation. It is a design choice.

## Thesis

The platform should optimize for a powerful terminal experience rather than expanding toward web, chat, or multi-surface UX.

That means:

- the terminal is the primary operator interface
- Git and GitHub remain the underlying durable collaboration surfaces
- richer runtime behavior should show up as better commands, better reports, and better local orchestration rather than as a separate UI product

## Why This Is Good

### 1. It Matches the Actual User

The platform should be optimized for the operator that exists, not the hypothetical one.

If the actual preferred interface is the terminal, forcing a UI strategy would create overhead without adding real value.

### 2. It Fits the Kernel

This repository is already strongest when:

- state is explicit
- artifacts are local
- commands are deterministic
- Git-native flows remain visible

A terminal-first UX reinforces those strengths.

### 3. It Reduces Hidden State

Graphical or service-heavy surfaces often create:

- local UI state
- hidden session assumptions
- action paths that bypass durable artifacts

A terminal-first model keeps interaction closer to the governed kernel and reduces the number of ways state can drift.

### 4. It Lowers Maintenance Cost

Terminal UX avoids building and maintaining:

- web frontends
- API-first product shells
- chat-channel adapters
- multi-client state coordination

That keeps effort focused on actual platform behavior.

## What Terminal-First Should Mean

Terminal-first does not mean primitive.

It should mean:

- excellent CLI entrypoints
- high-quality inspect/status/report commands
- resumable local sessions
- clear reconciliation flows
- strong local search and tool orchestration
- subagent support that still feels natural in the terminal

The goal is not austerity.

The goal is depth without unnecessary surfaces.

## What This Rules Out

This direction deprioritizes:

- web-first productization
- dashboard-driven interaction models
- chat-as-primary-control-surface
- UX choices that require service state to feel usable

Those things can still exist later as optional projections if ever needed, but they should not drive the architecture.

## Architectural Implication

Terminal-first strengthens the kernel-first strategy.

The likely architecture becomes:

### Kernel

Git/GitHub-native authority layer:

- graph
- ExecPlans
- validators
- merge-readiness
- audit and reporting artifacts

### Terminal Harness

Local execution-convenience layer:

- tools
- search
- subagents
- memory
- sandboxing
- workflow acceleration

### Bridge

Explicit contract layer from terminal runtime activity into durable kernel artifacts.

## UX Investment Areas

If the terminal is permanent, the right investments are:

- command ergonomics
- consistent machine-readable output
- rich human-readable summaries
- resumable workflows
- local trace inspection
- excellent error messages
- narrow, composable commands
- strong defaults with explicit escape hatches

## Recommendation

Treat terminal-first as a durable product decision and let that simplify the roadmap.

Do not spend design energy on surfaces you do not actually want.

Spend that energy on making the terminal experience unusually good.
