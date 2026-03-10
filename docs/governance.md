# Governance

Authority model:

- Agents draft work.
- Humans finalize work.

Finalization requires:

- SSH signed commit
- Updated ExecPlan frontmatter
- Metadata reference to ExecPlan id

Bypass/exception approvals require:

- Human approver identity
- Accountable owner
- Explicit rationale
- Expiry timestamp

Required check contract:

- Canonical check contract is defined in `spec/governance.yaml`.
- Check names must be stable snake_case and map to one deterministic command.
- Current required checks: `execplan_validate`, `sync_todos`, `repo_health_check`, `execplan_spec_tests`, `run_local_ci`.

Implementation slice validation rule:

- Every implementation ExecPlan must include at least one dedicated smoke-test command in its validation section.
- The smoke-test command should exercise the primary path for that implementation slice in one invocation.
- A slice is not merge-ready until its smoke-test command passes.

Exception lifecycle contract:

- Exception registry file: `.agent/governance/exceptions.yaml`.
- Required fields include owner, approver, rationale, created/expires timestamps, and bypass evidence.
- Active exceptions may not be expired.
- Exceptions nearing expiry (within renewal window) require renewal evidence.
