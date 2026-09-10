"""
environment.py — BLOON VOLCANO EXPERIMENT v0

World geometry, wind, and cloud layer.

HONESTY NOTE:
    Wind is a single slowly-drifting scalar (toy value), NOT an
    atmospheric model. No turbulence, no shear, no meteorological data.
"""

import random

# ---------------------------------------------------------------- geometry
WIDTH = 1180
HEIGHT = 820
SCENE_H = 560
STATE_PANEL = (0, SCENE_H, WIDTH, 130)
LOG_PANEL = (0, SCENE_H + 130, WIDTH, HEIGHT - SCENE_H - 130)

GROUND_Y = SCENE_H - 40
CRATER_X = WIDTH // 2
CRATER_Y = GROUND_Y - 170

# ---------------------------------------------------------------- constants
WIND_MIN = -2.0
WIND_MAX = 2.0
WIND_DRIFT = 0.03            # max |delta wind| per 1/30 s step
CLOUD_SPEED_SCALE = 14.0     # px/s per wind unit, times per-cloud factor
N_CLOUDS = 5

class Cloud:
    """Decorative cloud of circular puffs. Moves with wind, wraps around."""

    __slots__ = ("x", "y", "speed_factor", "puffs")

    def __init__(self, rng: random.Random):
        self.x = rng.uniform(0.0, float(WIDTH))
        self.y = rng.uniform(50.0, 190.0)
        self.speed_factor = rng.uniform(0.25, 0.70)  # != ash speed
        self.puffs = [
            (rng.uniform(-42.0, 42.0), rng.uniform(-10.0, 10.0),
             rng.uniform(18.0, 38.0))
            for _ in range(rng.randint(3, 5))
        ]

    def update(self, dt: float, wind_speed: float) -> None:
        self.x += wind_speed * self.speed_factor * CLOUD_SPEED_SCALE * dt
        if self.x > WIDTH + 160.0:
            self.x = -160.0
        elif self.x < -160.0:
            self.x = float(WIDTH) + 160.0

class Environment:
    """Wind + clouds. Deterministic given the shared rng."""

    def __init__(self, rng: random.Random):
        self.wind_speed = rng.uniform(-1.0, 1.0)
        self.clouds = [Cloud(rng) for _ in range(N_CLOUDS)]

    @property
    def wind_direction(self) -> int:
        """+1 = blowing right, -1 = blowing left."""
        return 1 if self.wind_speed >= 0.0 else -1

    def update(self, dt: float, rng: random.Random) -> None:
        drift = rng.uniform(-WIND_DRIFT, WIND_DRIFT) * (dt * 30.0)
        self.wind_speed = max(WIND_MIN, min(WIND_MAX, self.wind_speed + drift))
        for c in self.clouds:
            c.update(dt, self.wind_speed)