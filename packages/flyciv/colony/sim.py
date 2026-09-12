from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from flyciv.adapter.genome import Genome, good_forager_genome, random_genome
from flyciv.adapter.mutate import select_and_replace
from flyciv.brain.graph import ConnectomeGraph, load_toy_graph
from flyciv.colony.agent import Agent, Kind, make_crowd, make_hero, step_agent
from flyciv.colony.trainer import write_child_adapter
from flyciv.colony.wincheck import win_check
from flyciv.world.events import CivEvent
from flyciv.world.grid import (
    COLLAPSE_FLOOR,
    SURPLUS_THRESHOLD,
    World,
    decay_wear,
    make_world,
    paint_civilization,
    respawn_food,
)
from flyciv.world.stigmergy import detect_blocks, refresh_world_layers, trail_stability


def _place(world: World, rng: np.random.Generator, jitter: int) -> tuple[int, int, int]:
    y = world.nest_y + int(rng.integers(-jitter, jitter + 1))
    x = world.nest_x + int(rng.integers(-jitter, jitter + 1))
    y = min(world.size - 1, max(0, y))
    x = min(world.size - 1, max(0, x))
    heading = int(rng.integers(0, 4))
    return y, x, heading


def _new_id(prefix: str, n: int) -> str:
    return f"{prefix}-{n:04d}"


def _fitness(agent: Agent, world: World, trail_stab: float, trainer_ok: float) -> float:
    return (
        float(agent.calories_eaten)
        + 0.5 * float(agent.calories_deposited)
        + 0.3 * float(agent.brood_visits)
        + 0.05 * float(world.nest_calories) / max(1, 64)
        + 2.0 * trail_stab
        + trainer_ok
    )


def _snapshot(generation: int, world: World, agents: list[Agent], trail_stab: float, events: list[str]) -> dict[str, Any]:
    n_trails = int(world.trails.sum())
    n_roads = int(world.roads.sum())
    has_block = detect_blocks(world.roads, world.store, world.brood_sites)
    n_agents = sum(1 for a in agents if a.alive)
    collapsed = world.nest_calories < COLLAPSE_FLOOR and n_agents == 0
    world.collapsed = collapsed
    calories_eaten = float(sum(a.calories_eaten for a in agents))
    return {
        "generation": generation,
        "nest_calories": float(world.nest_calories),
        "calories_eaten": calories_eaten,
        "n_trails": n_trails,
        "n_roads": n_roads,
        "trail_stability": float(trail_stab),
        "brood_adults": int(world.brood_adults),
        "trainer_unlocked": bool(world.trainer_unlocked),
        "trainer_alive": bool(world.trainer_alive),
        "has_block": bool(has_block),
        "has_store": bool(world.store.any()),
        "n_agents": int(n_agents),
        "n_heroes": int(sum(1 for a in agents if a.kind is Kind.HERO)),
        "n_crowd": int(sum(1 for a in agents if a.kind is Kind.CROWD)),
        "wear_sum": float(world.wear.sum()),
        "collapsed": bool(collapsed),
        "events": list(events),
    }


