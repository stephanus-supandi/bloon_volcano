"""
birds.py — BLOON VOLCANO EXPERIMENT v0

Tiny deterministic birds. Pure environmental actors.

    x += vx * dt
    y  = base_y + sin(t * freq + phase) * amplitude

No AI. No flocking. Just vibes.
"""

import math
import random

from environment import WIDTH

MARGIN = 40.0

class Bird:
    __slots__ = ("id", "x", "y", "base_y", "vx", "freq", "amp", "phase")

    def __init__(self, rng: random.Random, bird_id: int):
        self.id = bird_id
        self.x = rng.uniform(0.0, float(WIDTH))
        self.base_y = rng.uniform(180.0, 330.0)
        self.vx = rng.choice([-1.0, 1.0]) * rng.uniform(30.0, 60.0)
        self.freq = rng.uniform(2.0, 5.0)
        self.amp = rng.uniform(6.0, 18.0)
        self.phase = rng.uniform(0.0, 2.0 * math.pi)
        self.y = self.base_y

    def update(self, dt: float, t: float) -> None:
        self.x += self.vx * dt
        if self.x > WIDTH + MARGIN:
            self.x = -MARGIN
        elif self.x < -MARGIN:
            self.x = float(WIDTH) + MARGIN
        self.y = self.base_y + math.sin(t * self.freq + self.phase) * self.amp

def make_flock(rng: random.Random, n: int):
    return [Bird(rng, i + 1) for i in range(n)]