from __future__ import annotations

import numpy as np

from flyciv.adapter.genome import Genome


def mutate(genome: Genome, rng: np.random.Generator, sigma: float = 0.12) -> Genome:
    child = Genome(
        genome.vector + rng.normal(0.0, sigma, size=genome.vector.shape),
        parent_id=genome.lineage_id,
    )
    return child


def select_and_replace(
    genomes: list[Genome],
    fitness: np.ndarray,
    rng: np.random.Generator,
    keep_frac: float = 0.5,
    sigma: float = 0.12,
) -> list[Genome]:
    """Keep top keep_frac; fill the rest with mutated copies of survivors."""
    n = len(genomes)
    if n == 0:
        return []
    k = max(1, int(np.ceil(n * keep_frac)))
    order = np.argsort(-np.asarray(fitness, dtype=np.float64))
    survivors = [genomes[int(i)].copy() for i in order[:k]]
    out = list(survivors)
    while len(out) < n:
        parent = survivors[int(rng.integers(0, len(survivors)))]
        out.append(mutate(parent, rng, sigma=sigma))
    return out[:n]