def run_colony(
    *,
    seed: int,
    n_heroes: int = 4,
    n_crowd: int = 64,
    n_generations: int = 20,
    steps_per_gen: int = 48,
    world_size: int = 128,
    layout: str = "default",
    construct_win: bool = False,
    initial_genomes: list[Genome] | None = None,
    graph: ConnectomeGraph | None = None,
    out_dir: Path | None = None,
    smoke: bool = False,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    graph = graph or load_toy_graph()
    if construct_win:
        layout = "constructed-win"
        n_generations = max(n_generations, 2)
    world = make_world(world_size, rng, layout=layout)
    if construct_win:
        paint_civilization(world)

    n_agents = n_heroes + n_crowd
    genomes: list[Genome] = []
    if initial_genomes:
        genomes = [g.copy() for g in initial_genomes]
        while len(genomes) < n_agents:
            genomes.append(random_genome(rng))
        genomes = genomes[:n_agents]
    else:
        if n_heroes:
            genomes.append(good_forager_genome())
        while len(genomes) < n_agents:
            genomes.append(random_genome(rng))

    for i, g in enumerate(genomes):
        if not g.lineage_id:
            g.lineage_id = _new_id("lin", i)

    def spawn(gs: list[Genome]) -> list[Agent]:
        agents: list[Agent] = []
        jitter = 2 if world_size < 32 else 4
        for i in range(n_heroes):
            y, x, h = _place(world, rng, jitter)
            agents.append(make_hero(y, x, h, gs[i], graph, agent_id=_new_id("hero", i)))
        for j in range(n_crowd):
            y, x, h = _place(world, rng, jitter)
            idx = n_heroes + j
            agents.append(make_crowd(y, x, h, gs[idx], agent_id=_new_id("crowd", j)))
        return agents

    agents = spawn(genomes)
    events: list[CivEvent] = []
    seen: set[str] = set()
    history: list[dict[str, Any]] = []
    prev_trails = world.trails.copy()
    lineage_log: list[dict[str, Any]] = []
    next_lin = n_agents

    def emit(name: str, generation: int, step: int) -> None:
        if name in seen:
            return
        seen.add(name)
        events.append(CivEvent(generation, step, name))

    if construct_win:
        emit("first_trail", 0, 0)
        emit("first_store", 0, 0)
        emit("trainer_unlocked", 0, 0)

    for gen in range(1, n_generations + 1):
        gen_event_names: list[str] = []
        for a in agents:
            a.calories_eaten = 0.0
            a.calories_deposited = 0.0
            a.brood_visits = 0
            if a.brain is not None:
                a.brain.reset()
        for t in range(steps_per_gen):
            for a in agents:
                if not a.alive:
                    continue
                outcome = step_agent(a, world, agents)
                if outcome == "store":
                    emit("first_store", gen, t)
                    gen_event_names.append("first_store")
            respawn_food(world)
            decay_wear(world)
            occupied = {a.pos() for a in agents if a.alive}
            flags = refresh_world_layers(world, occupied)
            if flags["first_trail"]:
                emit("first_trail", gen, t)
                gen_event_names.append("first_trail")
            if flags["first_road"]:
                emit("first_road", gen, t)
                gen_event_names.append("first_road")

        occupied = {a.pos() for a in agents if a.alive}
        refresh_world_layers(world, occupied)
        stab = trail_stability(prev_trails, world.trails)
        prev_trails = world.trails.copy()

        if world.nest_calories >= SURPLUS_THRESHOLD and not world.trainer_unlocked:
            world.trainer_unlocked = True
            world.trainer_alive = True
            emit("trainer_unlocked", gen, steps_per_gen)
            gen_event_names.append("trainer_unlocked")

        if world.trainer_alive:
            world.nest_calories = max(0.0, world.nest_calories - world.trainer_cost)
            if world.nest_calories < COLLAPSE_FLOOR:
                world.trainer_alive = False
            else:
                parents = sorted(agents, key=lambda a: a.calories_eaten, reverse=True)[:4]
                child = write_child_adapter([p.genome for p in parents], rng, n_candidates=3)
                child.lineage_id = _new_id("lin", next_lin)
                next_lin += 1
                # write child onto the worst crowd fly
                crowd = [a for a in agents if a.kind is Kind.CROWD]
                if crowd:
                    worst = min(crowd, key=lambda a: a.calories_eaten)
                    worst.genome = child
                emit("trainer_child", gen, steps_per_gen)
                gen_event_names.append("trainer_child")

        trainer_ok = 5.0 if world.trainer_alive else 0.0
        fits = np.array([_fitness(a, world, stab, trainer_ok) for a in agents], dtype=np.float64)
        snap = _snapshot(gen, world, agents, stab, [e.name for e in events])
        history.append(snap)

        for a, f in zip(agents, fits):
            lineage_log.append(
                {
                    **a.genome.to_json(),
                    "generation": gen,
                    "fitness": float(f),
                    "kind": a.kind.value,
                    "agent_id": a.agent_id,
                }
            )

        if gen < n_generations:
            genomes = select_and_replace([a.genome for a in agents], fits, rng)
            for i, g in enumerate(genomes):
                if not g.lineage_id:
                    g.lineage_id = _new_id("lin", next_lin)
                    next_lin += 1
            # keep a good forager prior only on generation 1 spawn; after that, selection speaks
            agents = spawn(genomes)
            if construct_win:
                world.nest_calories = max(world.nest_calories, 40.0)
                world.trainer_alive = True
                world.trainer_unlocked = True
                paint_civilization(world)

    win = win_check(history, k=min(2, len(history)))
    report = {
        "seed": seed,
        "graph": graph.graph_id,
        "heroes": n_heroes,
        "crowd": n_crowd,
        "generations": n_generations,
        "steps_per_gen": steps_per_gen,
        "world_size": world_size,
        "layout": layout,
        "construct_win": construct_win,
        "smoke": smoke,
        "nest_calories": history[-1]["nest_calories"] if history else 0.0,
        "calories_eaten": history[-1]["calories_eaten"] if history else 0.0,
        "trails": history[-1]["n_trails"] if history else 0,
        "roads": history[-1]["n_roads"] if history else 0,
        "trail_stability": history[-1]["trail_stability"] if history else 0.0,
        "brood_adults": history[-1]["brood_adults"] if history else 0,
        "trainer_unlocked": history[-1]["trainer_unlocked"] if history else False,
        "trainer_alive": history[-1]["trainer_alive"] if history else False,
        "has_block": history[-1]["has_block"] if history else False,
        "wear_sum": history[-1]["wear_sum"] if history else 0.0,
        "win": win["win"],
        "win_report": win,
        "events": [e.as_dict() for e in events],
        "history": history,
        "graph_note": "frozen W; only adapters evolve",
    }
    if out_dir is not None:
        _write_run(Path(out_dir), report, lineage_log, agents, world)
    return report


def _write_run(
    out_dir: Path,
    report: dict[str, Any],
    lineage_log: list[dict[str, Any]],
    agents: list[Agent],
    world: World,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lin_dir = out_dir / "lineages"
    lin_dir.mkdir(exist_ok=True)
    (lin_dir / "all.json").write_text(json.dumps(lineage_log, indent=2), encoding="utf-8")
    # last generation genomes
    last = [a.genome.to_json() for a in agents]
    (lin_dir / "latest.json").write_text(json.dumps(last, indent=2), encoding="utf-8")
    from flyciv.colony.report import format_report

    (out_dir / "report.txt").write_text(format_report(report), encoding="utf-8")
    from flyciv.viz.ascii import render_ascii

    (out_dir / "map.txt").write_text(render_ascii(world, agents), encoding="utf-8")
