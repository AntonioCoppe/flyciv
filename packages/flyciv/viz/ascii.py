from __future__ import annotations

from flyciv.colony.agent import Agent, Kind
from flyciv.world.grid import World


def render_ascii(world: World, agents: list[Agent], width: int = 32) -> str:
    size = world.size
    scale = max(1, size // width)
    w = max(1, size // scale)
    grid = [["." for _ in range(w)] for _ in range(w)]
    for y in range(0, size, scale):
        for x in range(0, size, scale):
            gy, gx = y // scale, x // scale
            if gy >= w or gx >= w:
                continue
            block = world.food[y : y + scale, x : x + scale]
            wear = world.wear[y : y + scale, x : x + scale]
            roads = world.roads[y : y + scale, x : x + scale]
            brood = world.brood[y : y + scale, x : x + scale]
            store = world.store[y : y + scale, x : x + scale]
            ch = "."
            if roads.any():
                ch = "#"
            elif wear.max() >= 6:
                ch = "*"
            if brood.max() > 0:
                ch = "b"
            if block.max() > 0:
                ch = "F"
            if store.any():
                ch = "S"
            if (world.nest_y // scale, world.nest_x // scale) == (gy, gx):
                ch = "N"
            grid[gy][gx] = ch
    for a in agents:
        if not a.alive:
            continue
        gy, gx = a.y // scale, a.x // scale
        if 0 <= gy < w and 0 <= gx < w:
            grid[gy][gx] = "H" if a.kind is Kind.HERO else "c"
    legend = "N nest  F food  b brood  S store  # road  * wear  H hero  c crowd"
    header = f"flyciv map {world.size}x{world.size}  calories={world.nest_calories:.2f}  trainer={world.trainer_alive}"
    body = "\n".join("".join(row) for row in grid)
    spikes = ""
    heroes = [a for a in agents if a.kind is Kind.HERO and a.spike_sketch]
    if heroes:
        spikes = "hero spikes: " + "".join("|" if s else "." for s in heroes[0].spike_sketch)
    return header + "\n" + legend + "\n" + body + ("\n" + spikes if spikes else "") + "\n"
