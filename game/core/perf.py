from __future__ import annotations

from collections import deque


class PerfOverlay:
    def __init__(self) -> None:
        self.frame_ms = 0.0
        self.max_ms = 0.0
        self.samples: deque[float] = deque(maxlen=120)

    def push(self, dt: float) -> None:
        ms = dt * 1000.0
        self.frame_ms = ms
        self.max_ms = max(self.max_ms * 0.98, ms)
        self.samples.append(ms)

    @property
    def avg_ms(self) -> float:
        if not self.samples:
            return 0.0
        return sum(self.samples) / len(self.samples)
