from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.port_execplan import port_execplan


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _legacy_plan() -> str:
    return """---
id: "20260414-legacy-plan-codex-01-execplan"
title: "Legacy plan"
owner: "agent/codex-01"
created: "2026-04-14T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/example.py
approve_policy: codeowners
reviewers:
  - "github:test"
initiative_branch: "initiative/example"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/legacy"
draft_created: "2026-04-14T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
---

# Purpose / Big Picture

Legacy context.

## Progress

- [ ] old progress item

## Surprises & Discoveries

- surprise

## Decision Log

- decision

## Outcomes & Retrospective

- pending

## Context and Orientation

- current context

## Plan of Work

- existing plan item

## Concrete Steps

1. old step

## Validation and Acceptance

- validate it

## Idempotence and Recovery

- rerun note

## Artifacts and Notes

- artifact

## Interfaces and Dependencies

- dep
"""


def test_port_execplan_rewrites_legacy_shape_to_contract_first(tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "legacy.md"
    _write(plan, _legacy_plan())

    code, report = port_execplan(path=plan.as_posix())

    assert code == 0
    assert report["wrote_file"] is False
    preview = report["preview"]
    assert "## Outcomes & Retrospective" in preview
    assert "## Context and Orientation" in preview
    assert "## Plan of Work" in preview
    assert "## Validation and Acceptance" in preview
    assert "## Artifacts and Notes" in preview
    assert "# Purpose / Big Picture" not in preview
    assert "## Concrete Steps" not in preview
    assert "draft_branch:" not in preview
    assert "draft_by:" not in preview
    assert "base_branch: initiative/example" in preview


def test_port_execplan_can_write_in_place(tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "legacy.md"
    _write(plan, _legacy_plan())

    code, report = port_execplan(path=plan.as_posix(), in_place=True)

    assert code == 0
    assert report["wrote_file"] is True
    rewritten = plan.read_text(encoding="utf-8")
    assert "## Artifacts and Notes" in rewritten
    assert "### Decision Log" in rewritten
    assert "### Interfaces and Dependencies" in rewritten
    assert "draft_created:" not in rewritten
