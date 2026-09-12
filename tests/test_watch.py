from __future__ import annotations

from pathlib import Path

import numpy as np

from flyciv.cli import main
from flyciv.colony.agent import make_crowd
from flyciv.adapter.genome import good_forager_genome
from flyciv.viz.frames import capture_frame
from flyciv.viz.hud import write_hud
from flyciv.world.grid import make_world


def test_capture_frame_has_map_and_agents():
    rng = np.random.default_rng(0)
    world = make_world(16, rng, layout="constructed-win")
    agent = make_crowd(world.nest_y, world.nest_x, heading=1, genome=good_forager_genome(), agent_id="c0")
    frame = capture_frame(world, [agent], generation=1, step=3, events=[])
    assert frame["size"] == 16
    assert frame["res"] == 16
    assert len(frame["agents"]) == 1
    assert frame["agents"][0]["k"] == "c"
    assert frame["calories"] > 0
    assert frame["trainer"] is True
    assert any(any(row) for row in frame["roads"])


def test_watch_writes_hud(tmp_path: Path, capsys):
    out = tmp_path / "watch"
    code = main(
        [
            "watch",
            "--seed",
            "1",
            "--heroes",
            "1",
            "--crowd",
            "3",
            "--generations",
            "2",
            "--steps",
            "4",
            "--size",
            "16",
            "--out",
            str(out),
            "--no-open",
        ]
    )
    assert code == 0
    html = (out / "hud.html").read_text(encoding="utf-8")
    assert "FLYCIV" in html
    assert "frames" in html
    assert "<canvas" in html
    printed = capsys.readouterr().out
    assert "HUD:" in printed
    assert "frames" in printed


def test_write_hud_embeds_frames(tmp_path: Path):
    path = write_hud(tmp_path / "hud.html", [{"generation": 1, "step": 0, "agents": [], "spikes": []}])
    text = path.read_text(encoding="utf-8")
    assert '"generation":1' in text.replace(" ", "")
