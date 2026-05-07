# Researcher Repo Architecture

## Objective

Define the standalone repo that implements the researcher capability the platform control plane will orchestrate.

## Repo Role

The researcher repo is the execution engine for governed research work.

It owns:

- the research runtime
- study-design execution logic
- domain-specific research adapters
- artifact generation logic
- source gathering and synthesis workflows
- evidence-quality checks
- tests for the runtime and contracts

It does not own:

- cross-repo governance policy
- platform branch and ExecPlan rules
- direct authority to change platform contracts without review
- unmanaged writes into arbitrary repos

## Architectural Layers

### 1. Contract Layer

This layer defines stable machine-readable contracts for:

- request inputs
- execution state
- artifact outputs
- self-review outputs
- plugin registration

The platform repo should depend only on this layer, not on internal runtime modules.

### 2. Runtime Layer

This layer performs the research loop:

- ingest bounded request
- resolve study-design plugin
- resolve domain plugin
- gather sources
- synthesize evidence
- write governed outputs
- emit completion or follow-up state

### 3. Plugin Layer

Plugins should extend the runtime without modifying its core orchestration rules.

Two plugin families are required:

- study-design plugins
- domain plugins

### 4. Adapter Layer

Adapters bridge the runtime to concrete destinations and tools:

- bibliography adapter
- evidence-note adapter
- decision-log adapter
- status-report adapter
- filesystem or repo-output adapter

Adapters should remain narrow and replaceable.

## Suggested Repo Shape

```text
researcher-harness/
  README.md
  pyproject.toml
  src/researcher_harness/
    contracts/
    runtime/
    plugins/
      study_designs/
      domains/
    adapters/
    cli/
  tests/
    contracts/
    runtime/
    plugins/
  docs/
    architecture/
    plugin-development/
```

## Ownership Boundaries

The researcher repo should be independently:

- testable
- releasable
- versioned
- replaceable

The platform repo should orchestrate it through declared interfaces only.

## Delivery Boundary

The researcher repo may write only under a declared output root and only for artifact classes permitted by the invoked contract.

If a result requires platform-governance changes, the researcher repo must emit a review artifact rather than writing directly into platform-governed files.
