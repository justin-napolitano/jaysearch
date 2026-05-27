# Jaysearch Demo Runner V1

## Objective

Create a short, repeatable demo path that proves Jaysearch can turn graph-shaped planning work into executable units and a governed ERA smoke report.

The demo is intentionally fixture-backed. It is meant for explanation and interview presentation, not as a claim that autonomous candidate generation is production-ready.

```text
fixture candidate DAGs
  -> candidate_dag_manifest
  -> select_candidate_dag
  -> materialize_selected_dag_execution_units
  -> run_execution_era_loop_smoke
  -> demo_report + demo_summary
```

## Scope

In scope:

- one command: `bin/run-jaysearch-demo`
- fixture DAG generation inside an isolated demo run directory
- candidate DAG selection using the real selector
- selected DAG to execution-unit materialization using the real materializer
- one metadata-only ERA smoke run for the first execution unit
- machine-readable `demo-report.json`
- presentation-friendly `demo-summary.md`
- README and Pages updates

Out of scope:

- autonomous candidate generation
- applying patches to the worktree
- claiming arbitrary repo task completion
- long-lived artifact retention policy

## Demo Claim

The demo proves:

- Jaysearch can evaluate competing DAG-shaped plans.
- Invalid or weaker plans remain visible instead of disappearing.
- The selected DAG can be converted into execution units.
- Execution units can enter the existing ERA packet loop.

The demo does not prove:

- real code synthesis
- semantic correctness of generated code
- production orchestration retries
- hosted CI reliability

## Acceptance

- `bin/run-jaysearch-demo --root .` exits `0`
- output includes `demo-report.json` and `demo-summary.md`
- demo report links selection, selected DAG, execution-unit manifest, execution units, and ERA smoke report
- tests cover the demo runner without writing outside a temp root
- Jaysearch CI includes the demo runner test
