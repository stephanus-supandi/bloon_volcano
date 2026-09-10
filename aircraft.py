"""
aircraft.py — BLOON VOLCANO EXPERIMENT v0

Toy aircraft flying straight across the scene at fixed altitude.
Deterministic. NOT a flight simulator, NOT a routing model, and it does
NOT implement any real aviation regulation. Entering the visual plume
box only raises a simulation event: ASH_ENCOUNTER.
"""

import random

from environment import WIDTH

MARGIN = 80.0

class Aircraft:
    __slots__ = ("id", "x", "y", "altitude", "speed", "heading", "in_plume")

    def __init__(self, rng: random.Random, aircraft_id: int):
        self.id = aircraft_id
        self.x = rng.uniform(0.0, float(WIDTH))
        self.altitude = rng.uniform(90.0, 240.0)
        self.y = self.altitude
        self.speed = rng.uniform(60.0, 110.0)   # px/s
        self.heading = rng.choice([-1.0, 1.0])  # -1 left, +1 right
        self.in_plume = False

    def update(self, dt: float) -> None:
        self.x += self.speed * self.heading * dt
        if self.x > WIDTH + MARGIN:
            self.x = -MARGIN
        elif self.x < -MARGIN:
            self.x = float(WIDTH) + MARGIN

def make_fleet(rng: random.Random, n: int):
    return [Aircraft(rng, i + 1) for i in range(n)]