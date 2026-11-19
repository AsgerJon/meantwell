"""
The 'pace' module is how a player walks on the ground (SPEC.md 21.23),
as the game reckons it each tick, and where it is on a way of straight
stretches. A player learns it by walking; the walker reckons it ahead to
know where to let go.

It is the game's reckoning for a living thing on most ground, written
down from memory of the game's code: the practice game is its check,
not this page. Places are across only: (x, z).

- push(yaw, forward, strafe, sneak): what the keys held add in a tick.
- tick(x, z, vx, vz, ax, az): a tick of it.
- coast(speed): how far it goes on with the keys let go.
- held(ticks): how far that many ticks of one key take it in the end.
- bearing(x, z, tx, tz): the way to look from a place to another.
- turned(yaw, wanted): the turn from a look to another, the short way.
- length(way), point(way, along), abreast(way, x, z, since): a way of
  straight stretches, the point so far along it, and where on it a
  place is abreast of.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from .glide import GROUND

#  What a key held adds to the motion in a tick, walking: a tenth of a
#  block, and 0.98 of that for one key; two keys at once add no more
#  than the whole of it
WHOLE = 0.1
PUSH = WHOLE * 0.98
#  What is left of it sneaking
SNEAK = 0.3
#  How fast a walk is once it has settled, in blocks a tick
SPEED = PUSH / (1.0 - GROUND)
#  As near as two places on a way are counted the same
_SAME = 1e-9


def push(yaw: float, forward: int, strafe: int,
         sneak: bool = False) -> tuple:
  """
  What the keys held add to the motion in a tick: (ax, az), looking
  'yaw' (0 is south, +z). 'forward' is 1 with the forward key, -1 with
  back, 0 with neither or both; 'strafe' 1 with left, -1 with right.
  """
  ahead, aside = forward * 0.98, strafe * 0.98
  if sneak:
    ahead, aside = ahead * SNEAK, aside * SNEAK
  whole = math.hypot(ahead, aside)
  if whole > 1.0:
    ahead, aside = ahead / whole, aside / whole
  sin, cos = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
  return ((aside * cos - ahead * sin) * WHOLE,
          (ahead * cos + aside * sin) * WHOLE)


def tick(x: float, z: float, vx: float, vz: float, ax: float,
         az: float) -> tuple:
  """
  A tick on the ground: (x, z, vx, vz) a tick on. What the keys add
  (ax, az) goes to its motion, it moves by that, and GROUND of it is
  kept.
  """
  vx, vz = vx + ax, vz + az
  return x + vx, z + vz, vx * GROUND, vz * GROUND


def coast(speed: float) -> float:
  """How far it goes on, to rest, with the keys let go and its motion
  'speed' blocks a tick."""
  return speed / (1.0 - GROUND)


def held(ticks: int) -> float:
  """How far 'ticks' ticks of one key take it from rest in the end,
  what it goes on after letting go counted in."""
  return ticks * SPEED


def bearing(x: float, z: float, tx: float, tz: float) -> float:
  """The yaw to look from (x, z) towards (tx, tz), in degrees: 0 is
  south (+z), 90 west."""
  return math.degrees(math.atan2(-(tx - x), tz - z))


def turned(yaw: float, wanted: float) -> float:
  """The turn from 'yaw' to 'wanted' the short way round, in degrees:
  from -180 up to, not with, 180."""
  return (wanted - yaw + 180.0) % 360.0 - 180.0


def _stretches(way: tuple) -> list:
  """The way's stretches: (how far along it begins, its length, where
  it begins, where it ends). One of no length for a way of one point."""
  if not way:
    raise ValueError('a way is at least a point, not %r' % (way,))
  found, along = [], 0.0
  for (ax, az), (bx, bz) in zip(way, way[1:]):
    far = math.hypot(bx - ax, bz - az)
    found.append((along, far, (ax, az), (bx, bz)))
    along += far
  return found or [(0.0, 0.0, tuple(way[0]), tuple(way[0]))]


def length(way: tuple) -> float:
  """How long the way is: its stretches, summed."""
  begins, far, _, _ = _stretches(way)[-1]
  return begins + far


def point(way: tuple, along: float) -> tuple:
  """The point 'along' blocks along the way, (x, z): never before its
  beginning, never past its end."""
  stretches = _stretches(way)
  for begins, far, (ax, az), (bx, bz) in stretches:
    if along <= begins + far and far > 0.0:
      part = max(0.0, along - begins) / far
      return ax + (bx - ax) * part, az + (bz - az) * part
  return stretches[-1][3]


def abreast(way: tuple, x: float, z: float, since: float = 0.0) -> tuple:
  """
  Where on the way the place (x, z) is abreast of: (how far along the
  way its nearest point is, how far from it that is). Only the way from
  'since' blocks along it on is looked at, so that it never goes back.
  As near to two stretches, it is the one further along.
  """
  best = None
  stretches = _stretches(way)
  since = min(max(0.0, since), length(way))
  for begins, far, (ax, az), (bx, bz) in stretches:
    if since > begins + far:
      continue
    least = max(0.0, since - begins)
    if far > 0.0:
      part = ((x - ax) * (bx - ax) + (z - az) * (bz - az)) / far
      part = min(max(part, least), far)
      px = ax + (bx - ax) * part / far
      pz = az + (bz - az) * part / far
    else:
      part, px, pz = 0.0, ax, az
    off = math.hypot(x - px, z - pz)
    if best is None or off <= best[1] + _SAME:
      best = begins + part, off
  return best
