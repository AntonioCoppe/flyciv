from __future__ import annotations

import numpy as np

from flyciv.adapter.genome import good_forager_genome, random_genome
from flyciv.colony.agent import make_crowd, step_agent
from flyciv.world.grid import make_world


def _calories(genome, *, seed: int, heading: int = 3, n_steps: int = 24, size: int = 16) -> float:
    rng = np.random.default_rng(seed)
    world = make_world(size, rng, layout="east_patch")
    agent = make_crowd(world.nest_y, world.nest_x, heading=heading, genome=genome, agent_id="eval")
    for _ in range(n_steps):
        step_agent(agent, world, [agent])
    return float(agent.calories_eaten)


def test_good_forager_beats_random_on_calories():
    seed = 0
    good = _calories(good_forager_genome(), seed=seed)
    rnd = _calories(random_genome(np.random.default_rng(0)), seed=seed)
    assert good > rnd
    assert good > 0.0
