"""Line-level analytics on top of :class:`ProductionLine`."""
from __future__ import annotations

from dataclasses import dataclass

from .line import ProductionLine, State


def bottleneck_index(line: ProductionLine) -> int:
    """The station that limits the line, from measured dynamics.

    Pure utilization is fooled by the first station: fed by an infinite source it
    can sit at 100 % in transient without being the constraint. The robust,
    data-derived signal is the **effective load** = measured cycle time x
    utilization — i.e. how much real work each station is forced to carry. The
    slowest, highly-loaded station wins, which matches the theoretical bottleneck
    (longest cycle time) once the line is warm.
    """
    return max(range(len(line.stations)),
               key=lambda i: line.stations[i].cycle_s * line.stations[i].utilization())


def theoretical_bottleneck(line: ProductionLine) -> int:
    return max(range(len(line.stations)), key=lambda i: line.stations[i].cycle_s)


def max_throughput_per_min(line: ProductionLine) -> float:
    """Ceiling imposed by the slowest station (parts/min)."""
    slowest = max(s.cycle_s for s in line.stations)
    return 60.0 / slowest


@dataclass
class LineSnapshot:
    throughput_per_min: float
    max_throughput_per_min: float
    efficiency: float                 # actual / theoretical max
    wip: int
    bottleneck: str
    produced: int
    stations: list[dict]

    def as_dict(self) -> dict:
        return {
            "throughput_per_min": round(self.throughput_per_min, 2),
            "max_throughput_per_min": round(self.max_throughput_per_min, 2),
            "efficiency": round(self.efficiency, 4),
            "wip": self.wip,
            "bottleneck": self.bottleneck,
            "produced": self.produced,
            "stations": self.stations,
        }


def snapshot(line: ProductionLine) -> LineSnapshot:
    bi = bottleneck_index(line)
    tp = line.throughput_per_min()
    mx = max_throughput_per_min(line)
    stations = [{
        "name": s.name,
        "cycle_s": s.cycle_s,
        "state": s.state.value,
        "utilization": round(s.utilization(), 3),
        "blocked": round(s.blocked_ratio(), 3),
        "starved": round(s.starved_ratio(), 3),
        "processed": s.processed,
        "is_bottleneck": (i == bi),
    } for i, s in enumerate(line.stations)]
    return LineSnapshot(
        throughput_per_min=tp,
        max_throughput_per_min=mx,
        efficiency=(tp / mx if mx else 0.0),
        wip=line.wip(),
        bottleneck=line.stations[bi].name,
        produced=line.produced,
        stations=stations,
    )
