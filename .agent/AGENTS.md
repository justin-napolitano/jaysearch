# AGENTS.md

Agent policy for this repository. This file defines how automated agents
(including Codex and local automation) are allowed to interact with the
repository and how human authority is preserved.

This repository follows a **plan-driven development model**. Agents
operate only through ExecPlans and never bypass governance.

------------------------------------------------------------------------

# Purpose

This document establishes:

• Agent capabilities and restrictions\
• ExecPlan draft workflow rules\
• Human finalization authority\
• Canonical metadata formats\
• Validation expectations\
• Audit and provenance requirements

All agent moves inherit platform board law before any local game or
phase rule is considered.

Agents **draft** work.\
Humans **finalize** work.

Every new Codex session and every worker session must bootstrap from
repository-local governance state before doing meaningful work.

------------------------------------------------------------------------

# Identity Model

Agents and humans must use canonical identifiers.

Agent format:

agent/`<agent-name>`{=html}

Example:

agent/codex-01

Human format:

github:`<username>`{=html}

Example:

github:jay.napolitano

Signer identity:

signer:`<ssh-key-fingerprint>`{=html}

------------------------------------------------------------------------

# Seeded Agent Identities

Initial seeded agents:

agent/codex-01\
agent/local-runner\
agent/test-bot-01

Initial human maintainer:

github:jay.napolitano

New identities must be introduced via an ExecPlan.

------------------------------------------------------------------------

# Allowed Agent Actions

Agents MAY:

• Read repository files\
• Propose ExecPlans on draft branches\
• Generate TODO entries in draft state\
• Run local validators and produce JSON output\
• Suggest reviewers and approval policies\
• Open draft pull requests labeled `agent/draft`

Agents may optimize behavior using metrics defined in:

.agent/metrics.yml

------------------------------------------------------------------------

# Forbidden Agent Actions

Agents MUST NOT:

• Finalize ExecPlans\
• Set finalized_by or finalized_at metadata\
• Push ExecPlan changes to protected branches\
• Bypass CODEOWNERS or branch protections\
• Modify governance files without an approved ExecPlan\
• Store secrets or credentials in repository artifacts\
• Create releases or tags that change governance rules\
• Forge Signed-off-by metadata

These forbidden moves are part of global board law, not just local phase
policy.

------------------------------------------------------------------------

# Draft Workflow

Agents must create ExecPlans only on branches matching:

draft-execplan/`<plan-id>`{=html}-`<agent>`{=html}-YYYYMMDD

Example:

draft-execplan/platform-validator-codex-20260304

ExecPlans must be stored in:

.agent/execplans/

Draft ExecPlan frontmatter must include:

id\
title\
owner\
created\
status: draft\
draft_by\
draft_branch\
draft_created\
changes

Agents must populate `changes` with explicit paths.

Implementation Workflow

Approved governed implementation work should execute under one bounded
initiative-scoped ExecPlan authority.

Worker implementation branches should match:

impl-execplan/`<initiative-scope>`{=html}-`<worker>`{=html}

Parallel workers must not share one implementation branch or worker
contract.

Optional queue branches may be used for deliberate integration stacking:

queue-execplan/`<queue-name>`{=html}-`<agent>`{=html}-YYYYMMDD

Queue branches do not replace the requirement for one worker branch per
active worker contract.

Session Bootstrap Rules

Before a new Codex session or worker session performs meaningful work, it
must:

• read repository-local governance state from `.agent/AGENTS.md`,
  `.agent/PLANS.md`, `spec/workflow.yaml`, and the active ExecPlan when
  one exists\
• determine the current branch role and stop if execution resolves to
  `main` or another protected branch\
• determine whether the session is acting as an initiative coordinator,
  draft-plan author, implementation worker, or integration-only queue
  session\
• inherit the authority limits of that branch role rather than invent a
  new session-local rule set\
• stop when the active ExecPlan, graph state, branch role, or required
  protected artifacts are ambiguous

Worker session-specific rules:

• one worker session maps to one isolated checkout or container-local
  clone\
• one worker session maps to one unique working branch\
• one worker session may execute at most one bounded lease or task scope
  at a time\
• one worker session must map to one initiative-owned worker contract
  before meaningful implementation work begins\
• one worker session must hold one active worker-session lease artifact
  before meaningful implementation work begins\
