# Planner Control Plane

## Purpose

The planner control plane is the terminal-first planning layer for this repository. It exists to turn adversarial planning dialogue into explicit local artifacts, a canonical task graph, and governed execution contracts. It does not replace ExecPlans, and it does not treat external project-management systems as workflow authorities.

## Core Model

The control plane consists of four layers:

1. Planner session
   Interactive terminal conversation plus extracted structured planning state.
2. Canonical task graph
   The durable, local source of truth for goals, decisions, tasks, risks, validation nodes, and dependencies.
3. Contract projection
   Rendered governed artifacts such as ExecPlan drafts derived from graph state when readiness criteria are met.
4. External projections
   Downstream sync targets for project-manager visibility such as GitHub Projects.

## Game Framing

The planner control plane should be understood as a governed game rather than a generic assistant.

Game interpretation:

- planner session artifacts capture moves
- the canonical graph is the board
- governed prompt roles are players with constrained powers
- validators are referees
- ExecPlans are commitment artifacts
- provider sync targets are observer boards

This framing is intentional. The platform is designed to reward explicit state, evidence, and legal transitions while punishing ambiguity, hidden state, and unsupported claims.

## Invariants

- The canonical source of truth is local graph state.
- Planner artifacts are durable local files.
- ExecPlans are contract projections from planner and graph state.
- External systems are projections only.
- Planner interaction is terminal-first under `bin/planner`.
- Planner default tone is hard/direct unless explicitly overridden.
- No hidden memory or hidden operational state is allowed.
- No implicit “current session” state is allowed outside explicit local artifacts.
- No direct code-writing path is allowed from planner ideation mode.
- Design and implementation claims that rely on prior work must cite explicit sources or be labeled as design inferences.

## Responsibilities

The planner control plane owns:

- planner session artifact creation and update
- graph derivation from planner state
- readiness evaluation for contract drafting
- explicit contract import and reconciliation back into canonical state
- governed prompt selection for planning roles
- auditable export and sync preparation

The planner control plane does not own:

- implementation execution authority
- human finalization authority
- external provider workflow semantics
- direct mutation of protected governance rules without explicit governed changes

## Internal Roles

The planner may use governed role prompts internally for:

- facilitation
- critique
- synthesis
- contract drafting

These roles are implementation techniques, not separate authorities. Any state they produce must be materialized into local artifacts or discarded.

## Provenance and Traceability

Planner state must support explicit traceability across:

- `session_id`
- `graph_id`
- `ExecPlan` identifiers
- related commit references

Commit linkage must be explicit metadata, not inferred hidden state. Commit references may be recorded in provenance fields and commit trailers such as:

- `Planner-Session`
- `Planner-Graph`
- `ExecPlan`

Research provenance must also be explicit:

- cited sources should be listed in `docs/references.md`
- source-backed versus inferred claims should be tracked in `docs/research-assumptions.md`
- bibliography relationships should be graphable through `artifacts/planner/research/bibliography-graph.json`

## Lifecycle

The expected lifecycle is:

1. Start or resume a planner session.
2. Capture transcript and extracted planning state locally.
3. Build or refresh the canonical graph from session artifacts.
4. Inspect readiness, blockers, and unresolved questions.
5. Draft an ExecPlan contract when readiness conditions are met.
6. Optionally import approved contract edits back into canonical state through explicit reconciliation.
7. Optionally project task subsets outward to provider adapters.

## Provider Strategy

GitHub Projects is the only named provider in the current design phase. Jira and Microsoft Lists are placeholders that must be supported by the adapter model later without changing canonical graph semantics.

Selective pullback is acceptable, but local canonical state wins by default when unresolved conflicts appear.
