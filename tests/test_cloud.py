from __future__ import annotations

from flyciv.viz.cloud import load_soma_xyz, spectator_cloud


def test_soma_cloud_is_malecns_subsample():
    ids, xyz, sc = load_soma_xyz()
    assert len(ids) > 1000
    assert xyz.shape[1] == 3
    assert "descending_neuron" in set(sc.tolist())
    assert "vnc_motor" in set(sc.tolist())


def test_spectator_cloud_maps_toy_cells():
    cloud = spectator_cloud()
    assert cloud["n"] > 1000
    assert cloud["dataset"] == "male-cns:v1.0"
    assert len(cloud["toy_idx"]) == 20
    assert len(cloud["halo"]) == 20
    assert all(0 <= i < cloud["n"] for i in cloud["toy_idx"])
    assert "xyz_b64" in cloud
    assert "scripted halo" in cloud["note"].lower() or "halo" in cloud["note"].lower()
