# ExecPlan Policy

ExecPlan requirements are defined in `spec/execplan.schema.yaml`.

Normative policy statements:

- All meaningful work must originate from an ExecPlan.
- ExecPlan identity uses canonical plan key format and matching filename stem.
- Required frontmatter and required sections are mandatory.
- Task limit is 20 and draft TTL is 14 days.
- Agents draft; humans finalize.
- ExecPlan implementation changes must be developed and reviewed on a dedicated ExecPlan branch; direct implementation commits to `main` are prohibited.
- Universal execution rule: repository actions (read/validate/edit/commit) must occur on a dedicated non-`main` branch.
- Branch compliance must satisfy workflow-specific branch naming patterns declared in `spec/ruleset.yaml` and `spec/workflow.yaml`.

Validator implementation must consume the schema spec directly instead of duplicating rule constants.
