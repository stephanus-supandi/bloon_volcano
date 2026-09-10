"""
visualization.py — BLOON VOLCANO EXPERIMENT v0

Pure rendering layer: reads Simulation state, never mutates it.
Visualization does NOT determine physics/state. Pygame primitives only,
no external assets.
"""

import math

import pygame

from environment import (WIDTH, SCENE_H, GROUND_Y, CRATER_X, CRATER_Y,
                         STATE_PANEL, LOG_PANEL)
from volcano import VolcanoState

SKY_TOP = (26, 30, 62)
SKY_BOT = (122, 140, 172)
GROUND_COL = (46, 60, 42)
ROCK_COL = (88, 72, 66)
ROCK_DARK = (62, 50, 46)
CRATER_COL = (40, 30, 30)
CLOUD_COL = (212, 216, 226)
PANEL_BG = (16, 18, 24)
LOG_BG = (12, 13, 18)
TEXT_COL = (222, 226, 232)
DIM_COL = (140, 146, 158)
ACCENT = (255, 170, 60)
WARN = (255, 90, 80)
BIRD_COL = (30, 32, 40)

def make_fonts():
    return {
        "title": pygame.font.Font(None, 30),
        "text": pygame.font.Font(None, 20),
        "small": pygame.font.Font(None, 17),
        "big": pygame.font.Font(None, 42),
    }

# ---------------------------------------------------------------- scene
def draw_sky(screen):
    bands = SCENE_H // 4
    for i in range(bands + 1):
        f = i / bands
        col = tuple(int(SKY_TOP[k] + (SKY_BOT[k] - SKY_TOP[k]) * f)
                    for k in range(3))
        pygame.draw.rect(screen, col, (0, i * 4, WIDTH, 5))

