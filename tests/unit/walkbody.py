"""
WalkBody: a body on the ground, without a game (not a test module
itself), for the walker's tests (SPEC.md 21.23). It has the five means
a routine asks and the mouse's: perceive, keyDown, keyUp, look, ticks
and mouseRate.

The ground is whole blocks: a floor whose top is at height 0 over a
span of columns, less the 'holes' (nothing, 'deep' blocks down); 'walls'
(two blocks on the floor) and 'steps' (one). Its blocks are perceived as
a game's are, each with its box, so a terrain can be read from them.

The body moves as a player does, near enough for a controller, in the
game's order of a tick (pace.py): what its keys add goes to its motion
(a fifth of it off the ground), it moves by that, up and down first
and then across each way, stopped by a block's side, and keeps 0.546 of
it on the ground and 0.91 off it. Jump, on the ground, lifts it 0.42 a
tick; it falls 0.08 a tick more each tick and keeps 0.98 of that. Not
reckoned: a sneaking player kept from an edge.

Every request waits for the end of the next tick first, as the probe
runs a step there. In each tick the look turns by the rate in force
(mouseRate), after the body has moved by the look it had: the game turns
it at every frame. A look set outright is there at that tick's end and
stops the rate; a rate asked is in force from the tick after, and is
answered with the bearing as it is before it acts.

'track' keeps every tick: a Tick each, for the verdicts a walk is held
to.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from collections import namedtuple

from meantwell import pace
from meantwell.glide import AIR, GRAVITY, GROUND, KEPT_Y
from unittas.bearing import Bearing
from unittas.box import Box
from unittas.mouserate import MouseRate
from unittas.nearblock import NearBlock
from unittas.perception import Perception
from unittas.values import BlockPos, Look, Vec3

HALF, TALL, EYE = 0.3, 1.8, 1.62
#  What jump lifts it by, and how much of what its keys add it gets off
#  the ground
JUMP, ALOFT = 0.42, 0.2
_EPS = 1e-9

#  A tick of the track: where it was at its end, how it looked, how fast
#  it moved across in it and which way, the keys held in it, whether it
#  stood on the ground
Tick = namedtuple('Tick', 'tick x y z yaw pitch speed heading keys '
                          'onGround')


class WalkBody:
  """
  The body, its feet at 'pos' (x, z) on the floor and looking 'yaw' to
  begin with. 'span' is the floor's columns: ((from x, to x), (from z,
  to z)), each end with it. Every 'late'-th request is answered a tick
  late (0: none). 'asked' holds each request's name, 'keys' the keys
  held now, 'track' every tick.
  """

  def __init__(self, pos: tuple = (0.5, 0.5), yaw: float = 0.0,
               span: tuple = ((-12, 12), (-12, 12)), holes: tuple = (),
               walls: tuple = (), steps: tuple = (),
               deep: int = 3, late: int = 0) -> None:
    self.blocks = set()
    (fromX, toX), (fromZ, toZ) = span
    for x in range(fromX, toX + 1):
      for z in range(fromZ, toZ + 1):
        if (x, z) in holes:
          self.blocks.add((x, -1 - deep, z))
          continue
        self.blocks.add((x, -1, z))
        if (x, z) in walls:
          self.blocks.update(((x, 0, z), (x, 1, z)))
        if (x, z) in steps:
          self.blocks.add((x, 0, z))
    self.x, self.y, self.z = float(pos[0]), 0.0, float(pos[1])
    self.vx, self.vy, self.vz = 0.0, -GRAVITY * KEPT_Y, 0.0
    self.yaw, self.pitch = float(yaw), 0.0
    self.rate = 0.0, 0.0
    self.onGround, self.collided = True, False
    self.keys = set()
    self.late = late
    self.tick = 0
    self.asked = []
    self.track = []

  # ------------------------------------------------------------ the means

  def perceive(self, around: int = 2, below: int = 1,
               above: int = 1) -> Perception:
    self._request('perceive')
    feet = math.floor(self.y + _EPS)
    here = math.floor(self.x), math.floor(self.z)
    near = []
    for x, y, z in sorted(self.blocks):
      if (abs(x - here[0]) <= around and abs(z - here[1]) <= around and
          feet - below <= y <= feet + 1 + above):
        near.append(NearBlock(
          pos=BlockPos(x, y, z), id='minecraft:stone', meta=-1,
          boxes=(Box(float(x), float(y), float(z), x + 1.0, y + 1.0,
                     z + 1.0),)))
    return Perception(
      tick=self.tick, pos=Vec3(self.x, self.y, self.z),
      eye=Vec3(self.x, self.y + EYE, self.z),
      box=Box(self.x - HALF, self.y, self.z - HALF, self.x + HALF,
              self.y + TALL, self.z + HALF),
      look=Look(self.yaw, self.pitch),
      motion=Vec3(self.vx, self.vy, self.vz), onGround=self.onGround,
      collidedHorizontally=self.collided,
      sneaking='key.sneak' in self.keys, blockReach=4.5,
      mouseRate=MouseRate(self.rate[0], self.rate[1], 0),
      blocks=tuple(near))

  def keyDown(self, key: str) -> None:
    self._request('keyDown')
    self.keys.add(key)

  def keyUp(self, key: str) -> None:
    self._request('keyUp')
    self.keys.discard(key)

  def look(self, yaw: float, pitch: float) -> None:
    self._request('look')
    self.yaw, self.pitch = float(yaw), float(pitch)
    self.rate = 0.0, 0.0
    self.track[-1] = self.track[-1]._replace(yaw=self.yaw,
                                             pitch=self.pitch)

  def mouseRate(self, yaw: float, pitch: float) -> Bearing:
    self._request('mouseRate')
    self.rate = float(yaw), float(pitch)
    return Bearing(tick=self.tick, pos=Vec3(self.x, self.y, self.z),
                   look=Look(self.yaw, self.pitch),
                   motion=Vec3(self.vx, self.vy, self.vz))

  def ticks(self, n: int = 1) -> int:
    self.asked.append('ticks')
    for _ in range(n):
      self._step()
    return self.tick

  # ------------------------------------------------------------- the game

  def _request(self, name: str) -> None:
    """A request: kept by name, and the tick it waits for passes; every
    'late'-th one waits a tick more, as a game doesn't wait for the one
    who asks."""
    self.asked.append(name)
    self._step()
    if self.late and len(self.asked) % self.late == 0:
      self._step()

  def _solid(self, minX: float, minY: float, minZ: float, maxX: float,
             maxY: float, maxZ: float) -> list:
    """The blocks that box is in."""
    found = []
    for x in range(math.floor(minX + _EPS), math.floor(maxX - _EPS) + 1):
      for y in range(math.floor(minY + _EPS), math.floor(maxY - _EPS) + 1):
        for z in range(math.floor(minZ + _EPS),
                       math.floor(maxZ - _EPS) + 1):
          if (x, y, z) in self.blocks:
            found.append((x, y, z))
    return found

  def _box(self, x: float, y: float, z: float) -> tuple:
    """Its own box with its feet there."""
    return x - HALF, y, z - HALF, x + HALF, y + TALL, z + HALF

  def _step(self) -> None:
    """A tick of the game."""
    self.tick += 1
    held = self.keys
    forward = ('key.forward' in held) - ('key.back' in held)
    strafe = ('key.left' in held) - ('key.right' in held)
    ax, az = pace.push(self.yaw, forward, strafe, 'key.sneak' in held)
    if not self.onGround:
      ax, az = ax * ALOFT, az * ALOFT
    elif 'key.jump' in held:
      self.vy = JUMP
    kept = GROUND if self.onGround else AIR
    vx, vz = self.vx + ax, self.vz + az
    #  up and down first
    y = self.y + self.vy
    under = self._solid(*self._box(self.x, y, self.z))
    self.onGround = False
    if under:
      if self.vy <= 0.0:
        y = max(top for _, top, _ in under) + 1.0
        self.onGround = True
      else:
        y = min(low for _, low, _ in under) - TALL
      self.vy = 0.0
    #  then across, each way
    self.collided = False
    x = self.x + vx
    sides = self._solid(*self._box(x, y, self.z))
    if sides:
      x = (min(at for at, _, _ in sides) - HALF if vx > 0.0 else
           max(at for at, _, _ in sides) + 1.0 + HALF)
      vx, self.collided = 0.0, True
    z = self.z + vz
    sides = self._solid(*self._box(x, y, z))
    if sides:
      z = (min(at for _, _, at in sides) - HALF if vz > 0.0 else
           max(at for _, _, at in sides) + 1.0 + HALF)
      vz, self.collided = 0.0, True
    speed = math.hypot(x - self.x, z - self.z)
    heading = (pace.bearing(self.x, self.z, x, z) if speed > 1e-6 else
               None)
    self.x, self.y, self.z = x, y, z
    self.vx, self.vz = vx * kept, vz * kept
    self.vy = (self.vy - GRAVITY) * KEPT_Y
    self.yaw = (self.yaw + self.rate[0] + 180.0) % 360.0 - 180.0
    self.pitch = min(max(self.pitch + self.rate[1], -90.0), 90.0)
    self.track.append(Tick(self.tick, x, y, z, self.yaw, self.pitch,
                           speed, heading, frozenset(held),
                           self.onGround))
