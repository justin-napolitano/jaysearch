# Researcher Plugin Model

## Objective

Define how the external researcher repo extends its behavior without collapsing into one-off project logic.

## Plugin Families

### Study-Design Plugins

These encode method.

Examples:

- option comparison
- architecture evaluation
- vendor assessment
- permissions analysis
- literature-backed process validation
- pilot evaluation

A study-design plugin defines:

- required inputs
- evidence expectations
- synthesis method
- stopping conditions
- output artifact requirements

### Domain Plugins

These encode subject-matter context.

Examples:

- cloud architecture
- Snowflake data engineering
- healthcare registries
- governance and policy
- identity and permissions

A domain plugin defines:

- domain vocabulary
- relevant source classes
- domain-specific heuristics
- evidence weighting hints
- output formatting expectations where needed

## Resolution Model

Each run should resolve:

- exactly one study-design plugin
- zero or more domain plugins

The runtime should reject ambiguous or undeclared plugin combinations.

## Plugin Contract Requirements

Every plugin should declare:

- `plugin_id`
- `version`
- `plugin_family`
- `supported_contract_versions`
- `required_inputs`
- `provided_outputs`
- `validation_hooks`

## Safety Boundaries

Plugins may shape analysis and outputs.

Plugins may not:

- bypass artifact contracts
- write outside the declared output root
- suppress required evidence or attribution
- mutate governance contracts silently

## Suggested Plugin Registry Layout

```text
plugins/
  study_designs/
    option_comparison/
    architecture_evaluation/
    permissions_analysis/
  domains/
    cloud_architecture/
    snowflake/
    healthcare_registries/
```

## First Recommended Plugins

### Study Design

- `option-comparison`
- `architecture-evaluation`
- `method-validation`

### Domain

- `cloud-architecture`
- `snowflake-registry-workflows`
- `governed-research-ops`

## Review Rule

New plugins should be added through reviewable source control changes with contract tests, not through runtime-only local configuration.
