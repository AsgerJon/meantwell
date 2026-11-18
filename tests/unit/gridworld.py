"""
GridAgent: the agent's own perceive and walkTo in a world of whole
blocks, without a game (not a test module itself), for the tests of what
stands above them (SPEC.md 21.11). It perceives as the probe does: the
blocks that aren't air within 'around' columns, from 'below' blocks
under its feet's block to 'above' over its head's. It walks as the
agent's walkTo decides: by unittas's own Terrain on one look of 8, to
the seen place nearest a place further off, 12 looks at most. Where the
real agent then moves by its keys, this one is simply there, 5 ticks a
block. It has no physics: what a player can walk is Terrain's to say.

- arena(wide, deep): a floor with a wall two high around it.
- wall(x0, z0, x1, z1): a wall two high on the floor, between corners.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import Optional, Union

from unittas.box import Box
from unittas.errors import TesttimeError
from unittas.nearblock import NearBlock
from unittas.perception import Perception
from unittas.terrain import Terrain
from unittas.values import BlockPos, Vec3

#  the floor's blocks are at y 3: a player stands at 4
FLOOR = 3
GROUND = 4.0


def wall(x0: int, z0: int, x1: int, z1: int) -> set:
  """A wall two high on the floor, over the columns between the corners."""
  return {(x, y, z) for x in range(min(x0, x1), max(x0, x1) + 1)
          for z in range(min(z0, z1), max(z0, z1) + 1)
          for y in (FLOOR + 1, FLOOR + 2)}


def arena(wide: int, deep: int) -> set:
  """A floor from (0, 0) to (wide - 1, deep - 1), walled around."""
  floor = {(x, FLOOR, z) for x in range(-1, wide + 1)
           for z in range(-1, deep + 1)}
  return (floor | wall(-1, -1, wide, -1) | wall(-1, deep, wide, deep) |
          wall(-1, -1, -1, deep) | wall(wide, -1, wide, deep))


class GridAgent:
  """
  An agent in a world of whole blocks: 'solid' holds each block's (x, y,
  z), and may be changed as a test goes. 'legs' are the places walkTo
  was asked for, each with its margin; 'looks' counts its perceptions;
  'stood' is every place a walk ended at. 'onLeg', when set, is called
  with the agent before each walkTo: a world that changes on the way.
  """

  LOOK = (8, 3, 3)
  LOOKS = 12
  PACE = 5

  def __init__(self, solid: set, start: Vec3) -> None:
    self.solid = set(solid)
    self.pos = start
    self.tick = 0
    self.looks = 0
    self.legs = []
    self.stood = [start]
    self.onLeg = None

  def perceive(self, around: int = 2, below: int = 1,
               above: int = 1) -> Perception:
    """What it perceives now, as player.perceive gives it."""
    self.looks += 1
    self.tick += 1
    fx, fz = math.floor(self.pos.x), math.floor(self.pos.z)
    fy = math.floor(self.pos.y + 1e-6)
    near = sorted((x, y, z) for x, y, z in self.solid
                  if abs(x - fx) <= around and abs(z - fz) <= around and
                  fy - below <= y <= fy + 1 + above)
    blocks = tuple(NearBlock(BlockPos(x, y, z), 'minecraft:stone', 0, (
      Box(float(x), float(y), float(z), x + 1.0, y + 1.0, z + 1.0),))
      for x, y, z in near)
    return Perception(tick=self.tick, pos=self.pos, blocks=blocks)

  def walkTo(self, place: Union[Vec3, BlockPos], within: float = 0.25,
             ticks: Optional[int] = None) -> Perception:
    """To the place, as the agent's walkTo finds its way on one look."""
    if isinstance(place, BlockPos):
      place = place.center()
    if self.onLeg is not None:
      self.onLeg(self)
    self.legs.append((place, within))
    first = self.tick
    seen = self.perceive(*self.LOOK)
    for _ in range(self.LOOKS):
      path, whole = Terrain(seen, *self.LOOK).path(seen.pos, place)
      if path is None:
        raise TesttimeError('walkTo', seen, 'no way to (%.2f, %.2f, %.2f) '
                            'in what the agent sees' % (place.x, place.y,
                                                        place.z))
      for point in path:
        self.tick += int(math.ceil(self.PACE * math.hypot(
          point.x - self.pos.x, point.z - self.pos.z)))
        self.pos = point
        if ticks is not None and self.tick - first > ticks:
          raise TesttimeError('walkTo', self.perceive(), 'the tick budget '
                              '(%d) is spent on the way' % ticks)
      if whole:
        self.stood.append(self.pos)
        return self.perceive()
      seen = self.perceive(*self.LOOK)
    self.stood.append(self.pos)
    raise TesttimeError('walkTo', seen, '(%.2f, %.2f, %.2f) is further than '
                        '%d looks around took the agent' % (
                          place.x, place.y, place.z, self.LOOKS))


def stoodIn(agent: GridAgent, x0: int, z0: int, x1: int, z1: int) -> int:
  """How many of the places its walks ended at are in the columns given."""
  return sum(1 for pos in agent.stood
             if x0 <= math.floor(pos.x) <= x1 and
             z0 <= math.floor(pos.z) <= z1)
