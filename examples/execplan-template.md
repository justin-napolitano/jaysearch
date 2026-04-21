---
id: "<plan-id>-YYYYMMDD"
title: "<short human-readable title>"
owner: "agent/<agent-name>"
created: "YYYY-MM-DDTHH:MM:SSZ"
status: draft
base_branch: main
changes:
  - path/to/file1
  - path/to/file2
approve_policy: codeowners
reviewers:
  - "github:<reviewer-username>"

initiative_branch: "initiative/<initiative-id>"
initiative_node_id: "initiative-<initiative-id>"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "<validator-name>"
      command: "<command>"
      expected_exit: 0

tasks:
  - title: "<task-title>"
    priority: "P1"

depends_on:
  - "<other-plan-id>"
---

## Outcomes & Retrospective

Keep this short while planning. Expand only when human readers need context that the contract fields cannot express.

## Context and Orientation

List the minimum local context a worker needs to execute safely under this initiative.

## Plan of Work

Prefer contract fields, explicit validations, and declared changes over narrative planning prose.

## Validation and Acceptance

Define pass/fail checks and acceptance criteria that are not already obvious from `validation.tests`.

## Artifacts and Notes

List only operator notes or generated artifacts that are not already captured elsewhere.
