from __future__ import annotations

from pathlib import Path

import numpy as np

from flyciv.brain.graph import load_graph, load_toy_graph
from flyciv.data.flyb import dump_flyb, load_flyb


def test_npz_and_flyb_roundtrip(tmp_path: Path):
    graph = load_toy_graph()
    npz = tmp_path / "toy.npz"
    np.savez(
        npz,
        W=graph.W,
        n_syn=graph.n_syn,
        names=np.array(graph.names, dtype=object),
        kinds=np.array(graph.kinds, dtype=object),
        id=graph.graph_id,
    )
    loaded = load_graph(npz)
    assert loaded.graph_id == graph.graph_id
    np.testing.assert_allclose(loaded.W, graph.W)

    flyb = tmp_path / "toy.flyb"
    dump_flyb(graph, flyb)
    from_bin = load_flyb(flyb)
    assert from_bin.graph_id == graph.graph_id
    np.testing.assert_allclose(from_bin.W, graph.W)
    via = load_graph(flyb)
    np.testing.assert_allclose(via.W, graph.W)
