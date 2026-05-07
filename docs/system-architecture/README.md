# System Architecture

## Objective

Define the platform as the control plane for governed cross-repo capabilities.

The immediate target is a researcher capability that is:

- implemented outside the platform repo
- orchestrated by the platform repo
- contract-bound at repo boundaries
- able to critically review its own harness without directly self-authorizing drift

## Package

- `control-plane-principles.md`
- `cross-repo-boundaries.md`
- `orchestration-model.md`
- `research-capability-contract.md`
- `researcher-self-improvement-loop.md`

## Operating Model

The platform repo should own:

- governance
- orchestration contracts
- capability registry rules
- repo boundary rules
- execution policy

The platform repo should not own:

- the full implementation of every specialized subsystem
- direct cross-repo imports into private internals
- uncontrolled mutation of target repos

## First Capability

The first externalized capability should be the researcher engine.

That capability should:

- accept one bounded research task
- execute under explicit artifact contracts
- emit governed outputs into a declared destination
- surface self-critique and improvement proposals as review artifacts, not silent self-modifications
