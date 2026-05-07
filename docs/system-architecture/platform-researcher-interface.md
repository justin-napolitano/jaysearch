# Platform to Researcher Interface

## Objective

Define the stable interface the platform repo should use to invoke the external researcher repo.

## Integration Principle

The platform should interact with the researcher repo through a narrow CLI or API contract, not through cross-repo imports.

The first usable interface should be CLI-first.

## Required Request Fields

The platform should supply:

- request id
- research question or topic id
- study-design plugin id
- artifact contract version
- output root

Optional fields:

- domain plugins
- required sources
- stop conditions
- review depth
- destination repo metadata

## Required Response Surface

The researcher should return:

- run status
- output root actually used
- artifact summary
- follow-up requirement state
- self-review artifact ref if generated

## Suggested CLI Shape

```text
researcher-harness run \
  --request-id <id> \
  --question-id <question> \
  --study-design <plugin-id> \
  --artifact-contract <version> \
  --output-root <path> \
  [--domain-plugin <plugin-id> ...]
```

## Platform Responsibilities

The platform repo should:

- validate that the request is governed and bounded
- resolve the correct destination root
- invoke the external runtime
- verify required outputs exist
- record resulting status in governed artifacts if needed

## Researcher Responsibilities

The researcher repo should:

- validate request shape
- reject unsupported plugin or contract combinations
- write only permitted artifacts
- return a machine-readable summary
- surface self-improvement proposals as explicit outputs

## Output Validation

The platform should verify:

- outputs stayed under the declared root
- required artifact classes were produced
- missing-evidence or blocked states are explicit
- self-improvement proposals are separated from ordinary research outputs

## Evolution Rule

If the interface changes, contract versions should advance explicitly and the platform should remain compatible only with declared supported versions.
