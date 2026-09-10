"""
main.py — BLOON VOLCANO EXPERIMENT v0

Entry point + Simulation orchestration (STATE -> SIMULATION).
Visualization lives in visualization.py and pygame is imported ONLY in
GUI mode, so headless mode and tests never need a display.

Usage:
    python main.py                        # GUI (pygame)
    python main.py --seed 7               # GUI, custom seed
    python main.py --headless 120         # 120 steps, no display
    python main.py --headless 120 --seed 42
"""

import argparse
import random
import sys

from aircraft import make_fleet
from birds import make_flock
from environment import Environment, CRATER_X, CRATER_Y
from particles import Particle, ParticleSystem, MAX_PARTICLES
from volcano import Volcano, VolcanoState

DT = 1.0 / 30.0   # fixed timestep (s)
MAX_SMOKE_RATE = 22.0

class Event:
    __slots__ = ("step", "tag", "msg")

    def __init__(self, step, tag, msg):
        self.step = step
        self.tag = tag
        self.msg = msg

    @property
    def line(self):
        return "[%03d] %s: %s" % (self.step, self.tag, self.msg)

class Simulation:
    """
    Owns ALL simulation state. Deterministic for a given seed: every
    random draw comes from self.rng in a fixed call order.
    """

    def __init__(self, seed: int = 42):
        self.seed = int(seed)
        self.reset()

    def reset(self) -> None:
        self.rng = random.Random(self.seed)
        self.step_count = 0
        self.time = 0.0
        self.events = []

        self.environment = Environment(self.rng)
        self.volcano = Volcano(self.rng, CRATER_X, CRATER_Y)
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.aircraft = make_fleet(self.rng, 2)
        self.birds = make_flock(self.rng, 5)

        self._ash_carry = 0.0
        self._smoke_carry = 0.0
        self.log_event("SIM", "initialized seed=%d" % self.seed)

    def log_event(self, tag: str, msg: str) -> None:
        self.events.append(Event(self.step_count, tag, msg))

    # ------------------------------------------------------------------
    def step(self, dt: float = DT) -> None:
        self.step_count += 1
        self.time += dt

        self.environment.update(dt, self.rng)

        prev_state = self.volcano.state
        self.volcano.update(dt)
        if self.volcano.state is not prev_state:
            self._log_transition(self.volcano.state)

        self._emit(dt)
        self.particles.update(dt, self.environment.wind_speed)

        for a in self.aircraft:
            a.update(dt)
            inside = self.volcano.plume_contains(
                a.x, a.y, self.environment.wind_speed)
            if inside and not a.in_plume:
                a.in_plume = True
                self.log_event("AIRCRAFT",
                               "aircraft %d entered ash region" % a.id)
                self.log_event("EVENT",
                               "ASH_ENCOUNTER aircraft=%d" % a.id)
            elif not inside and a.in_plume:
                a.in_plume = False
                self.log_event("AIRCRAFT",
                               "aircraft %d cleared ash region" % a.id)

        for b in self.birds:
            b.update(dt, self.time)

    # ------------------------------------------------------------------
    def _log_transition(self, state: VolcanoState) -> None:
        if state is VolcanoState.RUMBLING:
            self.log_event("VOLCANO", "rumbling detected")
        elif state is VolcanoState.ERUPTING:
            self.log_event("VOLCANO", "eruption started")
            self.log_event("ASH", "plume developing")
        elif state is VolcanoState.DECAYING:
            self.log_event("VOLCANO", "eruption weakening")
        elif state is VolcanoState.QUIET:
            self.log_event("VOLCANO", "returned to quiet")

    def _make_ash(self) -> Particle:
        rng, v = self.rng, self.volcano
        return Particle(
            x=v.x + rng.uniform(-14.0, 14.0),
            y=v.y + rng.uniform(-4.0, 4.0),
            vx=rng.uniform(-25.0, 25.0) + self.environment.wind_speed * 4.0,
            vy=-(90.0 + v.eruption_strength * 110.0 + rng.uniform(0.0, 40.0)),
            lifetime=rng.uniform(3.5, 7.0),
            size=rng.uniform(1.5, 3.5),
            kind="ash",
        )

    def _make_smoke(self) -> Particle:
        rng, v = self.rng, self.volcano
        return Particle(
            x=v.x + rng.uniform(-20.0, 20.0),
            y=v.y - 10.0,
            vx=rng.uniform(-12.0, 12.0),
            vy=-(50.0 + v.eruption_strength * 60.0 + rng.uniform(0.0, 25.0)),
            lifetime=rng.uniform(7.0, 12.0),
            size=rng.uniform(6.0, 14.0),
            kind="smoke",
        )

    def _emit(self, dt: float) -> None:
        self._ash_carry += self.volcano.ash_rate * dt
        n = int(self._ash_carry)
        self._ash_carry -= n
        for _ in range(n):
            self.particles.add(self._make_ash())      # silently capped

        self._smoke_carry += self.volcano.smoke_density * MAX_SMOKE_RATE * dt
        n = int(self._smoke_carry)
        self._smoke_carry -= n
        for _ in range(n):
            self.particles.add(self._make_smoke())

