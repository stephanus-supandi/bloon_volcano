"""
volcano.py — BLOON VOLCANO EXPERIMENT v0

Toy volcano state machine:

    QUIET -> RUMBLING -> ERUPTING -> DECAYING -> QUIET -> ...

Phase durations are drawn from random.Random(seed), so the whole cycle
is deterministic per seed.

HONESTY NOTE:
    NOT a volcanic eruption model. No magma chamber dynamics, no plume
    thermodynamics, no hazard forecast. Toy visual state machine only.
"""

import math
import random
from enum import Enum

MAX_ASH_RATE = 60.0    # particles/s at full strength

class VolcanoState(Enum):
    QUIET = "QUIET"
    RUMBLING = "RUMBLING"
    ERUPTING = "ERUPTING"
    DECAYING = "DECAYING"

class Volcano:
    """Minimal volcano state. All randomness comes from the injected rng."""

    def __init__(self, rng: random.Random, x: float, y: float):
        self.rng = rng
        self.x = float(x)
        self.y = float(y)
        self.state = VolcanoState.QUIET
        self.timer = 0.0
        self.phase_duration = rng.uniform(2.0, 5.0)
        self.eruption_strength = 0.0
        self.target_strength = rng.uniform(0.6, 1.0)
        self.lava_level = 0.05
        self.ash_rate = 0.0
        self.smoke_density = 0.0

    def _enter(self, new_state: VolcanoState, duration: float) -> None:
        self.state = new_state
        self.timer = 0.0
        self.phase_duration = duration

    def update(self, dt: float) -> None:
        self.timer += dt
        s = self.state

        if s is VolcanoState.QUIET:
            self.lava_level = min(1.0, self.lava_level + 0.03 * dt)
            self.eruption_strength = max(0.0, self.eruption_strength - 0.5 * dt)
            self.smoke_density = max(0.0, self.smoke_density - 0.2 * dt)
            self.ash_rate = 0.0
            if self.timer >= self.phase_duration:
                self._enter(VolcanoState.RUMBLING, self.rng.uniform(1.5, 3.0))

        elif s is VolcanoState.RUMBLING:
            self.lava_level = min(1.0, self.lava_level + 0.25 * dt)
            self.eruption_strength = min(
                self.target_strength,
                self.eruption_strength + self.target_strength * 0.5 * dt)
            self.smoke_density = max(self.smoke_density, 0.15)
            self.ash_rate = self.eruption_strength * MAX_ASH_RATE * 0.15
            if self.timer >= self.phase_duration:
                self._enter(VolcanoState.ERUPTING, self.rng.uniform(8.0, 15.0))

        elif s is VolcanoState.ERUPTING:
            wobble = 0.92 + 0.08 * math.sin(self.timer * 3.1)
            self.eruption_strength = self.target_strength * wobble
            self.lava_level = min(1.0, self.lava_level + 0.2 * dt)
            self.ash_rate = self.eruption_strength * MAX_ASH_RATE
            self.smoke_density = self.eruption_strength
            if self.timer >= self.phase_duration:
                self._enter(VolcanoState.DECAYING, self.rng.uniform(5.0, 9.0))

        else:  # DECAYING
            self.eruption_strength = max(0.0, self.eruption_strength - 0.12 * dt)
            self.ash_rate = self.eruption_strength * MAX_ASH_RATE
            self.smoke_density = self.eruption_strength * 0.8
            self.lava_level = max(0.1, self.lava_level - 0.12 * dt)
            if self.timer >= self.phase_duration or self.eruption_strength <= 0.05:
                self._enter(VolcanoState.QUIET, self.rng.uniform(2.0, 5.0))
                self.target_strength = self.rng.uniform(0.6, 1.0)
                self.lava_level = 0.15

    # ------------------------------------------------------------------
    def plume_region(self, wind_speed: float):
        """
        Axis-aligned box used ONLY for the toy ASH ENCOUNTER event.
        Returns (x0, y0, x1, y1) or None.

        NOTE: visual bounding box, NOT an ash concentration field and
        NOT an aviation safety threshold.
        """
        if self.state is VolcanoState.QUIET or self.eruption_strength <= 0.05:
            return None
        h = 80.0 + self.eruption_strength * 240.0
        drift = wind_speed * self.eruption_strength * 200.0
        x0 = min(self.x, self.x + drift) - 70.0
        x1 = max(self.x, self.x + drift) + 70.0
        return (x0, self.y - h, x1, self.y + 30.0)

    def plume_contains(self, px: float, py: float, wind_speed: float) -> bool:
        r = self.plume_region(wind_speed)
        if r is None:
            return False
        return r[0] <= px <= r[2] and r[1] <= py <= r[3]