from __future__ import annotations

import base64
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


def _b64_u8(arr: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(arr, dtype=np.uint8).tobytes()).decode("ascii")


def capture_frame(
    world: World,
    agents: list[Agent],
    generation: int,
    step: int,
    events: list[CivEvent],
    *,
    map_res: int = 64,
) -> dict[str, Any]:
    """Compact frame: packed map + hero spikes/rates/eye."""
    res = min(map_res, world.size)
    wear = _block_max(world.wear, res)
    wear_u8 = np.clip(wear * (255.0 / 24.0), 0, 255).astype(np.uint8)
    roads = _block_max(world.roads.astype(np.uint8), res) > 0
    trails = _block_max(world.trails.astype(np.uint8), res) > 0
    food = _block_max(world.food, res) > 0
    brood = _block_max(world.brood_sites.astype(np.uint8), res) > 0
    store = _block_max(world.store.astype(np.uint8), res) > 0
    mask = (
        roads.astype(np.uint8)
        | (trails.astype(np.uint8) << 1)
        | (food.astype(np.uint8) << 2)
        | (brood.astype(np.uint8) << 3)
        | (store.astype(np.uint8) << 4)
    )
    hero = next((a for a in agents if a.kind is Kind.HERO), None)
    names = list(hero.brain.graph.names) if hero is not None and hero.brain is not None else []
    spikes = list(hero.spike_sketch) if hero is not None else []
    rates = list(getattr(hero, "rates", []) or []) if hero is not None else []
    eye = dict(getattr(hero, "eye", {}) or {}) if hero is not None else {}
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
        "wear_b64": _b64_u8(wear_u8),
        "mask_b64": _b64_u8(mask.astype(np.uint8)),
        "agents": [
            {
                "k": "H" if a.kind is Kind.HERO else "c",
                "y": round(a.y / scale, 2),
                "x": round(a.x / scale, 2),
                "h": int(a.heading),
            }
            for a in agents
            if a.alive
        ],
        "spikes": spikes,
        "rates": [round(float(x), 4) for x in rates],
        "names": names,
        "eye": eye,
        "events": [e.as_dict() for e in events],
    }
