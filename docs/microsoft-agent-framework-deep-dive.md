# Microsoft Agent Framework Deep Dive

## Purpose

This document records a repo-specific read of Microsoft Agent Framework as a possible runtime substrate for the future dev harness layer.

## Summary

Microsoft Agent Framework looks like a serious candidate if the organization values:

- Microsoft alignment
- .NET and Python parity
- enterprise workflow posture
- middleware and telemetry
- a successor path from older Microsoft agent stacks

It does not remove the need for this repository’s kernel.

## Why It Is Attractive

### Organizational Fit

- Microsoft-backed
- open source
- likely easier to defend internally in a Microsoft-heavy environment
- likely better fit for enterprise support and adjacent tooling discussions

### Runtime Fit

- workflows and orchestration primitives
- sessions and state handling
- middleware hooks
- telemetry posture
- integrations story that appears broader than a minimal SDK

### Strategic Fit

If this repository wants a pluggable harness layer rather than a one-off local runtime, Microsoft Agent Framework may be the most organizationally durable choice.

## What It Still Does Not Solve

Even if adopted, it should not replace:

- canonical graph authority
- ExecPlan authority
- merge-readiness logic
- human-only finalization
- explicit reconciliation of durable decisions

Those remain kernel concerns.

## Risks

### 1. Preview Risk

Microsoft Agent Framework is still preview-era technology. Interface churn and migration cost remain possible.

### 2. Framework Gravity

A large framework can slowly become the de facto architecture.

That risk is especially high when teams start treating workflow state or session state as if it were canonical project state.

### 3. Enterprise Comfort Masking Design Weakness

A Microsoft-backed framework can feel “safe” organizationally even when the actual bridge contracts are still weak.

That would be a mistake here.

## Best Use in This Repo

Best use:

- runtime engine for the dev harness
- workflow/session machinery
- middleware and telemetry layer
- possible service/gateway substrate

Worst use:

- replacing the kernel
- owning canonical work-state truth
- becoming the approval or merge-readiness authority

## Evaluation Questions

1. How much control does it give over session and checkpoint semantics?
2. Can it operate cleanly with explicit bridge contracts to local artifacts?
3. Is its workflow model legible enough to coexist with the current graph-governed kernel?
4. Does its runtime state model help or hurt the no-hidden-authority stance?
5. Is .NET parity materially valuable for this platform’s expected users?

## Current Recommendation

Continue evaluating Microsoft Agent Framework as the leading organizational-fit runtime candidate, but only in the role of harness layer beneath explicit bridge contracts and above the current kernel.
