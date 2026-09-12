from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from flyciv.brain.params import SHIU2024

TOY_GRAPH_ID = "flyciv-toy-20-v1"


@dataclass
class ConnectomeGraph:
    """Frozen weighted graph. W[post, pre] in millivolts per spike."""

    graph_id: str
    names: tuple[str, ...]
    kinds: tuple[str, ...]
    W: NDArray[np.float64]
    n_syn: NDArray[np.int32]
    provenance: str = ""

    @property
    def n(self) -> int:
        return int(self.W.shape[0])

    def index(self, name: str) -> int:
        return self.names.index(name)

    def indices(self, kind: str) -> tuple[int, ...]:
        return tuple(i for i, k in enumerate(self.kinds) if k == kind)

    def copy_W(self) -> NDArray[np.float64]:
        return np.array(self.W, dtype=np.float64, copy=True)


def graph_from_spec(spec: dict[str, Any]) -> ConnectomeGraph:
    neurons = sorted(spec["neurons"], key=lambda n: int(n["i"]))
    n = len(neurons)
    names = tuple(str(n["name"]) for n in neurons)
    kinds = tuple(str(n["kind"]) for n in neurons)
    n_syn = np.zeros((n, n), dtype=np.int32)
    sign = np.zeros((n, n), dtype=np.int8)
    for e in spec["edges"]:
        pre, post = int(e["pre"]), int(e["post"])
        n_syn[post, pre] = int(e["n_syn"])
        sign[post, pre] = int(e["sign"])
    W = n_syn.astype(np.float64) * SHIU2024.w_per_synapse_mv * sign.astype(np.float64)
    return ConnectomeGraph(
        graph_id=str(spec["id"]),
        names=names,
        kinds=kinds,
        W=W,
        n_syn=n_syn,
        provenance=str(spec.get("provenance", "")),
    )


def load_json_graph(path: Path) -> ConnectomeGraph:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    return graph_from_spec(spec)


def load_npz_graph(path: Path) -> ConnectomeGraph:
    data = np.load(path, allow_pickle=True)
    names = tuple(str(x) for x in data["names"].tolist())
    kinds = tuple(str(x) for x in data["kinds"].tolist())
    W = np.array(data["W"], dtype=np.float64)
    if "n_syn" in data:
        n_syn = np.array(data["n_syn"], dtype=np.int32)
    else:
        n_syn = np.rint(np.abs(W) / SHIU2024.w_per_synapse_mv).astype(np.int32)
    graph_id = str(data["id"].item() if getattr(data["id"], "shape", ()) == () else data["id"])
    return ConnectomeGraph(
        graph_id=graph_id,
        names=names,
        kinds=kinds,
        W=W,
        n_syn=n_syn,
        provenance="npz",
    )


def load_graph(path: Path) -> ConnectomeGraph:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json_graph(path)
    if suffix == ".npz":
        return load_npz_graph(path)
    if suffix == ".flyb":
        from flyciv.data.flyb import load_flyb

        return load_flyb(path)
    raise ValueError(f"unknown graph format: {path}")


def load_toy_graph() -> ConnectomeGraph:
    from importlib.resources import files

    path = files("flyciv.brain.fixtures").joinpath("toy20.json")
    return graph_from_spec(json.loads(path.read_text(encoding="utf-8")))
