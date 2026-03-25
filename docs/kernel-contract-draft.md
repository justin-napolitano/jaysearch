# Kernel Contract Draft

## Status

Draft only.

This document is intentionally incomplete. It exists to make the kernel shape reviewable before the repository locks the contract down too early.

Open questions and unresolved boundaries are preserved on purpose.

## Purpose

Define the standard kernel layer for this platform.

The kernel is the durable authority layer that should work extremely well with Git first and GitHub second, while allowing multiple runtime or harness choices above it.

## Draft Thesis

The kernel should be:

- Git-native
- GitHub-compatible
- terminal-first
- explicit about state and authority
- pluggable with multiple runtime layers
- strong on governance, auditability, hostile review, and merge-backed reconciliation

It should not be:

- coupled to one agent runtime
- dependent on UI state
- dependent on hidden session memory
- dependent on one orchestration framework’s internal model

## Kernel Responsibilities

The kernel should own at least the following:

- canonical artifact classes
- graph-backed work-state authority
- ExecPlan authority
- validation and merge-readiness
- review and hostile-review evidence
- reconciliation rules
- board and projection metadata
- human authority boundaries

## Canonical Artifact Classes

The current likely artifact set is:

- research documents
- ExecPlans
- remaining-work graph
- validation reports
- reconciliation reports
- provider-sync metadata
- review and hostile-review artifacts

Open question:

- whether session transcripts themselves should be canonical artifacts or merely evidence inputs to canonical artifacts

## Kernel Event Model

The kernel likely needs an explicit event model.

Candidate event families:

- plan drafted
- plan finalized
- graph node registered
- graph node transitioned
- validation passed
- validation failed
- review requested
- hostile review recorded
- merge evidence detected
- completion reconciled

Open question:

- whether events should remain spread across current artifacts or be formalized into one stricter event contract

## Authority Model

Current intended authority order:

1. local canonical artifacts
2. Git-backed history and merge evidence
3. GitHub review and projection surfaces as secondary evidence
4. runtime sessions as convenience and proposal surfaces only

This still needs review, but the direction seems right.

## Git-First Contract

Git should remain the primary substrate for:

- versioning
- branching
- commit evidence
- merge evidence
- artifact durability
- replayable history

The kernel should feel native to Git rather than layered awkwardly on top of it.

Open question:

- which kernel artifacts should be required in every managed repo versus generated only when the relevant capabilities are adopted

## GitHub-Second Contract

GitHub should remain the primary collaboration and projection layer for:

- pull requests
- review
- merge identity
- board projection
- coordination visibility

GitHub should not outrank local artifacts as the source of truth.

## Runtime Boundary

The kernel should allow many runtimes above it.

Examples:

- DeerFlow-like local dev harness
- Microsoft Agent Framework runtime
- LangGraph orchestration runtime
- OpenAI Agents SDK-based local tooling

Open question:

- what the minimum bridge contract must be so all of these runtimes can plug in without bespoke one-off glue

## Session Boundary

The kernel must govern session-based work without becoming a chat system.

The kernel should likely treat sessions as:

- execution contexts
- evidence-producing processes
- proposal generators

But not as canonical truth by themselves.

Open question:

- what the minimum durable session record is for planning, execution, and review sessions

## Hostile Review Contract

Hostile review appears to be a core kernel concern, not an optional extension.

The kernel should likely preserve:

- hostile review findings
- blocker counts
- unresolved finding state
- relation between hostile review and merge-readiness

Open question:

- whether hostile review should remain a separate artifact/report family or become a more unified referee contract inside the kernel

## Managed Repo Contract

If this becomes a reusable kernel, it must support managed repos cleanly.

That implies:

- explicit bootstrap rules
- explicit required artifacts
- root-aware orchestration
- portable provider-sync rules
- portable review and merge evidence handling

Open question:

- how small the required managed-repo kernel surface can be without becoming vague

## Non-Goals

The kernel should probably not own:

- rich UI surfaces
- general chat UX
- runtime memory systems
- framework-specific agent behaviors
- framework-specific developer ergonomics

Those belong above the kernel.

## Draft Design Principles

1. Local artifacts outrank runtime state.
2. Git history outranks UI memory.
3. GitHub reflects and coordinates but does not define canonical truth.
4. Sessions produce proposals and evidence, not authority by themselves.
5. Hostile review remains central.
6. Runtime layers must plug into the kernel through explicit bridge contracts.

## Open Questions

1. What is the minimum kernel surface that still feels complete?
2. Which artifacts are mandatory versus optional projections?
3. How strict should the event model become?
4. What should the managed-repo bootstrap contract require on day one?
5. How should hostile review integrate with merge-readiness and graph legality?
6. Which session artifacts are worth preserving as first-class kernel objects?

## Next Review Direction

This draft should be reviewed for:

- overreach
- missing kernel responsibilities
- incorrect authority ordering
- Git/GitHub boundary mistakes
- places where the runtime boundary is still too fuzzy

It should not yet be treated as final architecture.
