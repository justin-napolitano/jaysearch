# Researcher MVP Backlog

## Objective

Define the smallest useful implementation path for the separate researcher repo.

## MVP Goal

The first release should support one governed research iteration from a bounded request to governed artifacts under a declared output root.

## Milestone 1: Contract and CLI Foundation

- define request and response schemas
- define artifact output schema expectations
- implement a CLI entrypoint for one bounded run
- add contract tests for supported request shapes

## Milestone 2: Core Runtime

- implement request validation
- implement plugin resolution for one study-design plugin
- implement output-root safety checks
- implement machine-readable completion summary

## Milestone 3: Artifact Adapters

- bibliography update adapter
- evidence note adapter
- decision-log update adapter
- status-report adapter

These should support the current research package layout already used in metadata repos.

## Milestone 4: Initial Plugin Set

### Study Design

- `option-comparison`

### Domain

- `cloud-architecture`
- `snowflake-registry-workflows`

This is enough to execute the current architecture-research use case.

## Milestone 5: Self-Review Output

- emit explicit self-critique artifact
- emit harness-improvement proposal artifact when appropriate
- keep self-review separate from direct platform mutation

## Milestone 6: Platform Integration

- add a platform plugin or command wrapper that invokes the external repo
- validate returned outputs against the platform contract
- record a summarized execution result in governed artifacts

## Explicit Non-Goals for MVP

- multi-agent parallel orchestration
- autonomous cross-repo edits without review
- direct governance mutation
- generalized API server before the CLI surface is stable

## Exit Criteria

The MVP is complete when a governed repo can invoke the external researcher against one bounded question and receive validated bibliography, evidence, status, and summary artifacts without undocumented manual steps.
