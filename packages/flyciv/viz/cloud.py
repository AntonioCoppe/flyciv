"""MaleCNS soma cloud for brain-view B.

Coordinates are a viz subsample of male-cns:v1.0 somaLocation (CC BY 4.0,
Berg et al., Cell 2026). Not meshes, not synapses. Toy-graph spikes are mapped
onto 20 stand-in somata plus a scripted halo — see HONESTY.md.
"""

from __future__ import annotations

import base64
from importlib.resources import files
from typing import Any

import numpy as np

from flyciv.brain.graph import load_toy_graph

TOY_SUPERCLASS = {
    "sugar_sensor": "ol_sensory",
    "light_sensor": "visual_projection",
    "loom_sensor": "visual_projection",
    "bitter_sensor": "ol_sensory",
    "food_inter": "cb_intrinsic",
    "wear_inter": "cb_intrinsic",
    "nearby_inter": "cb_intrinsic",
    "ppl1_reward": "cb_intrinsic",
    "ppl1_punish": "cb_intrinsic",
    "hidden_a": "cb_intrinsic",
    "hidden_b": "cb_intrinsic",
    "hidden_c": "cb_intrinsic",
    "hidden_d": "cb_intrinsic",
    "dn_walk": "descending_neuron",
    "dn_turn_left": "descending_neuron",
    "dn_turn_right": "descending_neuron",
    "dn_linger": "descending_neuron",
    "dn_follow": "descending_neuron",
    "mn_forward": "vnc_motor",
    "mn_turn": "vnc_motor",
}

SC_CODES = (
    "cb_intrinsic",
    "ol_intrinsic",
    "vnc_intrinsic",
    "visual_projection",
    "descending_neuron",
    "ascending_neuron",
    "vnc_motor",
    "cb_motor",
    "visual_centrifugal",
    "ol_sensory",
    "vnc_efferent",
    "cb_endocrine",
    "unknown",
)


def load_soma_xyz() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = files("flyciv.viz.fixtures").joinpath("malecns_somas_viz.npz")
    data = np.load(path, allow_pickle=True)
    xyz = np.asarray(data["xyz"], dtype=np.float32)
    ids = np.asarray(data["ids"], dtype=np.int64)
    sc = np.asarray(data["superclass"]).astype(str)
    return ids, xyz, sc


def _orient(xyz: np.ndarray, sc: np.ndarray) -> np.ndarray:
    """Rotate so VNC hangs +Y (down on the canvas after projection)."""
    cb = xyz[sc == "cb_intrinsic"].mean(axis=0) if np.any(sc == "cb_intrinsic") else xyz.mean(0)
    vnc = xyz[sc == "vnc_intrinsic"].mean(axis=0) if np.any(sc == "vnc_intrinsic") else cb + np.array([0, 0, 1])
    down = vnc - cb
    down = down / (np.linalg.norm(down) + 1e-9)
    # world Y = down, world X = a horizontal axis, world Z = depth
    helper = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    if abs(float(np.dot(helper, down))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    x_axis = np.cross(helper, down)
    x_axis = x_axis / (np.linalg.norm(x_axis) + 1e-9)
    z_axis = np.cross(x_axis, down)
    z_axis = z_axis / (np.linalg.norm(z_axis) + 1e-9)
    rot = np.stack([x_axis, down, z_axis], axis=1)  # columns = new axes in old coords? we want new = R @ old
    # points in new frame: [x_axis, down, z_axis] as rows
    R = np.stack([x_axis, down, z_axis], axis=0)
    centered = xyz - xyz.mean(axis=0)
    return (R @ centered.T).T.astype(np.float32)


def _pick_toy_indices(xyz: np.ndarray, sc: np.ndarray, names: tuple[str, ...]) -> np.ndarray:
    idx = np.zeros(len(names), dtype=np.int32)
    used: set[int] = set()
    for i, name in enumerate(names):
        want = TOY_SUPERCLASS.get(name, "cb_intrinsic")
        pool = np.where(sc == want)[0]
        if pool.size == 0:
            pool = np.arange(len(xyz))
        order = pool[np.argsort(xyz[pool, 1])]  # spread along VNC axis
        pick = int(order[int((i + 0.5) * (len(order) - 1) / max(1, len(names)))])
        if pick in used and pool.size > 1:
            for alt in order:
                if int(alt) not in used:
                    pick = int(alt)
                    break
        used.add(pick)
        idx[i] = pick
    return idx


def _halos(xyz: np.ndarray, centers: np.ndarray, k: int = 28) -> list[list[int]]:
    out: list[list[int]] = []
    for c in centers:
        d = np.sum((xyz - xyz[int(c)]) ** 2, axis=1)
        neigh = np.argpartition(d, min(k, len(d) - 1))[:k]
        out.append([int(i) for i in neigh])
    return out


def spectator_cloud() -> dict[str, Any]:
    ids, xyz, sc = load_soma_xyz()
    xyz = _orient(xyz, sc)
    scale = float(np.max(np.linalg.norm(xyz, axis=1))) or 1.0
    xyz = xyz / scale
    graph = load_toy_graph()
    toy_idx = _pick_toy_indices(xyz, sc, graph.names)
    codes = np.array([SC_CODES.index(s) if s in SC_CODES else SC_CODES.index("unknown") for s in sc], dtype=np.uint8)
    packed = np.ascontiguousarray(xyz.astype(np.float32))
    return {
        "n": int(len(xyz)),
        "xyz_b64": base64.b64encode(packed.tobytes()).decode("ascii"),
        "sc_b64": base64.b64encode(codes.tobytes()).decode("ascii"),
        "sc_names": list(SC_CODES),
        "toy_idx": toy_idx.tolist(),
        "toy_names": list(graph.names),
        "toy_kinds": list(graph.kinds),
        "halo": _halos(xyz, toy_idx),
        "dataset": "male-cns:v1.0",
        "license": "CC BY 4.0",
        "cite": "Berg et al., Cell 2026. Soma locations only; viz subsample, not the full connectome.",
        "note": "Toy spikes light 20 stand-in somata + a scripted halo. Not 176k LIF.",
    }
