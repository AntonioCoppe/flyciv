from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

# encoder: sugar, light, loom, bitter
N_ENCODER = 4
# actions: walk, turn, linger, follow
N_ACTIONS = 4
# crowd features: food_n, food_e, food_s, food_w, wear, nearby, brood_dx, brood_dy
N_FEATURES = 8
N_READOUT = N_ACTIONS * N_FEATURES
# outcomes: ate, brood, loom  ×  ppl1_reward, ppl1_punish
N_OUTCOMES = 3
N_PPL1 = 2
N_DOPA = N_OUTCOMES * N_PPL1
# roles: forage, guard, nurse, scout
N_ROLES = 4
GENOME_SIZE = N_ENCODER + N_READOUT + N_DOPA + N_ROLES  # 46

SUGAR, LIGHT, LOOM, BITTER = 0, 1, 2, 3
WALK, TURN, LINGER, FOLLOW = 0, 1, 2, 3
ATE, BROOD, LOOM_OUT = 0, 1, 2
FORAGE, GUARD, NURSE, SCOUT = 0, 1, 2, 3


def _split(vec: NDArray[np.float64]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if vec.shape != (GENOME_SIZE,):
        raise ValueError(f"genome vector must have length {GENOME_SIZE}, got {vec.shape}")
    i = 0
    enc = vec[i : i + N_ENCODER]
    i += N_ENCODER
    readout = vec[i : i + N_READOUT]
    i += N_READOUT
    dopa = vec[i : i + N_DOPA]
    i += N_DOPA
    roles = vec[i : i + N_ROLES]
    return enc, readout, dopa, roles


@dataclass
class Genome:
    """Small evolving adapter. Frozen W is not in here."""

    vector: NDArray[np.float64]
    lineage_id: str = ""
    parent_id: str = ""

    def __post_init__(self) -> None:
        self.vector = np.asarray(self.vector, dtype=np.float64).reshape(GENOME_SIZE).copy()

    @property
    def encoder_gains(self) -> NDArray[np.float64]:
        return _split(self.vector)[0]

    @property
    def readout(self) -> NDArray[np.float64]:
        return _split(self.vector)[1]

    def readout_matrix(self) -> NDArray[np.float64]:
        return self.readout.reshape(N_ACTIONS, N_FEATURES)

    @property
    def dopamine_routing(self) -> NDArray[np.float64]:
        return _split(self.vector)[2].reshape(N_OUTCOMES, N_PPL1)

    @property
    def role_bias(self) -> NDArray[np.float64]:
        return _split(self.vector)[3]

    def copy(self) -> Genome:
        return Genome(self.vector.copy(), lineage_id=self.lineage_id, parent_id=self.parent_id)

    def to_json(self) -> dict:
        return {
            "lineage_id": self.lineage_id,
            "parent_id": self.parent_id,
            "vector": [float(x) for x in self.vector],
        }

    @classmethod
    def from_json(cls, data: dict) -> Genome:
        return cls(
            np.asarray(data["vector"], dtype=np.float64),
            lineage_id=str(data.get("lineage_id", "")),
            parent_id=str(data.get("parent_id", "")),
        )

    @classmethod
    def zeros(cls) -> Genome:
        return cls(np.zeros(GENOME_SIZE, dtype=np.float64))


def random_genome(rng: np.random.Generator, scale: float = 0.15) -> Genome:
    return Genome(rng.normal(0.0, scale, size=GENOME_SIZE))


def good_forager_genome() -> Genome:
    """Hand-written adapter: high sugar gain, walk-from-food readout, forage bias.

    Not painted onto the world; it has to actually find food under the same
    body programs as everyone else.
    """
    g = Genome.zeros()
    vec = g.vector
    vec[0:4] = (2.5, 0.15, 0.2, 0.05)
    R = vec[N_ENCODER : N_ENCODER + N_READOUT].reshape(N_ACTIONS, N_FEATURES)
    R[WALK, 0:4] = 1.6  # food dirs drive walk
    R[WALK, 4:] = 0.0
    R[TURN, :] = -0.2
    R[LINGER, :] = -0.4
    R[FOLLOW, :] = 0.0
    dopa = vec[N_ENCODER + N_READOUT : N_ENCODER + N_READOUT + N_DOPA].reshape(N_OUTCOMES, N_PPL1)
    dopa[ATE, 0] = 1.0
    dopa[LOOM_OUT, 1] = 1.0
    vec[-4:] = (1.8, 0.0, 0.15, 0.1)  # forage, guard, nurse, scout
    return Genome(vec, lineage_id="good-forager")
