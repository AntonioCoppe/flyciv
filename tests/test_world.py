from __future__ import annotations

import numpy as np

from flyciv.world.stigmergy import detect_blocks, detect_trails, promote_roads


def test_wear_becomes_trail_then_road():
    size = 16
    wear = np.zeros((size, size), dtype=np.float64)
    food = np.zeros((size, size), dtype=np.float64)
    food[2, 2] = 3.0
    food[2, 12] = 3.0
    for x in range(2, 13):
        wear[2, x] = 10.0
    trails = detect_trails(wear, food)
    assert bool(trails[2, 7])
    occupied: set[tuple[int, int]] = set()
    roads = promote_roads(trails, occupied, wear=wear)
    assert bool(roads[2, 7])


def test_occupied_trail_cell_is_not_yet_a_road_without_hardening():
    size = 12
    wear = np.zeros((size, size), dtype=np.float64)
    food = np.zeros((size, size), dtype=np.float64)
    food[1, 1] = 1.0
    food[1, 9] = 1.0
    for x in range(1, 10):
        wear[1, x] = 8.0
    trails = detect_trails(wear, food, threshold=6.0)
    roads = promote_roads(trails, occupied={(1, 5)}, existing=np.zeros_like(trails), wear=None)
    assert bool(trails[1, 5])
    assert not bool(roads[1, 5])
    assert bool(roads[1, 4])


def test_block_needs_junction_store_and_brood():
    size = 8
    roads = np.zeros((size, size), dtype=np.bool_)
    store = np.zeros((size, size), dtype=np.bool_)
    brood = np.zeros((size, size), dtype=np.int32)
    roads[4, 2:7] = True
    roads[2:7, 4] = True
    assert detect_blocks(roads, store, brood) is False
    store[4, 5] = True
    brood[4, 3] = 2
    assert detect_blocks(roads, store, brood) is True
