"""Trainer tile: not an LLM. Best adapters → cheap inner eval → child genome."""

from __future__ import annotations

import numpy as np

from flyciv.adapter.genome import Genome
from flyciv.adapter.mutate import mutate
from flyciv.colony.agent import make_crowd, step_agent
from flyciv.world.grid import make_world


def inner_eval(genome: Genome, rng: np.random.Generator, n_steps: int = 20, size: int = 16) -> float:
    """Cheaper copy of one-generation foraging. Used by the trainer tile."""
    world = make_world(size, rng, layout="east_patch")
    agent = make_crowd(world.nest_y, world.nest_x, heading=1, genome=genome, agent_id="inner")
    for _ in range(n_steps):
        step_agent(agent, world, [agent])
    return float(agent.calories_eaten + world.nest_calories + 0.3 * agent.brood_visits)


def write_child_adapter(
    parents: list[Genome],
    rng: np.random.Generator,
    n_candidates: int = 4,
    eval_fn=None,
) -> Genome:
    """Take current best adapters, inner-loop, write a child distinct from parents."""
    if not parents:
        raise ValueError("trainer needs at least one parent adapter")
    eval_fn = eval_fn or (lambda g: inner_eval(g, rng))
    candidates = [mutate(parents[int(rng.integers(0, len(parents)))], rng) for _ in range(n_candidates)]
    scores = [float(eval_fn(c)) for c in candidates]
    child = candidates[int(np.argmax(np.asarray(scores)))]
    child.lineage_id = ""
    return child
