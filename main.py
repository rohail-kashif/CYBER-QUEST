#!/usr/bin/env python3
"""CyberQuest Kids - a cyber-safety adventure game for ages 6-11.

Run:  python main.py        (needs: pip install pygame)

Controls
  Mouse / touch   click, drag and drop
  1-9             pick quiz answers
  Enter / Space   press the main button (Check / Next)
  Esc             back
  M               mute / unmute        F11  fullscreen
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import struct
import sys
import time

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import LEVELS  # noqa: E402

W, H = 1100, 700
FPS = 60
SAVE_PATH = os.path.join(os.path.expanduser("~"), ".cyberquest_kids.json")

# ----------------------------------------------------------------- palette
INK = (31, 42, 68)
WHITE = (255, 255, 255)
BG_TOP = (118, 190, 255)
BG_BOT = (222, 243, 255)
BLUE = (47, 125, 225)
GREEN = (58, 166, 85)
TEAL = (30, 170, 150)
YELLOW = (242, 176, 30)
ORANGE = (240, 138, 36)
PURPLE = (122, 86, 201)
RED = (214, 69, 69)
GOOD = (46, 158, 87)
GREY = (170, 183, 204)
BROWN = (176, 112, 60)
SKY = (36, 150, 210)
PINK = (226, 92, 150)
INDIGO = (84, 90, 200)
LIME = (120, 165, 40)
CORAL = (224, 112, 80)
SLATE = (90, 110, 150)
MAGENTA = (170, 70, 170)
_PALETTE = [BLUE, GREEN, TEAL, ORANGE, BROWN, SKY, PINK, INDIGO, LIME, CORAL, SLATE, MAGENTA]
LEVEL_COLORS = [_PALETTE[i % len(_PALETTE)] for i in range(len(LEVELS))]
LEVEL_COLORS[-1] = PURPLE  # the finale is always purple
NAMED = {"red": RED, "green": GOOD, "blue": BLUE, "orange": ORANGE, "purple": PURPLE}


# ----------------------------------------------------------------- helpers
def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def circ(surf, col, c, r, w=0):
    pygame.draw.circle(surf, col, (int(c[0]), int(c[1])), max(1, int(r)), w)


_fonts: dict = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(
            "trebuchetms,verdana,dejavusans,arial,sans", size, bold=bold)
    return _fonts[key]


def text(surf, s, size, color, pos, anchor="topleft", bold=False, shadow=None):
    img = font(size, bold).render(s, True, color)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        surf.blit(font(size, bold).render(s, True, shadow), r.move(3, 3))
    surf.blit(img, r)
    return r


def wrap(s, size, width, bold=False):
    f = font(size, bold)
    lines = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split():
            test = (cur + " " + word).strip()
            if f.size(test)[0] <= width or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def paragraph(surf, s, size, color, rect, bold=False, gap=2, center=False):
    rect = pygame.Rect(rect)
    f = font(size, bold)
    y = rect.y
    for line in wrap(s, size, rect.w, bold):
        img = f.render(line, True, color)
        x = rect.centerx - img.get_width() // 2 if center else rect.x
        surf.blit(img, (x, y))
        y += f.get_linesize() + gap
    return y


_shadow_cache: dict = {}


def _shadow(w, h, r):
    key = (w, h, r)
    s = _shadow_cache.get(key)
    if s is None:
        s = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
        for grow, alpha in ((9, 12), (6, 16), (3, 22)):
            pygame.draw.rect(s, (20, 30, 60, alpha),
                             (12 - grow, 17 - grow, w + 2 * grow, h + 2 * grow),
                             border_radius=r + grow)
        _shadow_cache[key] = s
    return s


def panel(surf, rect, color=WHITE, radius=18, border=None, shadow=True, bw=3):
    rect = pygame.Rect(rect)
    if shadow:
        surf.blit(_shadow(rect.w, rect.h, radius), (rect.x - 12, rect.y - 12))
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, rect, bw, border_radius=radius)


def star_points(c, r, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        a = rot + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    return pts


def draw_star(surf, c, r, filled=True, rot=-math.pi / 2):
    pts = star_points(c, r, rot)
    if filled:
        pygame.draw.polygon(surf, YELLOW, pts)
        pygame.draw.polygon(surf, ORANGE, pts, max(2, int(r * 0.12)))
    else:
        pygame.draw.polygon(surf, (228, 233, 242), pts)
        pygame.draw.polygon(surf, (200, 208, 222), pts, max(2, int(r * 0.12)))


def draw_arrow(surf, c, s, color=WHITE):
    x, y = c
    pygame.draw.polygon(surf, color, [(x - s * 0.5, y - s * 0.6), (x + s * 0.6, y),
                                      (x - s * 0.5, y + s * 0.6)])


def draw_check(surf, c, s, color=GOOD, w=5):
    x, y = c
    pygame.draw.lines(surf, color, False,
                      [(x - s * 0.5, y), (x - s * 0.1, y + s * 0.4), (x + s * 0.55, y - s * 0.4)], w)


def draw_cross(surf, c, s, color=RED, w=5):
    x, y = c
    pygame.draw.line(surf, color, (x - s * 0.4, y - s * 0.4), (x + s * 0.4, y + s * 0.4), w)
    pygame.draw.line(surf, color, (x + s * 0.4, y - s * 0.4), (x - s * 0.4, y + s * 0.4), w)


def draw_shield(surf, c, s, color=BLUE):
    x, y = c
    pts = [(x - s * 0.8, y - s * 0.7), (x, y - s), (x + s * 0.8, y - s * 0.7),
           (x + s * 0.8, y + s * 0.1), (x, y + s), (x - s * 0.8, y + s * 0.1)]
    pygame.draw.polygon(surf, color, pts)
    inner = [(x - s * 0.62, y - s * 0.56), (x, y - s * 0.8), (x + s * 0.62, y - s * 0.56),
             (x + s * 0.62, y + s * 0.04), (x, y + s * 0.78), (x - s * 0.62, y + s * 0.04)]
    pygame.draw.polygon(surf, mix(color, WHITE, 0.82), inner)
    draw_check(surf, (x, y - s * 0.05), s * 0.9, color, max(3, int(s * 0.16)))


def draw_lock(surf, c, s, color=GREY):
    x, y = c
    pygame.draw.arc(surf, color, (x - s * 0.55, y - s * 1.0, s * 1.1, s * 1.2), 0, math.pi, max(3, int(s * 0.18)))
    pygame.draw.rect(surf, color, (x - s * 0.8, y - s * 0.2, s * 1.6, s * 1.2), border_radius=int(s * 0.2))
    circ(surf, WHITE, (x, y + s * 0.4), s * 0.18)


def make_icon():
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    draw_shield(s, (32, 32), 28, BLUE)
    return s


# --------------------------------------------------------- backgrounds/art
_bg_cache: dict = {}
_cloud_surf = None


def gradient(top, bottom):
    key = (top, bottom)
    if key not in _bg_cache:
        s = pygame.Surface((W, H))
        for y in range(H):
            pygame.draw.line(s, mix(top, bottom, y / H), (0, y), (W, y))
        _bg_cache[key] = s
    return _bg_cache[key]


def sky(surf, t, top=BG_TOP, bottom=BG_BOT, hills=None):
    global _cloud_surf
    surf.blit(gradient(top, bottom), (0, 0))
    if _cloud_surf is None:
        _cloud_surf = pygame.Surface((220, 100), pygame.SRCALPHA)
        for cx, cy, r in ((60, 60, 34), (110, 44, 42), (160, 60, 32), (110, 70, 36)):
            pygame.draw.circle(_cloud_surf, (255, 255, 255, 215), (cx, cy), r)
    for i in range(4):
        x = (i * 330 + t * (12 + i * 5)) % (W + 400) - 250
        y = 70 + (i * 61) % 170
        surf.blit(_cloud_surf, (x, y))
    if hills:
        pygame.draw.ellipse(surf, mix(hills, WHITE, 0.25), (-200, H - 140, 900, 300))
        pygame.draw.ellipse(surf, hills, (350, H - 110, 1100, 300))


def _tree(art, x, base, u):
    pygame.draw.rect(art, (130, 90, 55), (x - u * 0.15, base - u * 1.4, u * 0.3, u * 1.4))
    circ(art, (52, 150, 80), (x, base - u * 1.9), u * 0.95)
    circ(art, (70, 175, 98), (x - u * 0.3, base - u * 2.1), u * 0.5)


def _pine(art, x, base, u):
    pygame.draw.rect(art, (120, 85, 55), (x - u * 0.12, base - u * 0.6, u * 0.24, u * 0.6))
    for i in range(3):
        y = base - u * 0.5 - i * u * 0.8
        pygame.draw.polygon(art, (40, 140, 90), [(x - u * (1.0 - i * 0.2), y),
                                                 (x, y - u * 1.3), (x + u * (1.0 - i * 0.2), y)])


def _heart(surf, c, r, color):
    x, y = c
    circ(surf, color, (x - r * 0.5, y - r * 0.2), r * 0.62)
    circ(surf, color, (x + r * 0.5, y - r * 0.2), r * 0.62)
    pygame.draw.polygon(surf, color, [(x - r * 1.07, y + r * 0.05), (x + r * 1.07, y + r * 0.05), (x, y + r * 1.4)])


_art_cache: dict = {}


def level_art(idx, size):
    key = (idx, size)
    if key in _art_cache:
        return _art_cache[key]
    w, h = size
    col = LEVEL_COLORS[idx]
    name = LEVELS[idx].get("art", "house")
    art = pygame.Surface(size, pygame.SRCALPHA)
    art.fill(mix(col, WHITE, 0.78) + (255,))
    u, cx, base = h / 10, w / 2, h * 0.76
    circ(art, (255, 214, 90), (w * 0.16, h * 0.2), u * 1.1)
    for x, y, s in ((w * 0.74, h * 0.18, 1.0), (w * 0.45, h * 0.09, 0.7)):
        for dx, dy, r in ((-1.1, 0.2, 0.8), (0, 0, 1.0), (1.2, 0.2, 0.8)):
            circ(art, WHITE, (x + dx * u * s, y + dy * u * s), r * u * s)
    pygame.draw.ellipse(art, mix(col, (95, 195, 110), 0.7), (-w * 0.2, base - u * 1.2, w * 0.9, h))
    pygame.draw.ellipse(art, mix(col, (70, 170, 95), 0.85), (w * 0.2, base - u * 0.7, w * 1.1, h))
    if name == "house":
        bw, bh = u * 5, u * 3
        pygame.draw.rect(art, (255, 236, 190), (cx - bw / 2, base - bh, bw, bh))
        pygame.draw.polygon(art, (214, 80, 70), [(cx - bw / 2 - u * 0.5, base - bh),
                                                 (cx, base - bh - u * 2.2),
                                                 (cx + bw / 2 + u * 0.5, base - bh)])
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.55, base - u * 1.9, u * 1.1, u * 1.9), border_radius=4)
        for sx in (-1, 1):
            pygame.draw.rect(art, (150, 205, 245), (cx + sx * bw * 0.33 - u * 0.5, base - bh + u * 0.7, u, u))
        draw_shield(art, (cx, base - bh - u * 3.2), u * 0.95, BLUE)
        _tree(art, cx - bw / 2 - u * 1.8, base, u)
        _tree(art, cx + bw / 2 + u * 2.2, base, u * 0.9)
    elif name == "meadow":  # signpost + envelope
        pygame.draw.rect(art, (130, 90, 55), (cx - u * 0.12, base - u * 3.2, u * 0.24, u * 3.2))
        for dy, c2 in ((0, (240, 190, 90)), (1.0, (245, 215, 140))):
            r = pygame.Rect(cx - u * 1.5, base - u * 3.2 + dy * u, u * 2.6, u * 0.8)
            pygame.draw.rect(art, c2, r)
            pygame.draw.polygon(art, c2, [(r.right, r.top), (r.right + u * 0.5, r.centery), (r.right, r.bottom)])
        env = pygame.Rect(cx + u * 2.2, base - u * 2.3, u * 2.8, u * 1.9)
        pygame.draw.rect(art, WHITE, env, border_radius=5)
        pygame.draw.rect(art, GREY, env, 2, border_radius=5)
        pygame.draw.lines(art, GREY, False, [env.topleft, env.center, env.topright], 2)
        circ(art, RED, env.topright, u * 0.35)
        _tree(art, cx - u * 3.4, base, u)
    elif name == "park":  # tent + pines
        pygame.draw.polygon(art, ORANGE, [(cx - u * 2.4, base), (cx, base - u * 3.2), (cx + u * 2.4, base)])
        pygame.draw.polygon(art, (150, 80, 30), [(cx - u * 0.7, base), (cx, base - u * 1.8), (cx + u * 0.7, base)])
        pygame.draw.line(art, WHITE, (cx, base - u * 3.2), (cx, base - u * 1.8), 3)
        _pine(art, cx - u * 4.0, base, u)
        _pine(art, cx + u * 3.8, base, u * 1.1)
        draw_lock(art, (cx, base - u * 4.6), u * 0.7, (90, 110, 150))
    elif name == "trail":  # path + robot sign
        pygame.draw.polygon(art, (240, 215, 150), [(cx - u * 3.4, h), (cx + u * 3.4, h),
                                                   (cx + u * 0.6, base - u * 2.4), (cx - u * 0.3, base - u * 2.4)])
        for i in range(4):
            y = h - i * u * 1.1 - u * 0.4
            pygame.draw.line(art, WHITE, (cx + (i * 0.05) * u, y), (cx + (i * 0.05) * u, y - u * 0.4), 4)
        rx, ry = cx + u * 3.0, base - u * 2.4
        pygame.draw.rect(art, (120, 130, 150), (rx - u * 0.1, ry, u * 0.2, u * 2.4))
        head = pygame.Rect(rx - u * 0.9, ry - u * 1.4, u * 1.8, u * 1.4)
        pygame.draw.rect(art, (200, 210, 225), head, border_radius=8)
        for sx in (-1, 1):
            circ(art, BLUE, (rx + sx * u * 0.38, ry - u * 0.75), u * 0.22)
        pygame.draw.line(art, (120, 130, 150), (rx, ry - u * 1.4), (rx, ry - u * 1.8), 3)
        circ(art, RED, (rx, ry - u * 1.9), u * 0.16)
        _tree(art, cx - u * 4.0, base, u)
    elif name == "dunes":  # sand, download box, bug
        sand = (236, 205, 140)
        pygame.draw.ellipse(art, sand, (-w * 0.3, base - u * 1.5, w * 1.0, h))
        pygame.draw.ellipse(art, mix(sand, (214, 160, 90), 0.5), (w * 0.25, base - u * 0.8, w * 1.2, h))
        box = pygame.Rect(cx - u * 1.6, base - u * 3.9, u * 3.2, u * 3.2)
        pygame.draw.rect(art, WHITE, box, border_radius=int(u * 0.4))
        pygame.draw.rect(art, col, box, 5, border_radius=int(u * 0.4))
        pygame.draw.rect(art, col, (cx - u * 0.25, box.y + u * 0.5, u * 0.5, u * 1.3))
        pygame.draw.polygon(art, col, [(cx - u * 0.8, box.y + u * 1.75), (cx + u * 0.8, box.y + u * 1.75),
                                       (cx, box.y + u * 2.5)])
        pygame.draw.line(art, col, (cx - u * 0.9, box.y + u * 2.8), (cx + u * 0.9, box.y + u * 2.8), 5)
        bx, by = cx + u * 3.4, base - u * 0.7
        for k in (-1, 0, 1):
            pygame.draw.line(art, INK, (bx - u * 0.3, by + k * u * 0.25), (bx - u * 0.9, by + k * u * 0.45), 3)
        circ(art, RED, (bx, by), u * 0.55)
        circ(art, INK, (bx + u * 0.5, by - u * 0.2), u * 0.3)
        pygame.draw.rect(art, (60, 150, 90), (cx - u * 4.1, base - u * 2.0, u * 0.5, u * 2.0), border_radius=8)
        pygame.draw.rect(art, (60, 150, 90), (cx - u * 4.6, base - u * 1.5, u * 0.5, u * 0.9), border_radius=8)
    elif name == "wifi":  # sea, lighthouse, wifi signal
        pygame.draw.ellipse(art, (70, 160, 225), (-w * 0.2, base - u * 0.8, w * 1.4, h))
        for k in range(3):
            y = base + u * (0.3 + k * 0.6)
            pygame.draw.arc(art, (170, 215, 250), (cx - u * 5 + k * u * 2, y, u * 2, u * 0.7), 0, math.pi, 3)
        tw = u * 1.5
        pygame.draw.polygon(art, WHITE, [(cx - tw / 2, base), (cx + tw / 2, base),
                                         (cx + tw * 0.32, base - u * 4.0), (cx - tw * 0.32, base - u * 4.0)])
        for k in range(3):
            y0 = base - u * (0.7 + k * 1.2)
            pygame.draw.polygon(art, RED, [(cx - tw * 0.42, y0), (cx + tw * 0.42, y0),
                                           (cx + tw * 0.38, y0 - u * 0.55), (cx - tw * 0.38, y0 - u * 0.55)])
        pygame.draw.rect(art, (60, 70, 100), (cx - tw * 0.4, base - u * 4.7, tw * 0.8, u * 0.7))
        pygame.draw.polygon(art, RED, [(cx - tw * 0.5, base - u * 4.7), (cx, base - u * 5.4), (cx + tw * 0.5, base - u * 4.7)])
        sx, sy = cx + u * 3.2, base - u * 4.0
        for k in (1, 2, 3):
            r = u * 0.8 * k
            pygame.draw.arc(art, col, (sx - r, sy - r, 2 * r, 2 * r), math.pi * 0.25, math.pi * 0.75, 6)
        circ(art, col, (sx, sy - u * 0.1), u * 0.25)
    elif name == "kind":  # heart + friendly chat bubbles
        hx, hy, hr = cx, base - u * 3.4, u * 1.6
        pink = (235, 90, 140)
        circ(art, pink, (hx - hr * 0.5, hy - hr * 0.2), hr * 0.62)
        circ(art, pink, (hx + hr * 0.5, hy - hr * 0.2), hr * 0.62)
        pygame.draw.polygon(art, pink, [(hx - hr * 1.07, hy + hr * 0.05), (hx + hr * 1.07, hy + hr * 0.05),
                                        (hx, hy + hr * 1.4)])
        for bx, by, flip in ((cx - u * 3.4, base - u * 1.8, 1), (cx + u * 3.4, base - u * 1.4, -1)):
            r = pygame.Rect(0, 0, u * 2.4, u * 1.5)
            r.center = (bx, by)
            pygame.draw.rect(art, WHITE, r, border_radius=int(u * 0.5))
            pygame.draw.polygon(art, WHITE, [(bx - flip * u * 0.4, r.bottom - 2), (bx - flip * u * 0.9, r.bottom + u * 0.5),
                                             (bx + flip * u * 0.1, r.bottom - 2)])
            for sgn in (-1, 1):
                circ(art, INK, (bx + sgn * u * 0.4, by - u * 0.15), u * 0.1)
            pygame.draw.arc(art, INK, (bx - u * 0.5, by - u * 0.4, u * 1.0, u * 0.8), math.pi * 1.1, math.pi * 1.9, 3)
    elif name == "galaxy":  # space: planet, rocket, controller
        for yy in range(h):
            pygame.draw.line(art, mix((30, 30, 90), (90, 70, 170), yy / h), (0, yy), (w, yy))
        rnd = random.Random(7)
        for _ in range(45):
            circ(art, WHITE, (rnd.uniform(0, w), rnd.uniform(0, h)), rnd.choice((1, 1, 2)))
        pc = (w * 0.68, h * 0.36)
        circ(art, (255, 170, 80), pc, u * 1.9)
        circ(art, (255, 205, 130), (pc[0] - u * 0.6, pc[1] - u * 0.6), u * 0.6)
        pygame.draw.ellipse(art, (255, 235, 190), (pc[0] - u * 3.0, pc[1] - u * 0.45, u * 6.0, u * 0.9), 5)
        rx, ry = w * 0.27, h * 0.5
        pygame.draw.polygon(art, (255, 150, 60), [(rx - u * 0.45, ry + u * 1.5), (rx + u * 0.45, ry + u * 1.5), (rx, ry + u * 2.6)])
        for sgn in (-1, 1):
            pygame.draw.polygon(art, RED, [(rx + sgn * u * 0.7, ry + u * 0.3), (rx + sgn * u * 1.3, ry + u * 1.6),
                                           (rx + sgn * u * 0.7, ry + u * 1.5)])
        pygame.draw.rect(art, WHITE, (rx - u * 0.7, ry - u * 0.9, u * 1.4, u * 2.5), border_radius=int(u * 0.6))
        pygame.draw.polygon(art, RED, [(rx - u * 0.7, ry - u * 0.7), (rx, ry - u * 2.0), (rx + u * 0.7, ry - u * 0.7)])
        circ(art, SKY, (rx, ry + u * 0.1), u * 0.35)
        gx, gy = w * 0.64, h * 0.8
        pad = pygame.Rect(0, 0, u * 3.2, u * 1.5)
        pad.center = (gx, gy)
        pygame.draw.rect(art, (232, 232, 248), pad, border_radius=int(u * 0.7))
        pygame.draw.rect(art, (110, 100, 190), (pad.x + u * 0.55, pad.centery - u * 0.12, u * 0.8, u * 0.24))
        pygame.draw.rect(art, (110, 100, 190), (pad.x + u * 0.83, pad.centery - u * 0.4, u * 0.24, u * 0.8))
        circ(art, RED, (pad.right - u * 0.9, pad.centery + u * 0.15), u * 0.2)
        circ(art, GOOD, (pad.right - u * 0.5, pad.centery - u * 0.15), u * 0.2)
    elif name == "social":  # phone with a heart and floating reactions
        ph = pygame.Rect(0, 0, u * 3.0, u * 5.2)
        ph.center = (cx, base - u * 2.3)
        pygame.draw.rect(art, (50, 60, 90), ph, border_radius=int(u * 0.5))
        scr = ph.inflate(-u * 0.4, -u * 0.8)
        pygame.draw.rect(art, WHITE, scr, border_radius=int(u * 0.3))
        _heart(art, (scr.centerx, scr.y + u * 1.0), u * 0.8, PINK)
        for k in range(3):
            pygame.draw.rect(art, (205, 212, 230),
                             (scr.x + u * 0.3, scr.y + u * (2.4 + k * 0.6), scr.w - u * 0.6, u * 0.3), border_radius=4)
        for bx, by in ((cx - u * 3.6, base - u * 4.3), (cx + u * 3.7, base - u * 3.4), (cx - u * 3.3, base - u * 1.6)):
            circ(art, WHITE, (bx, by), u * 0.95)
            _heart(art, (bx, by - u * 0.1), u * 0.45, PINK)
    elif name == "forest":  # pines + magnifying glass
        for fx, fs in ((cx - u * 4.2, 1.2), (cx - u * 2.6, 0.9), (cx + u * 2.9, 1.1), (cx + u * 4.4, 0.8)):
            _pine(art, fx, base, u * fs)
        mx, my = cx, base - u * 2.7
        circ(art, (200, 230, 250), (mx, my), u * 1.5)
        pygame.draw.circle(art, (110, 80, 50), (int(mx), int(my)), int(u * 1.5), 6)
        pygame.draw.line(art, (110, 80, 50), (mx + u * 1.1, my + u * 1.1), (mx + u * 2.4, my + u * 2.4), 9)
        text(art, "?", int(u * 1.8), col, (mx, my), "center", bold=True)
    elif name == "camera":  # camera + photos
        body = pygame.Rect(0, 0, u * 5, u * 3.2)
        body.center = (cx, base - u * 1.9)
        pygame.draw.rect(art, (70, 75, 100), (body.x + u * 0.5, body.y - u * 0.6, u * 1.4, u * 0.9), border_radius=6)
        pygame.draw.rect(art, (70, 75, 100), body, border_radius=int(u * 0.5))
        circ(art, (40, 45, 65), body.center, u * 1.2)
        circ(art, (120, 170, 230), body.center, u * 0.9)
        circ(art, WHITE, (body.centerx - u * 0.3, body.centery - u * 0.3), u * 0.25)
        circ(art, RED, (body.right - u * 0.6, body.y + u * 0.6), u * 0.2)
        for px, py in ((cx + u * 3.5, base - u * 3.2), (cx - u * 4.4, base - u * 2.6)):
            pygame.draw.rect(art, WHITE, (px, py, u * 1.8, u * 2.1), border_radius=4)
            pygame.draw.rect(art, (170, 215, 165), (px + u * 0.2, py + u * 0.2, u * 1.4, u * 1.3))
            circ(art, (255, 214, 90), (px + u * 0.6, py + u * 0.65), u * 0.25)
    elif name == "station":  # train + stop sign
        pygame.draw.rect(art, (126, 134, 154), (0, base - u * 0.2, w, h))
        tr = pygame.Rect(w * 0.07, base - u * 2.7, w * 0.86, u * 2.3)
        pygame.draw.rect(art, col, tr, border_radius=int(u * 0.5))
        for k in range(6):
            pygame.draw.rect(art, (200, 230, 250),
                             (tr.x + u * 0.7 + k * (tr.w - u * 1.4) / 6, tr.y + u * 0.45, u * 0.9, u * 0.9), border_radius=4)
        for k in range(4):
            circ(art, (60, 60, 80), (tr.x + u * 1.6 + k * (tr.w - u * 3.2) / 3, tr.bottom), u * 0.35)
        pygame.draw.rect(art, (110, 110, 124), (cx - u * 0.1, base - u * 6.0, u * 0.2, u * 3.4))
        circ(art, RED, (cx, base - u * 6.2), u * 0.95)
        text(art, "STOP", int(u * 0.62), WHITE, (cx, base - u * 6.2), "center", bold=True)
    elif name == "fjord":  # cliffs, water, footprints
        pygame.draw.ellipse(art, (236, 205, 140), (-w * 0.1, base - u * 0.4, w * 1.2, h))
        for x0, d in ((0, 1), (w, -1)):
            pygame.draw.polygon(art, (116, 138, 160), [(x0, base - u * 0.4), (x0, base - u * 5.6),
                                                       (x0 + d * u * 2.6, base - u * 3.6),
                                                       (x0 + d * u * 4.2, base - u * 5.2),
                                                       (x0 + d * u * 6.5, base - u * 0.4)])
        pygame.draw.ellipse(art, (80, 165, 225), (cx - u * 3.2, base - u * 2.6, u * 6.4, u * 2.4))
        for k in range(6):
            pygame.draw.ellipse(art, (190, 150, 95),
                                (cx - u * 3.0 + k * u * 1.15, base + u * (0.5 + (k % 2) * 0.7), u * 0.5, u * 0.8))
    elif name == "alley":  # buildings and a billboard
        pygame.draw.rect(art, (150, 150, 178), (w * 0.05, base - u * 5.6, u * 3.8, u * 5.6))
        pygame.draw.rect(art, (130, 130, 162), (w * 0.95 - u * 4.0, base - u * 4.6, u * 4.0, u * 4.6))
        for bx, bh in ((w * 0.05, 5.6), (w * 0.95 - u * 4.0, 4.6)):
            for r_ in range(int(bh // 1.4)):
                for c_ in range(2):
                    pygame.draw.rect(art, (255, 230, 150),
                                     (bx + u * 0.5 + c_ * u * 1.7, base - u * bh + u * 0.5 + r_ * u * 1.3, u * 0.9, u * 0.8))
        bb = pygame.Rect(0, 0, u * 4.6, u * 2.4)
        bb.center = (cx, base - u * 3.8)
        pygame.draw.rect(art, (110, 110, 130), (cx - u * 0.15, bb.bottom, u * 0.3, u * 2.0))
        pygame.draw.rect(art, WHITE, bb, border_radius=8)
        pygame.draw.rect(art, col, bb, 5, border_radius=8)
        text(art, "WIN!!!", int(u * 0.95), RED, bb.center, "center", bold=True)
    elif name == "smarthome":  # house with wifi, camera, speaker
        bw, bh = u * 4.6, u * 3.0
        pygame.draw.rect(art, (255, 240, 205), (cx - bw / 2, base - bh, bw, bh))
        pygame.draw.polygon(art, col, [(cx - bw / 2 - u * 0.5, base - bh), (cx, base - bh - u * 2.0),
                                       (cx + bw / 2 + u * 0.5, base - bh)])
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.5, base - u * 1.8, u * 1.0, u * 1.8), border_radius=4)
        for k in (1, 2, 3):
            r = u * 0.55 * k
            pygame.draw.arc(art, col, (cx - r, base - bh - u * 2.2 - r, 2 * r, 2 * r), math.pi * 0.25, math.pi * 0.75, 5)
        circ(art, col, (cx, base - bh - u * 2.25), u * 0.2)
        pygame.draw.rect(art, (60, 70, 100), (cx + bw / 2 - u * 1.4, base - bh + u * 0.3, u * 1.1, u * 0.6), border_radius=4)
        circ(art, (120, 170, 230), (cx + bw / 2 - u * 0.6, base - bh + u * 0.6), u * 0.2)
        pygame.draw.rect(art, (60, 70, 100), (cx + bw / 2 + u * 0.9, base - u * 1.8, u * 1.0, u * 1.8), border_radius=int(u * 0.4))
        circ(art, (90, 200, 250), (cx + bw / 2 + u * 1.4, base - u * 1.4), u * 0.22)
        _tree(art, cx - bw / 2 - u * 1.8, base, u)
    elif name == "tower":  # stone tower with lock, phone code, key
        tw = u * 2.8
        pygame.draw.rect(art, (196, 186, 220), (cx - tw / 2, base - u * 6.2, tw, u * 6.2))
        for k in range(3):
            pygame.draw.rect(art, (196, 186, 220), (cx - tw / 2 + k * tw * 0.4, base - u * 6.7, tw * 0.22, u * 0.6))
        draw_lock(art, (cx, base - u * 3.9), u * 0.9, (96, 104, 160))
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.5, base - u * 1.6, u * 1.0, u * 1.6), border_radius=5)
        ph = pygame.Rect(cx + u * 2.7, base - u * 3.4, u * 1.9, u * 3.2)
        pygame.draw.rect(art, (50, 60, 90), ph, border_radius=int(u * 0.3))
        pygame.draw.rect(art, WHITE, ph.inflate(-u * 0.3, -u * 0.6), border_radius=int(u * 0.2))
        text(art, "428", int(u * 0.62), col, ph.center, "center", bold=True)
        circ(art, (240, 190, 60), (cx - u * 3.4, base - u * 1.0), u * 0.55)
        pygame.draw.rect(art, (240, 190, 60), (cx - u * 3.4, base - u * 1.1, u * 1.4, u * 0.25))
    elif name == "bay":  # cloud backup + drives
        pygame.draw.ellipse(art, (80, 165, 225), (-w * 0.2, base - u * 0.2, w * 1.4, h))
        cy = base - u * 4.0
        for dx, rr in ((-1.4, 1.1), (0.0, 1.55), (1.5, 1.1)):
            circ(art, WHITE, (cx + dx * u, cy), rr * u)
        pygame.draw.rect(art, WHITE, (cx - u * 2.4, cy, u * 4.8, u * 1.1), border_radius=int(u * 0.5))
        pygame.draw.rect(art, col, (cx - u * 0.2, cy - u * 0.4, u * 0.4, u * 1.4))
        pygame.draw.polygon(art, col, [(cx - u * 0.7, cy - u * 0.2), (cx + u * 0.7, cy - u * 0.2), (cx, cy - u * 0.95)])
        pygame.draw.ellipse(art, (236, 205, 140), (w * 0.02, base - u * 0.1, u * 5.2, u * 1.6))
        for k in range(2):
            dr = pygame.Rect(w * 0.06, base - u * (1.1 + k * 1.2), u * 3.2, u * 1.0)
            pygame.draw.rect(art, (90, 100, 125), dr, border_radius=8)
            circ(art, GOOD, (dr.right - u * 0.5, dr.centery), u * 0.15)
    elif name == "hub":  # help building with a heart and friendly people
        pygame.draw.rect(art, (255, 240, 220), (cx - u * 3.0, base - u * 4.6, u * 6.0, u * 4.6))
        pygame.draw.polygon(art, col, [(cx - u * 3.6, base - u * 4.6), (cx, base - u * 6.6), (cx + u * 3.6, base - u * 4.6)])
        _heart(art, (cx, base - u * 3.5), u * 1.0, PINK)
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.5, base - u * 1.5, u * 1.0, u * 1.5), border_radius=5)
        for dx, c2 in ((-4.2, (70, 130, 220)), (4.2, (240, 140, 60))):
            circ(art, (250, 205, 160), (cx + dx * u, base - u * 1.9), u * 0.5)
            pygame.draw.ellipse(art, c2, (cx + dx * u - u * 0.6, base - u * 1.5, u * 1.2, u * 1.6))
    elif name == "mail":  # envelope with train tracks
        env = pygame.Rect(0, 0, u * 5.2, u * 3.4)
        env.center = (cx, base - u * 2.6)
        pygame.draw.rect(art, WHITE, env, border_radius=int(u * 0.3))
        pygame.draw.rect(art, col, env, 5, border_radius=int(u * 0.3))
        pygame.draw.lines(art, col, False, [(env.x + 6, env.y + 6), env.center, (env.right - 6, env.y + 6)], 5)
        circ(art, RED, (env.right - u * 0.7, env.bottom - u * 0.7), u * 0.4)
        for dx in (-3.8, 3.8):
            pygame.draw.rect(art, (255, 255, 255), (cx + dx * u - u * 0.5, base - u * 1.2, u * 1.0, u * 0.8), border_radius=4)
    elif name == "lagoon":  # water with a QR code and a chain link
        pygame.draw.ellipse(art, (80, 165, 225), (cx - u * 4.8, base - u * 1.4, u * 9.6, u * 3.0))
        qr = pygame.Rect(0, 0, u * 3.2, u * 3.2)
        qr.center = (cx, base - u * 3.4)
        pygame.draw.rect(art, WHITE, qr, border_radius=6)
        pygame.draw.rect(art, INK, qr, 4, border_radius=6)
        for gx in range(4):
            for gy in range(4):
                if (gx * 3 + gy * 5) % 3 != 1:
                    pygame.draw.rect(art, INK, (qr.x + u * 0.35 + gx * u * 0.65, qr.y + u * 0.35 + gy * u * 0.65,
                                                u * 0.5, u * 0.5))
        for dx in (-4.0, 4.0):
            pygame.draw.ellipse(art, col, (cx + dx * u - u * 0.9, base - u * 3.1, u * 1.8, u * 0.9), 5)
    elif name == "cloud":  # big cloud with a lock
        cy = base - u * 4.0
        for dx, rr in ((-1.6, 1.2), (0.0, 1.7), (1.7, 1.2)):
            circ(art, WHITE, (cx + dx * u, cy), rr * u)
        pygame.draw.rect(art, WHITE, (cx - u * 2.8, cy, u * 5.6, u * 1.2), border_radius=int(u * 0.6))
        draw_lock(art, (cx, cy + u * 0.1), u * 0.8, col)
    elif name == "ai":  # robot screen with a chat bubble
        scr = pygame.Rect(0, 0, u * 4.4, u * 3.4)
        scr.center = (cx, base - u * 3.0)
        pygame.draw.rect(art, (60, 70, 100), scr, border_radius=int(u * 0.4))
        pygame.draw.rect(art, (200, 230, 250), scr.inflate(-u * 0.5, -u * 0.5), border_radius=int(u * 0.3))
        for sx in (-1, 1):
            circ(art, INK, (scr.centerx + sx * u * 0.9, scr.centery - u * 0.2), u * 0.35)
        pygame.draw.arc(art, INK, (scr.centerx - u * 0.9, scr.centery, u * 1.8, u * 1.0), math.pi * 1.1, math.pi * 1.9, 4)
        pygame.draw.line(art, (60, 70, 100), (scr.centerx, scr.y), (scr.centerx, scr.y - u * 0.8), 4)
        circ(art, RED, (scr.centerx, scr.y - u * 0.9), u * 0.25)
        pygame.draw.rect(art, (60, 70, 100), (cx - u * 1.2, scr.bottom, u * 2.4, u * 0.7), border_radius=6)
        bub = pygame.Rect(cx + u * 2.6, base - u * 5.8, u * 2.4, u * 1.4)
        pygame.draw.rect(art, WHITE, bub, border_radius=int(u * 0.5))
        text(art, "Hi!", int(u * 0.8), col, bub.center, "center", bold=True)
    elif name == "market":  # stall with striped awning and coins
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 3.0, base - u * 2.0, u * 6.0, u * 2.0))
        for k in range(6):
            pygame.draw.rect(art, col if k % 2 == 0 else WHITE, (cx - u * 3.3 + k * u * 1.1, base - u * 4.2, u * 1.1, u * 1.2))
        pygame.draw.rect(art, (110, 80, 50), (cx - u * 3.3, base - u * 4.2, u * 6.6, u * 1.2), 3)
        for k in range(3):
            circ(art, (255, 214, 90), (cx - u * 1.2 + k * u * 1.2, base - u * 2.3), u * 0.45)
            text(art, "$", int(u * 0.6), (150, 100, 20), (cx - u * 1.2 + k * u * 1.2, base - u * 2.3), "center", bold=True)
    elif name == "school":  # school building with a flag
        pygame.draw.rect(art, (250, 228, 190), (cx - u * 3.2, base - u * 3.4, u * 6.4, u * 3.4))
        pygame.draw.polygon(art, col, [(cx - u * 3.6, base - u * 3.4), (cx, base - u * 5.4), (cx + u * 3.6, base - u * 3.4)])
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.6, base - u * 1.8, u * 1.2, u * 1.8), border_radius=5)
        for sx in (-1, 1):
            for k in (1, 2):
                pygame.draw.rect(art, (150, 205, 245), (cx + sx * u * k * 1.0 - u * 0.35 + sx * u * 0.9, base - u * 2.8, u * 0.7, u * 0.9))
        pygame.draw.line(art, INK, (cx, base - u * 5.4), (cx, base - u * 6.8), 3)
        pygame.draw.polygon(art, RED, [(cx, base - u * 6.8), (cx + u * 0.9, base - u * 6.5), (cx, base - u * 6.2)])
    elif name == "chat":  # ranch fence and speech bubbles
        for k in range(7):
            pygame.draw.rect(art, (150, 100, 60), (cx - u * 4.2 + k * u * 1.4, base - u * 1.8, u * 0.35, u * 1.8))
        pygame.draw.rect(art, (170, 118, 70), (cx - u * 4.4, base - u * 1.5, u * 8.8, u * 0.3))
        pygame.draw.rect(art, (170, 118, 70), (cx - u * 4.4, base - u * 0.8, u * 8.8, u * 0.3))
        for bx, by, cc in ((cx - u * 2.2, base - u * 4.2, WHITE), (cx + u * 1.6, base - u * 5.0, col)):
            r2 = pygame.Rect(0, 0, u * 3.0, u * 1.8)
            r2.center = (bx, by)
            pygame.draw.rect(art, cc, r2, border_radius=int(u * 0.6))
            pygame.draw.polygon(art, cc, [(r2.x + u * 0.5, r2.bottom - 4), (r2.x + u * 0.2, r2.bottom + u * 0.6), (r2.x + u * 1.1, r2.bottom - 4)])
            for k in range(3):
                circ(art, INK if cc == WHITE else WHITE, (r2.centerx - u * 0.6 + k * u * 0.6, r2.centery), u * 0.17)
    elif name == "canyon":  # rock walls with a copyright symbol
        for x0, d in ((0, 1), (w, -1)):
            pygame.draw.polygon(art, (205, 150, 100), [(x0, base), (x0, base - u * 6.2), (x0 + d * u * 2.2, base - u * 5.0),
                                                       (x0 + d * u * 3.6, base - u * 3.0), (x0 + d * u * 5.0, base)])
        circ(art, WHITE, (cx, base - u * 3.4), u * 1.7)
        pygame.draw.circle(art, col, (int(cx), int(base - u * 3.4)), int(u * 1.7), 6)
        text(art, "C", int(u * 2.0), col, (cx, base - u * 3.4), "center", bold=True)
    elif name == "outpost":  # tent with a first-aid sign
        pygame.draw.polygon(art, col, [(cx - u * 3.2, base), (cx, base - u * 4.4), (cx + u * 3.2, base)])
        pygame.draw.polygon(art, shade(col, 0.7), [(cx - u * 0.9, base), (cx, base - u * 2.4), (cx + u * 0.9, base)])
        circ(art, WHITE, (cx, base - u * 5.6), u * 1.1)
        pygame.draw.rect(art, RED, (cx - u * 0.18, base - u * 6.5, u * 0.36, u * 1.8))
        pygame.draw.rect(art, RED, (cx - u * 0.9, base - u * 5.8, u * 1.8, u * 0.36))
        _tree(art, cx - u * 4.2, base, u * 0.9)
    elif name == "academy":  # building with columns and a star
        pygame.draw.polygon(art, (225, 215, 240), [(cx - u * 3.6, base - u * 3.8), (cx, base - u * 5.8), (cx + u * 3.6, base - u * 3.8)])
        pygame.draw.rect(art, (240, 235, 250), (cx - u * 3.2, base - u * 3.8, u * 6.4, u * 0.4))
        for k in range(5):
            pygame.draw.rect(art, (240, 235, 250), (cx - u * 2.8 + k * u * 1.4, base - u * 3.4, u * 0.6, u * 3.4))
        pygame.draw.rect(art, (205, 195, 230), (cx - u * 3.4, base - u * 0.4, u * 6.8, u * 0.5))
        draw_star(art, (cx, base - u * 4.6), u * 0.6, True)
    elif name == "stream":  # camera on tripod with LIVE tag
        pygame.draw.line(art, (90, 90, 110), (cx, base - u * 2.0), (cx - u * 1.4, base), 6)
        pygame.draw.line(art, (90, 90, 110), (cx, base - u * 2.0), (cx + u * 1.4, base), 6)
        cam = pygame.Rect(0, 0, u * 4.2, u * 2.6)
        cam.center = (cx, base - u * 3.3)
        pygame.draw.rect(art, (60, 70, 100), cam, border_radius=int(u * 0.4))
        circ(art, (120, 170, 230), (cam.centerx + u * 0.6, cam.centery), u * 0.9)
        circ(art, WHITE, (cam.centerx + u * 0.3, cam.centery - u * 0.3), u * 0.2)
        tag = pygame.Rect(cam.x + u * 0.3, cam.y + u * 0.3, u * 1.5, u * 0.7)
        pygame.draw.rect(art, RED, tag, border_radius=6)
        text(art, "LIVE", int(u * 0.5), WHITE, tag.center, "center", bold=True)
    elif name == "voice":  # speaker with sound waves
        sp = pygame.Rect(0, 0, u * 2.2, u * 3.4)
        sp.center = (cx, base - u * 2.0)
        pygame.draw.rect(art, (70, 80, 110), sp, border_radius=int(u * 1.0))
        circ(art, (90, 200, 250), (sp.centerx, sp.y + u * 0.7), u * 0.4)
        for k in (1, 2, 3):
            r = u * (1.2 + k * 0.7)
            pygame.draw.arc(art, col, (sp.centerx - r, sp.centery - r, 2 * r, 2 * r), -0.7, 0.7, 5)
            pygame.draw.arc(art, col, (sp.centerx - r, sp.centery - r, 2 * r, 2 * r), math.pi - 0.7, math.pi + 0.7, 5)
    elif name == "update":  # tablet with progress bar and circular arrows
        ph = pygame.Rect(0, 0, u * 4.6, u * 3.4)
        ph.center = (cx, base - u * 2.6)
        pygame.draw.rect(art, (50, 60, 90), ph, border_radius=int(u * 0.4))
        pygame.draw.rect(art, WHITE, ph.inflate(-u * 0.5, -u * 0.5), border_radius=int(u * 0.3))
        pygame.draw.rect(art, (205, 212, 230), (ph.x + u * 0.8, ph.centery + u * 0.5, ph.w - u * 1.6, u * 0.5), border_radius=6)
        pygame.draw.rect(art, col, (ph.x + u * 0.8, ph.centery + u * 0.5, (ph.w - u * 1.6) * 0.7, u * 0.5), border_radius=6)
        pygame.draw.arc(art, col, (cx - u * 0.9, ph.y + u * 0.5, u * 1.8, u * 1.8), 0.4, 4.6, 6)
        pygame.draw.polygon(art, col, [(cx + u * 0.9, ph.y + u * 1.1), (cx + u * 1.5, ph.y + u * 1.6), (cx + u * 0.5, ph.y + u * 1.8)])
    elif name == "bridge":  # arched bridge over water with a heart
        pygame.draw.ellipse(art, (80, 165, 225), (-w * 0.1, base - u * 0.6, w * 1.2, u * 2.4))
        pygame.draw.arc(art, (150, 100, 60), (cx - u * 4.0, base - u * 3.6, u * 8.0, u * 5.2), 0, math.pi, 14)
        pygame.draw.line(art, (150, 100, 60), (cx - u * 4.0, base - u * 1.0), (cx + u * 4.0, base - u * 1.0), 8)
        for k in range(5):
            pygame.draw.line(art, (150, 100, 60), (cx - u * 3.2 + k * u * 1.6, base - u * 1.0), (cx - u * 3.2 + k * u * 1.6, base - u * 2.4), 4)
        _heart(art, (cx, base - u * 4.7), u * 0.9, PINK)
    elif name == "summit":  # mountain with a flag and a sun/moon
        pygame.draw.polygon(art, (150, 160, 190), [(cx - u * 5.0, base), (cx, base - u * 6.0), (cx + u * 5.0, base)])
        pygame.draw.polygon(art, WHITE, [(cx - u * 1.2, base - u * 4.5), (cx, base - u * 6.0), (cx + u * 1.2, base - u * 4.5), (cx, base - u * 4.9)])
        pygame.draw.line(art, INK, (cx, base - u * 6.0), (cx, base - u * 7.4), 3)
        pygame.draw.polygon(art, col, [(cx, base - u * 7.4), (cx + u * 1.1, base - u * 7.0), (cx, base - u * 6.6)])
        circ(art, (255, 255, 255), (cx + u * 3.4, base - u * 5.4), u * 0.6)
    elif name == "creek":  # stream with a mask and lily pads
        pygame.draw.ellipse(art, (80, 165, 225), (cx - u * 4.8, base - u * 1.8, u * 9.6, u * 3.0))
        for dx in (-2.8, 0.2, 3.0):
            pygame.draw.ellipse(art, (90, 190, 100), (cx + dx * u - u * 0.7, base - u * 0.2, u * 1.4, u * 0.7))
        face = pygame.Rect(0, 0, u * 3.0, u * 3.4)
        face.center = (cx, base - u * 3.9)
        pygame.draw.ellipse(art, (250, 205, 160), face)
        pygame.draw.rect(art, INK, (face.x + u * 0.1, face.y + u * 1.0, face.w - u * 0.2, u * 0.9), border_radius=int(u * 0.4))
        for sx in (-1, 1):
            circ(art, WHITE, (face.centerx + sx * u * 0.55, face.y + u * 1.45), u * 0.2)
        text(art, "?", int(u * 1.5), col, (face.centerx, face.y + u * 2.6), "center", bold=True)
    elif name == "router":  # router box with wifi arcs on a ridge
        pygame.draw.polygon(art, (150, 160, 190), [(cx - u * 4.8, base), (cx - u * 1.2, base - u * 3.4), (cx + u * 2.0, base)])
        rt = pygame.Rect(0, 0, u * 3.6, u * 1.2)
        rt.center = (cx + u * 0.8, base - u * 1.4)
        pygame.draw.rect(art, (70, 80, 110), rt, border_radius=8)
        for k in range(3):
            circ(art, GOOD, (rt.x + u * 0.6 + k * u * 0.6, rt.centery), u * 0.15)
        for dx in (-1, 1):
            pygame.draw.line(art, (70, 80, 110), (rt.centerx + dx * u * 1.2, rt.y), (rt.centerx + dx * u * 1.6, rt.y - u * 1.2), 5)
        for k in (1, 2, 3):
            r = u * 0.8 * k
            pygame.draw.arc(art, col, (rt.centerx - r, rt.y - u * 1.6 - r, 2 * r, 2 * r), math.pi * 0.25, math.pi * 0.75, 5)
    elif name == "fort":  # stone fort with a phone and lock
        pygame.draw.rect(art, (200, 190, 215), (cx - u * 3.4, base - u * 3.4, u * 6.8, u * 3.4))
        for k in range(6):
            pygame.draw.rect(art, (200, 190, 215), (cx - u * 3.4 + k * u * 1.25, base - u * 3.9, u * 0.8, u * 0.6))
        ph = pygame.Rect(cx - u * 0.9, base - u * 3.0, u * 1.8, u * 3.0)
        pygame.draw.rect(art, (50, 60, 90), ph, border_radius=int(u * 0.3))
        pygame.draw.rect(art, WHITE, ph.inflate(-u * 0.3, -u * 0.5), border_radius=int(u * 0.2))
        draw_lock(art, (ph.centerx, ph.centery), u * 0.5, col)
    elif name == "swamp":  # murky pond, reeds and a phone with warning
        pygame.draw.ellipse(art, (90, 140, 110), (cx - u * 4.8, base - u * 1.4, u * 9.6, u * 3.0))
        for dx in (-4.0, -3.5, 3.6, 4.1):
            pygame.draw.line(art, (90, 120, 70), (cx + dx * u, base - u * 0.2), (cx + dx * u, base - u * 2.6), 4)
            circ(art, (140, 100, 60), (cx + dx * u, base - u * 2.8), u * 0.2)
        ph = pygame.Rect(0, 0, u * 2.4, u * 4.0)
        ph.center = (cx, base - u * 3.0)
        pygame.draw.rect(art, (50, 60, 90), ph, border_radius=int(u * 0.4))
        pygame.draw.rect(art, WHITE, ph.inflate(-u * 0.4, -u * 0.6), border_radius=int(u * 0.3))
        pygame.draw.polygon(art, (250, 190, 40), [(ph.centerx, ph.y + u * 0.9), (ph.centerx - u * 0.7, ph.y + u * 2.3), (ph.centerx + u * 0.7, ph.y + u * 2.3)])
        text(art, "!", int(u * 0.9), INK, (ph.centerx, ph.y + u * 1.8), "center", bold=True)
    elif name == "hq":  # HQ building with shield and flag
        pygame.draw.rect(art, (235, 235, 250), (cx - u * 3.0, base - u * 3.6, u * 6.0, u * 3.6))
        pygame.draw.rect(art, col, (cx - u * 3.3, base - u * 4.1, u * 6.6, u * 0.6))
        draw_shield(art, (cx, base - u * 2.4), u * 0.9, col)
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.5, base - u * 1.2, u * 1.0, u * 1.2), border_radius=4)
        pygame.draw.line(art, INK, (cx + u * 2.4, base - u * 4.1), (cx + u * 2.4, base - u * 5.9), 3)
        pygame.draw.polygon(art, RED, [(cx + u * 2.4, base - u * 5.9), (cx + u * 3.3, base - u * 5.6), (cx + u * 2.4, base - u * 5.3)])
    elif name == "vault":  # big safe with a dial
        sf = pygame.Rect(0, 0, u * 4.4, u * 4.0)
        sf.center = (cx, base - u * 2.2)
        pygame.draw.rect(art, (110, 120, 145), sf, border_radius=int(u * 0.4))
        pygame.draw.rect(art, (150, 160, 185), sf.inflate(-u * 0.6, -u * 0.6), border_radius=int(u * 0.3))
        circ(art, (110, 120, 145), sf.center, u * 1.0)
        circ(art, col, sf.center, u * 0.35)
        pygame.draw.line(art, WHITE, sf.center, (sf.centerx + u * 0.7, sf.centery - u * 0.7), 4)
    elif name == "pier":  # wooden pier, water and a camera
        pygame.draw.ellipse(art, (80, 165, 225), (-w * 0.1, base - u * 1.0, w * 1.2, u * 3.0))
        pygame.draw.rect(art, (150, 100, 60), (cx - u * 4.4, base - u * 1.2, u * 8.8, u * 0.5))
        for k in range(5):
            pygame.draw.rect(art, (120, 80, 50), (cx - u * 4.0 + k * u * 2.0, base - u * 0.7, u * 0.3, u * 1.6))
        cam = pygame.Rect(0, 0, u * 2.6, u * 1.8)
        cam.center = (cx, base - u * 2.2)
        pygame.draw.rect(art, (70, 75, 100), cam, border_radius=int(u * 0.3))
        circ(art, (120, 170, 230), cam.center, u * 0.6)
        circ(art, WHITE, (cam.centerx - u * 0.2, cam.centery - u * 0.2), u * 0.15)
    elif name == "hill":  # hill with a laptop and shield
        lp = pygame.Rect(0, 0, u * 3.6, u * 2.4)
        lp.center = (cx, base - u * 3.0)
        pygame.draw.rect(art, (60, 70, 100), lp, border_radius=int(u * 0.3))
        pygame.draw.rect(art, (30, 40, 70), lp.inflate(-u * 0.4, -u * 0.4), border_radius=int(u * 0.2))
        text(art, ">_", int(u * 0.9), (110, 230, 140), lp.center, "center", bold=True)
        pygame.draw.rect(art, (90, 100, 130), (lp.x - u * 0.4, lp.bottom, lp.w + u * 0.8, u * 0.3), border_radius=6)
        draw_shield(art, (cx + u * 3.4, base - u * 3.6), u * 0.8, col)
    elif name == "cafe":  # cafe table with cookie
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.2, base - u * 2.0, u * 0.4, u * 2.0))
        pygame.draw.ellipse(art, (150, 100, 60), (cx - u * 2.2, base - u * 2.4, u * 4.4, u * 0.9))
        circ(art, (222, 170, 100), (cx, base - u * 3.4), u * 1.2)
        for dx, dy in ((-0.4, -0.3), (0.5, 0.1), (-0.1, 0.5), (0.4, -0.6)):
            circ(art, (100, 60, 30), (cx + dx * u, base - u * 3.4 + dy * u), u * 0.15)
        pygame.draw.rect(art, col, (cx - u * 4.6, base - u * 3.2, u * 1.8, u * 1.0), border_radius=6)
        pygame.draw.rect(art, WHITE, (cx - u * 4.5, base - u * 3.1, u * 1.6, u * 0.4))
    elif name == "woods":  # pines and a smartwatch
        for fx, fs in ((cx - u * 4.2, 1.2), (cx - u * 2.8, 0.9), (cx + u * 3.4, 1.1)):
            _pine(art, fx, base, u * fs)
        wt = pygame.Rect(0, 0, u * 2.0, u * 2.4)
        wt.center = (cx, base - u * 2.8)
        pygame.draw.rect(art, (60, 70, 100), (wt.x + u * 0.5, wt.y - u * 1.0, u * 1.0, u * 4.4))
        pygame.draw.rect(art, (50, 60, 90), wt, border_radius=int(u * 0.5))
        pygame.draw.rect(art, WHITE, wt.inflate(-u * 0.4, -u * 0.4), border_radius=int(u * 0.3))
        circ(art, RED, (wt.centerx, wt.centery - u * 0.2), u * 0.3)
        pygame.draw.polygon(art, RED, [(wt.centerx - u * 0.3, wt.centery - u * 0.1), (wt.centerx + u * 0.3, wt.centery - u * 0.1), (wt.centerx, wt.centery + u * 0.5)])
    elif name == "lab":  # flask with a bug
        pygame.draw.polygon(art, (200, 230, 250), [(cx - u * 0.7, base - u * 4.8), (cx + u * 0.7, base - u * 4.8), (cx + u * 2.0, base - u * 1.0), (cx - u * 2.0, base - u * 1.0)])
        pygame.draw.polygon(art, col, [(cx - u * 1.5, base - u * 2.4), (cx + u * 1.5, base - u * 2.4), (cx + u * 2.0, base - u * 1.0), (cx - u * 2.0, base - u * 1.0)])
        pygame.draw.rect(art, (200, 230, 250), (cx - u * 0.9, base - u * 5.1, u * 1.8, u * 0.4), border_radius=4)
        circ(art, (60, 40, 40), (cx, base - u * 1.7), u * 0.35)
        for dx in (-1, 1):
            pygame.draw.line(art, (60, 40, 40), (cx + dx * u * 0.3, base - u * 1.7), (cx + dx * u * 0.8, base - u * 2.1), 3)
        for dx, r in ((-0.3, 0.3), (0.2, 0.45)):
            circ(art, WHITE, (cx + dx * u, base - u * 5.9 - r * u), u * r)
    elif name == "field":  # goal posts and a ball
        pygame.draw.rect(art, WHITE, (cx - u * 2.6, base - u * 3.6, u * 0.25, u * 3.6))
        pygame.draw.rect(art, WHITE, (cx + u * 2.4, base - u * 3.6, u * 0.25, u * 3.6))
        pygame.draw.rect(art, WHITE, (cx - u * 2.6, base - u * 3.6, u * 5.3, u * 0.25))
        for k in range(6):
            pygame.draw.line(art, (225, 230, 240), (cx - u * 2.5 + k * u * 1.0, base - u * 3.4), (cx - u * 2.5 + k * u * 1.0, base - u * 0.6), 2)
        circ(art, WHITE, (cx + u * 0.5, base - u * 0.7), u * 0.6)
        pygame.draw.circle(art, INK, (int(cx + u * 0.5), int(base - u * 0.7)), int(u * 0.6), 3)
        draw_star(art, (cx, base - u * 4.7), u * 0.7, True)
    elif name == "shore":  # beach with magnifying glass
        pygame.draw.ellipse(art, (80, 165, 225), (-w * 0.2, base - u * 1.8, w * 1.4, u * 3.0))
        pygame.draw.ellipse(art, (236, 205, 140), (-w * 0.1, base - u * 0.6, w * 1.2, h))
        mx, my = cx, base - u * 3.0
        circ(art, (200, 230, 250), (mx, my), u * 1.4)
        pygame.draw.circle(art, (110, 80, 50), (int(mx), int(my)), int(u * 1.4), 6)
        pygame.draw.line(art, (110, 80, 50), (mx + u * 1.0, my + u * 1.0), (mx + u * 2.3, my + u * 2.3), 9)
    elif name == "agency":  # building with an eye
        pygame.draw.rect(art, (200, 195, 215), (cx - u * 3.0, base - u * 4.0, u * 6.0, u * 4.0))
        pygame.draw.rect(art, (130, 86, 52), (cx - u * 0.5, base - u * 1.6, u * 1.0, u * 1.6), border_radius=4)
        pygame.draw.ellipse(art, WHITE, (cx - u * 1.5, base - u * 3.6, u * 3.0, u * 1.6))
        circ(art, col, (cx, base - u * 2.8), u * 0.55)
        circ(art, INK, (cx, base - u * 2.8), u * 0.25)
        pygame.draw.rect(art, col, (cx - u * 3.3, base - u * 4.4, u * 6.6, u * 0.5))
    elif name == "rock":  # big rock with a stop hand
        pygame.draw.polygon(art, (150, 155, 175), [(cx - u * 3.6, base), (cx - u * 2.6, base - u * 3.8), (cx - u * 0.4, base - u * 5.2), (cx + u * 2.0, base - u * 3.8), (cx + u * 3.6, base)])
        pygame.draw.polygon(art, (180, 185, 205), [(cx - u * 2.6, base - u * 3.8), (cx - u * 0.4, base - u * 5.2), (cx - u * 0.2, base - u * 3.0)])
        circ(art, RED, (cx, base - u * 2.4), u * 1.1)
        pygame.draw.line(art, WHITE, (cx - u * 0.6, base - u * 2.4), (cx + u * 0.6, base - u * 2.4), 6)
    elif name == "castle":
        keep = pygame.Rect(cx - u * 2, base - u * 3.6, u * 4, u * 3.6)
        pygame.draw.rect(art, (205, 195, 235), keep)
        for i in range(5):
            pygame.draw.rect(art, (205, 195, 235), (keep.x + i * u * 0.9, keep.y - u * 0.35, u * 0.55, u * 0.4))
        for tx, th in ((cx - u * 3.3, 4.6), (cx + u * 1.7, 4.6)):
            pygame.draw.rect(art, (190, 178, 228), (tx, base - u * th, u * 1.6, u * th))
            pygame.draw.polygon(art, PURPLE, [(tx - u * 0.2, base - u * th), (tx + u * 0.8, base - u * (th + 1.4)),
                                              (tx + u * 1.8, base - u * th)])
        pygame.draw.rect(art, (215, 205, 242), (cx - u * 0.9, base - u * 5.2, u * 1.8, u * 1.7))
        pygame.draw.polygon(art, (150, 110, 215), [(cx - u * 1.1, base - u * 5.2), (cx, base - u * 6.8),
                                                   (cx + u * 1.1, base - u * 5.2)])
        pygame.draw.line(art, INK, (cx, base - u * 6.8), (cx, base - u * 7.8), 3)
        pygame.draw.polygon(art, RED, [(cx, base - u * 7.8), (cx + u * 0.9, base - u * 7.5), (cx, base - u * 7.2)])
        pygame.draw.rect(art, (110, 80, 60), (cx - u * 0.6, base - u * 1.6, u * 1.2, u * 1.6), border_top_left_radius=int(u * 0.6), border_top_right_radius=int(u * 0.6))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=22)
    art.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    _art_cache[key] = art
    return art


def _eyes(surf, x, y, dx, r, blink):
    for sx in (-1, 1):
        cx = x + sx * dx
        if blink:
            pygame.draw.line(surf, INK, (cx - r * 0.7, y), (cx + r * 0.7, y), 3)
        else:
            circ(surf, WHITE, (cx, y), r)
            circ(surf, INK, (cx, y), r * 0.55)
            circ(surf, WHITE, (cx + r * 0.2, y - r * 0.2), r * 0.18)


def draw_guide(surf, kind, c, s, t, talking=False):
    """Draw an animated guide character (head + body) centred at c."""
    x, y = c[0], c[1] + math.sin(t * 3) * s * 0.05
    blink = (t % 3.3) < 0.12
    open_m = talking and int(t * 9) % 2 == 0
    if kind == "owl":
        body, belly = (156, 104, 64), (242, 218, 178)
        pygame.draw.ellipse(surf, body, (x - s, y - s * 1.05, 2 * s, 2.3 * s))
        pygame.draw.ellipse(surf, belly, (x - s * 0.62, y + s * 0.1, s * 1.24, s * 1.0))
        for sx in (-1, 1):
            pygame.draw.polygon(surf, shade(body, 0.8), [(x + sx * s * 0.95, y - s * 0.8), (x + sx * s * 0.6, y - s * 1.3),
                                                         (x + sx * s * 0.25, y - s * 0.85)])
            pygame.draw.ellipse(surf, shade(body, 0.85), (x + sx * s * 0.95 - s * 0.2, y - s * 0.1, s * 0.4, s * 1.0))
            circ(surf, (255, 235, 210), (x + sx * s * 0.42, y - s * 0.35), s * 0.46)
        _eyes(surf, x, y - s * 0.35, s * 0.42, s * 0.3, blink)
        pygame.draw.polygon(surf, ORANGE, [(x - s * 0.14, y - s * 0.12), (x + s * 0.14, y - s * 0.12), (x, y + s * 0.18)])
        if open_m:
            circ(surf, (120, 50, 30), (x, y + s * 0.22), s * 0.07)
    elif kind == "fox":
        orange = (240, 130, 45)
        pygame.draw.ellipse(surf, orange, (x - s * 0.8, y + s * 0.3, s * 1.6, s * 1.5))
        pygame.draw.ellipse(surf, WHITE, (x - s * 0.4, y + s * 0.55, s * 0.8, s * 1.0))
        for sx in (-1, 1):
            pygame.draw.polygon(surf, orange, [(x + sx * s * 0.9, y - s * 0.45), (x + sx * s * 0.75, y - s * 1.4),
                                               (x + sx * s * 0.2, y - s * 0.85)])
            pygame.draw.polygon(surf, (90, 45, 30), [(x + sx * s * 0.75, y - s * 0.6), (x + sx * s * 0.72, y - s * 1.1),
                                                     (x + sx * s * 0.4, y - s * 0.8)])
        circ(surf, orange, (x, y), s)
        pygame.draw.polygon(surf, WHITE, [(x - s * 0.95, y + s * 0.1), (x, y + s * 0.95), (x + s * 0.95, y + s * 0.1),
                                          (x, y + s * 0.2)])
        _eyes(surf, x, y - s * 0.2, s * 0.42, s * 0.2, blink)
        circ(surf, INK, (x, y + s * 0.45), s * 0.13)
        if open_m:
            pygame.draw.ellipse(surf, (120, 50, 30), (x - s * 0.1, y + s * 0.62, s * 0.2, s * 0.16))
    elif kind == "bear":
        brown, light = (150, 100, 65), (222, 188, 150)
        pygame.draw.ellipse(surf, brown, (x - s * 0.85, y + s * 0.35, s * 1.7, s * 1.5))
        pygame.draw.ellipse(surf, light, (x - s * 0.5, y + s * 0.6, s, s * 1.0))
        for sx in (-1, 1):
            circ(surf, brown, (x + sx * s * 0.75, y - s * 0.75), s * 0.34)
            circ(surf, light, (x + sx * s * 0.75, y - s * 0.75), s * 0.18)
        circ(surf, brown, (x, y), s)
        pygame.draw.ellipse(surf, light, (x - s * 0.45, y + s * 0.05, s * 0.9, s * 0.7))
        _eyes(surf, x, y - s * 0.25, s * 0.4, s * 0.2, blink)
        pygame.draw.ellipse(surf, INK, (x - s * 0.15, y + s * 0.12, s * 0.3, s * 0.2))
        if open_m:
            pygame.draw.ellipse(surf, (120, 50, 30), (x - s * 0.12, y + s * 0.4, s * 0.24, s * 0.18))
    elif kind == "dino":
        green, light = (96, 186, 108), (190, 230, 160)
        pygame.draw.ellipse(surf, green, (x - s * 0.85, y + s * 0.35, s * 1.7, s * 1.5))
        pygame.draw.ellipse(surf, light, (x - s * 0.5, y + s * 0.6, s, s))
        for k in (-1, 0, 1):
            bx = x + k * s * 0.5
            pygame.draw.polygon(surf, ORANGE, [(bx - s * 0.22, y - s * 0.8), (bx, y - s * (1.4 - abs(k) * 0.15)),
                                               (bx + s * 0.22, y - s * 0.8)])
        circ(surf, green, (x, y), s)
        pygame.draw.ellipse(surf, light, (x - s * 0.6, y + s * 0.05, s * 1.2, s * 0.75))
        _eyes(surf, x, y - s * 0.3, s * 0.45, s * 0.22, blink)
        for sx in (-1, 1):
            circ(surf, shade(green, 0.6), (x + sx * s * 0.18, y + s * 0.25), s * 0.06)
        if open_m:
            pygame.draw.ellipse(surf, (120, 50, 30), (x - s * 0.18, y + s * 0.45, s * 0.36, s * 0.2))
        else:
            pygame.draw.line(surf, shade(green, 0.6), (x - s * 0.3, y + s * 0.5), (x + s * 0.3, y + s * 0.5), 3)
    elif kind == "penguin":
        navy = (45, 60, 100)
        pygame.draw.ellipse(surf, navy, (x - s * 0.95, y - s * 1.05, s * 1.9, s * 2.4))
        pygame.draw.ellipse(surf, WHITE, (x - s * 0.62, y - s * 0.2, s * 1.24, s * 1.4))
        for sx in (-1, 1):
            pygame.draw.ellipse(surf, shade(navy, 0.85), (x + sx * s * 1.0 - s * 0.2, y - s * 0.1, s * 0.4, s * 1.0))
            pygame.draw.ellipse(surf, ORANGE, (x + sx * s * 0.45 - s * 0.3, y + s * 1.22, s * 0.6, s * 0.22))
        pygame.draw.ellipse(surf, WHITE, (x - s * 0.7, y - s * 0.75, s * 1.4, s * 0.95))
        _eyes(surf, x, y - s * 0.35, s * 0.32, s * 0.2, blink)
        pygame.draw.polygon(surf, ORANGE, [(x - s * 0.15, y - s * 0.12), (x + s * 0.15, y - s * 0.12),
                                           (x, y + s * (0.18 if open_m else 0.1))])
    elif kind == "cat":
        fur, pink = (236, 172, 100), (250, 170, 180)
        pygame.draw.ellipse(surf, fur, (x - s * 0.8, y + s * 0.35, s * 1.6, s * 1.5))
        pygame.draw.ellipse(surf, WHITE, (x - s * 0.4, y + s * 0.6, s * 0.8, s * 1.0))
        for sx in (-1, 1):
            pygame.draw.polygon(surf, fur, [(x + sx * s * 0.95, y - s * 0.2), (x + sx * s * 0.8, y - s * 1.3),
                                            (x + sx * s * 0.2, y - s * 0.8)])
            pygame.draw.polygon(surf, pink, [(x + sx * s * 0.78, y - s * 0.45), (x + sx * s * 0.72, y - s * 1.0),
                                             (x + sx * s * 0.4, y - s * 0.75)])
        circ(surf, fur, (x, y), s)
        for k in (-1, 0, 1):
            pygame.draw.line(surf, shade(fur, 0.7), (x + k * s * 0.22, y - s * 0.95), (x + k * s * 0.22, y - s * 0.65), 4)
        pygame.draw.ellipse(surf, WHITE, (x - s * 0.45, y + s * 0.1, s * 0.9, s * 0.65))
        _eyes(surf, x, y - s * 0.2, s * 0.42, s * 0.2, blink)
        pygame.draw.polygon(surf, pink, [(x - s * 0.1, y + s * 0.2), (x + s * 0.1, y + s * 0.2), (x, y + s * 0.32)])
        for sx in (-1, 1):
            pygame.draw.line(surf, INK, (x + sx * s * 0.35, y + s * 0.38), (x + sx * s * 0.95, y + s * 0.3), 2)
            pygame.draw.line(surf, INK, (x + sx * s * 0.35, y + s * 0.46), (x + sx * s * 0.95, y + s * 0.52), 2)
        if open_m:
            pygame.draw.ellipse(surf, (120, 50, 30), (x - s * 0.1, y + s * 0.42, s * 0.2, s * 0.16))
    elif kind == "alien":
        green = (120, 210, 130)
        pygame.draw.ellipse(surf, (110, 90, 190), (x - s * 0.7, y + s * 0.7, s * 1.4, s * 1.2))
        for sx in (-1, 1):
            pygame.draw.line(surf, green, (x + sx * s * 0.4, y - s * 1.0), (x + sx * s * 0.7, y - s * 1.45), 4)
            circ(surf, YELLOW, (x + sx * s * 0.72, y - s * 1.5), s * 0.14)
        pygame.draw.ellipse(surf, green, (x - s * 0.95, y - s * 1.1, s * 1.9, s * 2.0))
        for sx in (-1, 1):
            ex = x + sx * s * 0.42
            if blink:
                pygame.draw.line(surf, INK, (ex - s * 0.25, y - s * 0.1), (ex + s * 0.25, y - s * 0.1), 4)
            else:
                pygame.draw.ellipse(surf, INK, (ex - s * 0.3, y - s * 0.45, s * 0.6, s * 0.7))
                circ(surf, WHITE, (ex + s * 0.08, y - s * 0.22), s * 0.1)
        if open_m:
            pygame.draw.ellipse(surf, (40, 90, 60), (x - s * 0.15, y + s * 0.4, s * 0.3, s * 0.2))
        else:
            pygame.draw.arc(surf, (40, 90, 60), (x - s * 0.3, y + s * 0.2, s * 0.6, s * 0.4), math.pi * 1.15, math.pi * 1.85, 3)
    elif kind == "bunny":
        fur, pink, edge = (252, 248, 252), (250, 175, 195), (222, 222, 236)
        pygame.draw.ellipse(surf, fur, (x - s * 0.8, y + s * 0.35, s * 1.6, s * 1.5))
        pygame.draw.ellipse(surf, edge, (x - s * 0.8, y + s * 0.35, s * 1.6, s * 1.5), 3)
        pygame.draw.ellipse(surf, pink, (x - s * 0.4, y + s * 0.65, s * 0.8, s * 0.9))
        for sx in (-1, 1):
            ear = (x + sx * s * 0.45 - s * 0.22, y - s * 1.95, s * 0.44, s * 1.35)
            pygame.draw.ellipse(surf, fur, ear)
            pygame.draw.ellipse(surf, edge, ear, 3)
            pygame.draw.ellipse(surf, pink, (x + sx * s * 0.45 - s * 0.11, y - s * 1.75, s * 0.22, s * 0.9))
        circ(surf, fur, (x, y), s)
        circ(surf, edge, (x, y), s, 3)
        for sx in (-1, 1):
            circ(surf, pink, (x + sx * s * 0.6, y + s * 0.25), s * 0.15)
        _eyes(surf, x, y - s * 0.15, s * 0.4, s * 0.2, blink)
        pygame.draw.polygon(surf, pink, [(x - s * 0.1, y + s * 0.15), (x + s * 0.1, y + s * 0.15), (x, y + s * 0.28)])
        tooth = (x - s * 0.1, y + s * 0.3, s * 0.2, s * (0.3 if open_m else 0.2))
        pygame.draw.rect(surf, WHITE, tooth)
        pygame.draw.rect(surf, edge, tooth, 2)
    elif kind == "turtle":
        green, dark = (150, 205, 120), (70, 140, 85)
        pygame.draw.ellipse(surf, dark, (x - s * 1.05, y + s * 0.25, s * 2.1, s * 1.7))
        for k in (-1, 0, 1):
            pygame.draw.ellipse(surf, shade(dark, 1.3), (x + k * s * 0.55 - s * 0.25, y + s * 0.6, s * 0.5, s * 0.55))
        for sx in (-1, 1):
            pygame.draw.ellipse(surf, green, (x + sx * s * 0.7 - s * 0.25, y + s * 1.65, s * 0.5, s * 0.35))
        circ(surf, green, (x, y), s * 0.95)
        _eyes(surf, x, y - s * 0.15, s * 0.4, s * 0.22, blink)
        for sx in (-1, 1):
            circ(surf, (240, 170, 160), (x + sx * s * 0.62, y + s * 0.25), s * 0.13)
        if open_m:
            pygame.draw.ellipse(surf, (120, 50, 30), (x - s * 0.15, y + s * 0.35, s * 0.3, s * 0.2))
        else:
            pygame.draw.arc(surf, (60, 100, 60), (x - s * 0.3, y + s * 0.1, s * 0.6, s * 0.45), math.pi * 1.15, math.pi * 1.85, 3)
    elif kind == "panda":
        black, edge = (45, 45, 58), (220, 224, 234)
        pygame.draw.ellipse(surf, WHITE, (x - s * 0.85, y + s * 0.35, s * 1.7, s * 1.5))
        pygame.draw.ellipse(surf, edge, (x - s * 0.85, y + s * 0.35, s * 1.7, s * 1.5), 3)
        for sx in (-1, 1):
            pygame.draw.ellipse(surf, black, (x + sx * s * 0.95 - s * 0.25, y + s * 0.5, s * 0.5, s * 0.95))
            circ(surf, black, (x + sx * s * 0.75, y - s * 0.78), s * 0.33)
        circ(surf, WHITE, (x, y), s)
        circ(surf, edge, (x, y), s, 3)
        for sx in (-1, 1):
            ex = x + sx * s * 0.42
            pygame.draw.ellipse(surf, black, (ex - s * 0.24, y - s * 0.5, s * 0.48, s * 0.65))
            if blink:
                pygame.draw.line(surf, WHITE, (ex - s * 0.12, y - s * 0.15), (ex + s * 0.12, y - s * 0.15), 3)
            else:
                circ(surf, WHITE, (ex, y - s * 0.17), s * 0.13)
                circ(surf, INK, (ex, y - s * 0.17), s * 0.07)
        pygame.draw.ellipse(surf, black, (x - s * 0.17, y + s * 0.17, s * 0.34, s * 0.22))
        if open_m:
            pygame.draw.ellipse(surf, (150, 60, 60), (x - s * 0.13, y + s * 0.42, s * 0.26, s * 0.2))
        else:
            pygame.draw.arc(surf, black, (x - s * 0.25, y + s * 0.25, s * 0.5, s * 0.3), math.pi * 1.1, math.pi * 1.9, 3)
    elif kind == "lion":
        tan, mane = (240, 190, 110), (190, 115, 45)
        pygame.draw.ellipse(surf, tan, (x - s * 0.8, y + s * 0.5, s * 1.6, s * 1.5))
        pygame.draw.ellipse(surf, (250, 225, 175), (x - s * 0.4, y + s * 0.75, s * 0.8, s * 1.0))
        circ(surf, mane, (x, y), s * 1.3)
        for sx in (-1, 1):
            circ(surf, tan, (x + sx * s * 0.78, y - s * 0.82), s * 0.28)
        circ(surf, tan, (x, y + s * 0.05), s * 0.92)
        pygame.draw.ellipse(surf, (250, 225, 175), (x - s * 0.45, y + s * 0.1, s * 0.9, s * 0.65))
        _eyes(surf, x, y - s * 0.2, s * 0.4, s * 0.2, blink)
        pygame.draw.polygon(surf, (120, 70, 50), [(x - s * 0.14, y + s * 0.18), (x + s * 0.14, y + s * 0.18), (x, y + s * 0.34)])
        if open_m:
            pygame.draw.ellipse(surf, (120, 50, 30), (x - s * 0.13, y + s * 0.42, s * 0.26, s * 0.2))
        else:
            pygame.draw.line(surf, (120, 70, 50), (x, y + s * 0.34), (x, y + s * 0.45), 3)
    elif kind == "frog":
        green, dark, belly = (110, 200, 100), (60, 150, 70), (225, 245, 200)
        pygame.draw.ellipse(surf, green, (x - s * 0.85, y + s * 0.3, s * 1.7, s * 1.5))
        pygame.draw.ellipse(surf, belly, (x - s * 0.5, y + s * 0.6, s * 1.0, s * 1.0))
        circ(surf, green, (x, y), s)
        for sx in (-1, 1):
            circ(surf, green, (x + sx * s * 0.58, y - s * 0.85), s * 0.4)
            circ(surf, dark, (x + sx * s * 0.58, y - s * 0.85), s * 0.4, 3)
        _eyes(surf, x, y - s * 0.85, s * 0.58, s * 0.26, blink)
        for sx in (-1, 1):
            circ(surf, (245, 160, 160), (x + sx * s * 0.62, y + s * 0.2), s * 0.15)
        if open_m:
            pygame.draw.ellipse(surf, (150, 50, 50), (x - s * 0.4, y + s * 0.15, s * 0.8, s * 0.4))
        else:
            pygame.draw.arc(surf, dark, (x - s * 0.55, y - s * 0.2, s * 1.1, s * 0.7), math.pi * 1.1, math.pi * 1.9, 4)
    elif kind == "elephant":
        grey, dark, pink = (170, 180, 205), (120, 130, 160), (240, 190, 200)
        pygame.draw.ellipse(surf, grey, (x - s * 0.85, y + s * 0.4, s * 1.7, s * 1.5))
        for sx in (-1, 1):
            circ(surf, grey, (x + sx * s * 1.0, y - s * 0.1), s * 0.7)
            circ(surf, pink, (x + sx * s * 1.0, y - s * 0.1), s * 0.45)
        circ(surf, grey, (x, y), s)
        circ(surf, dark, (x, y), s, 3)
        _eyes(surf, x, y - s * 0.2, s * 0.4, s * 0.2, blink)
        pygame.draw.ellipse(surf, grey, (x - s * 0.22, y + s * 0.1, s * 0.44, s * 1.3))
        pygame.draw.ellipse(surf, dark, (x - s * 0.22, y + s * 0.1, s * 0.44, s * 1.3), 3)
        for sx in (-1, 1):
            pygame.draw.polygon(surf, WHITE, [(x + sx * s * 0.45, y + s * 0.3), (x + sx * s * 0.7, y + s * 0.95),
                                              (x + sx * s * 0.3, y + s * 0.75)])
    else:  # robot
        metal, dark = (190, 202, 222), (110, 124, 150)
        pygame.draw.rect(surf, dark, (x - s * 0.7, y + s * 0.5, s * 1.4, s * 1.3), border_radius=int(s * 0.25))
        pygame.draw.rect(surf, (120, 220, 255), (x - s * 0.3, y + s * 0.75, s * 0.6, s * 0.4), border_radius=6)
        pygame.draw.line(surf, dark, (x, y - s * 0.95), (x, y - s * 1.35), 4)
        circ(surf, RED, (x, y - s * 1.4), s * 0.14)
        pygame.draw.rect(surf, metal, (x - s * 0.95, y - s * 0.95, s * 1.9, s * 1.6), border_radius=int(s * 0.35))
        for sx in (-1, 1):
            pygame.draw.rect(surf, dark, (x + sx * s * 1.0 - s * 0.08, y - s * 0.3, s * 0.16, s * 0.5))
            if blink:
                pygame.draw.line(surf, BLUE, (x + sx * s * 0.42 - s * 0.2, y - s * 0.25), (x + sx * s * 0.42 + s * 0.2, y - s * 0.25), 4)
            else:
                pygame.draw.rect(surf, (60, 190, 255), (x + sx * s * 0.42 - s * 0.2, y - s * 0.45, s * 0.4, s * 0.4), border_radius=6)
        pygame.draw.rect(surf, (50, 60, 85), (x - s * 0.4, y + s * 0.15, s * 0.8, (s * 0.28 if open_m else s * 0.14)), border_radius=5)


# --------------------------------------------------------------- UI classes
class Button:
    def __init__(self, rect, label, color=BLUE, cb=None, size=26, arrow=False):
        self.rect = pygame.Rect(rect)
        self.label, self.color, self.cb, self.size, self.arrow = label, color, cb, size, arrow
        self.enabled = True
        self.hover = False
        self.pressed = False

    def handle(self, ev):
        if not self.enabled:
            self.hover = self.pressed = False
            return False
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            self.pressed = True
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            was, self.pressed = self.pressed, False
            if was and self.rect.collidepoint(ev.pos):
                if self.cb:
                    self.cb()
                return True
        return False

    def press(self):
        if self.enabled and self.cb:
            self.cb()

    def draw(self, surf):
        col = self.color if self.enabled else GREY
        if self.hover and self.enabled:
            col = shade(col, 1.1)
        r = self.rect.move(0, 3 if self.pressed else 0)
        pygame.draw.rect(surf, shade(col, 0.68), r.move(0, 5), border_radius=16)
        pygame.draw.rect(surf, col, r, border_radius=16)
        shift = -14 if self.arrow else 0
        text(surf, self.label, self.size, WHITE, (r.centerx + shift, r.centery), "center", bold=True)
        if self.arrow:
            tw = font(self.size, True).size(self.label)[0]
            draw_arrow(surf, (r.centerx + shift + tw // 2 + 20, r.centery), self.size * 0.55)


class Confetti:
    COLORS = [BLUE, GREEN, YELLOW, ORANGE, PURPLE, RED]

    def __init__(self):
        self.p = []

    def burst(self, pos, n=60):
        for _ in range(n):
            a, s = random.uniform(0, math.tau), random.uniform(150, 520)
            self.p.append([pos[0], pos[1], math.cos(a) * s, math.sin(a) * s - 220,
                           random.choice(self.COLORS), random.uniform(0.9, 1.7)])

    def rain(self, n=2):
        for _ in range(n):
            self.p.append([random.uniform(0, W), -10, random.uniform(-40, 40), random.uniform(60, 160),
                           random.choice(self.COLORS), random.uniform(3, 5)])

    def update(self, dt):
        for q in self.p:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += 650 * dt
            q[2] *= 0.992
            q[5] -= dt
        self.p = [q for q in self.p if q[5] > 0 and q[1] < H + 20]

    def draw(self, surf):
        for q in self.p:
            pygame.draw.rect(surf, q[4], (q[0], q[1], 9, 5))


class Audio:
    """Tiny synthesised sound effects (no asset files needed)."""

    def __init__(self):
        self.on = True
        self.sounds: dict = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.sounds = {
                "click": self._tone([(700, 0.04)], 0.18),
                "pop": self._tone([(880, 0.05), (1175, 0.07)], 0.2),
                "good": self._tone([(523, 0.09), (659, 0.09), (784, 0.17)], 0.22),
                "bad": self._tone([(260, 0.12), (190, 0.2)], 0.22),
                "star": self._tone([(988, 0.08), (1319, 0.2)], 0.2),
                "win": self._tone([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.3)], 0.22),
            }
        except (pygame.error, OSError):
            self.sounds = {}

    @staticmethod
    def _tone(notes, vol):
        rate = 22050
        buf = bytearray()
        for freq, dur in notes:
            n = int(rate * dur)
            for i in range(n):
                env = min(1.0, i / 150) * min(1.0, (n - i) / 400)
                buf += struct.pack("<h", int(32767 * vol * env * math.sin(math.tau * freq * i / rate)))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, name):
        if self.on and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.on = not self.on


class Save:
    """Progress is stored locally in a tiny JSON file (no server, no accounts)."""

    def __init__(self):
        n = len(LEVELS)
        self.data = {"stars": [0] * n, "unlocked": 1}
        try:
            with open(SAVE_PATH, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d.get("stars"), list):
                stars = [max(0, min(3, int(v))) for v in d["stars"]]
                unlocked = int(d.get("unlocked", 1))
                if len(stars) in (5, 9, 19, 29, 39) and n > len(stars):
                    # Older save: the old finale moved to the end, new levels start empty.
                    keep = len(stars) - 1
                    stars = stars[:keep] + [0] * (n - keep)
                    unlocked = min(unlocked, keep + 1)
                self.data["stars"] = (stars + [0] * n)[:n]
                self.data["unlocked"] = max(1, min(n, unlocked))
        except (OSError, ValueError, TypeError):
            pass

    def write(self):
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except OSError:
            pass

    def complete(self, idx, stars):
        self.data["stars"][idx] = max(self.data["stars"][idx], stars)
        self.data["unlocked"] = max(self.data["unlocked"], min(idx + 2, len(LEVELS)))
        self.write()

    def reset(self):
        self.data = {"stars": [0] * len(LEVELS), "unlocked": 1}
        self.write()


# ---------------------------------------------------------------- activities
class Activity:
    scored = True

    def __init__(self, game, data, area, color, idx):
        self.g, self.d, self.area, self.color, self.idx = game, data, pygame.Rect(area), color, idx
        self.audio = game.audio
        self.done = False
        self.mistakes = 0
        self.t = 0.0
        self.shake = 0.0
        self.feedback = None
        self.action_label = None
        self.action_enabled = False
        self.hint = data.get("hint", "")

    def handle(self, ev):
        pass

    def update(self, dt):
        self.t += dt
        self.shake = max(0.0, self.shake - dt)

    def draw(self, surf):
        pass

    def on_action(self):
        pass

    def points(self):
        return 3 if self.mistakes == 0 else 2 if self.mistakes == 1 else 1

    def good(self, msg):
        self.feedback = ("Great job! " + msg, "good")
        self.done = True
        self.action_label = None
        self.audio.play("good")

    def bad(self, msg):
        self.mistakes += 1
        self.feedback = (msg, "bad")
        self.shake = 0.4
        self.audio.play("bad")

    def shake_x(self):
        return int(math.sin(self.t * 60) * 9 * (self.shake / 0.4)) if self.shake > 0 else 0


class Story(Activity):
    scored = False

    def __init__(self, *a):
        super().__init__(*a)
        self.done = True

    def draw(self, surf):
        lv = LEVELS[self.idx]
        art = pygame.Rect(self.area.x, self.area.y + 4, 400, 340)
        surf.blit(level_art(self.idx, art.size), art)
        pygame.draw.rect(surf, WHITE, art, 5, border_radius=22)
        card = pygame.Rect(art.right + 28, art.y, self.area.right - art.right - 28, art.h)
        panel(surf, card, WHITE, 22)
        text(surf, "MISSION", 22, self.color, (card.x + 28, card.y + 22), bold=True)
        text(surf, lv["topic"], 28, INK, (card.x + 28, card.y + 50), bold=True)
        y = card.y + 108
        for line in lv["story"]:
            y = paragraph(surf, line, 25, INK, pygame.Rect(card.x + 28, y, card.w - 56, 200)) + 12


class Lesson(Activity):
    """Study card: three key facts and a golden rule, shown before the questions."""
    scored = False

    def __init__(self, *a):
        super().__init__(*a)
        self.done = True

    def draw(self, surf):
        lv = LEVELS[self.idx]
        les = lv["lesson"]
        card = pygame.Rect(self.area.x, self.area.y + 4, self.area.w, self.area.h - 8)
        panel(surf, card, WHITE, 22)
        text(surf, "STUDY TIME", 22, self.color, (card.x + 30, card.y + 20), bold=True)
        text(surf, lv["topic"], 30, INK, (card.x + 30, card.y + 46), bold=True)
        thumb = pygame.Rect(card.right - 160, card.y + 14, 130, 92)
        surf.blit(level_art(self.idx, thumb.size), thumb)
        pygame.draw.rect(surf, self.color, thumb, 4, border_radius=14)
        y = card.y + 112
        for n, fact in enumerate(les["facts"], 1):
            circ(surf, self.color, (card.x + 52, y + 22), 20)
            text(surf, str(n), 24, WHITE, (card.x + 52, y + 22), "center", bold=True)
            end = paragraph(surf, fact, 25, INK, pygame.Rect(card.x + 88, y + 4, card.w - 130, 60))
            y = max(y + 56, end + 8)
        rule = pygame.Rect(card.x + 24, card.bottom - 78, card.w - 48, 58)
        pygame.draw.rect(surf, self.color, rule, border_radius=16)
        draw_star(surf, (rule.x + 34, rule.centery), 16, True)
        text(surf, "Golden rule", 17, WHITE, (rule.x + 64, rule.y + 8), bold=True)
        paragraph(surf, les["rule"], 24, WHITE, pygame.Rect(rule.x + 64, rule.y + 28, rule.w - 90, 30), bold=True)


class Quiz(Activity):
    def __init__(self, *a):
        super().__init__(*a)
        d, area = self.d, self.area
        self.multi = d.get("multi", False)
        self.opts = d["opts"]
        self.ans = set(d["ans"])
        self.sel, self.locked = set(), set()
        y = area.y + len(wrap(d["q"], 30, area.w, True)) * (font(30, True).get_linesize() + 2) + 10
        self.msg_rect = None
        if d.get("msg"):
            mh = len(wrap(d["msg"], 24, area.w - 64)) * font(24).get_linesize() + 30
            self.msg_rect = pygame.Rect(area.x, y, area.w, mh)
            y += mh + 14
        n = len(self.opts)
        cols = 2 if n == 4 else 1
        rows = math.ceil(n / cols)
        gap = 12
        oh = min(74, (area.bottom - y - gap * (rows - 1)) // rows)
        ow = (area.w - gap * (cols - 1)) // cols
        self.rects = [pygame.Rect(area.x + (i % cols) * (ow + gap), y + (i // cols) * (oh + gap), ow, oh)
                      for i in range(n)]
        if self.multi:
            self.action_label = "Check"

    def handle(self, ev):
        if self.done:
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(ev.pos) and i not in self.locked:
                    self.choose(i)
                    break
        elif ev.type == pygame.KEYDOWN and pygame.K_1 <= ev.key <= pygame.K_9:
            i = ev.key - pygame.K_1
            if i < len(self.opts) and i not in self.locked:
                self.choose(i)

    def choose(self, i):
        self.audio.play("click")
        if self.multi:
            self.sel ^= {i}
            self.action_enabled = bool(self.sel)
        else:
            self.sel = {i}
            self.submit()

    def on_action(self):
        if self.multi and self.sel and not self.done:
            self.submit()

    def submit(self):
        if self.sel == self.ans:
            self.good(self.d["why"])
            return
        if self.multi:
            msg = f"Not quite. There are {len(self.ans)} right answers. Try again!"
        else:
            self.locked |= self.sel
            msg = "Not quite. Try another answer!"
        self.sel = set()
        self.action_enabled = False
        self.bad(msg)

    def draw(self, surf):
        paragraph(surf, self.d["q"], 30, INK, self.area, True, 2)
        if self.msg_rect:
            panel(surf, self.msg_rect, (244, 247, 252), 12, shadow=False)
            pygame.draw.rect(surf, self.color, (self.msg_rect.x, self.msg_rect.y, 8, self.msg_rect.h),
                             border_top_left_radius=12, border_bottom_left_radius=12)
            paragraph(surf, self.d["msg"], 24, INK, self.msg_rect.inflate(-48, -22).move(12, 0))
        sx = self.shake_x()
        mouse = self.g.mouse
        for i, r in enumerate(self.rects):
            rr = r.move(sx, 0)
            right = i in self.ans
            if self.done:
                fill, border = ((228, 247, 236), GOOD) if right else ((246, 248, 252), (222, 228, 238))
            elif i in self.sel:
                fill, border = (228, 240, 255), BLUE
            elif i in self.locked:
                fill, border = (253, 232, 232), RED
            else:
                fill, border = WHITE, (BLUE if rr.collidepoint(mouse) else (200, 212, 232))
            panel(surf, rr, fill, 14, border, shadow=not self.done)
            badge = (rr.x + 36, rr.centery)
            circ(surf, border if (right and self.done) or i in self.sel or i in self.locked else (214, 222, 236), badge, 19)
            text(surf, str(i + 1), 22, WHITE, badge, "center", bold=True)
            dim = self.done and not right
            paragraph(surf, self.opts[i], 25, GREY if dim else INK,
                      pygame.Rect(rr.x + 72, rr.y + max(6, (rr.h - 30 * len(wrap(self.opts[i], 25, rr.w - 130))) // 2),
                                  rr.w - 130, rr.h))
            if self.done and right:
                draw_check(surf, (rr.right - 34, rr.centery), 24, GOOD, 6)
            elif i in self.locked:
                draw_cross(surf, (rr.right - 34, rr.centery), 24, RED, 6)


class Sorter(Activity):
    def __init__(self, *a):
        super().__init__(*a)
        d, area = self.d, self.area
        self.bins = [(lab, NAMED[c]) for lab, c in d["bins"]]
        n, gap = len(self.bins), 20
        bw = (area.w - gap * (n - 1)) // n
        self.bin_rects = [pygame.Rect(area.x + i * (bw + gap), area.bottom - 165, bw, 155) for i in range(n)]
        self.placed = [[] for _ in self.bins]
        self.flash = [(0.0, GOOD)] * n
        f = font(22, True)
        sized = [(t, b, f.size(t)[0] + 38) for t, b in d["items"]]
        rows, cur, cw = [], [], 0
        for item in sized:
            if cur and cw + item[2] + 14 > area.w:
                rows.append(cur)
                cur, cw = [], 0
            cur.append(item)
            cw += item[2] + 14
        rows.append(cur)
        ch, rgap = (54, 14) if len(rows) <= 2 else (44, 10)
        y = area.y + 62
        self.cards = []
        for row in rows:
            total = sum(w for _, _, w in row) + 14 * (len(row) - 1)
            x = area.centerx - total // 2
            for t, b, w in row:
                home = (x, y)
                self.cards.append({"text": t, "bin": b, "home": home, "pos": [float(x), float(y)],
                                   "size": (w, ch), "placed": False, "wob": 0.0})
                x += w + 14
            y += ch + rgap
        self.drag = None
        self.off = (0, 0)
        self.moved = False
        self.down = (0, 0)
        self.selected = None

    @staticmethod
    def rect(c):
        return pygame.Rect(int(c["pos"][0]), int(c["pos"][1]), *c["size"])

    def bin_at(self, pos):
        for i, r in enumerate(self.bin_rects):
            if r.collidepoint(pos):
                return i
        return None

    def handle(self, ev):
        if self.done:
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            b = self.bin_at(ev.pos)
            if self.selected and b is not None:
                c, self.selected = self.selected, None
                self.drop(c, b)
                return
            for c in reversed(self.cards):
                if not c["placed"] and self.rect(c).collidepoint(ev.pos):
                    self.drag, self.moved, self.down = c, False, ev.pos
                    self.off = (ev.pos[0] - c["pos"][0], ev.pos[1] - c["pos"][1])
                    self.cards.remove(c)
                    self.cards.append(c)
                    break
        elif ev.type == pygame.MOUSEMOTION and self.drag:
            if math.dist(ev.pos, self.down) > 6:
                self.moved = True
            if self.moved:
                self.drag["pos"] = [ev.pos[0] - self.off[0], ev.pos[1] - self.off[1]]
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.drag:
            c, self.drag = self.drag, None
            if not self.moved:
                self.selected = None if self.selected is c else c
                self.audio.play("click")
                return
            b = self.bin_at(ev.pos)
            if b is None:
                return
            self.drop(c, b)

    def drop(self, c, b):
        if c["bin"] == b:
            c["placed"] = True
            self.placed[b].append(c["text"])
            self.flash[b] = (0.5, GOOD)
            if all(k["placed"] for k in self.cards):
                self.good(self.d["why"])
            else:
                self.feedback = ("Yes! That goes in " + self.bins[b][0] + ".", "good")
                self.audio.play("pop")
        else:
            c["wob"] = 0.4
            self.flash[b] = (0.5, RED)
            self.bad("Hmm, not that box. Think again!")

    def update(self, dt):
        super().update(dt)
        for c in self.cards:
            c["wob"] = max(0.0, c["wob"] - dt)
            if c is not self.drag and not c["placed"]:
                k = min(1.0, dt * 14)
                c["pos"][0] += (c["home"][0] - c["pos"][0]) * k
                c["pos"][1] += (c["home"][1] - c["pos"][1]) * k
        self.flash = [(max(0.0, t - dt), col) for t, col in self.flash]

    def draw(self, surf):
        paragraph(surf, self.d["prompt"], 30, INK, self.area, True)
        hover = self.bin_at(self.g.mouse) if (self.drag and self.moved) or self.selected else None
        for i, (r, (lab, col)) in enumerate(zip(self.bin_rects, self.bins)):
            panel(surf, r, mix(col, WHITE, 0.88), 18, col, bw=6 if hover == i else 3)
            text(surf, lab, 26, col, (r.centerx, r.y + 12), "midtop", bold=True)
            colw = (r.w - 30) // 2
            for k, t in enumerate(self.placed[i]):
                tx = r.x + 16 + (k % 2) * colw
                ty = r.y + 50 + (k // 2) * 28
                draw_check(surf, (tx + 8, ty + 12), 14, col, 3)
                text(surf, t, 19, INK, (tx + 22, ty), bold=True)
            tf, fcol = self.flash[i]
            if tf > 0:
                ov = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(ov, fcol + (int(110 * tf / 0.5),), ov.get_rect(), border_radius=18)
                surf.blit(ov, r)
        for c in self.cards:
            if c["placed"]:
                continue
            r = self.rect(c)
            if c["wob"] > 0:
                r.x += int(math.sin(self.t * 60) * 8 * c["wob"] / 0.4)
            lifted = c is self.drag and self.moved
            if lifted:
                r.y -= 4
            border = BLUE if (c is self.selected or lifted) else (200, 212, 232)
            panel(surf, r, WHITE, 14, border, shadow=True, bw=4 if c is self.selected else 3)
            text(surf, c["text"], 22, INK, r.center, "center", bold=True)


class Hunt(Activity):
    """Tap the warning signs hidden inside a fake message."""

    def __init__(self, *a):
        super().__init__(*a)
        area = self.area
        self.card = pygame.Rect(area.x, area.y + 62, 610, area.h - 70)
        self.side = pygame.Rect(self.card.right + 22, self.card.y, area.right - self.card.right - 22, self.card.h)
        f = font(26)
        lh = f.get_linesize() + 8
        x0, right = self.card.x + 26, self.card.right - 26
        y = self.card.y + 24
        self.segs = []
        for line in self.d["lines"]:
            x = x0
            for txt, flag in line:
                seg = {"flag": flag, "rects": [], "found": False}
                self.segs.append(seg)
                x += f.size(" ")[0] * (len(txt) - len(txt.lstrip(" ")))
                for token in re.findall(r"\S+\s*", txt):
                    word = token.rstrip()
                    ww = f.size(word)[0]
                    if x + ww > right and x > x0:
                        x, y = x0, y + lh
                    seg["rects"].append(pygame.Rect(x, y, ww, lh - 4))
                    x += f.size(token)[0]
            y += lh + 8
        self.total = sum(1 for s in self.segs if s["flag"])
        self.found = []

    def handle(self, ev):
        if self.done or ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        for seg in self.segs:
            if any(r.inflate(8, 4).collidepoint(ev.pos) for r in seg["rects"]):
                if seg["flag"] and not seg["found"]:
                    seg["found"] = True
                    self.found.append(seg["flag"])
                    if len(self.found) == self.total:
                        self.good(self.d["why"])
                    else:
                        self.feedback = (f"Found one! {self.total - len(self.found)} more to go.", "good")
                        self.audio.play("pop")
                elif not seg["flag"]:
                    self.bad("That part looks OK. Look for sneaky words!")
                return

    def draw(self, surf):
        paragraph(surf, self.d["prompt"], 30, INK, self.area, True)
        panel(surf, self.card, WHITE, 18)
        pygame.draw.rect(surf, self.color, (self.card.x, self.card.y, 10, self.card.h),
                         border_top_left_radius=18, border_bottom_left_radius=18)
        sx = self.shake_x()
        f = font(26)
        mouse = self.g.mouse
        for seg in self.segs:
            for r in seg["rects"]:
                rr = r.move(sx, 0)
                if seg["found"]:
                    pygame.draw.rect(surf, (255, 226, 130), rr.inflate(8, 2), border_radius=6)
                    pygame.draw.line(surf, RED, rr.bottomleft, rr.bottomright, 3)
                elif rr.inflate(8, 4).collidepoint(mouse) and not self.done:
                    pygame.draw.line(surf, BLUE, (rr.x, rr.bottom), (rr.right, rr.bottom), 3)
        for seg, (_, txt) in zip(self.segs, self._seg_texts()):
            for r, token in zip(seg["rects"], re.findall(r"\S+\s*", txt)):
                text(surf, token.rstrip(), 26, INK, r.move(sx, 0).topleft)
        side = self.side
        panel(surf, side, (255, 250, 238), 18, ORANGE)
        text(surf, "Red flags", 26, ORANGE, (side.x + 20, side.y + 14), bold=True)
        text(surf, f"{len(self.found)} / {self.total}", 26, INK, (side.right - 20, side.y + 14), "topright", bold=True)
        y = side.y + 58
        for i in range(self.total):
            if i < len(self.found):
                pygame.draw.polygon(surf, RED, [(side.x + 22, y + 2), (side.x + 22, y + 24), (side.x + 24, y + 24),
                                                (side.x + 24, y + 14), (side.x + 38, y + 8), (side.x + 24, y + 2)])
                y = paragraph(surf, self.found[i], 21, INK, pygame.Rect(side.x + 46, y, side.w - 62, 80)) + 8
            else:
                text(surf, "?", 24, GREY, (side.x + 24, y), bold=True)
                pygame.draw.line(surf, (225, 225, 232), (side.x + 46, y + 14), (side.right - 20, y + 14), 3)
                y += 36

    def _seg_texts(self):
        out = []
        for line in self.d["lines"]:
            for txt, flag in line:
                out.append((flag, txt))
        return out


class Builder(Activity):
    MAX_TILES = 6

    def __init__(self, *a):
        super().__init__(*a)
        area, d = self.area, self.d
        self.bad_tiles = set(d["bad"])
        self.chosen = []
        self.pw_rect = pygame.Rect(area.x, area.y + 58, area.w - 150, 64)
        self.clear_rect = pygame.Rect(self.pw_rect.right + 16, self.pw_rect.y, 134, 64)
        self.meter_rect = pygame.Rect(area.x + 130, area.y + 142, 560, 26)
        f = font(26, True)
        x, y = area.x, area.y + 196
        self.tiles = []
        for t in d["tiles"]:
            w = max(80, f.size(t)[0] + 40)
            if x + w > area.right:
                x, y = area.x, y + 62
            self.tiles.append((t, pygame.Rect(x, y, w, 50)))
            x += w + 14
        self.level = 0.0
        self.action_label = "Lock it in"

    def pw(self):
        return "".join(self.chosen)

    def score(self):
        pw, s = self.pw(), 0
        if len(pw) >= 12:
            s += 2
        elif len(pw) >= 8:
            s += 1
        if any(c.isupper() for c in pw):
            s += 1
        if any(c.isdigit() for c in pw):
            s += 1
        if any(not c.isalnum() for c in pw):
            s += 1
        if any(t in self.bad_tiles for t in self.chosen):
            s -= 2
        return max(0, min(5, s)) if pw else 0

    def toggle(self, t):
        if t in self.chosen:
            self.chosen.remove(t)
        elif len(self.chosen) < self.MAX_TILES:
            self.chosen.append(t)
        else:
            return
        self.audio.play("click")
        self.action_enabled = bool(self.chosen)

    def handle(self, ev):
        if self.done:
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.clear_rect.collidepoint(ev.pos):
                self.chosen.clear()
                self.action_enabled = False
                self.audio.play("click")
                return
            for t, r in self.tiles:
                if r.collidepoint(ev.pos):
                    self.toggle(t)
                    return
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_BACKSPACE and self.chosen:
            self.chosen.pop()
            self.action_enabled = bool(self.chosen)

    def on_action(self):
        if not self.chosen or self.done:
            return
        if self.score() >= 4:
            self.good(self.d["why"])
        else:
            if len(self.pw()) < 8:
                tip = "Not strong yet. Make it longer!"
            elif any(t in self.bad_tiles for t in self.chosen):
                tip = "Easy tiles like that are simple to guess. Swap them out!"
            else:
                tip = "Almost! Mix in capital letters, numbers and symbols."
            self.bad(tip)

    def update(self, dt):
        super().update(dt)
        self.level += (self.score() - self.level) * min(1.0, dt * 8)

    def draw(self, surf):
        paragraph(surf, self.d["prompt"], 30, INK, self.area, True)
        pr = self.pw_rect.move(self.shake_x(), 0)
        panel(surf, pr, WHITE, 16, self.color)
        if self.chosen:
            text(surf, self.pw(), 40, INK, pr.center, "center", bold=True)
        else:
            text(surf, "Tap the tiles below...", 28, GREY, pr.center, "center")
        panel(surf, self.clear_rect, (255, 240, 240), 16, RED, shadow=False)
        text(surf, "Clear", 26, RED, self.clear_rect.center, "center", bold=True)
        text(surf, "Strength", 24, INK, (self.area.x, self.meter_rect.y), bold=True)
        pygame.draw.rect(surf, (226, 232, 242), self.meter_rect, border_radius=13)
        frac = self.level / 5
        if frac > 0.01:
            col = RED if self.level < 2 else YELLOW if self.level < 3.5 else GOOD
            pygame.draw.rect(surf, col, (self.meter_rect.x, self.meter_rect.y, max(26, int(self.meter_rect.w * frac)),
                                         self.meter_rect.h), border_radius=13)
        sc = self.score()
        label = "Strong!" if sc >= 4 else "Almost..." if sc >= 2 else "Weak"
        text(surf, label if self.chosen else "-", 26, INK, (self.meter_rect.right + 18, self.meter_rect.y - 2), bold=True)
        mouse = self.g.mouse
        for t, r in self.tiles:
            used = t in self.chosen
            border = self.color if used else (BLUE if r.collidepoint(mouse) else (200, 212, 232))
            panel(surf, r, mix(self.color, WHITE, 0.82) if used else WHITE, 14, border, shadow=not used)
            text(surf, t, 26, INK, r.center, "center", bold=True)


ACTIVITY_CLASSES = {"story": Story, "lesson": Lesson, "quiz": Quiz, "sort": Sorter, "hunt": Hunt, "builder": Builder}
DEFAULT_HINTS = {"quiz": "Pick the best answer!", "sort": "Drag each card into the right box.",
                 "hunt": "Tap the sneaky words.", "builder": "Tap tiles to build your password.",
                 "story": "Ready for an adventure?", "lesson": "Read this first. It helps with the questions!"}


# ------------------------------------------------------------------- scenes
class Scene:
    def __init__(self, game):
        self.g = game
        self.t = 0.0
        self.confetti = Confetti()

    def handle(self, ev):
        pass

    def update(self, dt):
        self.t += dt
        self.confetti.update(dt)

    def draw(self, surf):
        pass


class TitleScene(Scene):
    def __init__(self, g):
        super().__init__(g)
        has = any(g.save.data["stars"])
        self.b_play = Button((410, 395, 280, 72), "Continue" if has else "Play", GREEN, self.play, 36)
        self.b_sound = Button((410, 485, 280, 56), "", BLUE, self.toggle_sound, 24)
        self.b_quit = Button((410, 560, 280, 56), "Quit", RED, self.quit, 24)
        self.b_reset = Button((940, 646, 130, 38), "Reset", GREY, self.reset, 18)
        self.reset_armed = False
        self.buttons = [self.b_play, self.b_sound, self.b_quit, self.b_reset]
        self.sync()

    def sync(self):
        self.b_sound.label = "Sound: " + ("On" if self.g.audio.on else "Off")
        self.b_reset.label = "Sure?" if self.reset_armed else "Reset"
        self.b_reset.color = RED if self.reset_armed else GREY

    def play(self):
        self.g.audio.play("click")
        self.g.go(MapScene(self.g))

    def toggle_sound(self):
        self.g.audio.toggle()
        self.g.audio.play("click")
        self.sync()

    def quit(self):
        self.g.running = False

    def reset(self):
        if self.reset_armed:
            self.g.save.reset()
            self.g.go(TitleScene(self.g))
        else:
            self.reset_armed = True
            self.sync()

    def handle(self, ev):
        for b in self.buttons:
            b.handle(ev)
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.play()

    def draw(self, surf):
        sky(surf, self.t, hills=(110, 200, 130))
        bob = math.sin(self.t * 2) * 6
        draw_shield(surf, (W // 2, 112 + bob), 62, BLUE)
        text(surf, "CyberQuest", 92, WHITE, (W // 2, 215), "center", bold=True, shadow=(30, 70, 140))
        panel(surf, (W // 2 - 95, 262, 190, 56), ORANGE, 28, shadow=True)
        text(surf, "KIDS", 40, WHITE, (W // 2, 291), "center", bold=True)
        text(surf, "Learn to stay safe online. Ages 6-11", 26, INK, (W // 2, 352), "center", bold=True)
        for kind, x, y, s in (("owl", 170, 520, 62), ("fox", 315, 560, 52), ("bear", 790, 560, 52), ("robot", 935, 520, 58)):
            draw_guide(surf, kind, (x, y), s, self.t + x, talking=False)
        for b in self.buttons:
            b.draw(surf)
        text(surf, "Enter = play   M = mute   F11 = fullscreen", 18, INK, (24, H - 30))


PER_PAGE = 10  # levels shown per map page (two rows of five)


def map_nodes(n):
    """Snake layout: 5 levels per row, rows alternate direction."""
    nodes = []
    for i in range(n):
        row, col = divmod(i, 5)
        if row % 2:
            col = 4 - col
        nodes.append((130 + 215 * col, 185 + 195 * row + (22 if col % 2 else 0)))
    return nodes


class MapScene(Scene):
    def __init__(self, g):
        super().__init__(g)
        d = g.save.data
        self.unlocked = d["unlocked"]
        self.sel = min(self.unlocked - 1, next((i for i, s in enumerate(d["stars"]) if s == 0), len(LEVELS) - 1))
        self.pages = max(1, math.ceil(len(LEVELS) / PER_PAGE))
        self.page = self.sel // PER_PAGE
        self.b_back = Button((20, 16, 120, 46), "Menu", GREY, lambda: g.go(TitleScene(g)), 22)
        self.b_prev = Button((930, 560, 56, 52), "<", BLUE, lambda: self.turn(-1), 30)
        self.b_next = Button((996, 560, 56, 52), ">", BLUE, lambda: self.turn(1), 30)

    def level_range(self):
        lo = self.page * PER_PAGE
        return range(lo, min(len(LEVELS), lo + PER_PAGE))

    @property
    def nodes(self):
        return map_nodes(len(self.level_range()))

    def turn(self, step):
        new = max(0, min(self.pages - 1, self.page + step))
        if new != self.page:
            self.page = new
            self.sel = new * PER_PAGE
            self.g.audio.play("click")

    def hit(self, pos):
        for k, n in enumerate(self.nodes):
            if math.dist(pos, n) <= 54:
                return self.page * PER_PAGE + k
        return None

    def start(self, i):
        if i < self.unlocked:
            self.g.audio.play("click")
            self.g.go(PlayScene(self.g, i))
        else:
            self.g.audio.play("bad")

    def handle(self, ev):
        self.b_back.handle(ev)
        if self.pages > 1:
            self.b_prev.enabled = self.page > 0
            self.b_next.enabled = self.page < self.pages - 1
            self.b_prev.handle(ev)
            self.b_next.handle(ev)
        if ev.type == pygame.MOUSEMOTION:
            h = self.hit(ev.pos)
            if h is not None:
                self.sel = h
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            h = self.hit(ev.pos)
            if h is not None:
                self.start(h)
        elif ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = min(len(LEVELS) - 1, self.sel + 1)
                self.page = self.sel // PER_PAGE
            elif ev.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = max(0, self.sel - 1)
                self.page = self.sel // PER_PAGE
            elif ev.key == pygame.K_PAGEDOWN:
                self.turn(1)
            elif ev.key == pygame.K_PAGEUP:
                self.turn(-1)
            elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start(self.sel)
            elif ev.key == pygame.K_ESCAPE:
                self.g.go(TitleScene(self.g))

    def draw(self, surf):
        sky(surf, self.t, hills=(120, 205, 135))
        text(surf, "Choose your adventure", 46, WHITE, (W // 2, 70), "center", bold=True, shadow=(30, 70, 140))
        if self.pages > 1:
            text(surf, f"World {self.page + 1} of {self.pages}", 22, INK, (W // 2, 112), "center", bold=True)
        pts = self.nodes
        pygame.draw.lines(surf, (236, 210, 150), False, pts, 26)
        for p in pts:
            circ(surf, (236, 210, 150), p, 13)
        for a, b in zip(pts, pts[1:]):
            d = math.dist(a, b)
            for k in range(0, int(d), 28):
                f = k / d
                circ(surf, WHITE, (lerp(a[0], b[0], f), lerp(a[1], b[1], f)), 4)
        stars = self.g.save.data["stars"]
        for i, n in zip(self.level_range(), pts):
            lv = LEVELS[i]
            col = LEVEL_COLORS[i]
            locked = i >= self.unlocked
            sel = i == self.sel
            r = 46 + (6 if sel else 0)
            if not locked and stars[i] == 0 and i == self.sel:
                circ(surf, WHITE, n, r + 10 + math.sin(self.t * 5) * 4, 4)
            circ(surf, (150, 170, 150), (n[0], n[1] + 7), r)
            circ(surf, GREY if locked else col, n, r)
            circ(surf, WHITE, n, r - 7, 4)
            if locked:
                draw_lock(surf, (n[0], n[1] - 4), 20, (120, 135, 160))
            else:
                text(surf, str(i + 1), 44, WHITE, n, "center", bold=True)
            lab = pygame.Rect(0, 0, 200, 56)
            lab.midtop = (n[0], n[1] + r + 8)
            panel(surf, lab, WHITE, 14, shadow=True)
            text(surf, lv["name"], 21, INK, (lab.centerx, lab.y + 16), "center", bold=True)
            for k in range(3):
                draw_star(surf, (lab.centerx - 22 + k * 22, lab.y + 40), 9, k < stars[i])
        lv = LEVELS[self.sel]
        draw_guide(surf, lv["guide"], (95, 590), 40, self.t, talking=False)
        bub = pygame.Rect(150, 548, 760, 74)
        panel(surf, bub, WHITE, 18)
        pygame.draw.polygon(surf, WHITE, [(150, 575), (132, 590), (150, 600)])
        text(surf, f"{self.sel + 1}. {lv['name']}", 26, INK, (172, 560), bold=True)
        if self.sel < self.unlocked:
            text(surf, lv["topic"], 22, BLUE, (172, 594))
        else:
            text(surf, "Finish the previous level to unlock this one!", 22, GREY, (172, 594))
        self.b_back.draw(surf)
        if self.pages > 1:
            self.b_prev.draw(surf)
            self.b_next.draw(surf)


class PlayScene(Scene):
    AREA = pygame.Rect(60, 202, 980, 408)

    def __init__(self, g, idx):
        super().__init__(g)
        self.idx = idx
        self.level = LEVELS[idx]
        self.color = LEVEL_COLORS[idx]
        self.step = 0
        self.points = 0
        self.max_points = 0
        self.btn = Button((850, 628, 190, 58), "Next", GREEN, self.on_btn, 28, arrow=True)
        self.b_map = Button((20, 10, 110, 44), "Map", GREY, self.to_map, 22)
        self.shown = None
        self.lines = []
        self.chars = 0.0
        self.celebrated = False
        self.start_activity()

    def to_map(self):
        self.g.go(MapScene(self.g))

    def start_activity(self):
        data = dict(self.level["activities"][self.step])
        data.setdefault("hint", DEFAULT_HINTS[data["kind"]])
        self.act = ACTIVITY_CLASSES[data["kind"]](self.g, data, self.AREA, self.color, self.idx)
        self.celebrated = False
        self.shown = None

    def on_btn(self):
        if self.act.done:
            self.advance()
        elif self.act.action_label and self.act.action_enabled:
            self.act.on_action()

    def advance(self):
        if self.act.scored:
            self.points += self.act.points()
            self.max_points += 3
        self.g.audio.play("click")
        self.step += 1
        if self.step >= len(self.level["activities"]):
            self.finish()
        else:
            self.start_activity()

    def finish(self):
        ratio = self.points / self.max_points if self.max_points else 1.0
        stars = 3 if ratio >= 0.8 else 2 if ratio >= 0.6 else 1
        g = self.g
        g.save.complete(self.idx, stars)
        g.total_points += self.points
        g.total_max += self.max_points
        g.go(CheckpointScene(g, self.idx, stars, self.points, self.max_points))

    def handle(self, ev):
        self.b_map.handle(ev)
        if self.btn_visible():
            self.btn.handle(ev)
        self.act.handle(ev)
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RETURN, pygame.K_SPACE) and self.btn_visible():
                self.btn.press()
            elif ev.key == pygame.K_ESCAPE:
                self.to_map()

    def btn_visible(self):
        return self.act.done or bool(self.act.action_label)

    def update(self, dt):
        super().update(dt)
        a = self.act
        a.update(dt)
        if a.done:
            self.btn.label = "Finish" if self.step == len(self.level["activities"]) - 1 else "Next"
            self.btn.color, self.btn.enabled, self.btn.arrow = GREEN, True, True
            if a.scored and not self.celebrated:
                self.celebrated = True
                self.confetti.burst((self.AREA.centerx, self.AREA.centery), 45)
        elif a.action_label:
            self.btn.label, self.btn.color, self.btn.enabled = a.action_label, BLUE, a.action_enabled
            self.btn.arrow = False
        msg, kind = (a.feedback if a.feedback else (a.hint, None))
        if msg != self.shown:
            self.shown = msg
            self.lines = wrap(msg, 26, 790, kind is not None)
            self.chars = 0.0
        self.chars += dt * 95

    def draw(self, surf):
        col = self.color
        sky(surf, self.t, mix(col, WHITE, 0.55), mix(col, WHITE, 0.92))
        pygame.draw.rect(surf, WHITE, (0, 0, W, 64))
        pygame.draw.rect(surf, col, (0, 62, W, 4))
        self.b_map.draw(surf)
        text(surf, f"Level {self.idx + 1}: {self.level['name']}", 28, INK, (W // 2, 32), "center", bold=True)
        draw_star(surf, (W - 150, 32), 17)
        text(surf, str(self.g.total_points + self.points), 30, INK, (W - 120, 32), "midleft", bold=True)
        # guide + bubble
        msg, kind = (self.act.feedback if self.act.feedback else (self.act.hint, None))
        talking = self.chars < len(msg)
        draw_guide(surf, self.level["guide"], (100, 140), 40, self.t, talking)
        bub = pygame.Rect(180, 80, 860, 108)
        border = GOOD if kind == "good" else RED if kind == "bad" else col
        panel(surf, bub, WHITE, 20, border)
        pygame.draw.polygon(surf, WHITE, [(bub.x + 2, 118), (bub.x - 18, 140), (bub.x + 2, 152)])
        pygame.draw.lines(surf, border, False, [(bub.x + 2, 118), (bub.x - 18, 140), (bub.x + 2, 152)], 3)
        remaining = int(self.chars)
        y = bub.y + 14
        f = font(26, kind is not None)
        for line in self.lines[:3]:
            surf.blit(f.render(line[:max(0, remaining)], True, GOOD if kind == "good" else RED if kind == "bad" else INK), (bub.x + 22, y))
            remaining -= len(line)
            y += f.get_linesize() + 2
        # activity
        self.act.draw(surf)
        # bottom bar
        pygame.draw.rect(surf, WHITE, (0, 620, W, 80))
        pygame.draw.rect(surf, col, (0, 618, W, 4))
        n = len(self.level["activities"])
        for i in range(n):
            x, yy = 70 + i * 42, 660
            if i < self.step:
                circ(surf, GOOD, (x, yy), 13)
                draw_check(surf, (x, yy), 12, WHITE, 3)
            elif i == self.step:
                circ(surf, col, (x, yy), 15)
                circ(surf, WHITE, (x, yy), 6)
            else:
                circ(surf, (214, 222, 236), (x, yy), 11)
        if self.btn_visible():
            self.btn.draw(surf)
        self.confetti.draw(surf)


class CheckpointScene(Scene):
    def __init__(self, g, idx, stars, pts, mx):
        super().__init__(g)
        self.idx, self.stars, self.pts, self.mx = idx, stars, pts, mx
        self.last = idx == len(LEVELS) - 1
        self.color = LEVEL_COLORS[idx]
        self.b_next = Button((560, 540, 270, 62), "See results" if self.last else "Next level", GREEN, self.next, 28, arrow=True)
        self.b_map = Button((290, 540, 240, 62), "Map", BLUE, lambda: g.go(MapScene(g)), 28)
        self.star_shown = 0
        g.audio.play("win")
        self.confetti.burst((W // 2, 260), 90)

    def next(self):
        self.g.audio.play("click")
        if self.last:
            self.g.go(FinalScene(self.g))
        else:
            self.g.go(PlayScene(self.g, self.idx + 1))

    def handle(self, ev):
        self.b_next.handle(ev)
        self.b_map.handle(ev)
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.next()

    def update(self, dt):
        super().update(dt)
        while self.star_shown < self.stars and self.t > 0.7 + 0.45 * self.star_shown:
            self.star_shown += 1
            self.g.audio.play("star")
            self.confetti.burst((W // 2 + (self.star_shown - 2) * 120, 330), 25)

    def draw(self, surf):
        col = self.color
        sky(surf, self.t, mix(col, WHITE, 0.5), mix(col, WHITE, 0.9), hills=mix(col, (110, 200, 130), 0.5))
        card = pygame.Rect(170, 60, 760, 560)
        panel(surf, card, WHITE, 28)
        pygame.draw.rect(surf, col, (card.x, card.y, card.w, 92), border_top_left_radius=28, border_top_right_radius=28)
        text(surf, "Checkpoint reached!", 44, WHITE, (card.centerx, card.y + 46), "center", bold=True)
        text(surf, LEVELS[self.idx]["name"] + " complete", 30, INK, (card.centerx, card.y + 128), "center", bold=True)
        for i in range(3):
            c = (card.centerx + (i - 1) * 130, 280)
            if i < self.star_shown:
                k = min(1.0, (self.t - (0.7 + 0.45 * i)) * 4)
                draw_star(surf, c, 58 * (0.4 + 0.6 * k + 0.2 * math.sin(k * math.pi)), True, -math.pi / 2 + (1 - k) * 0.8)
            else:
                draw_star(surf, c, 50, False)
        acc = int(100 * self.pts / self.mx) if self.mx else 100
        text(surf, f"Points earned: {self.pts} / {self.mx}", 28, INK, (card.centerx, 380), "center", bold=True)
        text(surf, f"First-try accuracy: {acc}%", 28, INK, (card.centerx, 418), "center", bold=True)
        nxt = LEVELS[self.idx + 1]["name"] if not self.last else None
        msg = "You are ready for the final quest!" if self.last else f"Next stop: {nxt}"
        text(surf, msg, 26, col, (card.centerx, 470), "center", bold=True)
        draw_guide(surf, LEVELS[self.idx]["guide"], (card.x + 90, card.bottom - 120), 36, self.t, False)
        self.b_map.draw(surf)
        self.b_next.draw(surf)
        self.confetti.draw(surf)


class FinalScene(Scene):
    def __init__(self, g):
        super().__init__(g)
        self.b_again = Button((300, 590, 240, 56), "Play again", GREEN, lambda: g.go(MapScene(g)), 26)
        self.b_menu = Button((560, 590, 240, 56), "Menu", BLUE, lambda: g.go(TitleScene(g)), 26)
        g.audio.play("win")
        self.confetti.burst((W // 2, 200), 120)

    def handle(self, ev):
        self.b_again.handle(ev)
        self.b_menu.handle(ev)

    def update(self, dt):
        super().update(dt)
        self.confetti.rain(2)

    def draw(self, surf):
        sky(surf, self.t, (255, 214, 120), (255, 244, 214), hills=(240, 190, 110))
        card = pygame.Rect(60, 40, 980, 620)
        panel(surf, card, (255, 252, 244), 30, YELLOW, bw=8)
        draw_shield(surf, (card.centerx, card.y + 66), 42, PURPLE)
        text(surf, "CYBER CHAMPION!", 54, PURPLE, (card.centerx, card.y + 150), "center", bold=True)
        text(surf, f"You finished all {len(LEVELS)} levels and learned how to stay safe online!", 24, INK,
             (card.centerx, card.y + 198), "center")
        stars = self.g.save.data["stars"]
        text(surf, f"Stars collected: {sum(stars)} / {3 * len(LEVELS)}", 28, INK, (card.centerx, card.y + 238), "center", bold=True)
        gx = self.g
        acc = int(100 * gx.total_points / gx.total_max) if gx.total_max else 100
        secs = int(time.time() - gx.t0)
        text(surf, f"First-try accuracy: {acc}%    Time played: {secs // 60}:{secs % 60:02d}", 24, INK,
             (card.centerx, card.y + 274), "center")
        text(surf, "Worlds you explored", 22, PURPLE, (card.centerx, card.y + 312), "center", bold=True)
        for i, lv in enumerate(LEVELS):
            x = card.x + 14 + (i % 7) * 137
            y = card.y + 330 + (i // 7) * 31
            circ(surf, LEVEL_COLORS[i], (x + 8, y + 11), 8)
            draw_check(surf, (x + 8, y + 11), 8, WHITE, 2)
            text(surf, lv["name"], 12, INK, (x + 21, y + 4), bold=True)
        self.b_again.draw(surf)
        self.b_menu.draw(surf)
        self.confetti.draw(surf)


# --------------------------------------------------------------------- game
class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("CyberQuest Kids")
        pygame.display.set_icon(make_icon())
        try:
            self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        except pygame.error:
            self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.save = Save()
        self.mouse = (0, 0)
        self.t0 = time.time()
        self.total_points = 0
        self.total_max = 0
        self.running = True
        self.fade = 0.0
        self.scene = TitleScene(self)

    def go(self, scene):
        self.scene = scene
        self.fade = 1.0

    def step(self, dt):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
                continue
            if ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                self.mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
                self.audio.toggle()
            else:
                self.scene.handle(ev)
        self.scene.update(dt)
        self.scene.draw(self.screen)
        if self.fade > 0:
            self.fade = max(0.0, self.fade - dt / 0.3)
            ov = pygame.Surface((W, H))
            ov.fill(WHITE)
            ov.set_alpha(int(255 * self.fade))
            self.screen.blit(ov, (0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.step(min(self.clock.tick(FPS) / 1000.0, 0.05))
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
