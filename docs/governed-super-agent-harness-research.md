# Governed Super-Agent Harness Research

## Purpose

This document captures the current research state for a possible DeerFlow-inspired evolution of this repository. It is intentionally pre-architectural: the goal is to preserve what is attractive, what is risky, and what remains unknown before the platform commits to a runtime direction.

## Source Snapshot

Comparison source reviewed on 2026-03-23:

- bytedance/deer-flow GitHub repository and README
- URL: `https://github.com/bytedance/deer-flow`

The DeerFlow README presents DeerFlow as a runtime harness built around skills, tools, subagents, memory, sandboxed execution, and user-facing service surfaces such as a web UI and chat channels. It also describes the system as LangGraph-based and oriented around a coordinator/planner/researcher/coder/reporter workflow.

## Current Repo Shape

This repository is currently much closer to a governed platform kernel than a super-agent runtime.

Strong existing properties:

- explicit local artifacts as the source of truth
- canonical graph-backed planning and work tracking
- deterministic validation and merge-readiness
- explicit human-only finalization boundaries
- explicit prohibition on hidden authority and hidden memory

Missing or thin runtime properties:

- no first-class skills/tool registry comparable to DeerFlow
- no session memory subsystem
- no sandbox abstraction for task execution
- no service gateway, web UI, or chat-channel ingress
- no explicit multi-agent runtime for subagent fan-out and synthesis

## Capability Matrix

### What DeerFlow Appears to Provide

- integrated runtime harness rather than only planning and governance artifacts
- configurable tools including search, crawling, file operations, code execution, and MCP
- subagent decomposition for longer-running work
- persistent memory and context compression
- sandboxed execution and filesystem isolation
- service surfaces including web UI and messaging-channel integrations

### What This Repo Already Does Better

- canonical local state is explicit and durable
- merge and execution legality are machine-checkable
- external systems are treated as projections rather than authorities
- important authority boundaries are written down as rules instead of left implicit

### What Looks Most Worth Adapting

- skill loading and progressive capability activation
- tool registry and MCP integration model
- sandbox abstraction for controlled runtime execution
- explicit runtime session model
- user-facing gateway surfaces once the underlying contracts are defined

### What Looks Risky Without Adaptation

- long-term memory becoming an authority instead of a convenience layer
- agent session state drifting away from canonical local artifacts
- UI or chat-channel interactions mutating state without explicit reconciliation
- parallel subagent work producing outputs that are useful but not governable

## Working Design Inference

The strongest current design direction is a layered system:

1. `kernel`
   Existing planner, graph, ExecPlan, validation, and merge-governance surfaces.
2. `harness`
   Runtime layer for sessions, skills, tools, sandboxing, memory, and subagent execution.
3. `gateway`
   Service and UI surfaces that talk to the harness while still projecting durable results back into kernel-governed artifacts.

This is an inference, not a settled architecture.

## Adopt / Adapt / Reject Questions

### Likely Adopt

- progressive skill loading
- configurable tool and MCP surfaces
- explicit runtime roles for research-oriented execution

### Likely Adapt

- memory, so it cannot silently become canonical truth
- subagents, so their outputs reconcile into durable artifacts
- service ingress, so chat or UI actions do not bypass local governance
- sandbox execution, so produced outputs remain attributable and auditable

### Possible Reject

- any runtime behavior that requires hidden mutable session authority
- any architecture that makes the external service layer more authoritative than local artifacts
- any “super-agent” abstraction that makes legality, provenance, or merge-readiness weaker than they are now

## Research Questions Before Architecture Commitment

1. What is the minimum runtime contract that materially improves this repository without destabilizing current invariants?
2. Which runtime actions must always reconcile into canonical local artifacts, and which can remain ephemeral?
3. What form of memory is acceptable if the repository forbids hidden authority?
4. How should sandbox outputs be stored, referenced, and validated?
5. What is the minimal useful gateway surface: HTTP only, terminal plus HTTP, or UI plus API?
6. What is the correct boundary between planning-time graph state and runtime session state?
7. Which DeerFlow capabilities are actually product-critical here versus merely attractive?

## Planning Guidance

No implementation sequence should be committed until the following are clearer:

- runtime artifact model
- memory authority boundary
- sandbox contract
- skill and tool loading contract
- reconciliation contract from runtime outputs into kernel-governed state

Until then, this work should remain research-backed and decision-gated.
