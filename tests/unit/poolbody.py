"""
PoolBody: a body in a pool, without a game (not a test module itself),
for the swimmer's tests (SPEC.md 21.16). It has the five means the
swimmer asks and no others: perceive, keyDown, keyUp, look and ticks.

The pool is water from its bed up to its top wherever x is under the
bank's; from there on is ground, 'lip' above the water's top (0: level
with it). A 'roof' is stone from a height up over a stretch of the pool,
leaving a gap between it and the bed.

The body moves as a player does in water, near enough for a controller,
in 1.7.10's order of a tick. Upright: the forward key pushes it 0.02
along its look and jump lifts it 0.04, it moves by its motion, keeps 0.8
of it and sinks 0.02. Out of the water it falls 0.08 a tick and keeps
0.98 of that; on the ground forward pushes it 0.1 and it keeps 0.546.
Pushing into the bank with nothing 0.6 over its feet lifts it 0.3: the
hop out.

In water is counted either way a game counts it, and that is also which
game it is:

- 'touching' (a modern game): in water while its feet are under the
  water's top at all. It swims as 1.13 has it: sprint and forward held
  with its eyes under water lay it level, 0.6 high, its eyes 0.4 up; it
  keeps 0.9 of its motion across, doesn't sink, and its motion up and
  down follows its look (6 parts in 100 a tick; 8.5 looking steeply
  down; never up out of the water). It swims on while sprint and forward
  are held and it is in water, and stays level where there is no room to
  stand.
- not 'touching' (1.7.10): in water only 0.4 deep or more, so that it
  bobs out of the water a tick at a time; and it has no such swimming.

Every request waits for the end of the next tick first, as the probe
runs a step there, so the swimmer meets the latency it meets in a game.
Creative's double tap is kept: jump pressed twice within 7 ticks would
make it fly ('flew').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import Optional

from unittas.box import Box
from unittas.perception import Perception
from unittas.values import Look, Vec3

HALF = 0.3
TALL, LEVEL = 1.8, 0.6
EYE, EYE_LEVEL = 1.62, 0.4


class PoolBody:
  """
  The body, at 'pos' to begin with. 'asked' holds each request's name,
  'presses' each (tick, key) pressed, 'keys' the keys held now, 'lowest'
  the least height it was at since 'mark()', 'level' how many ticks it
  swam level. 'roof' is (from x, to x, its underside's height).
  """

  def __init__(self, pos: Vec3, bank: float = 20.0, top: float = 4.0,
               bed: float = 1.0, lip: float = 0.0, touching: bool = True,
               roof: Optional[tuple] = None) -> None:
    self.x, self.y, self.z = pos.x, pos.y, pos.z
    self.vx = self.vy = self.vz = 0.0
    self.bank, self.top, self.bed, self.lip = bank, top, bed, lip
    self.touching = touching
    self.roof = roof
    self.yaw = self.pitch = 0.0
    self.tick = 0
    self.keys = set()
    self.asked = []
    self.presses = []
    self.flew = False
    self.swimming = False
    self.level = 0
    self.onGround = self.y <= self._floor(self.x) + 1e-9
    self.collided = False
    self.lowest = self.y

  # ------------------------------------------------------------ the five

  def perceive(self, around: int = 2, below: int = 1,
               above: int = 1) -> Perception:
    self._request('perceive')
    return Perception(
      tick=self.tick, pos=Vec3(self.x, self.y, self.z),
      eye=Vec3(self.x, self.y + self._eye(), self.z),
      box=Box(self.x - HALF, self.y, self.z - HALF, self.x + HALF,
              self.y + self._height(), self.z + HALF),
      look=Look(self.yaw, self.pitch),
      motion=Vec3(self.vx, self.vy, self.vz), onGround=self.onGround,
      collidedHorizontally=self.collided, inWater=self.inWater(),
      sprinting='key.sprint' in self.keys and 'key.forward' in self.keys)

  def keyDown(self, key: str) -> None:
    self._request('keyDown')
    if key in self.keys:
      return
    if key == 'key.jump' and any(
        self.tick - tick <= 7 for tick, each in self.presses
        if each == key):
      self.flew = True
    self.presses.append((self.tick, key))
    self.keys.add(key)

  def keyUp(self, key: str) -> None:
    self._request('keyUp')
    self.keys.discard(key)

  def look(self, yaw: float, pitch: float) -> None:
    self._request('look')
    self.yaw, self.pitch = yaw, pitch

  def ticks(self, n: int = 1) -> int:
    self.asked.append('ticks')
    for _ in range(n):
      self._step()
    return self.tick

  # --------------------------------------------------------- for a test

  def mark(self) -> None:
    """From here on 'lowest' is reckoned."""
    self.lowest = self.y

  def inWater(self) -> bool:
    """Whether the game would count it in water, the way it counts."""
    if self.x + HALF > self.bank and self.y >= self._floor(self.x) - 1e-9:
      return False
    return self.top - self.y > (1e-9 if self.touching else 0.4)

  # --------------------------------------------------------------- inside

  def _request(self, name: str) -> None:
    self.asked.append(name)
    self._step()

  def _height(self) -> float:
    return LEVEL if self.swimming else TALL

  def _eye(self) -> float:
    return EYE_LEVEL if self.swimming else EYE

  def _floor(self, x: float) -> float:
    """What is under it at x: the bank's ground, or the pool's bed."""
    return self.top + self.lip if x + HALF > self.bank else self.bed

  def _under(self, x: float) -> Optional[float]:
    """The roof's underside over it at x; None where there is no roof."""
    if self.roof is None:
      return None
    start, end, height = self.roof
    return height if x + HALF > start and x - HALF < end else None

  def _pose(self, wet: bool) -> None:
    """Whether it swims level this tick, as 1.13 has it."""
    if not self.touching:
      self.swimming = False
      return
    sprinting = 'key.sprint' in self.keys and 'key.forward' in self.keys
    if self.swimming:
      roof = self._under(self.x)
      cramped = roof is not None and self.y + TALL > roof
      self.swimming = (sprinting and wet) or cramped
    else:
      self.swimming = (sprinting and wet and
                       self.y + EYE < self.top)

  def _step(self) -> None:
    """
    One tick of the game, in 1.7.10's order: the keys push and lift, it
    moves by its motion, then what it keeps of it, then the sinking or
    the fall, and last the hop out, which so moves it whole the tick
    after.
    """
    self.tick += 1
    wet = self.inWater()
    self._pose(wet)
    if self.swimming:
      self.level += 1
    dx, dz = -math.sin(math.radians(self.yaw)), math.cos(
      math.radians(self.yaw))
    if 'key.forward' in self.keys:
      push = 0.02 if wet or not self.onGround else 0.1
      self.vx += push * dx
      self.vz += push * dz
    if self.swimming and wet:
      up = -math.sin(math.radians(self.pitch))
      above = self.y + LEVEL < self.top
      if up <= 0.0 or 'key.jump' in self.keys or above:
        self.vy += (up - self.vy) * (0.085 if up < -0.2 else 0.06)
    elif 'key.jump' in self.keys:
      if wet:
        self.vy += 0.04
      elif self.onGround:
        self.vy = 0.42
    nx, ny, nz = self.x + self.vx, self.y + self.vy, self.z + self.vz
    ground = self.top + self.lip
    self.collided = False
    if nx + HALF > self.bank and ny < ground and self.y < ground:
      #  the bank's side
      nx = self.bank - HALF
      self.vx = 0.0
      self.collided = True
    roof = self._under(nx)
    if roof is not None and ny + self._height() > roof:
      if self._under(self.x) is None:
        #  the roof's side: no room under it as it is
        nx = self.x
        self.vx = 0.0
        self.collided = True
      else:
        ny = roof - self._height()
        self.vy = min(self.vy, 0.0)
    hop = (self.collided and wet and not self.swimming and
           self.y + 0.6 >= ground)
    floor = self._floor(nx)
    wasOnGround = self.onGround
    self.onGround = ny <= floor
    if self.onGround:
      ny = floor
      self.vy = max(self.vy, 0.0) if self.swimming else 0.0
    self.x, self.y, self.z = nx, ny, nz
    self.lowest = min(self.lowest, self.y)
    if wet:
      across = 0.9 if self.swimming else 0.8
      self.vx *= across
      self.vy *= 0.8
      self.vz *= across
      if not self.swimming:
        self.vy -= 0.02
    else:
      kept = 0.546 if wasOnGround else 0.91
      self.vx *= kept
      self.vz *= kept
      if not self.onGround:
        self.vy = (self.vy - 0.08) * 0.98
    if hop:
      #  lifted, with nothing 0.6 over its feet
      self.vy = 0.3
