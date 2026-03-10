---
id: "20260310-codex-orchestrator-contract-codex-01-execplan"
title: "Design the Codex orchestrator contract for governed repository execution"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-codex-orchestrator-contract-codex-01-execplan.md
  - docs/codex-orchestrator-contract.md
  - docs/codex-orchestrator-execution-loop.md
  - docs/merge-readiness-contract.md
  - docs/codex-orchestrator-phase-2-backlog.md
  - spec/codex-orchestrator.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-codex-orchestrator-contract-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-codex-orchestrator-contract-codex-01-execplan.md"
      expected_exit: 0

tasks:
  - title: "Define Codex orchestrator authority and command contract"
    priority: "P1"
  - title: "Define machine-readable status and reporting contract"
    priority: "P1"
  - title: "Define orchestrator execution loop and stop conditions"
    priority: "P1"
  - title: "Define merge-readiness contract for orchestration"
    priority: "P1"
  - title: "Define artifact ownership and mutation boundaries"
    priority: "P1"
  - title: "Produce implementation backlog for orchestrator-facing runtime work"
    priority: "P1"

depends_on:
  - "20260310-planner-control-plane-design-codex-01-execplan"
  - "20260310-rule-graph-codex-01-execplan"
---

# Purpose / Big Picture

Design the contract by which Codex acts as the orchestrator of this repository. The platform should not optimize for richer human-facing UX. It should optimize for a safe, deterministic, machine-readable control surface that allows Codex to inspect state, select legal work, execute allowed moves, validate results, and determine merge readiness without hidden state or ambiguous prose.

This phase is contract design only. It does not implement the orchestrator. It defines the rules and interfaces required for later implementation.

## Progress

- [ ] Define orchestrator authority and non-authority boundaries
- [ ] Define allowed command surface for orchestration
- [ ] Define machine-readable output contract
- [ ] Define execution loop and stop conditions
- [ ] Define merge-readiness contract
- [ ] Define artifact ownership and mutation boundaries
- [ ] Produce implementation backlog

## Surprises & Discoveries

Expected discoveries to capture during execution:

- Some existing commands may be too human-oriented or insufficiently structured for reliable orchestration.
- Some current outputs may require stricter JSON contracts before Codex can safely depend on them.
- Merge readiness may expose missing integration between planner state, validator outputs, smoke tests, and rule-graph enforcement.

## Decision Log

Planned foundational decisions to record during execution:

- 2026-03-10 / agent-codex-01 / Codex is the orchestrator, not merely a user of the CLI.
- 2026-03-10 / agent-codex-01 / The platform must optimize for machine-readable control surfaces rather than richer human UX.
- 2026-03-10 / agent-codex-01 / Orchestrator authority is constrained by rule graph, transition rules, validators, and human finalization requirements.
- 2026-03-10 / agent-codex-01 / Merge readiness must become a first-class machine-readable contract.

## Outcomes & Retrospective

On completion, this plan should yield a design package that defines:

- Codex orchestrator authority contract
- allowed command contract
- required machine-readable outputs
- execution-loop contract
- stop conditions and escalation boundaries
- merge-readiness contract
- artifact ownership and mutation boundaries
- implementation backlog for orchestrator-facing runtime work

Retrospective notes must capture any commands, outputs, or artifacts that are discovered to be unsuitable for orchestration without redesign.

## Context and Orientation

This repository now contains the core governed components Codex would need to orchestrate:

- planner session and graph runtime
- move engine
- contract draft/import support
- citation/inference validator
- scoring engine
- rule graph
- smoke-test merge discipline

What remains missing is the explicit contract that defines how Codex should operate across those components as the orchestrator.

Intended architectural direction:

- Codex as orchestrator
- local artifacts as source of truth
- deterministic commands as control surface
- validators and rule graph as referees
- human authority retained for finalization, exception handling, and tie-breaks

## Plan of Work

The work should proceed in five layers:

1. Define orchestrator authority.
Specify what Codex may do, what it may not do, and what requires escalation or human intervention.

2. Define control surface.
Specify which commands and artifacts are canonical for orchestration, and what machine-readable outputs they must emit.

