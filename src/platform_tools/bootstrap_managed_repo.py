from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from platform_tools.integrations.github_projects_bootstrap import execute_bootstrap


COMMAND = "bootstrap-managed-repo"
FIELD_MAP_RELATIVE_PATH = Path("artifacts/provider-sync/github-projects-field-map.json")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "managed-repo"


def _write_text(path: Path, text: str, *, force: bool) -> tuple[bool, str]:
    if path.exists() and not force:
        return False, "exists"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True, "written"


def _write_json(path: Path, data: object, *, force: bool) -> tuple[bool, str]:
    return _write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n", force=force)


def _queue_doc(repo_slug: str, project_title: str) -> str:
    initiative_node_id = f"initiative-{repo_slug}-foundation"
    initiative_branch = f"initiative/{repo_slug}-foundation"
    product_execplan = f"{datetime.now(UTC):%Y%m%d}-{repo_slug}-product-foundation-codex-01-execplan"
    activity_execplan = f"{datetime.now(UTC):%Y%m%d}-{repo_slug}-activity-capture-mvp-codex-01-execplan"
    return "\n".join(
        [
            "# Queued ExecPlans",
            "",
            "Canonical source: `artifacts/planner/research/remaining-work-graph.json`",
            "",
            "## Active Initiative",
            "",
            f"- `{initiative_node_id}`",
            f"  - branch: `{initiative_branch}`",
            "  - status: `in_progress`",
            "",
            "## Queue",
            "",
            f"1. `rwg-002` `decision_gated`",
            f"   `{product_execplan}`",
            f"   Define product, experience, and architecture for {project_title}",
            "",
            f"2. `rwg-003` `decision_gated`",
            f"   `{activity_execplan}`",
            "   Plan activity recording, route capture, and local persistence MVP",
            "",
        ]
    )


def _workflow_doc() -> str:
    return "\n".join(
        [
            "allowed_branch_patterns:",
            "  - initiative/*",
            "  - draft-execplan/*",
            "  - impl-execplan/*",
            "  - docs/*",
            "  - hotfix/*",
            "  - release/*",
            "forbidden_branches:",
            "  - \"\"",
            "  - main",
            "  - master",
            "default_integration_mode: via_initiative",
            "direct_to_main_exception_modes:",
            "  - direct_to_main_hotfix",
            "  - direct_to_main_patch",
            "pr_template_sections:",
            "  - ExecPlan",
            "  - Purpose",
            "  - Scope",
            "  - Self Review",
            "  - Validation",
            "  - Handoff",
            "pr_template_mode: additive_only",
            "normal_flow:",
            "  - create_or_select_initiative_node",
            "  - create_initiative_branch",
            "  - draft_execplan",
            "  - human_finalize_plan",
            "  - implement_on_impl_branch",
            "  - merge_impl_to_initiative",
            "  - merge_initiative_to_main",
            "",
        ]
    )


def _remaining_work_graph(repo_slug: str, project_title: str) -> dict[str, Any]:
    today = datetime.now(UTC).strftime("%Y-%m-%dT00:00:00Z")
    initiative_node_id = f"initiative-{repo_slug}-foundation"
    initiative_branch = f"initiative/{repo_slug}-foundation"
    date_prefix = datetime.now(UTC).strftime("%Y%m%d")
    product_execplan = f"{date_prefix}-{repo_slug}-product-foundation-codex-01-execplan"
    activity_execplan = f"{date_prefix}-{repo_slug}-activity-capture-mvp-codex-01-execplan"
    return {
        "version": 1,
        "last_updated": today,
        "nodes": [
            {
                "node_id": initiative_node_id,
                "title": f"{project_title} foundation",
                "type": "initiative",
                "status": "in_progress",
                "initiative_branch": initiative_branch,
                "goal_area": "product",
            },
            {
                "node_id": "rwg-001",
                "title": "Bootstrap governed project skeleton",
                "type": "execplan",
                "status": "completed",
                "target_execplan_id": f"{date_prefix}-{repo_slug}-bootstrap-governed-project-codex-01-execplan",
                "implementation_branch": (
                    f"impl-execplan/{date_prefix}-{repo_slug}-bootstrap-governed-project-codex-01-execplan-codex-01-{date_prefix}"
                ),
                "initiative_branch": initiative_branch,
                "parent_initiative_node": initiative_node_id,
                "integration_mode": "via_initiative",
                "completion_ref": "bootstrap:repo-initialized",
                "goal_area": "governance",
            },
            {
                "node_id": "rwg-002",
                "title": f"Define product, experience, and architecture for {project_title}",
                "type": "execplan",
                "status": "decision_gated",
                "target_execplan_id": product_execplan,
                "implementation_branch": (
                    f"impl-execplan/{product_execplan}-codex-01-{date_prefix}"
                ),
                "initiative_branch": initiative_branch,
                "parent_initiative_node": initiative_node_id,
                "integration_mode": "via_initiative",
                "goal_area": "product",
            },
            {
                "node_id": "rwg-003",
                "title": "Plan activity recording, route capture, and local persistence MVP",
                "type": "execplan",
                "status": "decision_gated",
                "target_execplan_id": activity_execplan,
                "implementation_branch": (
                    f"impl-execplan/{activity_execplan}-codex-01-{date_prefix}"
                ),
                "initiative_branch": initiative_branch,
                "parent_initiative_node": initiative_node_id,
                "integration_mode": "via_initiative",
                "goal_area": "product",
            },
        ],
    }


