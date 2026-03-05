# ExecPlan Policy

ExecPlan requirements are defined in `spec/execplan.schema.yaml`.

Normative policy statements:

- All meaningful work must originate from an ExecPlan.
- ExecPlan identity uses canonical plan key format and matching filename stem.
- Required frontmatter and required sections are mandatory.
- Task limit is 20 and draft TTL is 14 days.
- Agents draft; humans finalize.

Validator implementation must consume the schema spec directly instead of duplicating rule constants.
