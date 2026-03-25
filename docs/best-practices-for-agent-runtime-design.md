# Best Practices for Agent Runtime Design

## Purpose

This document captures durable design practices for agent runtimes. It is intentionally independent of any single framework. The goal is to identify what seems to hold across strong systems and what repeatedly breaks down in practice.

## Core Principle

An agent runtime should optimize for useful execution, not mystical autonomy.

The best systems tend to be:

- explicit
- inspectable
- resumable
- typed at boundaries
- recoverable after partial failure
- subordinate to a durable source of truth

## Best Practices

### 1. Keep State Explicit

Use explicit workflow or graph state instead of relying on hidden runtime memory.

Good:

- checkpoints
- graph or workflow state
- stored task artifacts
- explicit handoff payloads

Bad:

- “the agent remembers”
- opaque internal routing with no durable trace
- implicit current-session truth

### 2. Treat Memory as Convenience

Memory is useful for speed and context continuity.

Memory is dangerous when it becomes authority.

Best practice:

- let memory help with recall, summarization, and personalization
- require durable artifacts for decisions, plans, and approvals

### 3. Keep Tool Contracts Narrow and Typed

Tool calls should have clear inputs, clear outputs, and clear failure semantics.

Good:

- typed input/output schemas
- small, composable tools
- explicit side-effect boundaries

Bad:

- giant “do everything” tools
- unclear mutation surfaces
- non-deterministic tool output that cannot be validated

### 4. Design for Interruption and Resume

Long-running agent work will be interrupted.

Best practice:

- checkpoint state
- make execution resumable
- make partial work legible
- avoid single-shot all-or-nothing flows

### 5. Separate Planning from Execution

Planning and execution inform each other, but they should not be collapsed into one uncontrolled loop.

Good:

- explicit planning artifacts
- explicit execution state
- explicit validation gates between them

### 6. Add Human Authority at Irreversible Boundaries

Human review should appear where actions are:

- externally visible
- expensive
- destructive
- security-sensitive
- merge/finalization related

The runtime should know when to stop.

### 7. Build Tracing and Evaluation In Early

If the runtime is not traceable, it is not governable.

If it is not evaluable, it will drift.

Best practice:

- request/response tracing
- tool-call logs
- checkpoint visibility
- output evaluation harnesses
- error and repair accounting

### 8. Prefer Small Primitives over Huge Magic Abstractions

Frameworks age better when their core concepts are small and composable.

Examples of durable primitives:

- agent
- tool
- handoff
- workflow node
- checkpoint
- guardrail

Systems become fragile when too much behavior is hidden behind one abstraction.

### 9. Keep External Systems as Projections When Possible

Boards, chats, and service surfaces are useful.

They are often poor authorities.

Best practice:

- let external systems reflect state
- avoid letting them silently define state

### 10. Make Parallelism Explicit

Parallel agent work is only safe when:

- dependencies are clear
- conflict domains are clear
- merge/reconciliation rules are clear

Parallelism without these controls creates impressive demos and poor systems.

## Common Failure Modes

- hidden mutable state becomes the real source of truth
- memory silently substitutes for artifacts
- agent handoffs lose important context or accountability
- tools have unclear side effects
- UI/chat surfaces mutate state outside controlled paths
- evaluation is bolted on too late
- framework abstraction drives architecture instead of the problem

## Implication for This Repo

The right runtime for this repository should:

- keep state explicit
- keep runtime subordinate to the kernel
- support interruption and resume
- expose typed tool and bridge contracts
- preserve human authority boundaries

That is more important than choosing the trendiest framework.
