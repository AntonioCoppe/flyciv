from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

from flyciv import __version__
from flyciv.brain.graph import load_toy_graph
from flyciv.colony.report import format_report, load_report
from flyciv.colony.sim import run_colony
from flyciv.data.fetch import fetch_dataset
from flyciv.data.manifest import MALE_CNS_V1


def _latest_dir(base: Path) -> Path:
    return base / "latest"


def cmd_smoke(args: argparse.Namespace) -> int:
    graph = load_toy_graph()
    out = Path(args.out) if args.out else Path("runs") / "latest"
    report = run_colony(
        seed=int(args.seed),
        n_heroes=2,
        n_crowd=8,
        n_generations=1,
        steps_per_gen=16,
        world_size=32,
        out_dir=out,
        smoke=True,
        graph=graph,
    )
    print("flyciv smoke")
    print(f"graph: {graph.graph_id} ({graph.n} neurons, frozen W, Shiu-2024 LIF)")
    print("generation 1/1 complete")
    print(f"nest_calories: {report['nest_calories']}")
    print(f"calories_eaten: {report['calories_eaten']}")
    print(f"wear_sum: {report['wear_sum']}")
    ev = report.get("events") or []
    print("events: " + (", ".join(e["name"] for e in ev) if ev else "(none this generation)"))
    print("ok")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else Path("runs") / "latest"
    report = run_colony(
        seed=int(args.seed),
        n_heroes=int(args.heroes),
        n_crowd=int(args.crowd),
        n_generations=int(args.generations),
        steps_per_gen=int(args.steps),
        world_size=int(args.size),
        construct_win=bool(args.construct_win),
        out_dir=out,
    )
    print(format_report(report), end="")
    print(f"wrote {out / 'report.json'}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    data = load_report(Path(args.run_dir))
    print(format_report(data), end="")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    result = fetch_dataset(args.dataset, Path(args.out), try_network=bool(args.try_network))
    print(f"dataset: {result['dataset']}")
    print(f"out: {result['out']}")
    print(f"instructions: {result['download_md']}")
    print(f"sha256 checked: {result['checked'] or '(no SHA256SUMS yet)'}")
    if result["network"] is not None:
        print(f"neuprint: {result['network']}")
    print(result["note"])
    print(f"cite: {MALE_CNS_V1['cite']}")
    return 0


def cmd_view(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    hud = run_dir / "hud.html"
    map_path = run_dir / "map.txt"
    if hud.is_file():
        print(f"HUD: {hud.resolve()}")
        if not args.no_open:
            _open(hud)
    if map_path.is_file():
        print(map_path.read_text(encoding="utf-8"), end="")
    elif (run_dir / "report.json").is_file():
        print(format_report(load_report(run_dir)), end="")
    else:
        print(f"no run at {run_dir}; try: flyciv watch", file=sys.stderr)
        return 1
    return 0


def _open(path: Path) -> None:
    uri = path.resolve().as_uri()
    try:
        webbrowser.open(uri)
    except Exception:
        subprocess.run(["open", str(path)], check=False)


def cmd_watch(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else Path("runs") / "watch"
    report = run_colony(
        seed=int(args.seed),
        n_heroes=int(args.heroes),
        n_crowd=int(args.crowd),
        n_generations=int(args.generations),
        steps_per_gen=int(args.steps),
        world_size=int(args.size),
        construct_win=not bool(args.plain),
        out_dir=out,
        collect_frames=True,
    )
    hud = out / "hud.html"
    print(format_report(report), end="")
    print(f"HUD: {hud.resolve()}  ({report.get('n_frames', 0)} frames)")
    print("Spectator: W world · B brain (soma cloud) · H neuroscope. Drag brain to orbit.")
    print("Toy LIF spikes light 20 stand-in MaleCNS somata + a scripted halo. Roads/trainer are designed rules.")
    if hud.is_file() and not args.no_open:
        _open(hud)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flyciv",
        description="Colony sim on the MaleCNS fruit-fly connectome. Frozen brains, evolving adapters.",
    )
    p.add_argument("--version", action="version", version=f"flyciv {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke", help="toy graph, one generation, no download")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--out", type=str, default="")
    s.set_defaults(func=cmd_smoke)

    r = sub.add_parser("run", help="run a colony")
    r.add_argument("--heroes", type=int, default=4)
    r.add_argument("--crowd", type=int, default=64)
    r.add_argument("--generations", type=int, default=20)
    r.add_argument("--seed", type=int, default=7)
    r.add_argument("--steps", type=int, default=48)
    r.add_argument("--size", type=int, default=128)
    r.add_argument("--out", type=str, default="")
    r.add_argument(
        "--construct-win",
        action="store_true",
        help="seeded surplus city used to gate the trainer/win-check mechanism (not emergence)",
    )
    r.set_defaults(func=cmd_run)

    rp = sub.add_parser("report", help="print trails, calories, trainer-unlocked")
    rp.add_argument("run_dir", nargs="?", default="runs/latest")
    rp.set_defaults(func=cmd_report)

    f = sub.add_parser("fetch", help="download instructions + SHA256 check")
    f.add_argument("--dataset", default=MALE_CNS_V1["dataset"])
    f.add_argument("--out", default="data/derived/")
    f.add_argument("--try-network", action="store_true")
    f.set_defaults(func=cmd_fetch)

    v = sub.add_parser("view", help="ASCII map of a run (opens HUD if present)")
    v.add_argument("run_dir", nargs="?", default="runs/latest")
    v.add_argument("--no-open", action="store_true")
    v.set_defaults(func=cmd_view)

    w = sub.add_parser("watch", help="run a colony and open a live-replay HUD in the browser")
    w.add_argument("--heroes", type=int, default=4)
    w.add_argument("--crowd", type=int, default=64)
    w.add_argument("--generations", type=int, default=2)
    w.add_argument("--seed", type=int, default=7)
    w.add_argument("--steps", type=int, default=48)
    w.add_argument("--size", type=int, default=128)
    w.add_argument("--out", type=str, default="")
    w.add_argument("--plain", action="store_true", help="do not paint the constructed city (random mill)")
    w.add_argument("--no-open", action="store_true")
    w.set_defaults(func=cmd_watch)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def _entry() -> None:
    raise SystemExit(main())
