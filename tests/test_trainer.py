from __future__ import annotations

import numpy as np

from flyciv.adapter.genome import good_forager_genome, random_genome
from flyciv.colony.trainer import inner_eval, write_child_adapter


def test_trainer_writes_child_distinct_from_parents():
    rng = np.random.default_rng(2)
    parents = [good_forager_genome(), random_genome(np.random.default_rng(1))]
    child = write_child_adapter(
        parents,
        rng,
        n_candidates=3,
        eval_fn=lambda g: inner_eval(g, np.random.default_rng(3), n_steps=8, size=12),
    )
    assert child.vector.shape == parents[0].vector.shape
    assert not np.allclose(child.vector, parents[0].vector)
    assert not np.allclose(child.vector, parents[1].vector)
