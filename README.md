# BLOON VOLCANO EXPERIMENT v0

🌋 → 🌬️ → ✈️

![BLOON VOLCANO EXPERIMENT](./krakatau_erruption.png)

A minimal, deterministic, toy computational experiment that makes
**VOLCANO → ERUPTION → ASH/SMOKE → WIND → CLOUDS → AIRCRAFT + BIRDS**
visible as a simple 2D visual dynamic system.

## ⚠️ Physics Honesty

**This is a toy computational experiment.** It is a visual dynamic system,
not a scientific model.

It does **NOT** model:

- real volcanic eruption physics
- magma chamber dynamics
- real plume thermodynamics
- atmospheric turbulence
- CFD / Navier-Stokes
- real volcanic ash concentration
- aviation safety thresholds
- actual flight routing
- real economic losses

The wind is a single slowly-drifting 2D scalar — **not an atmospheric
model**. Aircraft do not avoid ash and follow no aviation regulation;
if an aircraft enters the *visual* plume bounding box, the simulation
logs an `ASH ENCOUNTER` event. That is a simulation event, nothing more.

The volcano cycle (QUIET → RUMBLING → ERUPTING → DECAYING) uses
timer-based transitions with durations drawn from `random.Random(seed)`.
It is **not** an eruption forecast of any kind.

## Requirements

- Python 3.8+
- `pygame` (GUI mode only)
- No NumPy, no SciPy, no ML, no network, no external assets.

```bash
pip install -r requirements.txt
```

## Running

```bash
# GUI (1180 x 820)
python main.py
python main.py --seed 7

# Headless (no pygame display required)
python main.py --headless 120
python main.py --headless 120 --seed 42

# Tests (24)
python -m unittest discover -s tests -v
```

### Controls (GUI)

| Key   | Action                              |
|-------|-------------------------------------|
| SPACE | pause / resume                      |
| R     | reset (same seed → identical state) |
| N     | step forward to next event          |
| M     | toggle meteorological overlay       |
| ESC   | quit                                |

## Architecture

```
STATE ──> SIMULATION ──> VISUALIZATION
```

| File               | Role |
|--------------------|------|
| `environment.py`   | world geometry, wind state, cloud layer |
| `volcano.py`       | volcano state machine + toy plume region |
| `particles.py`     | capped 2D particle system (ash, smoke) |
| `aircraft.py`      | deterministic fly-across aircraft |
| `birds.py`         | deterministic sinusoidal birds |
| `main.py`          | `Simulation` (state + step + events), CLI, headless runner, GUI loop |
| `visualization.py` | pure rendering — reads state, never mutates it |
| `tests/`           | unittest suite |

Visualization never determines physics or state. Headless mode and the
test suite never import pygame (`main.py` imports it lazily inside
`run_gui`).

### Determinism

All randomness flows from a single `random.Random(seed)` consumed in a
fixed order inside `Simulation.step()`:

```
same seed → same initial state → same events → same final state
```

Fixed timestep `dt = 1/30 s`. Emission uses fractional carry so particle
spawn counts are dt-stable and deterministic.

### Particle safety

- Hard cap: `MAX_PARTICLES = 1500` (spawns are silently dropped at cap)
- Lifetime expiry, ground deposition (ash), out-of-world removal
- Regression tests assert: no explosion, no NaN/Inf, no negative lifetime

## Roadmap (NOT implemented in v0)

```
V0 — Volcano visual simulation        ← you are here
V1 — 2D ash advection
V2 — layered wind field
V3 — advection-diffusion
V4 — real meteorological data
V5 — 3D ash transport
V6 — airspace/network impact
V7 — economic impact model
V8 — BLOON numerical backend
```

## Verification Status

**STATUS: VERIFIED** until the program has actually been executed.
Run the headless mode and the test suite yourself; their output is the
runtime evidence.

## License

see `LICENSE`.
