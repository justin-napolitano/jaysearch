from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.execplan_lint import run as run_execplan_lint
from platform_tools.security_scan import scan_repository


def _load_weights(path: Path = Path(".agent/metrics.yml")) -> dict[str, float]:
    if not path.exists():
        return {
            "dq_weight": 0.25,
            "hed_weight": 0.25,
            "vpr_weight": 0.20,
            "sls_weight": 0.15,
            "bc_weight": 0.15,
        }
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "dq_weight": float(loaded.get("dq_weight", 0.25)),
        "hed_weight": float(loaded.get("hed_weight", 0.25)),
        "vpr_weight": float(loaded.get("vpr_weight", 0.20)),
        "sls_weight": float(loaded.get("sls_weight", 0.15)),
        "bc_weight": float(loaded.get("bc_weight", 0.15)),
    }


def score_repository(root: str = ".") -> dict[str, Any]:
    lint_code, lint_report = run_execplan_lint([])
    total_files = lint_report["files_checked"] or 1
    clean_files = sum(1 for item in lint_report["results"] if not item["errors"])
    dq = (clean_files / total_files) * 100
    vpr = 100.0 if lint_code == 0 else max(0.0, 100.0 - (lint_report["error_count"] * 5.0))
    bc = max(0.0, 100.0 - (lint_report["warning_count"] * 2.0))

    security = scan_repository(root)
    sls = 100.0 if security["finding_count"] == 0 else max(0.0, 100.0 - (security["finding_count"] * 20.0))

    # Human Edit Distance is not directly available without history; keep deterministic neutral value.
    hed = 80.0

    weights = _load_weights()
    weighted = (
        dq * weights["dq_weight"]
        + hed * weights["hed_weight"]
        + vpr * weights["vpr_weight"]
        + sls * weights["sls_weight"]
        + bc * weights["bc_weight"]
    )
    final_score = round(weighted, 2)
    return {
        "tool": "agent_score",
        "scores": {
            "Draft Quality (DQ)": round(dq, 2),
            "Human Edit Distance (HED)": round(hed, 2),
            "Validation Pass Rate (VPR)": round(vpr, 2),
            "Security Lint Score (SLS)": round(sls, 2),
            "Behavioral Correctness (BC)": round(bc, 2),
        },
        "weights": weights,
        "final_score": final_score,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    report = score_repository(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
