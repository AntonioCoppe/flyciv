"""Designed stigmergy rules (ant/RAnt ideas, our code). See HONESTY.md."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from flyciv.world.grid import ROAD_WEAR, TRAIL_WEAR, World


def connected_components(mask: NDArray[np.bool_]) -> list[list[tuple[int, int]]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=np.bool_)
    comps: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            cells: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            comps.append(cells)
    return comps


def detect_trails(
    wear: NDArray[np.float64],
    food: NDArray[np.float64],
    threshold: float = TRAIL_WEAR,
    min_length: int = 4,
    min_end_separation: int = 3,
) -> NDArray[np.bool_]:
    """High wear + food at both ends = trail."""
    h, w = wear.shape
    mask = wear >= threshold
    trails = np.zeros_like(mask)
    for cells in connected_components(mask):
        if len(cells) < min_length:
            continue
        food_cells: set[tuple[int, int]] = set()
        for y, x in cells:
            for ny in range(max(0, y - 1), min(h, y + 2)):
                for nx in range(max(0, x - 1), min(w, x + 2)):
                    if food[ny, nx] > 0:
                        food_cells.add((ny, nx))
        if len(food_cells) < 2:
            continue
        pts = list(food_cells)
        sep = 0
        for i, (y0, x0) in enumerate(pts):
            for y1, x1 in pts[i + 1 :]:
                sep = max(sep, abs(y0 - y1) + abs(x0 - x1))
        if sep < min_end_separation:
            continue
        for y, x in cells:
            trails[y, x] = True
    return trails


def promote_roads(
    trails: NDArray[np.bool_],
    occupied: set[tuple[int, int]],
    existing: NDArray[np.bool_] | None = None,
    wear: NDArray[np.float64] | None = None,
    road_wear: float = ROAD_WEAR,
) -> NDArray[np.bool_]:
    """Durable trail after the makers leave (or wear hardens)."""
    roads = np.zeros_like(trails) if existing is None else existing.copy()
    occ = np.zeros_like(trails)
    for y, x in occupied:
        if 0 <= y < occ.shape[0] and 0 <= x < occ.shape[1]:
            occ[y, x] = True
    roads |= trails & ~occ
    if wear is not None:
        # Harden only trail cells — nest milling is not a road.
        roads |= trails & (wear >= road_wear)
    return roads


def detect_blocks(
    roads: NDArray[np.bool_],
    store: NDArray[np.bool_],
    brood: NDArray[np.int32] | NDArray[np.bool_],
) -> bool:
    """3-road junction + store + brood = block (city morphology)."""
    brood_present = brood.astype(bool) if brood.dtype != np.bool_ else brood
    if not store.any() or not brood_present.any():
        return False
    h, w = roads.shape
    for y in range(h):
        for x in range(w):
            if not roads[y, x]:
                continue
            n = 0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and roads[ny, nx]:
                    n += 1
            if n >= 3:
                return True
    return False


def trail_stability(prev: NDArray[np.bool_], cur: NDArray[np.bool_]) -> float:
    prev_n = int(prev.sum())
    if prev_n == 0:
        return float(cur.any())
    return float((prev & cur).sum() / prev_n)


def refresh_world_layers(world: World, occupied: set[tuple[int, int]]) -> dict[str, bool]:
    new_trails = detect_trails(world.wear, world.food)
    first_trail = bool(new_trails.any() and not world.trails.any())
    world.trails = new_trails
    new_roads = promote_roads(world.trails, occupied, world.roads, wear=world.wear)
    first_road = bool(new_roads.any() and not world.roads.any())
    world.roads = new_roads
    first_block = detect_blocks(world.roads, world.store, world.brood_sites)
    return {
        "first_trail": first_trail,
        "first_road": first_road,
        "has_block": first_block,
    }
