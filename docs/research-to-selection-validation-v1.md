# Research To Selection Validation V1

## Objective

Validate the full currently-built research-to-selection toolchain before building planner and coding scopes.

This is not a full platform validation.

It validates:

- question to research problem
- research problem to hypotheses
- hypotheses to candidate tree
- candidates to evaluations
- evaluations to recommendation
- recommendation to selected solution scope

It explicitly does not validate:

- live external source retrieval
- execution-backed candidate evaluation
- planner DAG generation
- code generation
- governance execution intake

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

Evidence basis:

- `CRITIC`: validation should use external tools and artifacts, not unsupported self-reflection.
- `SWE-bench`: software work should be evaluated against task-grounded evidence rather than plausibility alone.
- W3C PROV: validation reports should preserve provenance across packet refs and handoff artifacts.
- `Self-Refine`: iterative improvement is useful when feedback is explicit and recorded.

## Runtime

Command:

- `bin/validate-research-to-selection-flow`

Runtime module:

- `src/platform_tools/validate_research_to_selection_flow.py`

## Inputs

Required:

- `research_question_packet`

Optional:

- `evidence_packet`

## Outputs

Primary report:

- `research_to_selection_validation_report`

The report records:

- run id
- validated scope
- explicitly unvalidated scope
- research basis
- artifact refs for every emitted packet
- step reports for every tool call
- validation checks
- blockers

## DAG

Canonical DAG:

- `artifacts/planner/research/research-to-selection-validation-v1-dag.json`

## Critical Review

This validator is useful because it proves the contracts and handoffs already built can execute as one chain.

It is not enough to authorize planner/code generation because:

- candidate evaluation remains static and contract-level
- evidence intake is still packet-provided
- no implementation DAG is generated
- no code execution task is evaluated
- no governance execution-intake packet is produced

The correct next step after this validator passes is planner-entry design, not coding-agent execution.

## Acceptance

The validator is acceptable when:

- all six current chain steps run in order
- every expected output ref is present
- packet types match contracts
- selected candidate matches recommendation
- selected candidate has an evaluation packet
- selected scope records the selection policy
- the report explicitly names unvalidated planner/code scopes
