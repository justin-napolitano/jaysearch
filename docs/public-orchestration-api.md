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

## Contract Source

- canonical schema catalog: `spec/public-orchestration-api.schema.yaml`
- each command now has:
  - one request definition under `$defs/request_*`
  - one response definition under `$defs/response_*`
- orchestrators should bind against those definitions, not infer fields from terminal examples

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
- request schema: `#/$defs/request_get_graph_state`
- response schema: `#/$defs/response_get_graph_state`
- example call:
  - `bin/get-graph-state --initiative-branch initiative/worker-orchestration-api`

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
- request schema: `#/$defs/request_resolve_worker_contract`
- response schema: `#/$defs/response_resolve_worker_contract`
- example call:
  - `bin/resolve-worker-contract --initiative-branch initiative/example`
  - `bin/resolve-worker-contract --contract-id contract-1`

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
- request schema: `#/$defs/request_run_worker_contract`
- response schema: `#/$defs/response_run_worker_contract`
- example call:
  - `bin/run-worker-contract --contract-id contract-1 --executor local_clone --push-mode staging`

`bin/run-research-capability`
- invokes the external `researcher-harness` repo through its CLI contract
- required inputs:
  - `--researcher-root`
  - `--request-path`
- optional input:
  - `--python-executable`
- output focus:
  - request id
  - research status
  - output root
  - recommendation
  - summary artifact path
  - self-review artifact path
  - structured improvement targets
  - structured improvement proposals
  - ranked improvement candidates
  - promotable candidate subset
  - follow-up questions proposed by the researcher
- request schema: `#/$defs/request_run_research_capability`
- response schema: `#/$defs/response_run_research_capability`
- example call:
  - `bin/run-research-capability --researcher-root ../researcher-harness --request-path /path/to/request.json`

`bin/prepare-research-followups`
- reads a completed `run-research-capability` report and emits deterministic draft follow-up inputs from ranked candidates
- required inputs:
  - `--report-path`
  - `--output-root`
- optional inputs:
  - `--max-promotions`
  - `--minimum-total-score`
- output focus:
  - source request and question provenance
  - applied promotion gate
  - selected promotable candidates
  - deferred candidates
  - follow-up questions
  - generated draft follow-up artifact path
- request schema: `#/$defs/request_prepare_research_followups`
- response schema: `#/$defs/response_prepare_research_followups`
- example call:
  - `bin/prepare-research-followups --report-path /path/to/research-report.json --output-root /path/to/prepared-followups`

`bin/project-research-followup-packets`
- reads a prepared follow-up artifact and emits repo-specific follow-up packets
- required inputs:
  - `--prepared-followups-path`
  - `--output-root`
- output focus:
  - source request and question provenance
  - platform ExecPlan seed packets
  - external repo follow-up request packets
  - generated packets artifact path
- request schema: `#/$defs/request_project_research_followup_packets`
- response schema: `#/$defs/response_project_research_followup_packets`
- example call:
  - `bin/project-research-followup-packets --prepared-followups-path /path/to/draft-followups.json --output-root /path/to/projected-packets`

`bin/materialize-research-followup-assets`
- reads projected repo follow-up packets and writes actual handoff assets
- required inputs:
  - `--packets-path`
  - `--output-root`
- output focus:
  - source request and question provenance
  - platform seed file paths
  - external repo request packet paths
  - generated manifest path
- request schema: `#/$defs/request_materialize_research_followup_assets`
- response schema: `#/$defs/response_materialize_research_followup_assets`
- example call:
  - `bin/materialize-research-followup-assets --packets-path /path/to/projected-packets.json --output-root /path/to/materialized-assets`

`bin/render-platform-execplan-drafts`
- reads materialized platform seed assets and renders draft ExecPlan candidate files
- required inputs:
  - `--materialized-manifest-path`
  - `--output-root`
- output focus:
  - source request and question provenance
  - rendered draft file paths
  - generated draft manifest path
- request schema: `#/$defs/request_render_platform_execplan_drafts`
- response schema: `#/$defs/response_render_platform_execplan_drafts`
- example call:
  - `bin/render-platform-execplan-drafts --materialized-manifest-path /path/to/materialized-assets.json --output-root /path/to/rendered-drafts`

`bin/start-next-worker`
- composite helper
- resolves the next runnable worker contract for an initiative and runs it
- intended for thin orchestrators that do not need separate resolve/run phases
- request schema: `#/$defs/request_start_next_worker`
- response schema: `#/$defs/response_start_next_worker`
- example call:
  - `bin/start-next-worker --initiative-branch initiative/example --executor local_clone --push-mode staging`

`bin/get-worker-status`
- returns compact worker session and recent-run state
- optional input: `--worker-id`
- output focus:
  - active workers
  - failed workers
  - abandoned workers
  - recent runs
- request schema: `#/$defs/request_get_worker_status`
- response schema: `#/$defs/response_get_worker_status`
- example call:
  - `bin/get-worker-status --worker-id example-worker`

## Stable Calling Rules

- send only documented request fields
- treat undocumented output fields as non-contractual unless they are added to the schema for the current version
- branch orchestration on `command`, `status`, `ok`, and command-specific required fields
- fail closed when `api_version` is unknown
- prefer explicit ids (`contract_id`, `worker_id`, `initiative_branch`) over title matching or freeform text

## Contract Validation

- use `bin/public-orchestration-api-check` to validate that live facade outputs still conform to the versioned contract catalog
- governed pre-push checks now include this validator so schema drift is blocked before merge

## Design Rules

- APIs are machine-oriented and compact.
- Facade responses are versioned so orchestrators can validate one stable contract.
- Governance stays underneath the facade.
- Executor choice is explicit and backend-oriented.
- Push policy is explicit and backend-oriented.
- Unsupported backends fail closed.
- These commands are stable facade surfaces; lower-level commands remain internal implementation details unless promoted deliberately.
