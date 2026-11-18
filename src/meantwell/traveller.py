"""
Traveller: long trips (SPEC.md 21.11, M1). The agent's own walkTo finds
its way on one look; the traveller remembers every look (Atlas), goes to
the edge of what it has seen to look further, and so gets around what no
single look shows whole: a wall wider than a look, a dead end.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import heapq
import math
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from unittas.errors import TesttimeError
from unittas.terrain import Terrain
from unittas.values import BlockPos, Vec3

from .atlas import Atlas
from .words import where

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Optional, Union

  from unittas.agent import Agent
  from unittas.perception import Perception

_EPS = 1e-6
_AROUND = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1),
           (-1, -1))


class Traveller(BaseObject):
  """
  The traveller of one agent. It asks the agent's own perceive and
  walkTo and nothing else, and holds no game. What it was shown stays in
  its atlas from one trip to the next.

    traveller = Traveller(agent)
    traveller.travel(Vec3(120.5, 64.0, -40.5))
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  How it looks around: blocks across, below, above, as the agent's
  #  walkTo does (further up or down to a place's level, 8 at most)
  LOOK = (8, 3, 3)
  #  How far a leg goes: well within one look, so the agent's own walkTo
  #  plans it whole
  LEG = 6.0
  #  The margin a leg on the way stops within: wide, so the agent lets go
  #  and stops without creeping up to it
  PASS = 1.0
  #  The least margin a trip ends within, the agent's own (one sneaking
  #  tap is about 0.065 blocks)
  LEAST = 0.05
  #  How far around the player it plans on what it remembers
  AROUND = 64
  #  How many legs in a row the agent may fail to complete
  STOPS = 3

  #  Fallback Variables

  #  Private Variables
  __agent__: Agent = None
  __atlas__: Atlas = None

  #  Public Variables
  agent = Field()
  atlas = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @agent.GET
  def _getAgent(self) -> Agent:
    """The agent that walks the trips."""
    return self.__agent__

  @atlas.GET
  def _getAtlas(self) -> Atlas:
    """What it remembers of the ground."""
    return self.__atlas__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, agent: Agent, atlas: Optional[Atlas] = None) -> None:
    """The traveller of 'agent', remembering in 'atlas' (a new one, left
    out)."""
    BaseObject.__init__(self)
    if atlas is None:
      atlas = Atlas()
    if not isinstance(atlas, Atlas):
      raise TypeError('a traveller remembers in an Atlas, not %r' % (atlas,))
    self.__agent__ = agent
    self.__atlas__ = atlas

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def travel(self, place: Union[Vec3, BlockPos], within: float = 0.25,
             ticks: Optional[int] = None) -> Perception:
    """
    Goes to 'place', however far, and stops there as walkTo does: within
    'within' blocks across, and still. It looks, remembers, and plans on
    all it remembers. With a way to the place it walks it, in legs. With
    none yet, it goes to the edge of what it has seen that is best by
    the way there and what is left from it, and looks again. What it
    perceives at the place.

    Parameters
    ----------
    place : Vec3 or BlockPos
      Where to stand; a BlockPos is its floor's middle.
    within : float
      How near is there, across.
    ticks : int, optional
      The trip's tick budget; 200 and 40 a block across, left out.

    Raises
    ------
    TesttimeError
      No way to the place in all it has seen, with no edge left to look
      from; the tick budget spent; or the agent couldn't complete a leg
      STOPS times in a row.
    """
    if isinstance(place, BlockPos):
      place = place.center()
    if not isinstance(place, Vec3):
      raise TypeError('travel goes to a Vec3 or a BlockPos, not %r' % (
        place,))
    if within < self.LEAST:
      raise ValueError('travel\'s margin is %r: the least a player can be '
                       'sure of is %r' % (within, self.LEAST))
    if ticks is not None and ticks <= 0:
      raise ValueError('a tick budget is above 0, not %r' % ticks)
    seen = self._lookAround(place, None)
    first = seen.tick
    if ticks is None:
      ticks = 200 + int(math.ceil(40 * math.hypot(place.x - seen.pos.x,
                                                 place.z - seen.pos.z)))
    stops = 0
    while True:
      spent = seen.tick - first
      if spent > ticks:
        infoSpec = """the tick budget (%d) is spent, %.2f blocks short, at
        %s"""
        short = math.hypot(place.x - seen.pos.x, place.z - seen.pos.z)
        info = infoSpec % (ticks, short, where(seen.pos))
        raise TesttimeError('travel', seen, ' '.join(info.split()))
      route = self._route(seen, place)
      if route is None:
        infoSpec = """no way to %s from %s in all it has seen (%d columns,
        in %d looks), and no edge left to look from"""
        info = infoSpec % (where(place), where(seen.pos),
                           self.__atlas__.columns, self.__atlas__.looks)
        raise TesttimeError('travel', seen, ' '.join(info.split()))
      leg, last = route
      left = max(1, ticks - spent)
      try:
        if last:
          return self.__agent__.walkTo(place, within, left)
        self.__agent__.walkTo(leg, self.PASS, left)
        stops = 0
      except TesttimeError as error:
        stops += 1
        if stops >= self.STOPS:
          infoSpec = """stopped %d times in a row on the way to %s; the
          last: %s"""
          info = infoSpec % (stops, where(place), error)
          raise TesttimeError('travel', error.seen, ' '.join(
            info.split())) from error
      seen = self._lookAround(place, seen)

  def _lookAround(self, place: Vec3,
                  before: Optional[Perception]) -> Perception:
    """A look around, remembered: further up or down to the place's
    level, from where it stood 'before' (None: it finds out first)."""
    look = self.LOOK if before is None else self._look(before.pos, place)
    seen = self.__agent__.perceive(*look)
    if before is None and self._look(seen.pos, place) != look:
      look = self._look(seen.pos, place)
      seen = self.__agent__.perceive(*look)
    self.__atlas__.note(seen, *look)
    return seen

  def _look(self, pos: Vec3, place: Vec3) -> tuple:
    """How far it looks from 'pos' on the way to 'place': LOOK's, and up
    or down to the place's floor and the room over it (8 at most)."""
    around, below, above = self.LOOK
    feet = math.floor(pos.y + _EPS)
    below = min(8, max(below, feet - math.floor(place.y) + 1))
    above = min(8, max(above, math.ceil(place.y) - feet))
    return around, below, above

  def _route(self, seen: Perception, place: Vec3) -> Optional[tuple]:
    """
    The next leg on what it remembers: (where to, whether it is the
    last, to the place itself). To the place when a way is known; else
    to the best edge it can get to. None when there is neither.
    """
    pos = seen.pos
    cx, cz = math.floor(pos.x), math.floor(pos.z)
    gx, gz = math.floor(place.x), math.floor(place.z)
    far = max(abs(gx - cx), abs(gz - cz))
    around = min(self.AROUND, far + 2 * self.LOOK[0])
    terrain = Terrain(self.__atlas__.ground(pos, around), around, 0, 0)
    if terrain.inside(gx, gz) and self.__atlas__.knows(gx, gz):
      path, _ = terrain.path(pos, place)
      if path is not None:
        return self._leg(terrain, pos, path, True)
    for spot in self._edgeSpots(terrain, pos, place, around):
      #  Terrain's own rules have the last word on what is a way
      path, _ = terrain.path(pos, spot)
      if path is not None:
        return self._leg(terrain, pos, path, False)
    return None

  def _leg(self, terrain: Terrain, pos: Vec3, path: list,
           whole: bool) -> tuple:
    """
    The leg to walk now along 'path' from 'pos': (where to, whether it
    ends the trip). LEG along the way at most. A stretch walked on a
    level is cut where the leg ends; a jump, a drop or a climb is gone
    to its end; and a leg never ends in water (walkTo stops on ground).
    """
    here, left = pos, self.LEG
    for at, point in enumerate(path):
      length = math.hypot(point.x - here.x, point.z - here.z)
      if length > left + _EPS:
        if abs(point.y - here.y) <= Terrain.STEP + _EPS:
          part = left / length
          point = Vec3(here.x + (point.x - here.x) * part, point.y,
                       here.z + (point.z - here.z) * part)
        return self._dry(terrain, point, path[at:]), False
      left -= length
      here = point
    return path[-1], whole

  @staticmethod
  def _dry(terrain: Terrain, point: Vec3, onward: list) -> Vec3:
    """'point', or when it is in water the next place on the way that
    isn't (the last, if none)."""
    for each in [point] + list(onward):
      if not terrain.wet(math.floor(each.x), math.floor(each.z), each.y):
        return each
    return onward[-1]

  def _edgeSpots(self, terrain: Terrain, pos: Vec3, place: Vec3,
                 around: int) -> Iterator[Vec3]:
    """
    The places to look further from, best first: where it can stand, by
    a rough reckoning, in a column at the edge of what it has seen; best
    by the way there plus what is left from it to the place.
    """
    cx, cz = math.floor(pos.x), math.floor(pos.z)
    edges = set(self.__atlas__.edges(cx, cz, around))
    scored = []
    for (x, z, h), steps in self._reach(terrain, pos).items():
      if (x, z) not in edges or (x, z) == (cx, cz):
        continue
      onward = math.hypot(x + 0.5 - place.x, z + 0.5 - place.z) + abs(
        h - place.y)
      scored.append((steps + onward, x, z, h))
    for _, x, z, h in sorted(scored):
      yield Vec3(x + 0.5, h, z + 0.5)

  @staticmethod
  def _reach(terrain: Terrain, pos: Vec3) -> dict:
    """
    Where the player gets to from 'pos', roughly, and how far each is:
    {(x, z, height): blocks}. Rough on the generous side: any floor or
    water beside it no more than a jump up or a drop down, and anything
    by a ladder, a door or water. It only orders and sifts the edges;
    Terrain's own rules then say whether there is a way (_route).
    """
    sx, sz = math.floor(pos.x), math.floor(pos.z)
    stands = [f for f in terrain.floors(sx, sz) + terrain.surfaces(sx, sz)
              if abs(f - pos.y) <= Terrain.HEAD]
    start = (sx, sz, min(stands, key=lambda f: abs(f - pos.y))
             if stands else pos.y)
    reach = {start: 0.0}
    queue = [(0.0, start)]
    loose = {}

    def isLoose(x: int, z: int) -> bool:
      if (x, z) not in loose:
        loose[(x, z)] = bool(terrain.doors(x, z) or terrain.ladders(x, z)
                             or terrain.surfaces(x, z))
      return loose[(x, z)]

    while queue:
      spent, node = heapq.heappop(queue)
      if spent > reach[node]:
        continue
      x, z, h = node
      for dx, dz in _AROUND:
        nx, nz = x + dx, z + dz
        if not terrain.inside(nx, nz):
          continue
        free = isLoose(x, z) or isLoose(nx, nz)
        total = spent + math.hypot(dx, dz)
        for f in terrain.floors(nx, nz) + terrain.surfaces(nx, nz):
          if not (free or (f - h <= Terrain.JUMP + _EPS and
                           h - f <= Terrain.DROP + _EPS)):
            continue
          if total < reach.get((nx, nz, f), math.inf):
            reach[(nx, nz, f)] = total
            heapq.heappush(queue, (total, (nx, nz, f)))
    return reach
