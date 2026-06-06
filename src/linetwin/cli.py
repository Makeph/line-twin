"""CLI: simulate a line and print throughput, WIP and the bottleneck.

    python -m linetwin run --cycles 2,2,3.5,2 --duration 600
    python -m linetwin run --cycles 2,2,3.5,2 --buffer 5 --json
"""
from __future__ import annotations

import argparse
import json

from .line import ProductionLine
from .metrics import snapshot


def run(args: argparse.Namespace) -> int:
    cycles = [float(x) for x in args.cycles.split(",")]
    line = ProductionLine(cycle_times=cycles, buffer_capacity=args.buffer,
                          cv=args.cv, seed=args.seed)
    line.run(duration_s=args.duration, dt=args.dt)
    snap = snapshot(line)
    if args.json:
        print(json.dumps(snap.as_dict(), indent=2))
        return 0
    print(f"line: {len(cycles)} stations  buffer={args.buffer}  "
          f"{args.duration:.0f}s simulated\n")
    print(f"{'station':<8}{'cycle':>7}{'util':>8}{'blocked':>9}{'starved':>9}{'made':>7}")
    for s in snap.stations:
        mark = "  <-- BOTTLENECK" if s["is_bottleneck"] else ""
        print(f"{s['name']:<8}{s['cycle_s']:>6.1f}s{s['utilization']*100:>7.0f}%"
              f"{s['blocked']*100:>8.0f}%{s['starved']*100:>8.0f}%{s['processed']:>7}{mark}")
    print(f"\nthroughput  {snap.throughput_per_min:5.1f} parts/min   "
          f"(ceiling {snap.max_throughput_per_min:.1f})")
    print(f"efficiency  {snap.efficiency*100:5.1f}%   WIP {snap.wip}   "
          f"produced {snap.produced}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="linetwin", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="simulate a production line")
    r.add_argument("--cycles", default="2,2,3.5,2", help="comma-separated cycle times (s)")
    r.add_argument("--buffer", type=int, default=5, help="buffer capacity between stations")
    r.add_argument("--duration", type=float, default=600.0, help="seconds to simulate")
    r.add_argument("--dt", type=float, default=0.1)
    r.add_argument("--cv", type=float, default=0.15, help="cycle-time coefficient of variation")
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=run)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
