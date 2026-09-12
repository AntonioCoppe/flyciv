from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

TRAIL_WEAR = 6.0
ROAD_WEAR = 12.0
SURPLUS_THRESHOLD = 25.0
COLLAPSE_FLOOR = 1.0
FOOD_MAX = 5.0
RESPAWN = 0.08
HEADINGS = ((-1, 0), (0, 1), (1, 0), (0, -1))  # N E S W


def wrap(v: int, size: int) -> int:
    return v % size


@dataclass
class World:
    size: int
    food: NDArray[np.float64]
    brood: NDArray[np.int32]  # remaining visits until adult; 0 = empty
    brood_sites: NDArray[np.bool_]  # designed nest cells; persist after a hatch
    wear: NDArray[np.float64]
    trails: NDArray[np.bool_]
    roads: NDArray[np.bool_]
    store: NDArray[np.bool_]
    nest_y: int
    nest_x: int
    nest_calories: float = 0.0
    brood_adults: int = 0
    trainer_unlocked: bool = False
    trainer_alive: bool = False
    trainer_cost: float = 2.0
    food_patches: list[tuple[int, int]] = field(default_factory=list)
    collapsed: bool = False
    showcase: bool = False
    wear_step: float = 1.0

    def occupy(self, y: int, x: int, amount: float | None = None) -> None:
        self.wear[y, x] += self.wear_step if amount is None else amount

    def in_bounds(self, y: int, x: int) -> bool:
        return 0 <= y < self.size and 0 <= x < self.size

    def neighbors4(self, y: int, x: int) -> list[tuple[int, int]]:
        out = []
        for dy, dx in HEADINGS:
            ny, nx = y + dy, x + dx
            if self.in_bounds(ny, nx):
                out.append((ny, nx))
        return out


def _clear(size: int) -> World:
    z = np.zeros((size, size), dtype=np.float64)
    return World(
        size=size,
        food=z.copy(),
        brood=np.zeros((size, size), dtype=np.int32),
        brood_sites=np.zeros((size, size), dtype=np.bool_),
        wear=z.copy(),
        trails=np.zeros((size, size), dtype=np.bool_),
        roads=np.zeros((size, size), dtype=np.bool_),
        store=np.zeros((size, size), dtype=np.bool_),
        nest_y=size // 2,
        nest_x=size // 2,
    )


def make_world(
    size: int,
    rng: np.random.Generator,
    layout: str = "default",
) -> World:
    """Designed world. layout=east_patch is the forager eval map."""
    world = _clear(size)
    ny, nx = world.nest_y, world.nest_x
    if layout == "east_patch":
        fx = min(size - 2, nx + max(4, size // 3))
        fy = ny
        world.food[fy, fx] = FOOD_MAX
        world.food_patches = [(fy, fx)]
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            by, bx = ny + dy, nx + dx
            if world.in_bounds(by, bx):
                world.brood[by, bx] = 3
                world.brood_sites[by, bx] = True
        return world
    if layout == "constructed-win":
        paint_civilization(world)
        return world
    if layout == "showcase":
        # Labeled video choreography: 4 foods on the axes so wear can become a cross.
        arm = max(10, size // 6)
        patches = [
            (max(1, ny - arm), nx),
            (ny, min(size - 2, nx + arm)),
            (min(size - 2, ny + arm), nx),
            (ny, max(1, nx - arm)),
        ]
        for fy, fx in patches:
            world.food[fy, fx] = FOOD_MAX
        world.food_patches = patches
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            by, bx = ny + dy, nx + dx
            if world.in_bounds(by, bx):
                world.brood[by, bx] = 3
                world.brood_sites[by, bx] = True
        world.showcase = True
        world.wear_step = 8.0
        return world

    n_patches = 8 if size >= 32 else max(2, size // 8)
    patches: list[tuple[int, int]] = []
    for _ in range(n_patches):
        y = int(rng.integers(2, size - 2))
        x = int(rng.integers(2, size - 2))
        if abs(y - ny) + abs(x - nx) < 4:
            continue
        world.food[y, x] = FOOD_MAX
        patches.append((y, x))
    if not patches:
        world.food[ny, min(size - 2, nx + 6)] = FOOD_MAX
        patches.append((ny, min(size - 2, nx + 6)))
    world.food_patches = patches
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1)):
        by, bx = ny + dy, nx + dx
        if world.in_bounds(by, bx):
            world.brood[by, bx] = 3
            world.brood_sites[by, bx] = True
    return world


def paint_civilization(world: World) -> None:
    """Seeded/constructed surplus city used by the win-check gate — not emergence."""
    ny, nx = world.nest_y, world.nest_x
    size = world.size
    west = max(1, nx - max(5, size // 6))
    east = min(size - 2, nx + max(5, size // 6))
    south = min(size - 2, ny + max(4, size // 8))
    world.food[ny, west] = FOOD_MAX
    world.food[ny, east] = FOOD_MAX
    world.food_patches = [(ny, west), (ny, east)]
    for x in range(west, east + 1):
        world.wear[ny, x] = ROAD_WEAR + 2
        world.trails[ny, x] = True
        world.roads[ny, x] = True
    for y in range(ny, south + 1):
        world.wear[y, nx] = ROAD_WEAR + 2
        world.trails[y, nx] = True
        world.roads[y, nx] = True
    world.store[ny, min(size - 1, nx + 1)] = True
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        by, bx = ny + dy, nx + dx
        if world.in_bounds(by, bx):
            world.brood[by, bx] = 3
            world.brood_sites[by, bx] = True
    world.nest_calories = 80.0
    world.trainer_unlocked = True
    world.trainer_alive = True


def respawn_food(world: World) -> None:
    for y, x in world.food_patches:
        if world.food[y, x] < FOOD_MAX:
            world.food[y, x] = min(FOOD_MAX, world.food[y, x] + RESPAWN)


def decay_wear(world: World, amount: float = 0.01) -> None:
    world.wear = np.maximum(0.0, world.wear - amount)
    world.wear[world.roads] = np.maximum(world.wear[world.roads], ROAD_WEAR)
