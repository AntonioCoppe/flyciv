from __future__ import annotations

from flyciv.colony.sim import run_colony


def test_showcase_grows_roads_and_spawns_a_child():
    frames: list[dict] = []
    report = run_colony(
        seed=1,
        n_heroes=4,
        n_crowd=12,
        n_generations=4,
        steps_per_gen=14,
        world_size=32,
        showcase=True,
        on_frame=lambda f, _w, _a: frames.append(f),
    )
    assert report["showcase"] is True
    assert report["trainer_unlocked"] is True
    assert any(e["name"] == "trainer_child" for e in report["events"])
    assert any(f.get("n_child", 0) > 0 for f in frames)
    assert any(a.get("k") == "C" for f in frames for a in f.get("agents", []))
    # Wear must actually accumulate on the axes (overcrank).
    assert report["wear_sum"] > 50
