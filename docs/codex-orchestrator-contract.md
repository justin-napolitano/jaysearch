# Codex Orchestrator Contract

## Objective

This repository is designed to be orchestrated by Codex rather than operated through a rich human-facing UX. The orchestrator contract defines what Codex may do, what it must not do, and which machine-readable surfaces it must rely on.

The orchestrator exists to drive governed execution, not to invent its own workflow.

## Authority Model

Codex is allowed to:

- inspect governed state through stable commands and artifacts
- select work that is ready under the canonical graph and rule set
- run permitted commands that mutate local canonical state
- run validators and smoke tests
- draft governed artifacts
- prepare merge-readiness evidence

Codex is not allowed to:

- bypass validators or rule-graph constraints
- treat external systems as canonical state
- finalize ExecPlans or override human approval requirements
- rely on hidden local state or unstored planning memory
- mutate canonical state outside governed command paths
- treat prose-only output as authoritative when machine-readable output exists

Codex must escalate to a human when:

- a required transition is blocked by unresolved authority rules
- merge readiness cannot be achieved without a policy exception
- a change would violate the no-hidden-state rule
- finalization or exception approval is required
- two governed artifacts conflict and no deterministic precedence rule resolves the conflict

## Canonical Control Surface

Codex should prefer command wrappers in `bin/` and canonical artifacts under `artifacts/`, `.agent/execplans/`, and `spec/`.

Primary command families:

- `bin/planner`
- `bin/citation-check`
- `bin/planner-score`
- `bin/rule-graph-check`
- `bin/remaining-work-graph-check`

Primary artifact families:

- planner session artifacts
- canonical graph artifacts
- remaining-work runtime state artifacts
- ExecPlan artifacts
- bibliography and claim registry artifacts
- rule graph artifacts

When both human-readable and machine-readable output exist, Codex must consume the machine-readable form.

## Managed Repos

The orchestrator may target an external repository root when:

- the external repo remains canonical for its own graph, ExecPlans, docs, and initiative state
- `platform-template-bootstrap` remains only the runtime and orchestration engine
- the external repo exposes the lightweight canonical artifacts declared in [workflow.yaml](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/spec/workflow.yaml)
- managed-repo bootstrap is performed through versioned platform commands rather than Codex-only behavior or ad hoc shell usage
- repo-local provider-sync artifacts are created during bootstrap and reused for later board sync
- the managed board surfaces canonical completion PR evidence as projection data rather than as independent authority
- root-targeted runtime commands fail closed when those artifacts are missing or ambiguous

This allows the platform runtime to operate on repos such as `jayrun` without absorbing those repos into platform canonical state.

## Local Hook Automation

Routine local automation may run through versioned git hooks when:

- the hook bodies are stored in-repo under `.githooks/`
- the hook bodies call only repo-owned commands
- mutating hooks are limited to deterministic reconciliation on eligible branches
- validation hooks remain validation-only
- local setup is installed through `bin/install-local-git-hooks` rather than hidden one-off shell edits

The initial governed hook surface is:

- `post-merge` -> `bin/auto-reconcile-main`
- `post-checkout` -> `bin/auto-reconcile-main`
- `pre-push` -> `bin/run-governed-pre-push-checks`

Hooks are automation surfaces, not authority surfaces. They may invoke governed commands, but they do not create new rules outside the machine-readable workflow contract.

## Required Output Contract

Commands used by Codex orchestration must eventually provide stable machine-readable output with:

- command identifier
- artifact or graph identifier
- status
- blockers
- required next validations
- evidence references where relevant
- non-zero exit codes on violated preconditions

If a command lacks a stable JSON contract, that command is not yet a complete orchestration surface and should be treated as a backlog gap rather than papered over with prompt inference.

## Mutation Boundaries

Codex may mutate:

- planner session artifacts through governed planner commands
- canonical graph state through legal move paths
- active initiative ExecPlan artifacts when the initiative branch is authoritative for in-flight plan state
- draft ExecPlan artifacts through governed draft/import commands when isolated review branches are used
- implementation files only under an active implementation ExecPlan

Codex may not mutate:

- finalized approval metadata
- human-only exception records
- canonical state through direct ad hoc file edits when a governed command path exists

Direct file edits remain allowed for implementation work, but they must be governed by the active ExecPlan, reflected in canonical state, and validated before merge readiness is claimed.

When an initiative branch is active, the orchestrator should treat the initiative branch ExecPlan as the authoritative in-flight planning source unless machine-readable state says otherwise. A signed merge on `main` remains the historical approval or completion event, not the only lawful place where plan authority may exist during active initiative execution.

When Codex completes work on an `impl-execplan/*` branch under an active initiative, the normal integration path is a PR back into the parent `initiative/*` branch. Codex should not treat local cherry-pick as the default governed merge-back mechanism unless a machine-readable exception path or explicit human direction allows it.

## Stop Conditions

Codex must stop or escalate when:

- required machine-readable state is missing
- no ready work exists
- the next legal move is blocked by missing evidence
- required validations fail
- merge-readiness checks fail without a deterministic remediation path
- the work would cross a rule boundary requiring human authority

## Design Implications

This contract implies the following implementation priorities:

- stronger machine-readable status commands
- stable JSON for validator outputs
- a merge-readiness engine
- explicit orchestrator stop-condition enforcement
- implementation-phase orchestration using the same board, rules, and evidence model

## Research Framing

This contract is a design inference built on the repository's existing mechanism-design, provenance, state-transition, and inspection references in `docs/references.md`.
