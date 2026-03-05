# Policy Index

This directory contains human-readable governance policy.

Machine-enforced rules live in `spec/` and are the canonical source for validators.

Policy files:

- `policy/execplans.md`
- `policy/agents.md`
- `policy/game-rules.md`

Rule source files:

- `spec/execplan.schema.yaml`
- `spec/governance.yaml`
- `spec/distribution.yaml`
- `spec/platform-architecture.yaml`
- `spec/ruleset.yaml`
- `spec/exit-codes.yaml`
- `spec/scoring.yaml`
- `spec/workflow.yaml`

Rule precedence:

1. `spec/*` (enforcement source)
2. `policy/*` (normative human text)
3. `docs/*` (explanatory guidance)
