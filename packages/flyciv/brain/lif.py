from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from flyciv.brain.graph import ConnectomeGraph
from flyciv.brain.params import LIFParams, SHIU2024


class LIFNetwork:
    """Leaky integrate-and-fire on a frozen W. Shiu 2024-style, not an MLP.

    Voltage: τ_m dV/dt = -(V - V_rest) + I_syn + I_ext
    Synapse: τ_syn dI/dt = -I + arriving spikes · W
    Spikes arrive after syn_delay_ms. W is never written.
    """

    def __init__(self, graph: ConnectomeGraph, params: LIFParams | None = None) -> None:
        self.graph = graph
        self.params = params or SHIU2024
        self._W = graph.copy_W()
        n = graph.n
        p = self.params
        self.delay_steps = max(1, int(round(p.syn_delay_ms / p.dt_ms)))
        self.n_ticks = max(1, int(round(p.brain_ms_per_world_step / p.dt_ms)))
        self.v = np.full(n, p.v_rest_mv, dtype=np.float64)
        self.i_syn = np.zeros(n, dtype=np.float64)
        self.refrac = np.zeros(n, dtype=np.float64)
        self._buf = np.zeros((self.delay_steps, n), dtype=np.bool_)
        self._buf_i = 0
        self.spike_count = np.zeros(n, dtype=np.int64)
        self.last_spikes = np.zeros(n, dtype=np.bool_)

    @property
    def W(self) -> NDArray[np.float64]:
        return self._W

    def reset(self) -> None:
        p = self.params
        self.v[:] = p.v_rest_mv
        self.i_syn[:] = 0.0
        self.refrac[:] = 0.0
        self._buf[:] = False
        self._buf_i = 0
        self.spike_count[:] = 0
        self.last_spikes[:] = False

    def step(self, i_ext: NDArray[np.float64]) -> NDArray[np.bool_]:
        """Advance one dt. Returns a boolean spike vector. Does not modify W."""
        p = self.params
        decay_syn = np.exp(-p.dt_ms / p.tau_syn_ms)
        self.i_syn *= decay_syn
        arriving = self._buf[self._buf_i]
        if arriving.any():
            # 0.275 mV/synapse is a PSP amplitude. Scale current so one spike
            # yields a peak near n_syn * 0.275 mV (Shiu unitary synapse).
            self.i_syn += (self._W @ arriving.astype(np.float64)) * (
                p.tau_m_ms / p.tau_syn_ms
            )
        active = self.refrac <= 0.0
        dv = (-(self.v - p.v_rest_mv) + self.i_syn + i_ext) * (p.dt_ms / p.tau_m_ms)
        self.v = np.where(active, self.v + dv, self.v)
        spiked = (self.v >= p.v_thresh_mv) & active
        self.v[spiked] = p.v_reset_mv
        self.refrac[spiked] = p.t_refrac_ms
        self.refrac = np.maximum(0.0, self.refrac - p.dt_ms)
        self._buf[self._buf_i] = spiked
        self._buf_i = (self._buf_i + 1) % self.delay_steps
        self.spike_count += spiked.astype(np.int64)
        self.last_spikes = spiked
        return spiked

    def run_ticks(self, i_ext: NDArray[np.float64], n_ticks: int | None = None) -> NDArray[np.float64]:
        """Run several dt ticks; return firing *rate* (spikes per ms)."""
        ticks = self.n_ticks if n_ticks is None else n_ticks
        start = self.spike_count.copy()
        for _ in range(ticks):
            self.step(i_ext)
        spikes = self.spike_count - start
        elapsed = ticks * self.params.dt_ms
        return spikes.astype(np.float64) / max(elapsed, 1e-9)
