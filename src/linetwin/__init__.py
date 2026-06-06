"""line-twin — a digital twin of a serial production line.

    from linetwin import ProductionLine, snapshot

    line = ProductionLine(cycle_times=[2.0, 2.0, 3.5, 2.0], buffer_capacity=5, seed=1)
    line.run(duration_s=600)
    print(snapshot(line).as_dict())   # throughput, WIP, bottleneck...
"""
from .line import ProductionLine, State, Station
from .metrics import (LineSnapshot, bottleneck_index, max_throughput_per_min,
                      snapshot, theoretical_bottleneck)

__all__ = [
    "ProductionLine", "Station", "State",
    "snapshot", "LineSnapshot", "bottleneck_index",
    "theoretical_bottleneck", "max_throughput_per_min",
]
__version__ = "0.1.0"
