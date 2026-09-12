from __future__ import annotations

from typing import Any, Mapping, Sequence

from flyciv.world.grid import COLLAPSE_FLOOR


def win_check(history: Sequence[Mapping[str, Any]], k: int = 2) -> dict[str, Any]:
    """City + roads + live trainer + K generations without collapse.

    Designed metric, not a claim of emergence. `history` is a list of generation
    snapshots produced by `run_colony`.
    """
    reasons: list[str] = []
    if len(history) < k:
        return {
            "win": False,
            "k": k,
            "reasons": [f"need {k} generations, have {len(history)}"],
        }
    last = list(history)[-k:]
    for i, snap in enumerate(last):
        gen = snap.get("generation", i)
        n_roads = int(snap.get("n_roads", 0))
        trainer_alive = bool(snap.get("trainer_alive", False))
        has_block = bool(snap.get("has_block", False))
        collapsed = bool(snap.get("collapsed", False))
        n_agents = int(snap.get("n_agents", 0))
        nest = float(snap.get("nest_calories", 0.0))
        if n_roads < 1:
            reasons.append(f"g{gen}: no roads")
        if not trainer_alive:
            reasons.append(f"g{gen}: trainer dead")
        if not has_block:
            reasons.append(f"g{gen}: no city block")
        if collapsed:
            reasons.append(f"g{gen}: collapsed")
        if n_agents < 1:
            reasons.append(f"g{gen}: no agents")
        if nest < COLLAPSE_FLOOR:
            reasons.append(f"g{gen}: nest below collapse floor")
    return {"win": not reasons, "k": k, "reasons": reasons, "generations": [s.get("generation") for s in last]}
