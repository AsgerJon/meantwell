"""
SkyBody: a body in the sky, without a game (not a test module itself),
for the glider's tests (SPEC.md 21.17). It has the five means the glider
asks and no others: perceive, keyDown, keyUp, look and ticks.

The world is flat ground, with a tower if one is given: a platform three
across at a height. Gliding, the body flies as the model has it
(meantwell.glide), which the practice game confirmed to a ten-thousandth
of a block: each tick its motion is reckoned from its look, and it moves
by it. Its wings open as the game opens them: on a press of jump while
it is off the ground and falling, when it wears them.

It comes down as the practice game measured (26.3; test_skybody.py holds
it to those numbers). It glides on for a tick on the ground it reached;
then its wings fold, and that tick its feet aren't on the ground: one is
on the ground only when the ground stopped one's way down, and it had
none. Not gliding it moves as a player does: it moves, then keeps 0.546
of its motion across if its feet were on the ground before the tick and
0.91 if not, and falls 0.08 a tick more, keeping 0.98, so that standing
it reads 0.0784 downward. Forward pushes it 0.1 on the ground and 0.02
in the air, jump lifts it 0.42: near enough for a controller.

A request waits for the end of a tick, as the probe runs a step there. A
perception takes one tick. A look takes two, and is the look it flies
with from the second (both measured). A key takes one (not measured).
The game doesn't wait for the one who asks, so a request can be late:
'late', given, says how many ticks each request waits first.
Creative's double tap is kept: jump pressed twice within 7 ticks would
make it fly ('flew').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import Callable, Optional

from meantwell import glide
from unittas.box import Box
from unittas.perception import Perception
from unittas.values import Look, Vec3

HALF = 0.3
TALL, LEVEL = 1.8, 0.6


class SkyBody:
  """
  The body, at 'pos' with 'motion' to begin with (standing, left out, as
  one standing reads), wearing wings unless 'wings' says not, and gliding
  already if 'gliding' says so. 'tower' is (x, z, height): ground three
  across there at that height. 'asked' holds each request's name,
  'presses' each (tick, key) pressed, 'keys' the keys held now, 'shown'
  each perception it gave, 'looks' each look asked for: (the tick it
  was asked at, yaw, pitch). 'down' is how it met the ground last,
  gliding: (the tick, where, its motion then). 'late', called before
  each request, gives how many ticks it waits first.
  """

  def __init__(self, pos: Vec3, motion: Optional[Vec3] = None,
               wings: bool = True, tower: Optional[tuple] = None,
               ground: float = 0.0, gliding: bool = False,
               late: Optional[Callable] = None) -> None:
    self.x, self.y, self.z = pos.x, pos.y, pos.z
    self.wings = wings
    self.late = late
    self.tower = tower
    self.ground = ground
    self.yaw = self.pitch = 0.0
    self.tick = 0
    self.keys = set()
    self.asked = []
    self.presses = []
    self.shown = []
    self.looks = []
    self.flew = False
    self.gliding = gliding
    self.down = None
    self.onGround = self.y <= self._floor(self.x, self.z) + 1e-9
    if motion is None:
      motion = Vec3(0.0, glide.STANDING if self.onGround else 0.0, 0.0)
    self.vx, self.vy, self.vz = motion.x, motion.y, motion.z
    #  the tick it reached the ground gliding, until its wings fold
    self._touched = None

  # ------------------------------------------------------------ the five

  def perceive(self, around: int = 2, below: int = 1,
               above: int = 1) -> Perception:
    self._request('perceive')
    high = LEVEL if self.gliding else TALL
    seen = Perception(
      tick=self.tick, pos=Vec3(self.x, self.y, self.z),
      box=Box(self.x - HALF, self.y, self.z - HALF, self.x + HALF,
              self.y + high, self.z + HALF),
      look=Look(self.yaw, self.pitch),
      motion=Vec3(self.vx, self.vy, self.vz), onGround=self.onGround)
    self.shown.append(seen)
    return seen

  def keyDown(self, key: str) -> None:
    self._request('keyDown')
    if key in self.keys:
      return
    if key == 'key.jump':
      if any(self.tick - tick <= 7 for tick, each in self.presses
             if each == key):
        self.flew = True
      elif self.wings and not self.onGround and self.vy < 0.0:
        self.gliding = True
    self.presses.append((self.tick, key))
    self.keys.add(key)

  def keyUp(self, key: str) -> None:
    self._request('keyUp')
    self.keys.discard(key)

  def look(self, yaw: float, pitch: float) -> None:
    #  two ticks: the first still flown as it looked before
    self._request('look')
    self.looks.append((self.tick - 1, yaw, pitch))
    self.yaw, self.pitch = yaw, pitch
    self._step()

  def ticks(self, n: int = 1) -> int:
    self.asked.append('ticks')
    for _ in range(n):
      self._step()
    return self.tick

  # --------------------------------------------------------------- inside

  def _request(self, name: str) -> None:
    self.asked.append(name)
    for _ in range(0 if self.late is None else self.late()):
      self._step()
    self._step()

  def _floor(self, x: float, z: float) -> float:
    """The ground under (x, z): the tower's top, or the ground."""
    if self.tower is not None:
      tx, tz, height = self.tower
      if abs(x - tx) <= 1.5 + HALF and abs(z - tz) <= 1.5 + HALF:
        return height
    return self.ground

  def _step(self) -> None:
    """One tick of the game."""
    self.tick += 1
    stood = self.onGround
    if self._touched is not None and self.tick >= self._touched + 2:
      #  two ticks after it reached the ground its wings fold, wherever
      #  it is then (the game's server says so, a tick behind)
      self.gliding, self._touched = False, None
    gliding = self.gliding
    if gliding:
      self.vx, self.vy, self.vz = glide.ahead(self.vx, self.vy, self.vz,
                                              self.yaw, self.pitch)
    else:
      dx, dz = -math.sin(math.radians(self.yaw)), math.cos(
        math.radians(self.yaw))
      if 'key.forward' in self.keys:
        push = 0.1 if stood else 0.02
        self.vx += push * dx
        self.vz += push * dz
      if 'key.jump' in self.keys and stood:
        self.vy = 0.42
    nx, ny, nz = self.x + self.vx, self.y + self.vy, self.z + self.vz
    floor = self._floor(nx, nz)
    #  on the ground: the ground stopped its way down
    self.onGround = self.vy < 0.0 and ny <= floor
    if self.onGround:
      if gliding and self._touched is None:
        self.down = (self.tick, Vec3(nx, floor, nz),
                     Vec3(self.vx, self.vy, self.vz))
        self._touched = self.tick
      self.vy = 0.0
    self.x, self.y, self.z = nx, max(ny, floor), nz
    if not gliding:
      kept = glide.GROUND if stood else glide.AIR
      self.vx *= kept
      self.vz *= kept
      self.vy = (self.vy - glide.GRAVITY) * glide.KEPT_Y
