from __future__ import annotations

import argparse
import json
from pathlib import Path

from platform_tools.reconcile_remaining_work_merge import reconcile_pending_merge_completions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--main-ref", default="main")
    args = parser.parse_args()
    report = reconcile_pending_merge_completions(repo_root=Path(args.repo_root), main_ref=args.main_ref)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
