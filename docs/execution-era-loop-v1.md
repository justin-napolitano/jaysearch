# Execution ERA Loop V1

## Objective

Formalize how an executor turns one `execution_unit` into a selected implementation result without losing search, evaluation, or provenance.

The executor should not directly mutate an execution unit into “done.”

It should generate implementation attempts, evaluate them, select the best attempt, and attach a solution artifact back to the graph.

## Core Model

```text
execution_unit
  -> implementation_attempt[]
  -> attempt_evaluation[]
  -> selected implementation_attempt
  -> solution_artifact
  -> completion_evidence
```

## Research Basis

Canonical bibliography:

- `docs/current-research-bibliography.md`
- `artifacts/planner/research/bibliography-graph.json`

Research support:

- Google-style evolutionary/tree-search coding systems motivate generating multiple implementation candidates and selecting the best by evaluator feedback.
- `SWE-bench` grounds software-agent evaluation in concrete repository tasks, patches, and tests: https://arxiv.org/abs/2310.06770
- `CRITIC` supports tool-grounded critique and correction rather than unsupported self-reflection: https://arxiv.org/abs/2305.11738
- `Reflexion` supports storing feedback from attempts and using it to improve later attempts: https://arxiv.org/abs/2303.11366
- W3C PROV supports preserving derivation from inputs, activities, generated entities, and responsible agents: https://www.w3.org/TR/prov-dm/

## Canonical Objects

### `execution_unit`

Purpose:

- contract for one buildable and evaluable unit of work

The execution unit is not the solution. It is the work contract.

### `implementation_attempt`

Purpose:

- one candidate implementation generated for an execution unit

Minimum fields:

- `attempt_id`
- `source_execution_unit_ref`
- `attempt_family`
- `implementation_summary`
- `changed_artifact_refs`
- `patch_ref`
- `validation_command_refs`
- `assumptions`
- `risks`
- `status`
- `created_by`
- `created_at`

Allowed statuses:

- `draft`
- `built`
- `validation_failed`
- `validated`
- `rejected`
- `selected`

### `attempt_evaluation`

Purpose:

- evaluator output for one implementation attempt

Minimum fields:

- `evaluation_id`
- `source_attempt_ref`
- `source_execution_unit_ref`
- `evaluation_method`
- `validation_results`
- `test_results`
- `review_findings`
- `score_breakdown`
- `promotion_status`
- `blockers`
- `evidence_refs`

### `solution_artifact`

Purpose:

- selected implementation result attached to the execution unit

Minimum fields:

- `solution_artifact_id`
- `source_execution_unit_ref`
- `selected_attempt_ref`
- `evaluation_ref`
- `artifact_refs`
- `patch_ref`
- `completion_evidence_refs`
- `validation_summary`
- `known_limitations`
- `follow_up_problem_node_refs`

The solution artifact completes or advances the execution unit. It does not erase the rejected attempts.

## Execution-Level Loop

1. load execution unit
2. generate one or more implementation attempts
3. run validation commands
4. evaluate attempts
5. select best valid attempt
6. emit solution artifact
7. attach completion evidence
8. update source problem node feedback refs
9. rerank affected project graph nodes

## Selection Rule

An implementation attempt can be selected only if:

- it references the source execution unit
- it stays within owned changes
- it runs required validation commands or records why they cannot run
- it has an attempt evaluation
- it has no blocking findings
- it produces completion evidence

## Anti-Drift Rules

The executor must not:

- overwrite the execution unit with implementation output
- hide failed attempts
- select an attempt without evaluation
- claim completion without validation evidence
- mutate files outside owned changes without updating the execution unit
- treat passing tests as sufficient if contract acceptance checks are unmet

## Graph Relationships

Recommended edges:

- `implementation_attempt` `derived_from` `execution_unit`
- `attempt_evaluation` `evaluates` `implementation_attempt`
- `solution_artifact` `selects` `implementation_attempt`
- `solution_artifact` `completes` `execution_unit`
- `solution_artifact` `informs` downstream `problem_node`

## Practical Implication

The executor can be ERA-style without making the whole project chaotic.

The search happens inside an execution unit boundary.

That boundary controls:

- allowed files
- required tests
- acceptance checks
- rollback plan
- evidence requirements

The executor may explore multiple attempts, but only the selected solution artifact is allowed to complete the work.

## Materialization Boundary

Execution starts only after a selected scope is materialized into an `execution_unit`.

The local materializer is:

- `bin/materialize-execution-unit`

The materializer may emit:

- `problem_node`
- `node_option`
- `execution_unit`
- materialization report

It must not generate implementation attempts or write solution code.
