# Attempt Evaluation Command Execution Research V1

## Purpose

Research and design the next improvement to `attempt-evaluation-runner-v1`:

- execute declared validation commands directly
- capture command results as evidence
- keep command execution bounded by the `execution_unit`
- avoid turning the evaluator into an autonomous executor

## Research Sources

### SWE-agent

Source:

- https://arxiv.org/abs/2405.15793

Relevant claim:

- software agents benefit from an explicit agent-computer interface that includes repository navigation, file editing, and command/test execution.

Design implication:

- command execution should be an explicit tool surface with captured outputs, not hidden transcript context.

### Agentless

Source:

- https://arxiv.org/abs/2407.01489

Relevant claim:

- a simple localization, repair, and patch-validation flow can perform strongly without letting an agent freely decide future actions or operate complex tool loops.

Design implication:

- V1 command execution should only run declared validation commands from the execution unit or attempt. It should not discover new tests, repair failures, or choose future actions.

### SWE-bench / SWE-bench Verified

Sources:

- https://arxiv.org/abs/2310.06770
- https://www.swebench.com/verified.html

Relevant claim:

- software engineering evaluation should be task-grounded and execution-backed where possible.

Design implication:

- attempt evaluation should prefer real command output over narrative evidence when validation commands are available.

### OpenHands

Source:

- https://arxiv.org/abs/2407.16741

Relevant claim:

- practical software-development agents need sandboxed runtimes, command execution, browser/file interactions, and reproducible benchmark harnesses.

Design implication:

- command execution must have policy controls: timeout, allowed command prefixes, output capture, and explicit non-autonomous behavior.

## Design Decision

Add command execution as an optional, policy-gated mode of `evaluate-implementation-attempt`.

Do not create an autonomous executor.

The evaluator may run commands only when:

- `--execute-validation-commands` is passed
- command refs are already declared by the attempt
- command refs are present in the execution unit `validation_commands`
- command prefixes pass the local execution policy
- timeout is bounded

## Proposed Policy

New file:

- `spec/attempt-evaluation-command-policy.yaml`

Policy fields:

- `policy_id`
- `default_timeout_seconds`
- `max_output_chars`
- `allowed_command_prefixes`
- `forbidden_shell_tokens`
- `require_declared_command`

Initial allowed prefixes:

- `uv run pytest`
- `python3 -m py_compile`
- `python3 -m json.tool`
- `bin/`

Forbidden shell tokens:

- `>`
- `>>`
- `<`
- `|`
- `&&`
- `||`
- `;`
- `$(`
- `` ` ``

V1 should reject commands containing forbidden shell control tokens.

## Runtime Behavior

When command execution is disabled:

- preserve command refs
- require or accept `validation_result_ref`
- do not run shell commands

When command execution is enabled:

- run allowed declared commands in repo root
- capture exit code, stdout tail, stderr tail, duration
- emit validation result records inside `attempt_evaluation.validation_results`
- add a generated evidence ref for the command-output artifact
- promote only if all executed commands exit `0` and no boundary blockers exist

## Required Artifacts

Runtime:

- update `src/platform_tools/evaluate_implementation_attempt.py`
- update `bin/evaluate-implementation-attempt`

Policy:

- add `spec/attempt-evaluation-command-policy.yaml`

Tests:

- command execution promotes when declared pytest command passes
- command execution blocks when command exits nonzero
- undeclared command blocks
- forbidden shell token blocks
- command output artifact is written and referenced
- command execution remains disabled unless flag is passed

Docs:

- update `docs/execution-era-runtime-research-v1.md`
- update `docs/project-format-and-state-v1.md`

## Critical Risks

- shell injection through validation command strings
- long-running commands
- accidental mutation by validation commands
- false confidence if command output is truncated too aggressively
- policy drift if commands are run without being declared by the execution unit

## Recommendation

Build `attempt-evaluation-command-execution-v1` before adding autonomous code mutation.

This gives the loop real execution-backed validation evidence while preserving the current graph and contract boundaries.