• worker sessions must not share one mutable filesystem checkout\
• worker sessions must reconcile outputs through Git commits, validator
  output, and pull-request or merge evidence rather than session memory\
• worker-session lease issue and close actions must leave durable audit
  records in repository-local artifacts\
• worker sessions must die after handoff; they are not durable authority
  holders

------------------------------------------------------------------------

# Human Finalization Rules

ExecPlans become authoritative only after a **human-signed commit**.

Finalization requirements:

• Commit must be SSH-signed\
• Commit must update ExecPlan frontmatter\
• `status` must change to `proposed` or `approved`\
• `finalized_by` must match commit signer\
• `finalized_at` must contain ISO8601 UTC timestamp

Commit message must include:

Metadata: ExecPlan: `<id>`{=html}

Signed-off-by: `<github-user>`{=html}

Signature verification must succeed.

Governed ExecPlan finalization should treat the signed merge commit on `main` as the canonical authority event. Future automation may prepare finalization metadata, but human authority remains at the signed merge boundary.

When merge-backed reconciliation is available, governed ExecPlans should
be updated to `status: completed` from that canonical merge event rather
than left in draft-shaped metadata indefinitely.

Deterministic reconciliation may derive:

• `finalized_at` from the merge commit timestamp\
• merge-backed `finalized_in_pr` from the merge commit subject\
• `finalized_by` from the signed merge identity after resolving it
through the canonical signer identity map in `spec/governance.yaml`

If merge history, signature verification, or identity mapping is
ambiguous, the reconciliation command must block rather than infer
completion.

Board review runtime rules:

• synced provider boards are review surfaces, not authority sources\
• live board sync requires the canonical field-map artifact\
• once a project id is known, bootstrap should reuse that board rather
than fabricate a replacement\
• once item ids are known, sync should prefer item updates rather than
new item creation\
• human-operations runtime output must be takeover-safe so another human
or agent can continue from canonical state alone

Policy-compliance rules:

• governed slices must not advance by agent assertion, prose judgment,
  or board edits alone\
• policy compliance and downstream referees must pass before a slice can
  claim review-readiness or later completion\
• graph and queue reconciliation are part of governed branch legality,
  not post hoc cleanup

------------------------------------------------------------------------

# ExecPlan Metadata Schema

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

Optional:

validation\
tasks\
depends_on

------------------------------------------------------------------------

# Timestamp Rules

All timestamps must use ISO8601 UTC format.

Example:

2026-03-04T17:00:00Z

Validators should reject timestamps more than one hour in the future.

------------------------------------------------------------------------

# Validation Expectations

Validation tools must enforce:

1.  Filename matches ExecPlan id
2.  Required frontmatter exists
3.  Required headings exist
4.  `changes` field is populated
5.  Draft branches are used correctly
6.  SSH signatures match finalizer identity
7.  No secret material exists
8.  Task count does not exceed limits

Exit codes:

0 = success\
1 = structural failure\
2 = security failure

------------------------------------------------------------------------

# Audit Artifacts

After finalization, tools must produce a signed artifact stored under:

.agent/audit/

Artifact format:

`<plan-id>`{=html}.`<final-sha>`{=html}.signed.json

The artifact records:

plan_id\
draft_shas\
final_sha\
finalizer\
timestamp\
optional metrics\
evidence logs

Local artifacts may later be moved to immutable storage.

------------------------------------------------------------------------

# Metrics and Optimization

Agents may optimize behavior using deterministic metrics defined in:

.agent/metrics.yml

Example metrics:

Draft Quality (DQ)\
Human Edit Distance (HED)\
Validation Pass Rate (VPR)\
Security Lint Score (SLS)\
Behavioral Correctness (BC)

Metrics must remain deterministic and publicly documented.

Random human audits should review approximately 5--10% of finalized
plans.

------------------------------------------------------------------------

# Exception Process

Emergency changes require:

1.  Draft ExecPlan flagged with security/important
2.  Human review recorded in Decision Log
3.  Human signed finalization commit

No agent may bypass this process.

------------------------------------------------------------------------

# Revision Policy

Changes to this file require a dedicated ExecPlan:

agent-policy-update-`<date>`{=html}

The plan must be finalized via signed commit before this document
changes.

------------------------------------------------------------------------

# Initial Revision

Initial policy created to establish governance for plan-driven agent
execution and SSH-signed human authority.