# ----------------------------------------------------------------------
# HEADLESS (no pygame import at all)
# ----------------------------------------------------------------------
def advance_to_next_event(sim: Simulation, max_steps: int = 3600) -> int:
    """Step until a new event is logged. Returns steps taken."""
    base = len(sim.events)
    for i in range(1, max_steps + 1):
        sim.step()
        if len(sim.events) > base:
            return i
    return max_steps

def run_headless(steps: int, seed: int, stream=None) -> None:
    out = stream if stream is not None else sys.stdout
    sim = Simulation(seed)

    def w(line=""):
        print(line, file=out)

    w("BLOON VOLCANO EXPERIMENT v0 -- headless (toy simulation)")
    w("seed=%d steps=%d dt=%.4f" % (seed, steps, DT))
    w()

    prev = len(sim.events)
    for _ in range(steps):
        sim.step()
        w("STEP %03d volcano=%s ash=%d smoke=%d wind=%+.2f aircraft=%d birds=%d"
          % (sim.step_count, sim.volcano.state.name,
             sim.particles.count("ash"), sim.particles.count("smoke"),
             sim.environment.wind_speed,
             len(sim.aircraft), len(sim.birds)))
        for ev in sim.events[prev:]:
            w("STEP %03d EVENT %s: %s" % (sim.step_count, ev.tag, ev.msg))
        prev = len(sim.events)

    w()
    w("FINAL volcano=%s particles=%d/%d events=%d"
      % (sim.volcano.state.name, sim.particles.count(),
         sim.particles.max_particles, len(sim.events)))

# ----------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------
def run_gui(seed: int) -> None:
    import pygame                     # lazy: headless never touches pygame
    import visualization as viz
    from environment import WIDTH, HEIGHT

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("BLOON VOLCANO EXPERIMENT v0")
    clock = pygame.time.Clock()
    fonts = viz.make_fonts()

    sim = Simulation(seed)
    paused = False
    overlay = False
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key == pygame.K_r:
                    sim.reset()        # same seed -> exact same initial state
                    paused = False
                elif e.key == pygame.K_n:
                    advance_to_next_event(sim)
                elif e.key == pygame.K_m:
                    overlay = not overlay

        if not paused:
            sim.step()

        viz.draw(screen, sim, fonts, overlay=overlay, paused=paused)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

# ----------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="BLOON VOLCANO EXPERIMENT v0 (toy visual simulation)")
    parser.add_argument("--headless", type=int, default=None, metavar="STEPS",
                        help="run STEPS simulation steps without a display")
    parser.add_argument("--seed", type=int, default=42,
                        help="deterministic seed (default: 42)")
    args = parser.parse_args(argv)

    if args.headless is not None:
        run_headless(args.headless, args.seed)
    else:
        run_gui(args.seed)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())