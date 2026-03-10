# Planner CLI Contract

## Command Surface

The planner command is the terminal-first operator surface for the control plane.

```text
bin/planner session start
bin/planner session chat
bin/planner session show
bin/planner session summarize

bin/planner graph build
bin/planner graph show
bin/planner graph ready
bin/planner graph blocked
bin/planner graph validate

bin/planner contract draft-execplan
bin/planner contract show

bin/planner validate
bin/planner sync github-projects
```

## Session Commands

`session start`

- creates a new planner session identity and local artifact layout
- records the initial objective, if provided
- records no implicit active session outside local artifacts
- does not mutate graph or contract artifacts by itself
- returns the created `session_id` for explicit later use

`session chat`

- opens an interactive terminal conversation
- behaves like a Codex-style session rather than a one-shot prompt
- records transcript and extracted structured state as local artifacts
- may use governed internal role prompts, but all accepted outputs must be written to local artifacts
- must target an explicit `session_id` rather than hidden process-local state

`session show`

- renders current session metadata, extracted goals, decisions, constraints, questions, and related graph references
- must target an explicit `session_id`

`session summarize`

- emits a concise human-readable session summary without changing canonical semantics
- must target an explicit `session_id`

## Graph Commands

`graph build`

- derives or refreshes canonical graph state from planner session artifacts
- updates provenance and evidence links
- does not silently discard unresolved conflicts or invalid extracted state
- must record source `session_id` and any related commit references used as evidence

`graph show`

- renders graph nodes, edges, and relevant metadata in terminal-readable form

`graph ready`

- shows nodes or task groups ready for contract projection or later implementation planning

`graph blocked`

- shows nodes blocked by unresolved questions, missing decisions, failed validation, or upstream dependencies

`graph validate`

- checks graph invariants, required fields, edge legality, and provider-agnostic schema compliance

## Contract Commands

`contract draft-execplan`

- renders a draft ExecPlan from graph state only when readiness criteria are satisfied
- records why drafting was allowed or refused
- never treats the rendered ExecPlan as the canonical source of truth
- must record source `session_id` and `graph_id` in projection provenance

`contract show`

- renders current contract projections and their graph/session provenance

`contract import-execplan`

- performs explicit reconciliation from an edited ExecPlan draft back into canonical planner artifacts
- exists because direct reverse-sync from markdown contracts is forbidden
- must emit a reconciliation report describing accepted, rejected, and unresolved changes
- must preserve original contract provenance and record resulting canonical updates
- must conform to `spec/planner-contract-import.yaml`

## Validation and Sync

`validate`

- runs planner-specific validation across session artifacts, graph artifacts, and contract projections

`sync github-projects`

- is scaffold-only in the current design phase
- projects a selected task subset outward
- never grants provider authority over local canonical state
- allows selective pullback later, but defaults to local-wins when conflicts remain unresolved

## Explicit Non-Commands

The v1 design intentionally omits:

- `bin/planner execute`
- `bin/planner codegen`
- any UI command surface
- implicit “current session” mutation outside local artifacts

Those concepts are excluded until execution authority, safety boundaries, and implementation semantics are defined explicitly in a later phase.
