from __future__ import annotations

from typing import Any

import numpy as np

from flyciv.colony.agent import Agent, Kind
from flyciv.world.events import CivEvent
from flyciv.world.grid import World


def _block_max(grid: np.ndarray, out: int) -> np.ndarray:
    h, _w = grid.shape
    if h <= out:
        return np.asarray(grid)
    step = h // out
    cropped = grid[: out * step, : out * step]
    return cropped.reshape(out, step, out, step).max(axis=(1, 3))


def _down_max(grid: np.ndarray, out: int) -> list[list[float]]:
    return _block_max(grid, out).astype(np.float64).tolist()


def _down_any(grid: np.ndarray, out: int) -> list[list[int]]:
    return _block_max(grid.astype(np.int8), out).astype(int).tolist()


def capture_frame(
    world: World,
    agents: list[Agent],
    generation: int,
    step: int,
    events: list[CivEvent],
    *,
    map_res: int = 64,
) -> dict[str, Any]:
    """Compact frame for the HUD. Designed world layers, not emergence."""
    res = min(map_res, world.size)
    hero = next((a for a in agents if a.kind is Kind.HERO), None)
    names = list(hero.brain.graph.names) if hero is not None and hero.brain is not None else []
    spikes = list(hero.spike_sketch) if hero is not None else []
    scale = world.size / res
    return {
        "generation": generation,
        "step": step,
        "size": world.size,
        "res": res,
        "nest": [world.nest_y / scale, world.nest_x / scale],
        "calories": float(world.nest_calories),
        "trainer": bool(world.trainer_alive),
        "unlocked": bool(world.trainer_unlocked),
        "wear": _down_max(world.wear, res),
        "roads": _down_any(world.roads, res),
        "trails": _down_any(world.trails, res),
        "food": _down_max(world.food, res),
        "brood": _down_any(world.brood_sites, res),
        "store": _down_any(world.store, res),
        "agents": [
            {
                "k": "H" if a.kind is Kind.HERO else "c",
                "y": a.y / scale,
                "x": a.x / scale,
            }
            for a in agents
            if a.alive
        ],
        "spikes": spikes,
        "names": names,
        "events": [e.as_dict() for e in events],
    }
