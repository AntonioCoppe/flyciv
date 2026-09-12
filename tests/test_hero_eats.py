from __future__ import annotations

import numpy as np

from flyciv.adapter.genome import good_forager_genome
from flyciv.brain.graph import load_toy_graph
from flyciv.colony.agent import make_hero, step_agent
from flyciv.world.grid import make_world


def test_hero_walks_toward_food_and_eats():
    rng = np.random.default_rng(7)
    world = make_world(16, rng, layout="east_patch")
    graph = load_toy_graph()
    genome = good_forager_genome()
    # Face west so eating requires turning toward the east food patch.
    agent = make_hero(world.nest_y, world.nest_x, heading=3, genome=genome, graph=graph, agent_id="hero0")
    start_x = agent.x
    for _ in range(30):
        step_agent(agent, world, [agent])
    assert agent.x > start_x
    assert agent.calories_eaten > 0.0
