from __future__ import annotations

from flyciv.colony.sim import run_colony
from flyciv.colony.wincheck import win_check


def _snap(**kwargs):
    base = {
        "generation": 1,
        "n_roads": 10,
        "trainer_alive": True,
        "has_block": True,
        "collapsed": False,
        "n_agents": 8,
        "nest_calories": 50.0,
    }
    base.update(kwargs)
    return base


def test_win_check_true_on_constructed_surplus_k2():
    history = [_snap(generation=1), _snap(generation=2)]
    out = win_check(history, k=2)
    assert out["win"] is True


def test_win_check_false_if_trainer_dead():
    history = [_snap(generation=1), _snap(generation=2, trainer_alive=False)]
    out = win_check(history, k=2)
    assert out["win"] is False
    assert any("trainer dead" in r for r in out["reasons"])


def test_win_check_false_if_no_roads():
    history = [_snap(generation=1, n_roads=0), _snap(generation=2, n_roads=0)]
    out = win_check(history, k=2)
    assert out["win"] is False
    assert any("no roads" in r for r in out["reasons"])


def test_run_colony_construct_win():
    report = run_colony(
        seed=1,
        n_heroes=1,
        n_crowd=4,
        n_generations=2,
        steps_per_gen=4,
        world_size=16,
        construct_win=True,
    )
    assert report["trainer_unlocked"] is True
    assert report["win"] is True
    assert report["roads"] >= 1
