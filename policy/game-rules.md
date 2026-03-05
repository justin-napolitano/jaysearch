# Game Rules Policy

The game model is defined in:

- `spec/ruleset.yaml`
- `spec/scoring.yaml`
- `spec/workflow.yaml`
- `spec/exit-codes.yaml`

Activation gate:

- Ruleset remains `NO-GO` until a human marks `APPROVED-RULESET` and lands an SSH-signed approval commit.

Referee commands and outputs must be deterministic and machine-readable.
