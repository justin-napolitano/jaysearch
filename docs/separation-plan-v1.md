# Separation Plan V1

## Objective

Define the initial separation strategy for the tool ecosystem:

- what stays in this repository now
- what is incubated here first
- what is extracted later
- what signals justify extraction

This plan is meant to prevent premature repo sprawl while still preserving a path to clean tool boundaries.

## Core Principle

Separate by proven operational boundary, not by conceptual enthusiasm.

A capability should remain in this repository until:

- its contract is stable enough
- its runtime/storage needs are distinct enough
- its reuse beyond this repo is real enough
- local iteration is being hurt by coupling

## Current Repo Role

For now, this repository should act as:

- control-plane incubation repo
- design-lab repo
- contract-definition repo
- orchestration incubation repo

It is the right place to define and test:

- core contracts
- design iteration
- runner semantics
- tool boundary discipline
- first orchestration workflows

## What Stays Here Now

These should remain in this repository during the current phase.

### 1. Shared Contract Layer

Includes:

- `core-contract-spec-v1`
- DAG model
- message envelope
- packet taxonomy
- versioning rules

Reason:

- this is the central anti-drift authority

### 2. Design Iteration Tool

Includes:

- design review logic
- validator definitions
- design-iteration DAG
- findings and gap emission

Reason:

- it needs tight access to contracts, workflow specs, and critique artifacts

### 3. First Orchestration Runner

Includes:

- workflow DAG execution over existing tools
- event log
- failure handling
- packet movement

Reason:

- early orchestration should be developed close to the tools it wraps

### 3a. Plan Quality Score

Includes:

- plan-quality policy
- candidate plan comparison logic
- best-plan ranking semantics

Reason:

- this needs tight coupling to the evolving planner contracts and design-review rules before extraction

### 4. Wrapped Existing Capabilities

Includes:

- current question capability
- current research capability
- current planner capability
- current governance capability

Reason:

- these should first be wrapped and observed before extraction

## What Is Incubated Here First

The immediate incubation targets are:

1. `design-iteration-tool`
2. `orchestration-runner`
3. `plan-quality-score`
4. wrapper contracts for existing question/research/planner/governance capabilities

These should become operational before repo extraction decisions are made.

## What Gets Extracted Later

These are likely later extraction candidates, not immediate ones.

### 1. `evidence-search-tool`

Reason:

- likely distinct retrieval logic
- likely distinct source normalization and ranking behavior
- useful outside this repo once stable

### 2. `memory-tool`

Reason:

- distinct storage and retrieval model
- cross-project reuse potential
- should remain separate from orchestration state

### 3. `research-tool`

Reason:

- distinct runtime and evaluation behavior
- likely to need its own execution environment and experimentation cadence

### 4. `planner-tool`

Reason:

- extract only after planner packets and DAG semantics stabilize
- current planner concepts already exist locally and should be hardened first

### 4a. `plan-quality-score`

Reason:

- extract only after plan-model and scoring-policy contracts stabilize
- this tool should remain close to planner hardening until valid-plan comparison semantics settle

### 5. `governance-tool`

Reason:

- extract only after packet boundaries are real and the oversized harness can be simplified against those boundaries

## What Should Not Be Separate Yet

Do not create these yet:

### Separate docs-only repo

Reason:

- docs will drift unless code and contracts are already stable

### Separate design-iteration repo

Reason:

- the tool still needs direct local access to contracts, validators, specs, and workflow artifacts

### Separate shared-contracts repo

Reason:

- contract shapes are still being actively refined

## Extraction Triggers

Only extract a capability when one or more of these are true:

### Trigger 1: Stable Contract

- packet contract is no longer changing in major ways

### Trigger 2: Distinct Runtime

- the capability needs its own execution environment, scaling model, or dependency stack

### Trigger 3: Distinct Storage Model

- the capability needs storage patterns materially different from the current repo

### Trigger 4: Cross-Project Reuse

- the capability is needed across multiple repos or problem domains

### Trigger 5: Local Coupling Cost

- keeping the capability here is actively slowing iteration or causing drift

### Trigger 6: Clear Ownership

- the extracted capability can have a clear canonical owner and upgrade policy

## Repo Extraction Order

When extraction becomes justified, the most likely order should be:

1. `evidence-search-tool`
2. `memory-tool`
3. `research-tool`
4. `planner-tool`
5. `plan-quality-score`
6. `governance-tool`

This order reflects increasing architectural sensitivity.

## Why Design Iteration Stays Here First

The design-iteration tool is the mechanism that helps determine future separation.

That means it should remain close to:

- the contracts it critiques
- the workflow DAGs it reviews
- the build plan it updates
- the current mixed-capability implementations it observes

Extracting it too early would weaken its usefulness.

## Why Docs Stay With Code For Now

Right now:

- contracts are evolving
- DAG semantics are evolving
- validator rules are evolving
- extraction decisions are evolving

Keeping docs near the code and control-plane artifacts reduces drift while the system is still being shaped.

## Role Of The Design Iteration Tool In Separation

The design-iteration tool should help refine separation later by:

- detecting mixed responsibilities
- detecting duplicate authority
- detecting missing handoff contracts
- grouping extraction-worthy gaps
- emitting next-step questions about separation

But it should not be the sole authority for the first separation plan.

The first separation plan is still a bootstrap human decision.

## Bootstrap Separation Rule

Initial separation decisions should be:

- human-locked
- contract-backed
- revised later by design-iteration findings

This avoids letting an immature critique tool become prematurely authoritative.

## First Review Checkpoint

Before any repo extraction is approved, the following should be true:

1. core contracts are locked
2. design-iteration validators exist
3. runner can execute at least one real workflow over existing tools
4. observed friction justifies the extraction

If those are not true, extraction is too early.

## V1 Success Criteria

This separation plan is working if:

- the repository remains a productive incubation space
- tool boundaries get clearer over time
- extraction happens later and cleaner
- docs stay aligned with code and contracts
- the design-iteration tool produces useful evidence for future separation