def _write_provider_preview(path: Path, preview: dict[str, Any], *, force: bool) -> tuple[bool, str]:
    return _write_json(path, preview, force=force)


def bootstrap_managed_repo(
    *,
    root: str,
    repo_name: str,
    owner: str,
    owner_type: str,
    board_title: str | None = None,
    existing_project_id: str | None = None,
    execute_provider_bootstrap: bool = False,
    force: bool = False,
) -> tuple[int, dict[str, Any]]:
    target_root = Path(root).resolve()
    repo_slug = _slugify(repo_name)
    project_title = repo_name.strip() or repo_slug
    created: list[str] = []
    skipped: list[dict[str, str]] = []

    paths = {
        "workflow": target_root / "spec" / "workflow.yaml",
        "graph": target_root / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        "queue": target_root / "docs" / "queued-execplans.md",
        "execplans_dir": target_root / ".agent" / "execplans",
        "field_map": target_root / FIELD_MAP_RELATIVE_PATH,
    }

    paths["execplans_dir"].mkdir(parents=True, exist_ok=True)
    if not any(item["path"] == ".agent/execplans" for item in skipped):
        created.append(".agent/execplans")

    wrote, reason = _write_text(paths["workflow"], _workflow_doc(), force=force)
    (created if wrote else skipped).append("spec/workflow.yaml" if wrote else {"path": "spec/workflow.yaml", "reason": reason})

    wrote, reason = _write_json(paths["graph"], _remaining_work_graph(repo_slug, project_title), force=force)
    (created if wrote else skipped).append(
        "artifacts/planner/research/remaining-work-graph.json"
        if wrote
        else {"path": "artifacts/planner/research/remaining-work-graph.json", "reason": reason}
    )

    wrote, reason = _write_text(paths["queue"], _queue_doc(repo_slug, project_title), force=force)
    (created if wrote else skipped).append(
        "docs/queued-execplans.md" if wrote else {"path": "docs/queued-execplans.md", "reason": reason}
    )

    bootstrap_code, bootstrap_report = execute_bootstrap(
        root=str(Path(__file__).resolve().parents[2]),
        owner=owner,
        owner_type=owner_type,
        title=board_title or f"{project_title} Execution Board",
        field_map_output_path=paths["field_map"].as_posix(),
        existing_project_id=existing_project_id,
        dry_run=not execute_provider_bootstrap,
    )

    if bootstrap_report.get("field_map"):
        wrote, reason = _write_json(paths["field_map"], bootstrap_report["field_map"], force=force)
    else:
        wrote, reason = _write_provider_preview(
            paths["field_map"],
            bootstrap_report.get("field_map_preview", {}),
            force=force,
        )
    (created if wrote else skipped).append(
        FIELD_MAP_RELATIVE_PATH.as_posix()
        if wrote
        else {"path": FIELD_MAP_RELATIVE_PATH.as_posix(), "reason": reason}
    )

    ok = bootstrap_code == 0
    report = {
        "command": COMMAND,
        "ok": ok,
        "status": "ok" if ok else "blocked",
        "root": target_root.as_posix(),
        "repo_name": project_title,
        "repo_slug": repo_slug,
        "created": sorted(item for item in created if isinstance(item, str)),
        "skipped": sorted(
            (item for item in skipped if isinstance(item, dict)),
            key=lambda item: item["path"],
        ),
        "provider_bootstrap": bootstrap_report,
    }
    return (0 if ok else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--owner-type", choices=["user", "organization"], default="user")
    parser.add_argument("--board-title", default=None)
    parser.add_argument("--existing-project-id", default=None)
    parser.add_argument("--execute-provider-bootstrap", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    code, report = bootstrap_managed_repo(
        root=args.root,
        repo_name=args.repo_name,
        owner=args.owner,
        owner_type=args.owner_type,
        board_title=args.board_title,
        existing_project_id=args.existing_project_id,
        execute_provider_bootstrap=args.execute_provider_bootstrap,
        force=args.force,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
