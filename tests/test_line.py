from linetwin import ProductionLine, snapshot
from linetwin.line import State
from linetwin.metrics import (bottleneck_index, max_throughput_per_min,
                              theoretical_bottleneck)


def test_part_conservation():
    """No part is created or destroyed: produced + WIP == total admitted."""
    line = ProductionLine(cycle_times=[2.0, 2.0, 3.5, 2.0], buffer_capacity=4, seed=1)
    line.run(duration_s=300)
    admitted = line._next_id           # parts pulled from the source
    in_system = line.wip()
    assert admitted == line.produced + in_system


def test_slowest_station_is_bottleneck():
    line = ProductionLine(cycle_times=[2.0, 2.0, 4.0, 2.0, 2.0], buffer_capacity=5, seed=2)
    line.run(duration_s=600)
    bi = bottleneck_index(line)
    assert bi == theoretical_bottleneck(line) == 2
    assert snapshot(line).bottleneck == "S2"
    # the bottleneck runs nearly flat-out
    assert line.stations[bi].utilization() > 0.9


def test_throughput_capped_by_bottleneck():
    line = ProductionLine(cycle_times=[2.0, 2.0, 4.0, 2.0], buffer_capacity=5, seed=3)
    line.run(duration_s=900)
    snap = snapshot(line)
    ceiling = max_throughput_per_min(line)        # 60/4 = 15 parts/min
    assert snap.throughput_per_min <= ceiling + 1e-6
    assert snap.throughput_per_min > 0.8 * ceiling  # should run near the ceiling


def test_upstream_buffer_fills_downstream_starves():
    line = ProductionLine(cycle_times=[1.0, 5.0, 1.0], buffer_capacity=3, seed=4)
    line.run(duration_s=300)
    # station before the slow one is often blocked; the one after is often starved
    assert line.stations[0].blocked_ratio() > 0.2
    assert line.stations[2].starved_ratio() > 0.2


def test_snapshot_is_serialisable():
    import json
    line = ProductionLine(cycle_times=[2.0, 3.0, 2.0], seed=5)
    line.run(duration_s=120)
    json.dumps(snapshot(line).as_dict())
