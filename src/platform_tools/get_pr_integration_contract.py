from __future__ import annotations

import argparse
import json

from platform_tools.mergeback_orchestration import project_pr_integration_contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-branch", default=None)
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--execplan-id", default=None)
    args = parser.parse_args()
    code, report = project_pr_integration_contract(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
