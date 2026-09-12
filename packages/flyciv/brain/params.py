"""Shiu et al., Nature 634:210–219 (2024) LIF constants.

These are published model parameters reused by hobbyist engines
(fly-brain-minecraft, fly.ai, doomfly). We reimplemented from the paper,
not by copying those repos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LIFParams:
    tau_m_ms: float = 20.0
    tau_syn_ms: float = 5.0
    v_rest_mv: float = -52.0
    v_reset_mv: float = -52.0
    v_thresh_mv: float = -45.0
    t_refrac_ms: float = 2.2
    syn_delay_ms: float = 1.8
    w_per_synapse_mv: float = 0.275
    dt_ms: float = 0.5  # sim approximation; delay 1.8→2 steps, refrac 2.2→4 steps
    brain_ms_per_world_step: float = 20.0


SHIU2024 = LIFParams()
