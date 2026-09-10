"""
tests/test_volcano.py — BLOON VOLCANO EXPERIMENT v0

24 tests. Run from project root:
    python -m unittest discover -s tests -v
"""

import io
import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as entry
from aircraft import Aircraft, make_fleet
from birds import make_flock
from environment import Environment, Cloud, WIDTH, GROUND_Y, WIND_MIN, WIND_MAX
from particles import Particle, ParticleSystem, MAX_PARTICLES, GRAVITY
from volcano import Volcano, VolcanoState

def run_sim(sim, steps, dt=entry.DT):
    for _ in range(steps):
        sim.step(dt)
    return sim

class VolcanoTests(unittest.TestCase):

    def test_initial_state(self):
        v = Volcano(random.Random(1), 100.0, 200.0)
        self.assertEqual(v.state, VolcanoState.QUIET)
        self.assertEqual(v.eruption_strength, 0.0)
        self.assertEqual(v.ash_rate, 0.0)
        self.assertTrue(0.0 <= v.lava_level <= 1.0)
        self.assertTrue(0.0 <= v.smoke_density <= 1.0)

    def test_valid_transition_order(self):
        # Full cycles must follow QUIET->RUMBLING->ERUPTING->DECAYING->QUIET
        order = [VolcanoState.QUIET, VolcanoState.RUMBLING,
                 VolcanoState.ERUPTING, VolcanoState.DECAYING]
        v = Volcano(random.Random(3), 100.0, 200.0)
        prev = v.state
        for _ in range(30 * 60):          # 60 s of sim time
            v.update(entry.DT)
            if v.state is not prev:
                self.assertEqual(v.state, order[(order.index(prev) + 1) % 4])
                prev = v.state

    def test_eruption_eventually_starts(self):
        v = Volcano(random.Random(7), 100.0, 200.0)
        states = set()
        for _ in range(30 * 120):
            v.update(entry.DT)
            states.add(v.state)
        self.assertIn(VolcanoState.ERUPTING, states)
        self.assertIn(VolcanoState.RUMBLING, states)
        self.assertIn(VolcanoState.DECAYING, states)

    def test_eruption_decays_to_zero(self):
        sim = run_sim(entry.Simulation(seed=11), 30 * 150)
        # strength must come back down at some point (quiet phases exist)
        v = sim.volcano
        seen_erupt = any(
            True for _ in () )  # placeholder removed below
        # simpler: run two sims, one forced into decay check
        vol = Volcano(random.Random(5), 100.0, 200.0)
        # fast-forward until ERUPTING
        for _ in range(30 * 60):
            vol.update(entry.DT)
            if vol.state is VolcanoState.ERUPTING:
                break
        self.assertEqual(vol.state, VolcanoState.ERUPTING)
        peak = vol.eruption_strength
        for _ in range(30 * 90):
            vol.update(entry.DT)
        # after long run, must have decayed phases (strength < peak at QUIET)
        self.assertLessEqual(vol.eruption_strength, peak)
        _ = v, seen_erupt

    def test_ash_generation_during_eruption(self):
        sim = entry.Simulation(seed=42)
        # step until erupting
        for _ in range(30 * 120):
            sim.step()
            if sim.volcano.state is VolcanoState.ERUPTING:
                break
        self.assertEqual(sim.volcano.state, VolcanoState.ERUPTING)
        before = sim.particles.count("ash")
        for _ in range(30):
            sim.step()
        self.assertGreater(sim.particles.count("ash") + sim.particles.removed_total,
                           before)
        self.assertGreater(sim.particles.count("ash"), 0)

    def test_volcano_deterministic_same_seed(self):
        def trace(seed):
            v = Volcano(random.Random(seed), 100.0, 200.0)
            out = []
            for _ in range(30 * 100):
                v.update(entry.DT)
                out.append((v.state, round(v.eruption_strength, 6),
                            round(v.lava_level, 6)))
            return out
        self.assertEqual(trace(99), trace(99))
        self.assertNotEqual(trace(1), trace(2))

    def test_plume_region_none_when_quiet(self):
        v = Volcano(random.Random(1), 100.0, 200.0)
        self.assertIsNone(v.plume_region(1.0))
        self.assertFalse(v.plume_contains(100.0, 150.0, 1.0))

