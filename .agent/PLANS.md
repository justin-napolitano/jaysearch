# PLANS.md

This document defines the **ExecPlan system** used in this repository.

ExecPlans are the primary mechanism used to plan, execute, and validate
work performed by humans and agents. They ensure all changes are
traceable, auditable, and reproducible.

This repository follows **plan‑driven development**.

All meaningful work must originate from an ExecPlan.

------------------------------------------------------------------------

# Core Principles

1.  Every meaningful change must originate from an ExecPlan.
2.  ExecPlans are **living documents**.
3.  Agents draft work.
4.  Humans finalize work.
5.  Finalization requires a **signed commit**.
6.  Validation must be deterministic and machine‑checkable.

------------------------------------------------------------------------

# What is an ExecPlan

An ExecPlan is a structured markdown document that:

• Defines the work to be done\
• Records design decisions\
• Tracks progress\
• Defines validation criteria\
• Captures evidence of completion

ExecPlans live in:

.agent/execplans/

File naming convention:

YYYYMMDD-`<plan-name>`{=html}-`<owner>`{=html}-execplan.md

Example:

20260304-platform-validator-jnapolitano-execplan.md

------------------------------------------------------------------------

# ExecPlan Structure

Every ExecPlan must include the following sections.

Required headings:

Purpose / Big Picture\
Progress\
Surprises & Discoveries\
Decision Log\
Outcomes & Retrospective\
Context and Orientation\
Plan of Work\
Concrete Steps\
Validation and Acceptance\
Idempotence and Recovery\
Artifacts and Notes\
Interfaces and Dependencies

Validators must enforce the presence of these sections.

------------------------------------------------------------------------

# Required Frontmatter

Each ExecPlan must contain YAML frontmatter.

Required fields:

id\
title\
owner\
created\
status\
base_branch\
changes\
approve_policy\
reviewers

Draft metadata:

draft_by\
draft_branch\
draft_created

Finalization metadata:

finalized_by\
finalized_at\
finalized_in_pr

Optional fields:

validation\
tasks\
depends_on

------------------------------------------------------------------------

# Status Values

Valid status values:

draft\
proposed\
approved\
executing\
completed\
archived

Agents may only create ExecPlans with:

status: draft

Only humans may change status beyond draft.

------------------------------------------------------------------------

# Draft Workflow

ExecPlans must be drafted on branches named:

draft-execplan/`<plan-id>`{=html}-`<agent>`{=html}-YYYYMMDD

Example:

draft-execplan/platform-validator-codex-20260304

Draft plans must include:

draft_by\
draft_branch\
draft_created

Agents must populate the `changes` field with explicit paths.

------------------------------------------------------------------------

# Implementation Workflow

Implementation execution should occur on branches named:

impl-execplan/`<plan-id>`{=html}-`<agent>`{=html}-YYYYMMDD

Parallel implementation ExecPlans must use distinct implementation branches.

Optional integration branches may be named:

queue-execplan/`<queue-name>`{=html}-`<agent>`{=html}-YYYYMMDD

Queue branches are for deliberate stacking and integration only. They do
not replace the canonical implementation branch for an individual
ExecPlan slice.

------------------------------------------------------------------------

# Human Finalization

An ExecPlan becomes authoritative only after human finalization.

Finalization requirements:

• SSH signed commit • ExecPlan frontmatter updated • status changed to
`proposed` or `approved` • finalized_by set to GitHub username •
finalized_at timestamp added

Commit message must include:

Metadata: ExecPlan: `<id>`{=html}

Signed-off-by: `<github-user>`{=html}

Validators must confirm the commit signature matches the finalizer
identity.

For governed ExecPlans, the signed merge commit on `main` is the
canonical finalization event. Future automation should derive
`finalized_by`, `finalized_at`, and `finalized_in_pr` from that merge
event where feasible.

`finalized_by` must be resolved through the signer identity map defined
in `spec/governance.yaml`. Repository prose alone is not a sufficient
source of finalizer identity for automated completion reconciliation.

When a governed ExecPlan has a deterministic merge-backed reconciliation
path, `status: completed` should be set from that canonical merge event.
Completion should not depend on manual prose follow-up when merge
evidence is already machine-detectable.

If the merge event, signature verification result, or finalizer identity
cannot be derived deterministically, reconciliation must fail with
explicit blockers rather than silently leaving an authoritative plan in
an ambiguous state.

Board review runtime:

The external review board is a projection of canonical local state. It
must not become a second authority source.

Operational rules:

- live board sync requires the canonical field-map artifact
- known project ids must be reused rather than replaced
- known item ids must be updated rather than duplicated
- human operations and takeover state must be derivable from canonical
  local evidence without relying on session memory

------------------------------------------------------------------------

# Validation

ExecPlans must define validation criteria.

Example validation block:

validation: tests: - name: execplan_lint command: bin/execplan-validate
expected_exit: 0

Validation tools must verify:

• structure\
• frontmatter schema\
• signature rules\
• security checks

Exit codes:

0 = success\
1 = structural error\
2 = security failure

------------------------------------------------------------------------

# Tasks and TODO Generation

ExecPlans may define tasks.

Example:

tasks: - title: Implement ExecPlan validator priority: P1

Tasks can automatically generate TODO entries.

TODO tracking is stored in:

TODO.md

------------------------------------------------------------------------

# ExecPlan Dependencies

ExecPlans may depend on other plans.

Example:

depends_on: - platform-validator-20260304

Validators must ensure dependency order is respected.

------------------------------------------------------------------------

# Task Limits

ExecPlans must not exceed:

20 tasks

Large work must be split into multiple plans.

------------------------------------------------------------------------

# Draft Expiration

Draft ExecPlans expire after:

14 days

Expired drafts must be refreshed, finalized, or archived.

------------------------------------------------------------------------

# Audit Artifacts

After finalization a signed artifact should be generated.

Location:

.agent/audit/

Format:

`<plan-id>`{=html}.`<commit-sha>`{=html}.signed.json

Artifacts record:

plan_id\
draft_shas\
final_sha\
finalizer\
timestamp\
optional metrics\
evidence

------------------------------------------------------------------------

# Metrics

Agent behavior is evaluated using deterministic metrics defined in:

.agent/metrics.yml

Examples:

Draft Quality (DQ)\
Human Edit Distance (HED)\
Validation Pass Rate (VPR)\
Security Lint Score (SLS)\
Behavioral Correctness (BC)

Metrics must be deterministic and transparent.

------------------------------------------------------------------------

# Exception Process

Emergency changes require:

1.  Draft ExecPlan marked security/important
2.  Human review documented
3.  Signed human finalization commit

Agents may not bypass this process.

------------------------------------------------------------------------

# Changing This Document

Changes to PLANS.md require a dedicated ExecPlan.

Example:

agent-policy-update-YYYYMMDD

The ExecPlan must be finalized via a signed commit before this document
can change.

------------------------------------------------------------------------

# Initial Version

This document establishes the ExecPlan system used by this repository.