def draw_ground(screen):
    pygame.draw.rect(screen, GROUND_COL, (0, GROUND_Y, WIDTH, SCENE_H - GROUND_Y))
    pygame.draw.line(screen, (34, 46, 32), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

def draw_clouds(screen, sim):
    for c in sim.environment.clouds:
        for (ox, oy, r) in c.puffs:
            pygame.draw.circle(screen, CLOUD_COL,
                               (int(c.x + ox), int(c.y + oy)), int(r))

def draw_volcano(screen, sim):
    v = sim.volcano
    pygame.draw.polygon(screen, ROCK_COL, [
        (CRATER_X - 220, GROUND_Y), (CRATER_X - 30, CRATER_Y),
        (CRATER_X + 30, CRATER_Y), (CRATER_X + 220, GROUND_Y)])
    pygame.draw.polygon(screen, ROCK_DARK, [
        (CRATER_X, GROUND_Y), (CRATER_X + 30, CRATER_Y),
        (CRATER_X + 220, GROUND_Y)])
    pygame.draw.ellipse(screen, CRATER_COL, (CRATER_X - 30, CRATER_Y - 7, 60, 14))

    if v.lava_level > 0.12 or v.state is VolcanoState.ERUPTING:
        flick = math.sin(sim.time * 12.0) * 2.0
        r = max(3, int(6 + 14 * v.lava_level + flick))
        glow = (255, int(110 + 90 * v.lava_level), 40)
        pygame.draw.circle(screen, glow, (CRATER_X, CRATER_Y), r)

    if v.state is VolcanoState.ERUPTING and int(sim.time * 8.0) % 2 == 0:
        pygame.draw.line(screen, (235, 110, 40),
                         (CRATER_X - 18, CRATER_Y + 4),
                         (CRATER_X - 120, GROUND_Y), 3)
        pygame.draw.line(screen, (235, 110, 40),
                         (CRATER_X + 18, CRATER_Y + 4),
                         (CRATER_X + 120, GROUND_Y), 3)

def draw_particles(screen, sim):
    for p in sim.particles.particles:
        fade = max(0.0, min(1.0, 1.0 - p.age / p.lifetime))
        if p.kind == "ash":
            g = int(50 + 45 * fade)
            pygame.draw.circle(screen, (g, max(0, g - 4), max(0, g - 4)),
                               (int(p.x), int(p.y)), max(1, int(p.size)))
        else:
            g = int(115 + 62 * fade)
            pygame.draw.circle(screen, (g, g, min(255, g + 6)),
                               (int(p.x), int(p.y)), max(2, int(p.size)))

def draw_aircraft(screen, sim, fonts):
    for a in sim.aircraft:
        h = a.heading
        x, y = a.x, a.y
        col = WARN if a.in_plume else (238, 240, 244)
        pygame.draw.polygon(screen, col, [
            (x + 20 * h, y), (x - 14 * h, y - 4), (x - 14 * h, y + 4)])
        pygame.draw.polygon(screen, col, [
            (x - 2 * h, y), (x + 4 * h, y - 11),
            (x + 9 * h, y - 11), (x + 3 * h, y)])
        pygame.draw.polygon(screen, col, [
            (x - 2 * h, y), (x + 4 * h, y + 11),
            (x + 9 * h, y + 11), (x + 3 * h, y)])
        if a.in_plume:
            label = fonts["small"].render("ASH ENCOUNTER", True, WARN)
            screen.blit(label, (int(x) - 40, int(y) - 30))

def draw_birds(screen, sim):
    for b in sim.birds:
        flap = math.sin(sim.time * b.freq * 2.0 + b.phase) * 3.0
        pygame.draw.line(screen, BIRD_COL,
                         (int(b.x) - 5, int(b.y)),
                         (int(b.x), int(b.y - 2 + flap)), 2)
        pygame.draw.line(screen, BIRD_COL,
                         (int(b.x), int(b.y - 2 + flap)),
                         (int(b.x) + 5, int(b.y)), 2)

def draw_overlay(screen, sim, fonts):
    """Meteorological overlay: plume box + wind arrow. Visual only."""
    v = sim.volcano
    region = v.plume_region(sim.environment.wind_speed)
    if region is not None:
        surf = pygame.Surface((WIDTH, SCENE_H), pygame.SRCALPHA)
        rect = pygame.Rect(int(region[0]), int(region[1]),
                           int(region[2] - region[0]),
                           int(region[3] - region[1]))
        pygame.draw.rect(surf, (255, 90, 80, 40), rect)
        pygame.draw.rect(surf, (255, 90, 80, 160), rect, 2)
        screen.blit(surf, (0, 0))

    # wind arrow
    wx, wy = 90, 40
    w = sim.environment.wind_speed
    length = int(30 + abs(w) * 40)
    d = 1 if w >= 0 else -1
    pygame.draw.line(screen, ACCENT, (wx, wy), (wx + length * d, wy), 3)
    pygame.draw.polygon(screen, ACCENT, [
        (wx + (length + 10) * d, wy),
        (wx + length * d, wy - 6),
        (wx + length * d, wy + 6)])
    txt = fonts["small"].render("wind %+.2f (toy)" % w, True, ACCENT)
    screen.blit(txt, (wx - 20, wy + 10))

# ---------------------------------------------------------------- panels
def draw_state_panel(screen, sim, fonts, paused):
    pygame.draw.rect(screen, PANEL_BG, STATE_PANEL)
    pygame.draw.line(screen, (40, 44, 56),
                     (0, STATE_PANEL[1]), (WIDTH, STATE_PANEL[1]), 2)

    x, y = 16, STATE_PANEL[1] + 10
    title = fonts["title"].render("STATE", True, TEXT_COL)
    screen.blit(title, (x, y))

    v = sim.volcano
    wind = sim.environment.wind_speed
    arrow = "->" if wind >= 0 else "<-"
    rows = [
        ("Volcano: %s" % v.state.name,
         WARN if v.state is VolcanoState.ERUPTING else TEXT_COL),
        ("Wind: %s %.2f (toy value)" % (arrow, abs(wind)), TEXT_COL),
        ("Ash particles: %d / %d"
         % (sim.particles.count("ash"), sim.particles.max_particles), TEXT_COL),
        ("Aircraft: %d   Birds: %d"
         % (len(sim.aircraft), len(sim.birds)), TEXT_COL),
        ("strength=%.2f lava=%.2f smoke=%.2f step=%d t=%.1fs seed=%d"
         % (v.eruption_strength, v.lava_level, v.smoke_density,
            sim.step_count, sim.time, sim.seed), DIM_COL),
    ]
    y += 32
    for line, col in rows:
        screen.blit(fonts["text"].render(line, True, col), (x, y))
        y += 19

    if paused:
        screen.blit(fonts["big"].render("PAUSED", True, ACCENT),
                    (WIDTH - 190, STATE_PANEL[1] + 40))

def draw_log_panel(screen, sim, fonts):
    pygame.draw.rect(screen, LOG_BG, LOG_PANEL)
    pygame.draw.line(screen, (40, 44, 56),
                     (0, LOG_PANEL[1]), (WIDTH, LOG_PANEL[1]), 2)

    x, y = 16, LOG_PANEL[1] + 8
    screen.blit(fonts["title"].render("EVENT LOG", True, TEXT_COL), (x, y))
    y += 28

    visible = 6
    for ev in sim.events[-visible:]:
        col = WARN if ev.tag == "EVENT" else (
            ACCENT if ev.tag in ("VOLCANO", "ASH") else DIM_COL)
        screen.blit(fonts["small"].render(ev.line, True, col), (x, y))
        y += 17

    screen.blit(fonts["small"].render(
        "SPACE pause | R reset | N next event | M overlay | ESC quit",
        True, DIM_COL), (WIDTH - 430, LOG_PANEL[1] + 8))

# ---------------------------------------------------------------- frame
def draw(screen, sim, fonts, overlay=False, paused=False):
    draw_sky(screen)
    draw_clouds(screen, sim)
    if overlay:
        draw_overlay(screen, sim, fonts)
    draw_volcano(screen, sim)
    draw_particles(screen, sim)
    draw_ground(screen)
    draw_birds(screen, sim)
    draw_aircraft(screen, sim, fonts)
    draw_state_panel(screen, sim, fonts, paused)
    draw_log_panel(screen, sim, fonts)

    hdr = fonts["title"].render(
        "BLOON VOLCANO EXPERIMENT v0 -- toy simulation, not a volcanic "
        "hazard model", True, TEXT_COL)
    screen.blit(hdr, (16, 10))