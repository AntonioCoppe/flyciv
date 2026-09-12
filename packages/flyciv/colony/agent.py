from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from flyciv.adapter.genome import ATE, BROOD, FOLLOW, LINGER, LOOM_OUT, TURN, WALK, Genome
from flyciv.adapter.policy import Sensors, action_from_logits, chemotax_heading, crowd_logits
from flyciv.brain.graph import ConnectomeGraph
from flyciv.brain.lif import LIFNetwork
from flyciv.world.grid import HEADINGS, World


class Kind(str, Enum):
    HERO = "hero"
    CROWD = "crowd"


@dataclass
class Agent:
    kind: Kind
    y: int
    x: int
    heading: int
    genome: Genome
    brain: LIFNetwork | None = None
    carried: float = 0.0
    calories_eaten: float = 0.0
    calories_deposited: float = 0.0
    brood_visits: int = 0
    alive: bool = True
    agent_id: str = ""
    last_action: int = LINGER
    last_outcome: str = ""
    spike_sketch: list[int] = field(default_factory=list)
    rates: list[float] = field(default_factory=list)
    eye: dict = field(default_factory=dict)
    is_child: bool = False
    showcase_axis: int | None = None

    def pos(self) -> tuple[int, int]:
        return self.y, self.x


def sense(agent: Agent, world: World, others: list[Agent], radius: int = 6) -> Sensors:
    s = Sensors()
    size = world.size
    y, x = agent.y, agent.x
    s.food_here = float(world.food[y, x])
    s.wear = float(world.wear[y, x])
    s.brood_here = 1.0 if world.brood[y, x] > 0 else 0.0
    s.nest_dx = float(world.nest_x - x)
    s.nest_dy = float(world.nest_y - y)
    s.light = 1.0 / (1.0 + abs(s.nest_dx) + abs(s.nest_dy))
    dirs = [(0, (-1, 0)), (1, (0, 1)), (2, (1, 0)), (3, (0, -1))]
    acc = [0.0, 0.0, 0.0, 0.0]
    for r in range(1, radius + 1):
        for di, (dy, dx) in dirs:
            ny, nx = y + dy * r, x + dx * r
            if 0 <= ny < size and 0 <= nx < size:
                acc[di] += float(world.food[ny, nx]) / r
    s.food_n, s.food_e, s.food_s, s.food_w = acc
    nearby = 0.0
    loom = 0.0
    for o in others:
        if o is agent or not o.alive:
            continue
        d = abs(o.y - y) + abs(o.x - x)
        if d == 0:
            continue
        if d <= 3:
            nearby += 1.0 / d
        if d == 1:
            loom += 1.0
    s.nearby = nearby
    s.loom = loom
    # brood vector (nearest brood cell)
    brood_pos = np.argwhere(world.brood > 0)
    if len(brood_pos):
        dgrid = np.abs(brood_pos[:, 0] - y) + np.abs(brood_pos[:, 1] - x)
        i = int(np.argmin(dgrid))
        s.brood_dy = float(brood_pos[i, 0] - y)
        s.brood_dx = float(brood_pos[i, 1] - x)
    return s


