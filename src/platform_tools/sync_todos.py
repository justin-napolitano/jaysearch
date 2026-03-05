from __future__ import annotations

import json

from platform_tools.generate_todos import generate_todos


def main() -> int:
    report = generate_todos("TODO.md")
    wrapped = {"tool": "sync_todos", **report}
    print(json.dumps(wrapped, indent=2, sort_keys=True))
    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
