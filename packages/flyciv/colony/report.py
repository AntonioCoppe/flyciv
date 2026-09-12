from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def format_report(data: dict[str, Any]) -> str:
    events = data.get("events") or []
    event_s = ", ".join(f"{e['name']}@g{e['generation']}" for e in events) or "(none)"
    win = data.get("win_report") or {}
    lines = [
        "flyciv report",
        "==============",
        f"graph: {data.get('graph')}",
        f"seed: {data.get('seed')}",
        f"heroes: {data.get('heroes')}  crowd: {data.get('crowd')}",
        f"generations: {data.get('generations')}  steps_per_gen: {data.get('steps_per_gen')}",
        f"world: {data.get('world_size')}x{data.get('world_size')}",
        f"nest_calories: {data.get('nest_calories')}",
        f"calories_eaten: {data.get('calories_eaten')}",
        f"trails: {data.get('trails')}",
        f"roads: {data.get('roads')}",
        f"trail_stability: {data.get('trail_stability')}",
        f"brood_adults: {data.get('brood_adults')}",
        f"trainer_unlocked: {data.get('trainer_unlocked')}",
        f"trainer_alive: {data.get('trainer_alive')}",
        f"has_block: {data.get('has_block')}",
        f"wear_sum: {data.get('wear_sum')}",
        f"win: {data.get('win')}",
        f"win_reasons: {win.get('reasons')}",
        f"events: {event_s}",
        "note: city/roads/trainer are designed rules; connectome is frozen.",
    ]
    return "\n".join(lines) + "\n"


def load_report(run_dir: Path) -> dict[str, Any]:
    path = Path(run_dir) / "report.json"
    if not path.is_file():
        raise FileNotFoundError(f"no report.json in {run_dir}")
    return json.loads(path.read_text(encoding="utf-8"))