def _hero_logits(agent: Agent, sensors: Sensors) -> np.ndarray:
    assert agent.brain is not None
    g = agent.genome
    graph = agent.brain.graph
    i_ext = np.zeros(graph.n, dtype=np.float64)
    enc = g.encoder_gains
    food_max = max(sensors.food_n, sensors.food_e, sensors.food_s, sensors.food_w, sensors.food_here)
    i_ext[graph.index("sugar_sensor")] = 28.0 * float(enc[0]) * food_max
    i_ext[graph.index("light_sensor")] = 18.0 * float(enc[1]) * sensors.light
    i_ext[graph.index("loom_sensor")] = 22.0 * float(enc[2]) * sensors.loom
    i_ext[graph.index("bitter_sensor")] = 10.0 * float(enc[3])
    i_ext[graph.index("wear_inter")] = 8.0 * min(sensors.wear, 20.0) / 20.0
    i_ext[graph.index("nearby_inter")] = 12.0 * sensors.nearby
    # dopamine routing onto PPL1-style cells (does not change W)
    if agent.last_outcome == "ate":
        route = g.dopamine_routing[ATE]
        i_ext[graph.index("ppl1_reward")] += 15.0 * float(route[0])
        i_ext[graph.index("ppl1_punish")] += 15.0 * float(route[1])
    elif agent.last_outcome == "brood":
        route = g.dopamine_routing[BROOD]
        i_ext[graph.index("ppl1_reward")] += 12.0 * float(route[0])
        i_ext[graph.index("ppl1_punish")] += 12.0 * float(route[1])
    elif agent.last_outcome == "loom":
        route = g.dopamine_routing[LOOM_OUT]
        i_ext[graph.index("ppl1_reward")] += 12.0 * float(route[0])
        i_ext[graph.index("ppl1_punish")] += 12.0 * float(route[1])
    before = agent.brain.spike_count.copy()
    rates = agent.brain.run_ticks(i_ext)
    fired = (agent.brain.spike_count - before) > 0
    agent.spike_sketch = fired.astype(int).tolist()
    agent.rates = [float(x) for x in rates]
    dn = [
        rates[graph.index("dn_walk")],
        rates[graph.index("dn_turn_left")],
        rates[graph.index("dn_turn_right")],
        rates[graph.index("dn_linger")],
        rates[graph.index("dn_follow")],
        rates[graph.index("mn_forward")],
        rates[graph.index("mn_turn")],
        0.0,
    ]
    feats = np.array(dn, dtype=np.float64)
    logits = g.readout_matrix() @ feats
    food_signal = food_max
    logits[WALK] += float(g.role_bias[0]) * food_signal
    # If the sugar pathway is actually firing, boost walk (scripted readout prior).
    logits[WALK] += 0.5 * rates[graph.index("dn_walk")]
    logits[TURN] += 0.3 * (rates[graph.index("dn_turn_left")] + rates[graph.index("dn_turn_right")])
    logits[LINGER] += 0.3 * rates[graph.index("dn_linger")]
    logits[FOLLOW] += 0.3 * rates[graph.index("dn_follow")]
    return logits


def decide(agent: Agent, sensors: Sensors) -> int:
    if agent.kind is Kind.HERO and agent.brain is not None:
        logits = _hero_logits(agent, sensors)
    else:
        logits = crowd_logits(agent.genome, sensors)
    return action_from_logits(logits)


def _step_toward(agent: Agent, ty: int, tx: int, world: World) -> None:
    dy = 0 if ty == agent.y else (1 if ty > agent.y else -1)
    dx = 0 if tx == agent.x else (1 if tx > agent.x else -1)
    if abs(ty - agent.y) >= abs(tx - agent.x):
        nx, ny = agent.x, agent.y + dy
    else:
        nx, ny = agent.x + dx, agent.y
    if world.in_bounds(ny, nx):
        agent.y, agent.x = ny, nx
        if dy == -1:
            agent.heading = 0
        elif dx == 1:
            agent.heading = 1
        elif dy == 1:
            agent.heading = 2
        elif dx == -1:
            agent.heading = 3


