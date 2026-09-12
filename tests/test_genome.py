from __future__ import annotations

import numpy as np

from flyciv.adapter.genome import GENOME_SIZE, good_forager_genome, random_genome
from flyciv.adapter.mutate import mutate


def test_mutate_changes_the_genome_vector():
    rng = np.random.default_rng(0)
    parent = random_genome(rng)
    child = mutate(parent, rng, sigma=0.2)
    assert child.vector.shape == (GENOME_SIZE,)
    assert not np.allclose(child.vector, parent.vector)
    assert child.parent_id == parent.lineage_id


def test_good_forager_is_small_adapter():
    g = good_forager_genome()
    assert g.vector.shape == (GENOME_SIZE,)
    assert GENOME_SIZE < 100
    assert float(g.encoder_gains[0]) > 1.0
    assert float(g.role_bias[0]) > 1.0
