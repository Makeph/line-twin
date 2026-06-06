"""Discrete-time digital twin of a serial production line.

A line is N stations in series, each with an input buffer of finite capacity:

    source ──▶ [buf0] ──▶ S0 ──▶ [buf1] ──▶ S1 ──▶ ... ──▶ S(n-1) ──▶ sink

Each station pulls a part from its input buffer, processes it for a (noisy)
cycle time, then pushes it to the next buffer. If the next buffer is full the
station is **blocked** (it holds the finished part and cannot start a new one).
If its own input buffer is empty the station is **starved**.

The slowest station becomes the **bottleneck**: its upstream buffer fills, its
downstream stations starve, and it caps the throughput of the whole line. The
twin measures all of this so it can be visualised and optimised — pure stdlib.
"""
from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    STARVED = "starved"   # idle, no input
    BUSY = "busy"         # processing a part
    BLOCKED = "blocked"   # finished, downstream buffer full


@dataclass
class Station:
    name: str
    cycle_s: float                 # nominal processing time per part
    cv: float = 0.15               # coefficient of variation (process noise)
    state: State = State.STARVED
    remaining: float = 0.0
    processed: int = 0
    _busy_t: float = 0.0
    _blocked_t: float = 0.0
    _starved_t: float = 0.0
    _t: float = 0.0
    _rng: random.Random = field(default=None, repr=False)

    def _sample(self) -> float:
        sigma = self.cycle_s * self.cv
        return max(0.05, self._rng.gauss(self.cycle_s, sigma))

    def utilization(self) -> float:
        return self._busy_t / self._t if self._t else 0.0

    def blocked_ratio(self) -> float:
        return self._blocked_t / self._t if self._t else 0.0

    def starved_ratio(self) -> float:
        return self._starved_t / self._t if self._t else 0.0


@dataclass
class ProductionLine:
    cycle_times: list[float]
    buffer_capacity: int = 5
    cv: float = 0.15
    seed: int = 0
    stations: list[Station] = field(default_factory=list)
    buffers: list[deque] = field(default_factory=list)
    produced: int = 0              # parts reaching the sink
    _next_id: int = 0
    _t: float = 0.0

    def __post_init__(self):
        rng = random.Random(self.seed)
        self.stations = []
        for i, c in enumerate(self.cycle_times):
            s = Station(name=f"S{i}", cycle_s=c, cv=self.cv)
            s._rng = random.Random(rng.randint(0, 1 << 30))
            self.stations.append(s)
        # one input buffer per station; source feeds buffer[0] on demand
        self.buffers = [deque() for _ in self.cycle_times]

    # ---- simulation -------------------------------------------------
    def step(self, dt: float = 0.1) -> None:
        n = len(self.stations)
        self._t += dt

        # advance processing time of busy stations
        for s in self.stations:
            s._t += dt
            if s.state is State.BUSY:
                s.remaining -= dt
                s._busy_t += dt

        # unload finished stations, downstream-first so space frees up
        for i in range(n - 1, -1, -1):
            s = self.stations[i]
            if s.state is State.BUSY and s.remaining <= 0:
                s.state = State.BLOCKED      # finished, try to hand off
            if s.state is State.BLOCKED:
                if i == n - 1:               # last station -> sink
                    self.produced += 1
                    s.processed += 1
                    s.state = State.STARVED
                elif len(self.buffers[i + 1]) < self.buffer_capacity:
                    self.buffers[i + 1].append(self._next_id)
                    s.processed += 1
                    s.state = State.STARVED
                else:
                    s._blocked_t += dt       # still blocked this tick

        # load idle stations from their input buffer (source for S0)
        for i, s in enumerate(self.stations):
            if s.state is State.STARVED:
                if i == 0:                   # infinite source
                    self._next_id += 1
                    s.state = State.BUSY
                    s.remaining = s._sample()
                elif self.buffers[i]:
                    self.buffers[i].popleft()
                    s.state = State.BUSY
                    s.remaining = s._sample()
                else:
                    s._starved_t += dt

    def run(self, duration_s: float, dt: float = 0.1):
        steps = int(duration_s / dt)
        for _ in range(steps):
            self.step(dt)
        return self

    # ---- live state -------------------------------------------------
    def wip(self) -> int:
        """Work-in-process: parts in buffers + parts being processed/held."""
        in_buf = sum(len(b) for b in self.buffers)
        in_station = sum(1 for s in self.stations if s.state in (State.BUSY, State.BLOCKED))
        return in_buf + in_station

    def throughput_per_min(self) -> float:
        return self.produced / self._t * 60 if self._t else 0.0
