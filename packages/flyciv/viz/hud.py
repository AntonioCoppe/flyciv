from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from flyciv.viz.cloud import spectator_cloud


def write_hud(path: Path, frames: list[dict[str, Any]], meta: dict[str, Any] | None = None) -> Path:
    path = Path(path)
    payload_meta = dict(meta or {})
    if "cloud" not in payload_meta:
        payload_meta["cloud"] = spectator_cloud()
    payload = {"meta": payload_meta, "frames": frames}
    tmpl = files("flyciv.viz.fixtures").joinpath("spectator.html").read_text(encoding="utf-8")
    html = tmpl.replace("__FRAMES__", json.dumps(payload, separators=(",", ":")))
    path.write_text(html, encoding="utf-8")
    return path
