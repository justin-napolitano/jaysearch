# Execution ERA Runtime Research V1

## Purpose

Back the next execution runtime plans with sources before implementation.

This document covers:

- implementation attempt generation
- attempt evaluation
- solution artifact emission
- full execution ERA smoke loop

## Sources

### AlphaEvolve

Source:

- https://arxiv.org/abs/2506.13131

Relevant claim:

- candidate generation should be paired with evaluation and selection, not one-shot acceptance

Design implication:

- execution must preserve multiple attempts and select through evaluation

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Relevant claim:

- repository-level software tasks require concrete codebase context, edits, and validation

Design implication:

- attempts must link to an execution unit, changed artifacts, patch refs, and validation outputs

### SWE-agent

Source:

- https://arxiv.org/abs/2405.15793

Relevant claim:

- software agents benefit from an explicit agent-computer interface for file editing, navigation, and test execution

Design implication:

- the execution runtime should expose bounded operations and capture command outputs instead of relying on informal transcript memory

### OpenHands

Source:

- https://arxiv.org/abs/2407.16741

Relevant claim:

- software-development agents need explicit interaction surfaces for writing code, using a command line, and browsing/inspecting context

Design implication:

- later executor implementations should be built around explicit tool surfaces and recorded actions, not hidden agent state

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- simple localization, repair, and validation flows can outperform more complex autonomous setups on SWE-bench Lite

Design implication:

- V1 should not be an unconstrained autonomous coding agent
- V1 should generate bounded attempts from one execution unit, validate them, and stop

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Relevant claim:

- tool-interactive critique is stronger than unsupported self-correction

Design implication:

- attempt evaluation should consume test outputs, review findings, and blockers as explicit evidence

### Reflexion

Source:

- https://arxiv.org/abs/2303.11366

Relevant claim:

- retained feedback can improve future decisions

Design implication:

- rejected attempts and evaluations must remain available as feedback refs

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Relevant claim:

- provenance should preserve entities, activities, agents, usage, generation, and derivation

Design implication:

- solution artifacts must link back to execution units, attempts, evaluations, evidence, and generated artifacts

## Critical Design Decision

V1 should be bounded and non-autonomous.

It should not let an executor decide arbitrary future actions. The execution unit already defines owned changes, validation commands, and completion evidence requirements.

Therefore V1 runtime planning should split into four slices:

1. `implementation-attempt-generator-v1`
2. `attempt-evaluation-runner-v1`
3. `solution-artifact-emitter-v1`
4. `execution-era-loop-smoke-v1`

## Anti-Drift Rules

- attempt generation does not select
- evaluation does not edit source files
- solution emission does not invent validation evidence
- failed attempts are retained
- selected attempts require nonblocking evaluation
- solution artifacts complete or advance execution units, not the other way around

## Open Research Questions

- What is the minimum attempt generator that is useful without becoming an autonomous agent?
- Should V1 attempts store patch files, changed file refs, or both?
- Should evaluation score be binary promotion first, numeric score second?
- Should solution emission require all validation commands to pass, or allow explicit waivers?

## Recommendation

Build the runtime in the following order:

1. generate attempt packets from execution units without applying code changes
2. evaluate attempts by consuming declared validation evidence and command refs
3. emit solution artifacts only for promoted attempts
4. add a smoke runner that exercises the packet loop with fixture artifacts

This gives us the graph and governance surface before adding higher-risk autonomous code modification.

## Source Sufficiency Matrix

### `implementation-attempt-generator-v1`

Sufficiently supported:

- generating bounded candidate attempts from a task contract
- keeping attempt generation separate from evaluation and selection
- preserving source execution-unit refs and intended changed artifacts

Sources:

- AlphaEvolve
- SWE-bench
- SWE-agent
- Agentless
- PROV-DM

Not yet justified:

- autonomous patch generation strategy
- best number of attempts
- optimal attempt-family taxonomy

V1 consequence:

- generate attempt packets first; do not implement autonomous code editing yet

### `attempt-evaluation-runner-v1`

Sufficiently supported:

- evaluating software work against task-specific validation evidence
- using tool/output-grounded critique instead of self-approval
- emitting blockers and score breakdowns separately from generation

Sources:

- SWE-bench
- CRITIC
- Agentless
- PROV-DM

Not yet justified:

- final scoring weights
- whether validation should run commands directly or consume precomputed validation refs first
- waiver policy for commands that cannot run locally

V1 consequence:

- consume explicit validation evidence and command refs first; add direct command execution only behind a clear policy

### `solution-artifact-emitter-v1`

Sufficiently supported:

- selecting only evaluated candidates
- retaining rejected attempts and feedback
- linking selected result to attempt, evaluation, patch, artifacts, and evidence

Sources:

- AlphaEvolve
- Reflexion
- PROV-DM

Not yet justified:

- multi-objective selection policy
- automatic project-node completion rules

V1 consequence:

- emit solution artifacts only for promoted, nonblocking evaluations; do not close project nodes automatically

### `execution-era-loop-smoke-v1`

Sufficiently supported:

- composing generate/evaluate/select as a traceable loop
- using a bounded local smoke flow before adding full autonomy

Sources:

- AlphaEvolve
- Agentless
- SWE-agent
- OpenHands
- PROV-DM

Not yet justified:

- general-purpose autonomous execution
- retry policy
- multi-attempt ranking beyond simple promoted/nonblocking selection

V1 consequence:

- build a fixture-backed smoke runner over packet tools, not an unrestricted executor
