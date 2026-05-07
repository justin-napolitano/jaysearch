# Research Capability Contract

## Objective

Define the first external capability the platform should orchestrate: the researcher engine.

## Capability Purpose

The researcher capability exists to:

- evaluate bounded questions
- gather evidence
- maintain bibliography and decision artifacts
- synthesize recommendations
- surface self-critique and improvement proposals

## Inputs

Required:

- research topic or question id
- target repo or output root
- study-design or plugin id
- artifact contract version

Optional:

- required sources
- stop conditions
- review depth

## Outputs

Expected outputs should include:

- bibliography updates
- evidence notes
- decision-log updates when conclusions are stable
- status or iteration updates
- summary artifact for the invoking control plane

## Capability Rules

- the capability may critique its own method
- the capability may propose harness changes
- the capability may not directly self-authorize governance changes in the platform repo
- any harness-improvement proposal must appear as an explicit review artifact

## Validation Expectations

The platform should verify:

- outputs were written only under the declared destination root
- required artifact classes exist
- any self-improvement proposal is surfaced as review material, not silent mutation
