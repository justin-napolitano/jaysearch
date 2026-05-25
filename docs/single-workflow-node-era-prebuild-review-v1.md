# Single Workflow Node ERA Prebuild Review V1

## Objective

Stop architectural drift by choosing one end-to-end workflow to research and test before implementing the next contract/runtime slices.

This document is a prebuild review, not an implementation ExecPlan.

## Critical Conclusion

The node-based idea is coherent, but it should not be implemented as a pile of independent contracts.

We should build and validate one workflow:

```text
selected_solution_scope
  -> problem_node
  -> node_option[]
  -> selected node_option
  -> execution_unit
  -> implementation_attempt[]
  -> attempt_evaluation[]
  -> selected implementation_attempt
  -> solution_artifact
  -> feedback refs back into project graph
```

If this workflow is coherent, then contracts and runtimes can be built in order.

If this workflow is not coherent, adding more schemas will only make the system look rigorous while still drifting.

## Research Basis

### AlphaEvolve

Source:

- https://arxiv.org/abs/2506.13131

Implication:

- generate multiple code candidates
- evaluate candidates against metrics
- select/improve high-performing candidates

Limit:

- AlphaEvolve is strongest for algorithmic/code optimization with evaluator feedback. Our project-management graph still needs explicit problem decomposition, governance, and provenance.

### SWE-bench

Source:

- https://arxiv.org/abs/2310.06770

Implication:

- implementation work should be grounded in concrete repository tasks, expected edits, and tests
- vague strategy labels are not enough for implementation evaluation

Limit:

- SWE-bench evaluates issue-resolution behavior; it does not define our planning graph or governance model.

### CRITIC

Source:

- https://arxiv.org/abs/2305.11738

Implication:

- critique should use tools, validators, local artifacts, and source refs
- unsupported self-review is not enough to select attempts

Limit:

- CRITIC supports tool-grounded correction; it does not remove the need for explicit contracts.

### Reflexion

Source:

- https://arxiv.org/abs/2303.11366

Implication:

- feedback from failed/rejected attempts should be retained and reused
- graph nodes should preserve feedback refs

Limit:

- feedback memory helps iteration but can reinforce bad signals if evaluators are weak.

### W3C PROV-DM

Source:

- https://www.w3.org/TR/prov-dm/

Implication:

- problem nodes, attempts, evaluations, and solution artifacts should be linked as provenance entities and activities
- selected artifacts should not overwrite source work contracts

Limit:

- PROV gives provenance structure, not project-specific scoring.

## Workflow Roles

### `selected_solution_scope`

Role:

- authorizes a selected direction after research/recommendation

Not enough for implementation:

- may not contain implementation intent
- may not contain owned changes
- may not contain validation commands

### `problem_node`

Role:

- manageable problem in the project DAG

Must answer:

- what problem matters?
- why does it matter?
- what does it unlock?
- what is missing before action?

### `node_option`

Role:

- one possible way to solve or advance a problem node

Must answer:

- what is the strategy?
- what changes are expected?
- what evidence supports it?
- what tradeoffs does it carry?

### `execution_unit`

Role:

- buildable/evaluable contract derived from a selected node option

Must answer:

- what exactly will be built?
- what files/artifacts may change?
- what validations must run?
- what proves completion?

### `implementation_attempt`

Role:

- one generated candidate implementation for an execution unit

Must answer:

- what changed?
- what patch/artifacts were produced?
- what validations were run?

### `attempt_evaluation`

Role:

- evaluator output for one attempt

Must answer:

- did it satisfy tests?
- did it satisfy acceptance checks?
- did review find blockers?
- should it be promoted, rejected, or refined?

### `solution_artifact`

Role:

- selected implementation result

Must answer:

- which attempt won?
- why did it win?
- what evidence proves completion?
- what follow-up nodes remain?

## Prebuild Test Plan

### Test 1: Generic Scope Detection

Input:

- current A/B selected scopes

Expected result:

- they should be classified as `planning_authority_only`, not `implementation_ready`

Reason:

- they lack concrete implementation intent, owned changes, and validation commands.

### Test 2: Problem Node Readiness

Input:

- A/B selected scopes

Expected result:

- each can become a `problem_node`
- each should start below `implementation_ready`
- missing fields should be explicit

### Test 3: Node Option Specificity

Input:

- problem node for `evaluation-strength-contract-v1`

Expected result:

- options must include concrete expected changes, not just family labels

Example expected changes:

- add `evaluation_strength`
- add `evaluation_basis`
- propagate strength into recommendation and selection gates
- warn/block static-only evaluations where stronger evidence is required

### Test 4: Execution Unit Readiness

Input:

- selected node option

Expected result:

- execution unit must include owned changes, validation commands, rollback plan, non-goals, and completion evidence requirements

### Test 5: Execution ERA Loop

Input:

- execution unit

Expected result:

- executor may generate multiple attempts
- attempts are evaluated
- rejected attempts remain visible
- selected attempt becomes `solution_artifact`

## Single Workflow Decision

The first workflow to build should be:

```text
A/B selected scope
  -> problem_node
  -> node_option
  -> execution_unit
```

Do not build executor attempts yet.

Reason:

- execution attempts require implementation-ready units
- current selected scopes are not implementation-ready
- building the executor first would encourage generic work contracts

## Build Order After This Review

1. `problem-node-execution-unit-contract-v1`
2. `implementation-intent-candidate-contract-v1`
3. `node-readiness-validator-v1`
4. `execution-unit-materializer-v1`
5. `execution-era-loop-contract-v1`

## Decision Gate

We are ready to formalize build ExecPlans only when:

- selected scopes can be converted into problem nodes
- problem nodes can identify missing fields
- selected node options carry implementation intent
- execution units can be blocked when owned changes or validation commands are missing

Until then, the system is research/planning-ready but not implementation-ready.