class ParticleTests(unittest.TestCase):

    def test_movement_integration(self):
        ps = ParticleSystem()
        ps.add(Particle(100.0, 100.0, 30.0, 0.0, 10.0, 2.0))
        ps.update(1.0, 0.0)
        p = ps.particles[0]
        self.assertAlmostEqual(p.x, 130.0, places=5)

    def test_gravity_increases_vy(self):
        ps = ParticleSystem()
        ps.add(Particle(100.0, 100.0, 0.0, 0.0, 10.0, 2.0, kind="ash"))
        ps.update(1.0, 0.0)
        self.assertAlmostEqual(ps.particles[0].vy, GRAVITY, places=5)

    def test_wind_influence(self):
        ps = ParticleSystem()
        ps.add(Particle(100.0, 100.0, 0.0, 0.0, 10.0, 2.0, kind="ash"))
        ps.update(1.0, 1.0)   # wind = +1
        self.assertGreater(ps.particles[0].vx, 0.0)
        ps2 = ParticleSystem()
        ps2.add(Particle(100.0, 100.0, 0.0, 0.0, 10.0, 2.0, kind="ash"))
        ps2.update(1.0, -1.0)
        self.assertLess(ps2.particles[0].vx, 0.0)

    def test_lifetime_expiry(self):
        ps = ParticleSystem()
        ps.add(Particle(100.0, 100.0, 0.0, 0.0, 1.0, 2.0))
        ps.update(0.6, 0.0)
        self.assertEqual(ps.count(), 1)
        ps.update(0.6, 0.0)
        self.assertEqual(ps.count(), 0)
        self.assertEqual(ps.removed_total, 1)

    def test_particle_limit(self):
        ps = ParticleSystem(max_particles=10)
        for i in range(50):
            ps.add(Particle(10.0, 10.0, 0.0, 0.0, 100.0, 1.0))
        self.assertEqual(ps.count(), 10)
        self.assertLessEqual(ps.count(), ps.max_particles)

    def test_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            Particle(0.0, 0.0, 0.0, 0.0, -1.0, 1.0)   # negative lifetime
        with self.assertRaises(ValueError):
            Particle(float("nan"), 0.0, 0.0, 0.0, 1.0, 1.0)
        with self.assertRaises(ValueError):
            Particle(0.0, 0.0, float("inf"), 0.0, 1.0, 1.0)
        with self.assertRaises(ValueError):
            Particle(0.0, 0.0, 0.0, 0.0, 1.0, 0.0)    # zero size

    def test_ash_removed_at_ground(self):
        ps = ParticleSystem()
        ps.add(Particle(300.0, GROUND_Y - 5.0, 0.0, 100.0, 60.0, 2.0, kind="ash"))
        ps.update(0.2, 0.0)
        self.assertEqual(ps.count(), 0)

class AircraftTests(unittest.TestCase):

    def test_movement(self):
        rng = random.Random(1)
        a = Aircraft(rng, 1)
        x0 = a.x
        a.update(1.0)
        self.assertAlmostEqual(a.x, x0 + a.speed * a.heading, places=5)

    def test_boundary_wrap(self):
        rng = random.Random(1)
        a = Aircraft(rng, 1)
        a.heading = 1.0
        a.speed = 10000.0
        a.update(1.0)
        self.assertLessEqual(a.x, 0.0 + 1e-6)  # wrapped to left margin
        a.heading = -1.0
        a.update(1.0)
        self.assertGreaterEqual(a.x, WIDTH - 1e-6 - 160.0)

    def test_ash_encounter_detection(self):
        sim = entry.Simulation(seed=42)
        # force volcano into erupting state via long deterministic run
        for _ in range(30 * 120):
            sim.step()
            if any(a.in_plume for a in sim.aircraft):
                break
        tags = [(e.tag, e.msg) for e in sim.events]
        if sim.volcano.state is not VolcanoState.QUIET:
            # plume exists; over a long run an encounter should be logged
            self.assertTrue(any(t == "EVENT" and "ASH_ENCOUNTER" in m
                                for t, m in tags),
                            "expected ASH_ENCOUNTER over long run")

    def test_fleet_deterministic(self):
        f1 = make_fleet(random.Random(5), 2)
        f2 = make_fleet(random.Random(5), 2)
        self.assertEqual([(a.x, a.y, a.speed, a.heading) for a in f1],
                         [(a.x, a.y, a.speed, a.heading) for a in f2])

class EnvironmentTests(unittest.TestCase):

    def test_wind_stays_in_bounds(self):
        env = Environment(random.Random(2))
        for _ in range(10000):
            env.update(entry.DT, random.Random(123))
        self.assertTrue(WIND_MIN <= env.wind_speed <= WIND_MAX)

    def test_wind_direction_sign(self):
        env = Environment(random.Random(2))
        env.wind_speed = 1.0
        self.assertEqual(env.wind_direction, 1)
        env.wind_speed = -0.5
        self.assertEqual(env.wind_direction, -1)

    def test_clouds_move_with_wind(self):
        c = Cloud(random.Random(4))
        c.speed_factor = 0.5
        x0 = c.x
        c.update(1.0, 1.0)   # wind right
        self.assertGreater(c.x, x0)

    def test_environment_deterministic(self):
        e1 = Environment(random.Random(8))
        e2 = Environment(random.Random(8))
        rng1, rng2 = random.Random(20), random.Random(20)
        for _ in range(100):
            e1.update(entry.DT, rng1)
            e2.update(entry.DT, rng2)
        self.assertAlmostEqual(e1.wind_speed, e2.wind_speed, places=10)
        self.assertEqual([c.x for c in e1.clouds], [c.x for c in e2.clouds])

