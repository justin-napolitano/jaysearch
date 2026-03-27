# Orchestrate Governed Slice API

This document defines the top-level terminal control-loop entrypoint for governed orchestration.

`bin/orchestrate-governed-slice` is intentionally thin. It should summarize one current orchestration turn by composing:

- `bin/get-control-plane-status`
- `bin/get-next-orchestration-action`
- post-merge reconciliation status

It must not invent a second orchestration authority surface.

## Contract Source

- canonical schema catalog: `spec/orchestrate-governed-slice-api.schema.yaml`

## Required Output Focus

- current branch, branch role, and initiative branch
- explicit target repo root
- aggregate blockers
- embedded control-plane status report
- embedded next-orchestration-action report
- projected next actions for the current turn

## Design Rules

- this command remains read-only and terminal-first
- managed repos are targeted only through explicit `repo_root`
- if the embedded control-plane APIs are blocked, this entrypoint must also block rather than guess
