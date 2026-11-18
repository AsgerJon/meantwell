"""
The 'glide' module is how an elytra flies (SPEC.md 21.17), as the game
reckons it each tick, from the glider's motion and its look alone. A
player learns it by flying; the glider flies it ahead to choose where to
look.

It is the game's formula for a living thing that is fall flying (its
travel, the same since 1.9), written down from memory of the game's
code: the practice game is its check, not this page. How it comes down
is from the practice game alone, measured there tick by tick.

- look(yaw, pitch): where a look points, a unit vector.
- step(motion, yaw, pitch): the motion a tick on.
- flight(pos, motion, yaw, pitch, ticks): each tick's place and motion.
- ahead(motion, yaw, pitch): the same tick, on bare numbers (for flying
  many flights ahead).
- slide(vx, vz, yaw, pitch): how far it goes on once it has reached the
  ground, to rest.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from unittas.values import Vec3

#  What a tick of falling adds downward, in blocks a tick
GRAVITY = 0.08
#  What is kept of the motion each tick: across, and up and down
KEPT, KEPT_Y = 0.99, 0.98
#  Coming down slower than this takes no fall damage, in blocks a tick
SOFT = 0.5
#  What is kept of the motion across each tick by one not gliding: its
#  feet on the ground (most ground: ice and slime keep more), and not
GROUND, AIR = 0.546, 0.91
#  How fast downward one standing reads: a tick of falling, stopped
STANDING = -GRAVITY * KEPT_Y


def look(yaw: float, pitch: float) -> tuple:
  """Where a look points: (x, y, z), a unit vector. Yaw 0 is south
  (+z), pitch 90 straight down."""
  across = math.cos(math.radians(pitch))
  return (-math.sin(math.radians(yaw)) * across,
          -math.sin(math.radians(pitch)),
          math.cos(math.radians(yaw)) * across)


def ahead(vx: float, vy: float, vz: float, yaw: float,
          pitch: float) -> tuple:
  """
  A tick of gliding: the motion (vx, vy, vz) a tick on, looking 'yaw'
  and 'pitch'.

  - Gravity pulls, less the lift of its wings: three quarters of it
    held off when it looks level, none looking straight down.
  - Falling, a tenth of its fall (by the same lift) goes forward along
    its look, and comes off the fall.
  - Looking up, its speed across is spent on climbing: 4 parts in 100
    by how steeply it looks, taken off along its look and 3.2 times
    that added upward.
  - Its motion across turns a tenth of the way towards its look.
  - 0.99 of it is kept across, 0.98 up and down.
  """
  lx, ly, lz = look(yaw, pitch)
  tilt = math.radians(pitch)
  flat = math.hypot(lx, lz)
  speed = math.hypot(vx, vz)
  lift = math.cos(tilt) ** 2 * min(1.0, math.hypot(flat, ly) / 0.4)
  vy += GRAVITY * (-1.0 + lift * 0.75)
  if vy < 0.0 and flat > 0.0:
    forward = vy * -0.1 * lift
    vx += lx * forward / flat
    vy += forward
    vz += lz * forward / flat
  if tilt < 0.0 and flat > 0.0:
    climb = speed * -math.sin(tilt) * 0.04
    vx -= lx * climb / flat
    vy += climb * 3.2
    vz -= lz * climb / flat
  if flat > 0.0:
    vx += (lx / flat * speed - vx) * 0.1
    vz += (lz / flat * speed - vz) * 0.1
  return vx * KEPT, vy * KEPT_Y, vz * KEPT


def slide(vx: float, vz: float, yaw: float, pitch: float) -> tuple:
  """
  Coming down: how far across it goes on, (dx, dz), from where it
  reached the ground with the motion (vx, vz) looking 'yaw' and 'pitch',
  to rest. As the practice game has it (SPEC.md 21.17):

  - a tick more it glides, on the ground;
  - its wings fold, and for a tick it goes on as fast, its feet not yet
    on the ground;
  - then GROUND of that is kept, then AIR of that (its feet weren't on
    the ground the tick before), and GROUND each tick from there.
  """
  vx, _, vz = ahead(vx, 0.0, vz, yaw, pitch)
  whole = 2.0 + GROUND + GROUND * AIR / (1.0 - GROUND)
  return vx * whole, vz * whole


def step(motion: Vec3, yaw: float, pitch: float) -> Vec3:
  """The glider's motion a tick on, from its 'motion' and its look."""
  return Vec3(*ahead(motion.x, motion.y, motion.z, yaw, pitch))


def flight(pos: Vec3, motion: Vec3, yaw: float, pitch: float,
           ticks: int) -> list:
  """
  The flight from 'pos' with 'motion', the look held: (where it is, its
  motion) after each of 'ticks' ticks. Each tick its motion is reckoned
  anew, and it moves by it.
  """
  flown = []
  x, y, z = pos.x, pos.y, pos.z
  vx, vy, vz = motion.x, motion.y, motion.z
  for _ in range(ticks):
    vx, vy, vz = ahead(vx, vy, vz, yaw, pitch)
    x, y, z = x + vx, y + vy, z + vz
    flown.append((Vec3(x, y, z), Vec3(vx, vy, vz)))
  return flown
