from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml

ALLOWED_FINAL_STATUSES = {"proposed", "approved", "completed"}
MERGE_ROLE_PRIORITY = {
    "impl-execplan": 3,
    "draft-execplan": 2,
    "other": 1,
}


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout


def _read_frontmatter(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.as_posix()}: missing_frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path.as_posix()}: malformed_frontmatter")
    raw = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.as_posix()}: invalid_frontmatter_type")
    return data, body, text


def _render(frontmatter: dict[str, Any], body: str) -> str:
    rendered = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=False)
    return f"---\n{rendered}---\n{body}"


def _to_utc_z(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _initial_human_maintainer(repo_root: Path) -> str:
    agents_path = repo_root / ".agent" / "AGENTS.md"
    if not agents_path.exists():
        raise ValueError("missing_agents_policy")
    matches = re.findall(r"^github:[a-zA-Z0-9_.-]+$", agents_path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    unique = sorted(set(matches))
    if len(unique) != 1:
        raise ValueError("finalized_by_not_deterministic")
    return unique[0]


def _merge_candidates(repo_root: Path, main_ref: str, plan_id: str, draft_branch: str) -> list[dict[str, str]]:
    output = _git(
        repo_root,
        "log",
        "--merges",
        "--format=%H%x1f%cI%x1f%an%x1f%ae%x1f%s%x1f%b%x1e",
        main_ref,
    )
    candidates: list[dict[str, str]] = []
    for chunk in output.split("\x1e"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("\x1f", 5)
        if len(parts) == 5:
            parts.append("")
        if len(parts) != 6:
            continue
        commit, committed_at, author_name, author_email, subject, body = parts
        text = "\n".join([subject, body])
        if plan_id not in text and draft_branch not in text:
            continue
        pr_match = re.search(r"Merge pull request #(\d+)", subject)
        branch_match = re.search(r"Merge pull request #\d+ from [^/]+/([^\n]+)", subject)
        branch_ref = branch_match.group(1) if branch_match else ""
        if "impl-execplan/" in text:
            merge_role = "impl-execplan"
        elif "draft-execplan/" in text:
            merge_role = "draft-execplan"
        else:
            merge_role = "other"
        candidates.append(
            {
                "commit": commit,
                "committed_at": _to_utc_z(committed_at),
                "author_name": author_name,
                "author_email": author_email,
                "subject": subject,
                "body": body.strip(),
                "pull_request": pr_match.group(1) if pr_match else "",
                "branch_ref": branch_ref,
                "merge_role": merge_role,
            }
        )
    return candidates


def _select_merge_candidate(repo_root: Path, main_ref: str, plan_id: str, draft_branch: str) -> dict[str, str]:
    candidates = _merge_candidates(repo_root, main_ref, plan_id, draft_branch)
    if not candidates:
        raise ValueError("missing_merge_commit")

    max_priority = max(MERGE_ROLE_PRIORITY[item["merge_role"]] for item in candidates)
    strongest = [item for item in candidates if MERGE_ROLE_PRIORITY[item["merge_role"]] == max_priority]
    if len(strongest) != 1:
        raise ValueError("ambiguous_merge_commit")
    return strongest[0]


def finalize_execplan(
    path: Path,
    finalized_by: str | None = None,
    finalized_in_pr: str | None = None,
    status: str | None = None,
    finalized_at: str | None = None,
    repo_root: Path | None = None,
    main_ref: str = "main",
    derive_from_merge: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root or path.parent.parent.parent
    frontmatter, body, before = _read_frontmatter(path)
    plan_id = str(frontmatter.get("id", "")).strip()
    draft_branch = str(frontmatter.get("draft_branch", "")).strip()

    merge_evidence: dict[str, str] | None = None
    if derive_from_merge:
        merge_evidence = _select_merge_candidate(repo_root, main_ref, plan_id, draft_branch)
        status = status or "completed"
        finalized_at = finalized_at or merge_evidence["committed_at"]
        finalized_in_pr = finalized_in_pr or merge_evidence["pull_request"]
        finalized_by = finalized_by or _initial_human_maintainer(repo_root)
    else:
        status = status or "proposed"

    if status not in ALLOWED_FINAL_STATUSES:
        raise ValueError(f"invalid_status:{status}")
    if not finalized_by:
        raise ValueError("missing_finalized_by")
    if not finalized_in_pr:
        raise ValueError("missing_finalized_in_pr")
    if not finalized_at:
        raise ValueError("missing_finalized_at")

    frontmatter["status"] = status
    frontmatter["finalized_by"] = finalized_by
    frontmatter["finalized_at"] = finalized_at
    frontmatter["finalized_in_pr"] = finalized_in_pr

    after = _render(frontmatter, body)
    changed = before != after
    if changed:
        path.write_text(after, encoding="utf-8")

    return {
        "command": "finalize-execplan",
        "plan": path.as_posix(),
        "id": plan_id,
        "status": status,
        "finalized_by": finalized_by,
        "finalized_at": finalized_at,
        "finalized_in_pr": finalized_in_pr,
        "changed": changed,
        "merge_evidence": merge_evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="ExecPlan markdown path(s)")
    parser.add_argument("--finalized-by", default=None, help="github:<username>")
    parser.add_argument("--finalized-in-pr", default=None, help="PR number or URL")
    parser.add_argument("--status", default=None, choices=sorted(ALLOWED_FINAL_STATUSES))
    parser.add_argument(
        "--finalized-at",
        default=None,
        help="ISO8601 UTC timestamp",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--main-ref", default="main")
    parser.add_argument("--derive-from-merge", action="store_true")
    args = parser.parse_args()

    results = []
    blockers: list[str] = []
    try:
        for p in args.paths:
            results.append(
                finalize_execplan(
                    path=Path(p),
                    finalized_by=args.finalized_by,
                    finalized_in_pr=args.finalized_in_pr,
                    status=args.status,
                    finalized_at=args.finalized_at,
                    repo_root=Path(args.repo_root),
                    main_ref=args.main_ref,
                    derive_from_merge=args.derive_from_merge,
                )
            )
        code = 0
    except ValueError as exc:
        blockers = [str(exc)]
        code = 1

    payload = {
        "command": "finalize-execplan",
        "status": "ok" if code == 0 else "blocked",
        "blockers": blockers,
        "next_validations": [],
        "count": len(results),
        "results": results,
        "derive_from_merge": args.derive_from_merge,
        "repo_root": str(Path(args.repo_root)),
        "main_ref": args.main_ref,
    }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
