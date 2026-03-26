# Public Orchestration API

This is the thin orchestration-facing surface over the governed worker runtime. The canonical authority still lives underneath in:

- remaining-work graph
- ExecPlans
- worker contract registries
- leases, runtime artifacts, and reconciliation state

Orchestrators should prefer these commands instead of calling lower-level internal commands directly.

## Versioning

- all facade responses use the versioned envelope in `spec/public-orchestration-api.schema.yaml`
- current version: `public-orchestration.v1`
- required top-level fields:
  - `api_version`
  - `command`
  - `status`
  - `ok`
- additive fields are allowed within a version; breaking field or semantic changes require a new `public-orchestration.vN` value

## Commands

`bin/get-graph-state`
- returns a compact projection of graph state
- optional input: `--initiative-branch`
- output focus:
  - graph id
  - last action id
  - initiative nodes
  - active node
  - queued nodes

`bin/resolve-worker-contract`
- resolves one explicit or next runnable worker contract
- optional inputs:
  - `--initiative-branch`
  - `--contract-id`
  - `--branch`
  - `--worker-id`
- output focus:
  - initiative branch
  - contract id
  - execplan id
  - worker branch
  - worker id

`bin/run-worker-contract`
- runs one resolved worker contract through the governed worker runtime
- explicit backend controls:
  - `--executor local_clone|local_worktree`
  - `--push-mode none|staging|github|staging_and_github`
- optional task controls:
  - `--task-command`
  - `--commit`
  - `--create-pr`
  - `--cleanup`

`bin/start-next-worker`
- composite helper
- resolves the next runnable worker contract for an initiative and runs it
- intended for thin orchestrators that do not need separate resolve/run phases

`bin/get-worker-status`
- returns compact worker session and recent-run state
- optional input: `--worker-id`
- output focus:
  - active workers
  - failed workers
  - abandoned workers
  - recent runs

## Design Rules

- APIs are machine-oriented and compact.
- Facade responses are versioned so orchestrators can validate one stable contract.
- Governance stays underneath the facade.
- Executor choice is explicit and backend-oriented.
- Push policy is explicit and backend-oriented.
- Unsupported backends fail closed.
- These commands are stable facade surfaces; lower-level commands remain internal implementation details unless promoted deliberately.