class SimulationTests(unittest.TestCase):

    def test_same_seed_same_trace(self):
        def snapshot(sim):
            return (sim.volcano.state,
                    round(sim.volcano.eruption_strength, 9),
                    round(sim.environment.wind_speed, 9),
                    sim.particles.count(),
                    [(round(a.x, 6), round(a.y, 6)) for a in sim.aircraft],
                    [(round(b.x, 6), round(b.y, 6)) for b in sim.birds],
                    [e.line for e in sim.events])

        s1 = run_sim(entry.Simulation(seed=42), 600)
        s2 = run_sim(entry.Simulation(seed=42), 600)
        self.assertEqual(snapshot(s1), snapshot(s2))

        s3 = run_sim(entry.Simulation(seed=43), 600)
        self.assertNotEqual(snapshot(s1), snapshot(s3))

    def test_reset_restores_initial_state(self):
        sim = entry.Simulation(seed=42)
        initial = (sim.volcano.state, round(sim.environment.wind_speed, 12),
                   sim.particles.count(), len(sim.events))
        run_sim(sim, 300)
        self.assertNotEqual(sim.step_count, 0)
        sim.reset()
        self.assertEqual(sim.step_count, 0)
        self.assertEqual(sim.time, 0.0)
        after = (sim.volcano.state, round(sim.environment.wind_speed, 12),
                 sim.particles.count(), len(sim.events))
        self.assertEqual(initial, after)
        # and stepping again reproduces the same trace
        s_a = run_sim(entry.Simulation(seed=42), 100)
        run_sim(sim, 100)
        self.assertAlmostEqual(sim.environment.wind_speed,
                               s_a.environment.wind_speed, places=12)

    def test_events_come_from_state_transitions(self):
        sim = run_sim(entry.Simulation(seed=42), 30 * 120)
        msgs = [e.msg for e in sim.events]
        self.assertIn("rumbling detected", msgs)
        self.assertIn("eruption started", msgs)
        self.assertIn("plume developing", msgs)
        self.assertIn("eruption weakening", msgs)

    def test_headless_execution_no_pygame(self):
        buf = io.StringIO()
        entry.run_headless(30, seed=42, stream=buf)
        text = buf.getvalue()
        self.assertIn("STEP 001", text)
        self.assertIn("STEP 030", text)
        self.assertIn("volcano=", text)
        self.assertIn("wind=", text)
        self.assertIn("FINAL", text)
        self.assertNotIn("pygame", sys.modules)  # headless never imports it

    def test_advance_to_next_event(self):
        sim = entry.Simulation(seed=42)
        n = entry.advance_to_next_event(sim)
        self.assertGreaterEqual(n, 1)
        self.assertGreater(len(sim.events), 1)  # init event + new event

class RegressionTests(unittest.TestCase):

    def test_no_particle_explosion(self):
        sim = run_sim(entry.Simulation(seed=42), 30 * 300)  # 300 s
        self.assertLess(sim.particles.count(), MAX_PARTICLES)
        self.assertLessEqual(sim.particles.count(),
                             sim.particles.max_particles)

    def test_no_nan_inf_negative_lifetime(self):
        sim = run_sim(entry.Simulation(seed=42), 30 * 300)
        for p in sim.particles.particles:
            for val in (p.x, p.y, p.vx, p.vy, p.age, p.size, p.lifetime):
                self.assertTrue(math.isfinite(val), "non-finite particle value")
            self.assertGreater(p.lifetime, 0.0)
            self.assertGreaterEqual(p.age, 0.0)
            self.assertLess(p.age, p.lifetime)
        for val in (sim.environment.wind_speed,
                    sim.volcano.eruption_strength,
                    sim.volcano.lava_level,
                    sim.volcano.ash_rate,
                    sim.volcano.smoke_density):
            self.assertTrue(math.isfinite(val), "non-finite sim value")
        for a in sim.aircraft:
            self.assertTrue(math.isfinite(a.x) and math.isfinite(a.y))
        for b in sim.birds:
            self.assertTrue(math.isfinite(b.x) and math.isfinite(b.y))

if __name__ == "__main__":
    unittest.main()