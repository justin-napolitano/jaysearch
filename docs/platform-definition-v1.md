# Platform Definition v1

This document defines the minimum standard for this repository to qualify as a governed AI engineering platform template.

## Scope

This platform standard covers:

- ExecPlan-driven execution
- agent/human governance
- deterministic validation
- canonical graph-backed work state
- machine-readable rule authority
- signed finalization and audit evidence

## Core Invariants

These invariants are mandatory:

1. All meaningful work originates from an ExecPlan in `.agent/execplans/`.
2. Agents draft and implement under governed branches; humans finalize with SSH-signed authority events.
3. Validation outputs are deterministic and machine-readable.
4. Enforced rules live in `spec/` and are consumed by code from canonical machine-readable artifacts.
5. The remaining-work graph is the canonical work-state authority.
6. Projection surfaces such as `TODO.md`, queue docs, and provider boards are non-authoritative.
7. Validation tests declared in ExecPlans are executable by one governed runner.
8. Finalized plans and merge-backed completion state must be reconcilable from repository evidence.

## Execution Surface

- human/operator entrypoints: `bin/*`
- canonical implementation logic: `src/platform_tools/*`
- canonical rule inventory: `spec/rule-registry.yaml`
- canonical work-state authority: `artifacts/planner/research/remaining-work-graph.json`

## Data Contracts

- ExecPlan: markdown plus YAML frontmatter defined by `.agent/PLANS.md`
- Rule registry: canonical machine-readable inventory of enforced, derived, human-gated, backlog, and deprecated rules
- Rule graph: relationship projection over the rule registry
- Remaining-work graph: canonical slice readiness, gating, and reconciliation state
- Queue doc: human-readable mirror of remaining-work graph metadata
- TODO: optional projection only
- Health report: deterministic machine-readable repo summary
- Test report: deterministic per-test pass/fail with expected and actual exits

## Required Commands

Minimum required command surface:

- `bin/execplan-validate`
- `bin/run-local-ci`
- `bin/execplan-test`
- `bin/repo-health-check`
- `bin/rule-graph-check`
- `bin/remaining-work-graph-check`

`bin/sync-todos` remains supported as a projection command, not as a canonical workflow authority.

## Acceptance Checklist

A repository qualifies as this template only when all checks pass:

- `bin/execplan-validate .agent/execplans/*.md` exits `0` on valid inputs.
- validator output is deterministic and machine-readable.
- branch roles and protected-branch restrictions are enforced.
- `spec/rule-registry.yaml` exists and active enforced rules are registered there.
- `bin/rule-graph-check` validates the graph projection against the rule registry.
- `bin/remaining-work-graph-check` validates canonical work-state and queue-projection reconciliation.
- `bin/execplan-test` executes `validation.tests` blocks from ExecPlans.
- `bin/run-local-ci` runs the governed check chain in deterministic order.
- repo health does not depend on deprecated projection surfaces being authoritative.
- finalized plans and completion state can be derived from signed merge-backed evidence.

## Current Direction

Current platform work is focused on consolidation rather than bootstrap gaps:

- unify rule authority under `spec/rule-registry.yaml`
- keep the rule graph as a validated projection rather than a separate rule source
- treat TODO as projection-only
- formalize draft self-review, additive PR structure, and implementation handoff
- keep graph and queue state reconciled as governed workflow evidence

## Platform Completion

Platform-layer work is complete only when:

- rule, workflow, and projection authority are machine-readable and internally consistent
- graph-backed execution and merge reconciliation are canonical
- human authority boundaries remain explicit and machine-detectable
- documentation explains current runtime truth rather than preserving obsolete historical gap maps
