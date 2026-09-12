"""Minimal FLYB (not the Minecraft binary). Magic FLYB, then edges.

*.flyb is gitignored. This exists so a loader can read FLYB-or-npz when present.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

from flyciv.brain.graph import ConnectomeGraph
from flyciv.brain.params import SHIU2024

MAGIC = b"FLYB"
VERSION = 1


def dump_flyb(graph: ConnectomeGraph, path: Path) -> None:
    n = graph.n
    edges: list[tuple[int, int, int, int]] = []
    for post in range(n):
        for pre in range(n):
            count = int(graph.n_syn[post, pre])
            if count == 0:
                continue
            sign = 1 if graph.W[post, pre] >= 0 else -1
            edges.append((pre, post, count, sign))
    path = Path(path)
    with path.open("wb") as fh:
        fh.write(MAGIC)
        fh.write(struct.pack("<I", VERSION))
        fh.write(struct.pack("<I", n))
        fh.write(struct.pack("<I", len(edges)))
        for name, kind in zip(graph.names, graph.kinds):
            nb, kb = name.encode("utf-8"), kind.encode("utf-8")
            fh.write(struct.pack("<H", len(nb)))
            fh.write(nb)
            fh.write(struct.pack("<H", len(kb)))
            fh.write(kb)
        for pre, post, count, sign in edges:
            fh.write(struct.pack("<IIIb", pre, post, count, sign))
        gid = graph.graph_id.encode("utf-8")
        fh.write(struct.pack("<H", len(gid)))
        fh.write(gid)


def load_flyb(path: Path) -> ConnectomeGraph:
    data = Path(path).read_bytes()
    if data[:4] != MAGIC:
        raise ValueError(f"not FLYB: {path}")
    version, n, n_edges = struct.unpack_from("<III", data, 4)
    if version != VERSION:
        raise ValueError(f"unsupported FLYB version {version}")
    offset = 16
    names: list[str] = []
    kinds: list[str] = []
    for _ in range(n):
        ln = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        names.append(data[offset : offset + ln].decode("utf-8"))
        offset += ln
        lk = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        kinds.append(data[offset : offset + lk].decode("utf-8"))
        offset += lk
    n_syn = np.zeros((n, n), dtype=np.int32)
    sign = np.zeros((n, n), dtype=np.int8)
    for _ in range(n_edges):
        pre, post, count, s = struct.unpack_from("<IIIb", data, offset)
        offset += 13
        n_syn[post, pre] = count
        sign[post, pre] = s
    ln = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    graph_id = data[offset : offset + ln].decode("utf-8")
    W = n_syn.astype(np.float64) * SHIU2024.w_per_synapse_mv * sign.astype(np.float64)
    return ConnectomeGraph(
        graph_id=graph_id,
        names=tuple(names),
        kinds=tuple(kinds),
        W=W,
        n_syn=n_syn,
        provenance=f"flyb:{path}",
    )
