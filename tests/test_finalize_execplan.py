from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools import finalize_execplan as finalize_module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_body() -> str:
    return """
## Outcomes & Retrospective

Test.

## Context and Orientation

Test.

## Plan of Work

Test.

## Validation and Acceptance

Test.

## Artifacts and Notes

Test.
"""


def _plan_text(draft_branch: str) -> str:
    return f"""---
id: "20260312-test-plan-codex-01-execplan"
title: "Test plan"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-test-plan-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jay.napolitano"
draft_by: "agent/codex-01"
draft_branch: "{draft_branch}"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-test-plan-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Test"
    priority: "P1"
depends_on: []
---

{_minimal_body().strip()}
"""


def _base_repo(root: Path, draft_branch: str) -> Path:
    _write(
        root / "spec" / "governance.yaml",
        """version: v1
finalization:
  canonical_event: signed_merge_commit_on_main
  allowed_signature_statuses:
    - G
  derived_fields:
    - finalized_by
    - finalized_at
    - finalized_in_pr
  completion_status: completed
  preferred_merge_branch_role_order:
    - impl-execplan
    - draft-execplan
  ambiguity_policy: block
  signer_identity_map:
    - github: github:jay.napolitano
      emails:
        - jay.napolitano@adventhealth.com
      signer_names:
        - Jay Napolitano
      signer_fingerprints:
        - SHA256:test-fingerprint
""",
    )
    _write(root / ".agent" / "AGENTS.md", "# AGENTS.md\n")
    plan = root / ".agent" / "execplans" / "20260312-test-plan-codex-01-execplan.md"
    _write(plan, _plan_text(draft_branch))
    return plan