3. Define execution loop.
Specify how Codex moves from inspection to selection to execution to validation to review to merge check.

4. Define merge gate.
Specify which machine-readable conditions determine whether a branch is merge-ready.

5. Define implementation runway.
Produce a concrete backlog for making the orchestrator contract executable.

This design must favor explicit command contracts, JSON output expectations, and stop conditions over prose-only workflow descriptions.

## Concrete Steps

1. Review the current orchestrator-relevant command surface:
   - `bin/planner`
   - `bin/citation-check`
   - `bin/planner-score`
   - `bin/rule-graph-check`

2. Write `docs/codex-orchestrator-contract.md` defining:
   - orchestrator role
   - authority boundaries
   - allowed commands
   - forbidden actions
   - artifact read/write boundaries

3. Write `docs/codex-orchestrator-execution-loop.md` defining:
   - inspect
   - select
   - execute
   - validate
   - review
   - recover or escalate
   - merge-check

4. Write `docs/merge-readiness-contract.md` defining:
   - required passing checks
   - smoke-test status
   - clean or stashed generated artifacts
   - citation compliance
   - rule-graph compliance
   - commit-size compliance
   - unresolved blocker handling

5. Write `spec/codex-orchestrator.yaml` defining the machine-readable orchestrator contract:
   - command categories
   - expected output modes
   - required JSON fields
   - stop conditions
   - escalation conditions

6. Write `docs/codex-orchestrator-phase-2-backlog.md` defining the runtime implementation backlog for:
   - orchestrator-facing status commands
   - merge-readiness engine
   - richer machine-readable planner/report outputs
   - implementation orchestrator integration

7. Run `bin/execplan-validate .agent/execplans/20260310-codex-orchestrator-contract-codex-01-execplan.md`.

## Validation and Acceptance

This design phase is accepted only if all of the following are true:

- A reviewer can determine exactly how Codex should orchestrate the repo without inference.
- The command/output contract is machine-oriented rather than prose-oriented.
- Stop conditions and escalation boundaries are explicit.
- Merge readiness is defined in machine-checkable terms.
- Artifact ownership boundaries are explicit enough to prevent hidden-state orchestration.
- The implementation backlog is specific enough to drive the next runtime slice.

Validation commands:

1. `bin/execplan-validate .agent/execplans/20260310-codex-orchestrator-contract-codex-01-execplan.md`

Additional manual review checks:

- verify that the design does not drift back into human-UX-first thinking
- verify that command outputs are specified as stable machine-readable surfaces
- verify that merge-readiness requirements align with existing smoke-test and rule-graph governance
- verify that human finalization authority remains intact

## Idempotence and Recovery

This is a design-only plan. Reruns are safe if:

- decisions are recorded explicitly
- deferred questions remain explicit
- conflicting interpretations are resolved in the decision log rather than silently replaced

If design direction changes materially, the affected contract docs and spec must be updated together.

## Artifacts and Notes

Expected artifacts:

- `docs/codex-orchestrator-contract.md`
- `docs/codex-orchestrator-execution-loop.md`
- `docs/merge-readiness-contract.md`
- `docs/codex-orchestrator-phase-2-backlog.md`
- `spec/codex-orchestrator.yaml`

Open design questions intentionally left for this plan to resolve:

- which existing commands require stronger JSON contracts
- whether orchestration should rely on one composite status command or several narrower status commands
- what exact machine-readable merge-readiness report shape should be used later
- where orchestrator stop conditions should be enforced first: command layer, merge-readiness layer, or both

## Interfaces and Dependencies

Primary dependencies:

- `bin/planner`
- `bin/citation-check`
- `bin/planner-score`
- `bin/rule-graph-check`
- `spec/game-transitions.yaml`
- `spec/task-graph.schema.yaml`
- `spec/scoring.yaml`
- `spec/rule-graph.schema.yaml`
- `docs/agent-game-rules-v1.md`
- `docs/governance.md`

Planned interfaces to define:

- Codex orchestrator command contract
- machine-readable status/report contract
- merge-readiness contract
- stop/escalation contract
