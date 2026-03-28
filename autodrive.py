from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "STATE.json"
GOALS_DIR = ROOT / "goals"
README_PATH = ROOT / "README.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {
            "current_phase": "DISCOVER",
            "current_goal": None,
            "cycle_count": 0,
            "goals_completed": 0,
            "goals_abandoned": 0,
            "last_retrospective_at": 0,
        }
    return json.loads(STATE_PATH.read_text())


def parse_spec(goal_dir: Path) -> dict | None:
    spec_path = goal_dir / "SPEC.md"
    if not spec_path.exists():
        return None

    data = {
        "name": goal_dir.name,
        "title": goal_dir.name,
        "one_liner": "",
        "status": "UNKNOWN",
        "started": "",
    }

    for line in spec_path.read_text().splitlines():
        if line.startswith("# "):
            data["title"] = line[2:].strip()
        elif line.startswith("**One-liner**:"):
            data["one_liner"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Started**:"):
            data["started"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Status**:"):
            data["status"] = line.split(":", 1)[1].strip()

    return data


def parse_done_metadata(goal_dir: Path) -> dict:
    done_path = goal_dir / "DONE.md"
    metadata = {
        "completion_timestamp": "-",
        "standalone_repo": "",
    }
    if not done_path.exists():
        return metadata

    for line in done_path.read_text().splitlines():
        if line.startswith("Completion timestamp:"):
            metadata["completion_timestamp"] = line.split(":", 1)[1].strip()
        elif line.startswith("Standalone repo:"):
            metadata["standalone_repo"] = line.split(":", 1)[1].strip()

    return metadata


def render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def render_readme() -> None:
    state = load_state()
    goals = []
    for goal_dir in sorted(GOALS_DIR.iterdir()) if GOALS_DIR.exists() else []:
        if goal_dir.is_dir():
            spec = parse_spec(goal_dir)
            if spec:
                goals.append(spec)

    in_progress = [g for g in goals if g["status"] == "IN_PROGRESS"]
    completed = [g for g in goals if g["status"] == "COMPLETE"]
    abandoned = [g for g in goals if g["status"] == "ABANDONED"]

    lines = [
        "# AUTODRIVE",
        "",
        "An autonomous agent that discovers its own goals, builds them, and moves on.",
        "",
        "This repository is maintained by the AUTODRIVE workflow. State is stored in `STATE.json`, goal records live in `goals/`, and the README summary is regenerated each cycle.",
        "",
        f"_Last updated: {utc_now()}_",
        "",
        "## Current State",
        "",
    ]
    lines.extend(
        render_table(
            ["Field", "Value"],
            [
                ["Phase", f"`{state['current_phase']}`"],
                ["Current goal", f"`{state['current_goal'] or 'none'}`"],
                ["Cycle count", f"`{state['cycle_count']}`"],
                ["Goals completed", f"`{state['goals_completed']}`"],
                ["Goals abandoned", f"`{state['goals_abandoned']}`"],
            ],
        )
    )
    lines.extend(["", "## In-Progress Goals", ""])

    if in_progress:
        lines.extend(
            render_table(
                ["Goal", "One-liner", "Status", "Started"],
                [
                    [f"`{g['name']}`", g["one_liner"], g["status"], g["started"]]
                    for g in in_progress
                ],
            )
        )
    else:
        lines.extend(render_table(["Goal", "One-liner", "Status", "Started"], [["_None yet_", "-", "-", "-"]]))

    lines.extend(["", "## Completed Goals", ""])
    if completed:
        rows = []
        for g in completed:
            done_metadata = parse_done_metadata(GOALS_DIR / g["name"])
            repo_url = done_metadata["standalone_repo"]
            repo_cell = f"[repo]({repo_url})" if repo_url else "-"
            rows.append([f"`{g['name']}`", g["one_liner"], done_metadata["completion_timestamp"], repo_cell])
        lines.extend(render_table(["Goal", "One-liner", "Completed", "Repo"], rows))
    else:
        lines.extend(render_table(["Goal", "One-liner", "Completed", "Repo"], [["_None yet_", "-", "-", "-"]]))

    lines.extend(["", "## Abandoned Goals", ""])
    if abandoned:
        rows = []
        for g in abandoned:
            note = "See POSTMORTEM.md" if (GOALS_DIR / g["name"] / "POSTMORTEM.md").exists() else "-"
            rows.append([f"`{g['name']}`", g["one_liner"], note])
        lines.extend(render_table(["Goal", "One-liner", "Notes"], rows))
    else:
        lines.extend(render_table(["Goal", "One-liner", "Notes"], [["_None yet_", "-", "-"]]))

    README_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render_readme()
