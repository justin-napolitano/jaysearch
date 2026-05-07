# Orchestration Model

## Objective

Define how the platform control plane should route work to an external capability such as a researcher engine.

## High-Level Flow

```text
platform repo
  -> governed plan or worker contract
  -> capability invocation contract
  -> external capability repo
  -> validated artifacts
  -> declared target repo output root
  -> governed review and merge flow
```

## Core Elements

### 1. Capability Registry

The platform should know:

- capability name
- invocation surface
- required inputs
- allowed outputs
- validation rules

### 2. Invocation Contract

For each run, the control plane should pass:

- capability id
- task id
- input artifact paths
- output destination root
- execution mode
- review expectations

### 3. Output Validation

The platform should validate:

- allowed artifact types
- required artifact presence
- schema conformance where applicable
- destination-root compliance

### 4. Review Surface

Every run should emit:

- result summary
- artifact inventory
- unresolved issues
- self-review or critique if applicable

## Failure Model

The control plane should fail closed when:

- destination root is ambiguous
- capability contract is missing
- required outputs are missing
- validation fails
- the capability proposes governance-changing updates without an explicit review artifact