def _showcase_walk(agent: Agent, world: World) -> None:
    """Video-only axial walk. Labeled showcase, not emergence."""
    axis = 0 if agent.showcase_axis is None else int(agent.showcase_axis) % 4
    arm = max(8, world.size // 6)
    dist = abs(agent.y - world.nest_y) + abs(agent.x - world.nest_x)
    if dist >= arm:
        agent.heading = (axis + 2) % 4
    elif dist == 0:
        agent.heading = axis
    dy, dx = HEADINGS[agent.heading]
    ny, nx = agent.y + dy, agent.x + dx
    if world.in_bounds(ny, nx):
        agent.y, agent.x = ny, nx
    agent.last_action = WALK


def body_program(agent: Agent, action: int, sensors: Sensors, world: World, others: list[Agent]) -> None:
    """Scripted body programs (neurocraft split). HONESTY.md."""
    if world.showcase and agent.kind is Kind.HERO:
        _showcase_walk(agent, world)
        return
    if world.showcase and agent.kind is Kind.CROWD:
        # Mill near the nest so 64 flies read as a crowd.
        if abs(agent.y - world.nest_y) + abs(agent.x - world.nest_x) > 7:
            _step_toward(agent, world.nest_y, world.nest_x, world)
        else:
            agent.heading = (agent.heading + (1 if action == TURN else 0)) % 4
            dy, dx = HEADINGS[agent.heading]
            ny, nx = agent.y + dy, agent.x + dx
            if world.in_bounds(ny, nx):
                agent.y, agent.x = ny, nx
        agent.last_action = WALK
        return
    # Return to nest when full — scripted.
    if agent.carried >= 2.0:
        _step_toward(agent, world.nest_y, world.nest_x, world)
        agent.last_action = WALK
        return
    heading = chemotax_heading(agent.genome, sensors)
    if action == WALK:
        if heading is not None:
            agent.heading = heading
        dy, dx = HEADINGS[agent.heading]
        ny, nx = agent.y + dy, agent.x + dx
        if world.in_bounds(ny, nx):
            agent.y, agent.x = ny, nx
    elif action == TURN:
        agent.heading = (agent.heading + 1) % 4
    elif action == FOLLOW:
        nearest = None
        best = 10**9
        for o in others:
            if o is agent or not o.alive:
                continue
            d = abs(o.y - agent.y) + abs(o.x - agent.x)
            if 0 < d < best:
                best = d
                nearest = o
        if nearest is not None:
            _step_toward(agent, nearest.y, nearest.x, world)
    # linger: no move
    agent.last_action = action


def interact(agent: Agent, world: World) -> str:
    y, x = agent.y, agent.x
    outcome = ""
    if world.food[y, x] > 0:
        bite = min(1.0, float(world.food[y, x]))
        world.food[y, x] -= bite
        agent.carried += bite
        agent.calories_eaten += bite
        outcome = "ate"
    if world.brood[y, x] > 0:
        world.brood[y, x] -= 1
        agent.brood_visits += 1
        outcome = "brood" if not outcome else outcome
        if world.brood[y, x] == 0:
            world.brood_adults += 1
    if abs(agent.y - world.nest_y) + abs(agent.x - world.nest_x) <= 1 and agent.carried > 0:
        world.nest_calories += agent.carried
        agent.calories_deposited += agent.carried
        agent.carried = 0.0
        # store: a designed stockpile cell next to the nest
        sy, sx = world.nest_y, min(world.size - 1, world.nest_x + 1)
        first = not world.store[sy, sx]
        world.store[sy, sx] = True
        if first:
            outcome = "store" if not outcome else outcome
    agent.last_outcome = outcome
    return outcome


def step_agent(agent: Agent, world: World, others: list[Agent]) -> str:
    sensors = sense(agent, world, others)
    agent.eye = {
        "food": [
            round(sensors.food_n, 3),
            round(sensors.food_e, 3),
            round(sensors.food_s, 3),
            round(sensors.food_w, 3),
            round(sensors.food_here, 3),
        ],
        "loom": round(sensors.loom, 3),
        "wear": round(sensors.wear, 3),
        "heading": int(agent.heading),
    }
    action = decide(agent, sensors)
    body_program(agent, action, sensors, world, others)
    world.occupy(agent.y, agent.x)
    return interact(agent, world)


def make_hero(y: int, x: int, heading: int, genome: Genome, graph: ConnectomeGraph, agent_id: str) -> Agent:
    return Agent(
        kind=Kind.HERO,
        y=y,
        x=x,
        heading=heading,
        genome=genome,
        brain=LIFNetwork(graph),
        agent_id=agent_id,
    )


def make_crowd(y: int, x: int, heading: int, genome: Genome, agent_id: str) -> Agent:
    return Agent(kind=Kind.CROWD, y=y, x=x, heading=heading, genome=genome, agent_id=agent_id)
