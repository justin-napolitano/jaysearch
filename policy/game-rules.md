# Game Rules Policy

The game model is defined in:

- `spec/ruleset.yaml`
- `spec/scoring.yaml`
- `spec/workflow.yaml`
- `spec/exit-codes.yaml`

Activation gate:

- Ruleset remains `NO-GO` until a human marks `APPROVED-RULESET` and lands an SSH-signed approval commit.

Referee commands and outputs must be deterministic and machine-readable.

Universal branch-first policy:

- All repository actions must run on a dedicated non-`main` branch.
- Running execution/validation flows on `main` or `master` is a policy violation.
- Validators must emit machine-readable branch-policy findings and fail deterministically on violation.

Hostile review policy:

- Hostile review runs must execute on a dedicated branch matching
  `draft-execplan/hostile-review-<agent>-YYYYMMDD`.
- Auditable artifacts are mandatory:
  - `artifacts/review/hostile-review-report.json`
  - `artifacts/review/hostile-review-summary.md`
  - `artifacts/review/validation-evidence.json`
- Validation commands must run in deterministic order:
  1. `bin/execplan-validate .agent/execplans/*.md`
  2. `bin/sync-todos`
  3. `bin/repo-health-check`
  4. `bin/execplan-test`
  5. `bin/run-local-ci`
