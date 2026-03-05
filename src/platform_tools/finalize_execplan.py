from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ALLOWED_FINAL_STATUSES = {"proposed", "approved"}


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


def finalize_execplan(
    path: Path,
    finalized_by: str,
    finalized_in_pr: str,
    status: str,
    finalized_at: str,
) -> dict[str, Any]:
    if status not in ALLOWED_FINAL_STATUSES:
        raise ValueError(f"invalid_status:{status}")

    frontmatter, body, before = _read_frontmatter(path)
    frontmatter["status"] = status
    frontmatter["finalized_by"] = finalized_by
    frontmatter["finalized_at"] = finalized_at
    frontmatter["finalized_in_pr"] = finalized_in_pr

    after = _render(frontmatter, body)
    changed = before != after
    if changed:
        path.write_text(after, encoding="utf-8")

    return {
        "plan": path.as_posix(),
        "id": frontmatter.get("id"),
        "status": status,
        "finalized_by": finalized_by,
        "finalized_at": finalized_at,
        "finalized_in_pr": finalized_in_pr,
        "changed": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="ExecPlan markdown path(s)")
    parser.add_argument("--finalized-by", required=True, help="github:<username>")
    parser.add_argument("--finalized-in-pr", required=True, help="PR number or URL")
    parser.add_argument("--status", default="proposed", choices=sorted(ALLOWED_FINAL_STATUSES))
    parser.add_argument(
        "--finalized-at",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        help="ISO8601 UTC timestamp",
    )
    args = parser.parse_args()

    results = []
    for p in args.paths:
        results.append(
            finalize_execplan(
                path=Path(p),
                finalized_by=args.finalized_by,
                finalized_in_pr=args.finalized_in_pr,
                status=args.status,
                finalized_at=args.finalized_at,
            )
        )

    print(
        json.dumps(
            {
                "tool": "finalize_execplan",
                "count": len(results),
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
