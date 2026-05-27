# Jaysearch

Jaysearch is a governed research, planning, and ERA-inspired execution toolkit.

It is currently a modular toolkit repo: contracts, docs, CLIs, artifacts, tests, and Python tools live together until the boundaries are stable enough to split into separate repos.

## What This Is

Jaysearch turns project work into explicit graph nodes and packet handoffs.

The core idea:

```text
research and planning define the work
governance validates legal state transitions
execution generates candidate artifacts
evaluation scores evidence
selection chooses a winner
apply happens only through a governed boundary
```

The current execution spine is:

```text
candidate_dag_manifest
  -> candidate_dag_selection
  -> dag_execution_unit_manifest
execution_unit
  -> candidate_patch_manifest
  -> implementation_attempt[]
  -> attempt_evaluation[]
  -> attempt_selection
  -> solution_artifact
  -> applied_solution
```

See the full node graph:

- [docs/toolchain-node-graph.mmd](docs/toolchain-node-graph.mmd)

Public site:

- <https://justin-napolitano.github.io/jaysearch/>

## Fast Demo

Run the fixture-backed demo:

```bash
bin/run-jaysearch-demo --root .
```

The demo proves the current graph-to-execution bridge:

```text
fixture candidate DAGs
  -> selected DAG
  -> execution units
  -> ERA smoke report
```

Outputs are written to:

```text
artifacts/demo/runs/<run_id>/
  demo-report.json
  demo-summary.md
```

This is a technical demo, not a production autonomy claim. It does not synthesize code, apply patches to the source worktree, or complete arbitrary repo tasks.

## Repository Map

- `src/platform_tools/`: Python tools and materializers.
- `bin/`: CLI wrappers for the tools.
- `spec/contracts/`: packet contracts and registry.
- `docs/`: research notes, policies, and design docs.
- `artifacts/`: DAGs, validation packets, generated run artifacts.
- `.agent/execplans/`: execution plans for build slices.
- `tests/`: contract, tool, and flow tests.

## Main Toolchain Nodes

- `problem_node`: a manageable project problem. Not executable.
- `node_option`: a candidate approach for a problem. Not executable.
- `execution_unit`: the first buildable work contract.
- `candidate_patch_manifest`: artifact-backed candidate patches for an execution unit.
- `implementation_attempt`: one candidate implementation attempt, usually with a patch ref.
- `attempt_evaluation`: evidence-backed evaluation of one attempt.
- `attempt_selection`: deterministic selection among evaluated attempts.
- `solution_artifact`: selected implementation result and completion evidence.
- `applied_solution`: isolated applied result after post-apply validation.

## Full Smoke Path

Given an execution unit and a candidate patch manifest:

```bash
bin/run-execution-era-loop-smoke \
  --root . \
  --execution-unit-path artifacts/execution-unit.packet.json \
  --candidate-patch-manifest-path artifacts/candidate-patch-manifest.packet.json \
  --validate-patch \
  --validate-patch-ref \
  --apply-solution
```

Given one patch file:

```bash
bin/run-execution-era-loop-smoke \
  --root . \
  --execution-unit-path artifacts/execution-unit.packet.json \
  --patch-source-path artifacts/change.patch \
  --validate-patch \
  --validate-patch-ref \
  --max-attempts 2 \
  --apply-solution
```

## Candidate Patch Manifest

Use this when you want multiple distinct candidate patches:

```bash
bin/materialize-candidate-patch-manifest \
  --root . \
  --execution-unit-path artifacts/execution-unit.packet.json \
  --patch-source-path artifacts/candidate-a.patch \
  --patch-source-path artifacts/candidate-b.patch \
  --validate-patches
```

The manifest preserves valid and invalid candidates. Invalid candidates remain visible with blockers instead of disappearing from the trace.

## Validation

Run the Jaysearch readiness gate:

```bash
bin/run-jaysearch-ci
```

Run the design review:

```bash
bin/design-iteration --root .
```

`bin/run-local-ci` remains available for legacy platform-template compatibility checks, but it is not the default Jaysearch readiness gate.

## Current Boundary

Jaysearch can now rank and apply supplied patch candidates in an isolated target.

The next major boundary is autonomous candidate generation: tools that synthesize candidate patches while emitting the same `candidate_patch_manifest` contract.
