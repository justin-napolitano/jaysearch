from __future__ import annotations

import argparse
import json

from platform_tools.mergeback_orchestration import prepare_next_impl_branch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--execplan-id", default=None)
    parser.add_argument("--node-id", default=None)
    args = parser.parse_args()
    code, report = prepare_next_impl_branch(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
