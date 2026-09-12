from __future__ import annotations

from pathlib import Path

from flyciv.cli import main
from flyciv.colony.sim import run_colony


def test_cli_smoke(tmp_path: Path, capsys):
    code = main(["smoke", "--seed", "1", "--out", str(tmp_path / "smoke")])
    assert code == 0
    out = capsys.readouterr().out
    assert "flyciv-toy-20-v1" in out
    assert "generation 1/1 complete" in out
    assert "nest_calories" in out
    assert (tmp_path / "smoke" / "report.json").is_file()


def test_same_seed_same_numbers():
    kwargs = dict(
        seed=7,
        n_heroes=2,
        n_crowd=6,
        n_generations=2,
        steps_per_gen=8,
        world_size=24,
    )
    a = run_colony(**kwargs)
    b = run_colony(**kwargs)
    assert a["nest_calories"] == b["nest_calories"]
    assert a["calories_eaten"] == b["calories_eaten"]
    assert a["trails"] == b["trails"]
    assert a["roads"] == b["roads"]
    assert a["wear_sum"] == b["wear_sum"]
    assert a["trainer_unlocked"] == b["trainer_unlocked"]
