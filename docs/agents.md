
# Agent Behavior

Agents may:

• Draft ExecPlans
• Generate TODO tasks
• Run validators

Agents may NOT:

• Finalize plans
• Push changes to protected branches
• Modify governance without ExecPlan approval

## Persona to Agent ID Mapping

Use a concrete `agent/<name>` identity for each operating persona.

- `agent/codex-01`: primary Codex implementation persona
- `agent/local-runner`: local validation and execution persona
- `agent/test-bot-01`: test/referee persona

If you introduce a new persona, add a new governed `agent/<name>` identity through an ExecPlan first.

## Audit Conventions

Every agent run must be traceable through:

- Branch name:
  - `draft-execplan/<plan-id>-<agent>-YYYYMMDD`
  - `impl-execplan/<plan-id>-<agent>-YYYYMMDD`
  - `queue-execplan/<queue-name>-<agent>-YYYYMMDD`
- ExecPlan frontmatter:
  - `owner: "agent/<name>"`
  - `draft_by: "agent/<name>"`
  - `draft_branch: "draft-execplan/..."`
- Commit metadata:
  - Use `bin/codex-commit "message"` for Codex-authored commits
  - Commit subject prefix includes agent identity (example: `[agent/codex-01]`)
  - Commit trailer includes `Agent: agent/<name>`

These conventions ensure persona-level actions are auditable across plans, branches, commits, and artifacts.

## Branch Roles

- `draft-execplan/*` is for plan drafting and review.
- `impl-execplan/*` is for one implementation ExecPlan slice.
- Parallel implementation slices should not share one implementation branch.
- `queue-execplan/*` is optional and should be treated as an integration branch, not as the sole execution branch for multiple slices.

## Finalization Direction

Governed ExecPlans should treat the signed merge commit on `main` as the canonical finalization event. A future `finalize-execplan` flow should derive finalization metadata from that merge event while preserving human signing authority.

## Board Review Runtime

GitHub Projects and other provider boards are review surfaces backed by
canonical local state. They are not workflow authorities.

Operational baseline:

- live sync requires the canonical field-map artifact
- existing project ids must be reused
- existing item ids must be updated rather than duplicated
- human review and takeover state should be recoverable from canonical
  local evidence without relying on agent session memory