def test_finalize_execplan_derives_completed_state_from_signed_impl_merge(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    plan = _base_repo(tmp_path, branch)

    monkeypatch.setattr(
        finalize_module,
        "_merge_candidates",
        lambda *_args, **_kwargs: [
            {
                "commit": "abc123",
                "committed_at": "2026-03-12T12:34:56Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "G",
                "signer_name": "Jay Napolitano",
                "signer_fingerprint": "SHA256:test-fingerprint",
                "subject": f"Merge pull request #77 from JNA31A_AIT/{branch}",
                "body": "",
                "pull_request": "77",
                "branch_ref": branch,
                "merge_role": "impl-execplan",
            }
        ],
    )

    result = finalize_module.finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")

    assert result["status"] == "completed"
    assert result["finalized_by"] == "github:jay.napolitano"
    assert result["finalized_in_pr"] == "77"
    assert result["merge_evidence"]["merge_role"] == "impl-execplan"
    assert result["changed"] is True
    assert 'status: completed' in plan.read_text(encoding="utf-8")


def test_finalize_execplan_prefers_signed_impl_merge_over_signed_draft_merge(monkeypatch, tmp_path: Path) -> None:
    draft_branch = "draft-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    impl_branch = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    plan = _base_repo(tmp_path, draft_branch)

    monkeypatch.setattr(
        finalize_module,
        "_merge_candidates",
        lambda *_args, **_kwargs: [
            {
                "commit": "draft1",
                "committed_at": "2026-03-12T10:00:00Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "G",
                "signer_name": "Jay Napolitano",
                "signer_fingerprint": "SHA256:test-fingerprint",
                "subject": f"Merge pull request #70 from JNA31A_AIT/{draft_branch}",
                "body": "",
                "pull_request": "70",
                "branch_ref": draft_branch,
                "merge_role": "draft-execplan",
            },
            {
                "commit": "impl1",
                "committed_at": "2026-03-12T11:00:00Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "G",
                "signer_name": "Jay Napolitano",
                "signer_fingerprint": "SHA256:test-fingerprint",
                "subject": f"Merge pull request #71 from JNA31A_AIT/{impl_branch}",
                "body": "",
                "pull_request": "71",
                "branch_ref": impl_branch,
                "merge_role": "impl-execplan",
            },
        ],
    )

    result = finalize_module.finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")

    assert result["finalized_in_pr"] == "71"
    assert result["merge_evidence"]["merge_role"] == "impl-execplan"


def test_finalize_execplan_blocks_when_merge_history_is_ambiguous(monkeypatch, tmp_path: Path) -> None:
    branch = "draft-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    plan = _base_repo(tmp_path, branch)

    monkeypatch.setattr(
        finalize_module,
        "_merge_candidates",
        lambda *_args, **_kwargs: [
            {
                "commit": "impl1",
                "committed_at": "2026-03-12T10:00:00Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "G",
                "signer_name": "Jay Napolitano",
                "signer_fingerprint": "SHA256:test-fingerprint",
                "subject": "Merge pull request #80 from JNA31A_AIT/impl-execplan/foo",
                "body": "",
                "pull_request": "80",
                "branch_ref": "impl-execplan/foo",
                "merge_role": "impl-execplan",
            },
            {
                "commit": "impl2",
                "committed_at": "2026-03-12T11:00:00Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "G",
                "signer_name": "Jay Napolitano",
                "signer_fingerprint": "SHA256:test-fingerprint",
                "subject": "Merge pull request #81 from JNA31A_AIT/impl-execplan/bar",
                "body": "",
                "pull_request": "81",
                "branch_ref": "impl-execplan/bar",
                "merge_role": "impl-execplan",
            },
        ],
    )

    try:
        finalize_module.finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")
    except ValueError as exc:
        assert str(exc) == "ambiguous_merge_commit"
    else:
        raise AssertionError("expected ambiguous merge history to block reconciliation")


def test_finalize_execplan_blocks_when_signed_merge_is_missing(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    plan = _base_repo(tmp_path, branch)

    monkeypatch.setattr(
        finalize_module,
        "_merge_candidates",
        lambda *_args, **_kwargs: [
            {
                "commit": "abc123",
                "committed_at": "2026-03-12T12:34:56Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "N",
                "signer_name": "",
                "signer_fingerprint": "",
                "subject": f"Merge pull request #77 from JNA31A_AIT/{branch}",
                "body": "",
                "pull_request": "77",
                "branch_ref": branch,
                "merge_role": "impl-execplan",
            }
        ],
    )

    try:
        finalize_module.finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")
    except ValueError as exc:
        assert str(exc) == "missing_signed_merge_commit"
    else:
        raise AssertionError("expected unsigned merge history to block reconciliation")


def test_finalize_execplan_blocks_when_signer_identity_map_is_ambiguous(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    plan = _base_repo(tmp_path, branch)
    _write(
        tmp_path / "spec" / "governance.yaml",
        """version: v1
finalization:
  canonical_event: signed_merge_commit_on_main
  allowed_signature_statuses:
    - G
  signer_identity_map:
    - github: github:jay.napolitano
      emails:
        - jay.napolitano@adventhealth.com
      signer_names:
        - Jay Napolitano
      signer_fingerprints: []
    - github: github:other.user
      emails:
        - jay.napolitano@adventhealth.com
      signer_names: []
      signer_fingerprints: []
""",
    )

    monkeypatch.setattr(
        finalize_module,
        "_merge_candidates",
        lambda *_args, **_kwargs: [
            {
                "commit": "abc123",
                "committed_at": "2026-03-12T12:34:56Z",
                "author_name": "Jay Napolitano",
                "author_email": "jay.napolitano@adventhealth.com",
                "signature_status": "G",
                "signer_name": "Jay Napolitano",
                "signer_fingerprint": "",
                "subject": f"Merge pull request #77 from JNA31A_AIT/{branch}",
                "body": "",
                "pull_request": "77",
                "branch_ref": branch,
                "merge_role": "impl-execplan",
            }
        ],
    )

    try:
        finalize_module.finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")
    except ValueError as exc:
        assert str(exc) == "finalized_by_not_deterministic"
    else:
        raise AssertionError("expected ambiguous signer identity to block reconciliation")
