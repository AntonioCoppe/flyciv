from __future__ import annotations

import numpy as np

from flyciv.brain.graph import load_toy_graph
from flyciv.brain.lif import LIFNetwork
from flyciv.brain.params import SHIU2024


def test_lif_steps_with_frozen_w():
    graph = load_toy_graph()
    assert graph.graph_id == "flyciv-toy-20-v1"
    assert graph.n == 20
    w0 = graph.copy_W()
    net = LIFNetwork(graph)
    i_ext = np.zeros(graph.n)
    i_ext[graph.index("sugar_sensor")] = 25.0
    for _ in range(200):
        net.step(i_ext)
    np.testing.assert_array_equal(net.W, w0)
    np.testing.assert_array_equal(graph.W, w0)
    assert int(net.spike_count.sum()) > 0


def test_sugar_drive_reaches_dn_walk():
    graph = load_toy_graph()
    net = LIFNetwork(graph)
    i_ext = np.zeros(graph.n)
    i_ext[graph.index("sugar_sensor")] = 25.0
    dn = graph.index("dn_walk")
    for _ in range(400):
        net.step(i_ext)
    assert int(net.spike_count[dn]) > 0


def test_shiu_constants():
    p = SHIU2024
    assert p.tau_m_ms == 20.0
    assert p.tau_syn_ms == 5.0
    assert p.v_rest_mv == -52.0
    assert p.v_reset_mv == -52.0
    assert p.v_thresh_mv == -45.0
    assert p.t_refrac_ms == 2.2
    assert p.syn_delay_ms == 1.8
    assert p.w_per_synapse_mv == 0.275
