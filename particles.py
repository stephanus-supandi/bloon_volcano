"""
particles.py — BLOON VOLCANO EXPERIMENT v0

Minimal 2D particle system (ash + smoke):

    vy += gravity * dt
    vx += wind * wind_factor * dt
    x  += vx * dt
    y  += vy * dt

Particles expire via lifetime; the system is hard-capped at MAX_PARTICLES.
No infinite growth. No CFD. No diffusion. Toy transport only.
"""

import math

from environment import WIDTH, GROUND_Y

MAX_PARTICLES = 1500

GRAVITY = 90.0             # px/s^2, ash falls
SMOKE_BUOYANCY = -12.0     # px/s^2, smoke slowly rises
ASH_WIND_FACTOR = 20.0
SMOKE_WIND_FACTOR = 34.0

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "lifetime", "age", "size", "kind")

    def __init__(self, x, y, vx, vy, lifetime, size, kind="ash"):
        if not (math.isfinite(x) and math.isfinite(y)
                and math.isfinite(vx) and math.isfinite(vy)):
            raise ValueError("particle position/velocity must be finite")
        if lifetime <= 0.0:
            raise ValueError("lifetime must be positive")
        if size <= 0.0:
            raise ValueError("size must be positive")
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.lifetime = float(lifetime)
        self.age = 0.0
        self.size = float(size)
        self.kind = kind  # "ash" | "smoke"

class ParticleSystem:
    def __init__(self, max_particles: int = MAX_PARTICLES):
        self.max_particles = int(max_particles)
        self.particles = []
        self.spawned_total = 0
        self.removed_total = 0

    def add(self, p: Particle) -> bool:
        """Add particle. Returns False (drops it) when at capacity."""
        if len(self.particles) >= self.max_particles:
            return False
        self.particles.append(p)
        self.spawned_total += 1
        return True

    def update(self, dt: float, wind_speed: float) -> None:
        keep = []
        for p in self.particles:
            if p.kind == "ash":
                g, wf = GRAVITY, ASH_WIND_FACTOR
            else:
                g, wf = SMOKE_BUOYANCY, SMOKE_WIND_FACTOR

            p.vy += g * dt
            p.vx += wind_speed * wf * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.age += dt

            alive = p.age < p.lifetime
            if alive and p.kind == "ash" and p.y >= GROUND_Y and p.vy > 0.0:
                alive = False            # deposited on ground
            if alive and (p.x < -120.0 or p.x > WIDTH + 120.0):
                alive = False            # blown out of the world
            if alive and p.y < -160.0:
                alive = False            # smoke escaped upwards

            if alive:
                keep.append(p)
            else:
                self.removed_total += 1
        self.particles = keep

    def count(self, kind=None) -> int:
        if kind is None:
            return len(self.particles)
        return sum(1 for p in self.particles if p.kind == kind)

    def clear(self) -> None:
        self.particles = []