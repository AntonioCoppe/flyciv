from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from flyciv.adapter.genome import FOLLOW, FORAGE, LINGER, NURSE, SUGAR, TURN, WALK, Genome

ACTION_NAMES = ("walk", "turn", "linger", "follow")


@dataclass
class Sensors:
    food_n: float = 0.0
    food_e: float = 0.0
    food_s: float = 0.0
    food_w: float = 0.0
    food_here: float = 0.0
    wear: float = 0.0
    nearby: float = 0.0
    brood_dx: float = 0.0
    brood_dy: float = 0.0
    brood_here: float = 0.0
    nest_dx: float = 0.0
    nest_dy: float = 0.0
    light: float = 0.0
    loom: float = 0.0
    bitter: float = 0.0


def feature_vector(genome: Genome, sensors: Sensors) -> NDArray[np.float64]:
    enc = genome.encoder_gains
    sugar = float(enc[SUGAR])
    return np.array(
        [
            sensors.food_n * sugar,
            sensors.food_e * sugar,
            sensors.food_s * sugar,
            sensors.food_w * sugar,
            sensors.wear * 0.05,
            sensors.nearby * float(enc[2]),
            sensors.brood_dx * float(enc[1]),
            sensors.brood_dy * float(enc[1]),
        ],
        dtype=np.float64,
    )


def crowd_logits(genome: Genome, sensors: Sensors) -> NDArray[np.float64]:
    feats = feature_vector(genome, sensors)
    logits = genome.readout_matrix() @ feats
    roles = genome.role_bias
    food_max = max(sensors.food_n, sensors.food_e, sensors.food_s, sensors.food_w, sensors.food_here)
    logits[WALK] += float(roles[FORAGE]) * food_max
    logits[LINGER] += float(roles[NURSE]) * sensors.brood_here
    logits[FOLLOW] += float(roles[3]) * sensors.nearby
    return logits


def action_from_logits(logits: NDArray[np.float64]) -> int:
    return int(np.argmax(np.asarray(logits, dtype=np.float64)))


def chemotax_heading(genome: Genome, sensors: Sensors) -> int | None:
    """Scripted body-program helper: face food if sugar encoder gain is high enough."""
    if float(genome.encoder_gains[SUGAR]) < 0.8:
        return None
    dirs = np.array(
        [sensors.food_n, sensors.food_e, sensors.food_s, sensors.food_w],
        dtype=np.float64,
    )
    if float(dirs.max()) <= 0.0:
        return None
    return int(np.argmax(dirs))
