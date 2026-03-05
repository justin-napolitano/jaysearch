# Platform Program Migration Table

## Target 5-Plan Model

1. `platform-architecture-lock`
2. `platform-kernel-implementation`
3. `platform-governance-enforcement`
4. `platform-distribution`
5. `platform-adoption-pilot`

Execution rule:

- A plan cannot execute while any dependency remains in `draft`.
- Only one target plan may be `executing` at a time.

## Source Draft -> Target Mapping

| Source Draft Plan ID | Target Plan | Disposition | Notes |
|---|---|---|---|
| `20260305-platform-program-architecture-codex-01-execplan` | `platform-architecture-lock` | Keep | Becomes authoritative architecture contract. |
| `20260305-platform-core-packageization-codex-01-execplan` | `platform-distribution` | Merge | Package/CLI contract belongs to distribution lane. |
| `20260305-platform-template-extraction-sync-codex-01-execplan` | `platform-distribution` | Merge | Template sync and drift controls belong to distribution lane. |
| `20260305-platform-governance-required-checks-codex-01-execplan` | `platform-governance-enforcement` | Keep | Required checks and protection contracts. |
| `20260305-platform-exception-lifecycle-enforcement-codex-01-execplan` | `platform-governance-enforcement` | Merge | Exception model is governance subdomain. |
| `20260305-platform-manual-update-rollout-codex-01-execplan` | `platform-adoption-pilot` | Split | Rollout operations split: runbook part to adoption, mechanics to distribution. |
| `20260305-platform-pilot-repo-migration-codex-01-execplan` | `platform-adoption-pilot` | Keep | Pilot migration and promotion decision. |

## Admission Gates (Hard)

A plan is eligible for execution only if all are true:

- dependencies are `approved` or `completed` (not `draft`)
- `changes` contains concrete files, not broad placeholder-only directories
- acceptance criteria map to deterministic commands with expected exits
- scope does not overlap with any active plan in the same execution wave
- branch naming and commit identity policy checks pass

## Recommended Immediate Sequence

1. Finalize `platform-architecture-lock`.
2. Create `platform-kernel-implementation` plan by extracting currently scattered validator/runtime hardening work.
3. Merge governance plans into one `platform-governance-enforcement` plan with explicit sub-scopes.
4. Merge distribution plans into one `platform-distribution` plan (core package + template sync).
5. Execute `platform-adoption-pilot` only after previous four are accepted.


## Source Draft Preservation Note

The pre-consolidation platform program drafts were checkpointed for later revision in:

- branch: `draft-execplan/platform-program-drafts-codex-01-20260305`
- commit: `d254c1e`

Execution-prep action:

- keep only the target 5-plan set active on `main`
- treat checkpointed source drafts as superseded planning material unless explicitly revived
