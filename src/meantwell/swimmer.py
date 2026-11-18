"""
Swimmer: swimming, a routine (SPEC.md 21.16). Under water it comes up to
the water's top; it swims to a place as 1.13 has swimming, laid level
and one block high, by sprint and its look; and where a game has no such
swimming, or the water ends, it paddles: upright, afloat, jump held. The
agent's own walkTo swims only water one look shows whole, and a walk
that ends in deeper water sinks (SPEC.md 21.14).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from unittas.errors import TesttimeError
from unittas.values import BlockPos, Vec3

from .words import where

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union

  from unittas.perception import Perception


def _turn(a: float, b: float) -> float:
  """How far the yaw b is from a, either way, in degrees."""
  return abs((b - a + 180.0) % 360.0 - 180.0)


class Swimmer(BaseObject):
  """
  The swimmer of one body. It plays the body directly, by five of a
  player's means and no others: perceive, keyDown, keyUp, look and
  ticks.

  - 'swim' is swimming as 1.13 brought it: sprint and forward held under
    water lay the player level, 0.6 high, and it goes where it looks. It
    gets through a gap one block high, and it is the fast way.
  - 'paddle' is the way every version has: upright at the water's top,
    jump held to stay afloat, forward held.
  - 'surface' brings it up from under water. It, and a 'paddle' that
    ends afloat, return with jump still held: 'letGo' lets it go, and
    then it sinks.

    swimmer = Swimmer(body)
    swimmer.swim(Vec3(40.5, 63.0, 12.5))
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  Jump pressed again within 7 ticks makes a creative player fly (its
  #  double tap): it is pressed no sooner than this after its last press
  JUMP_AGAIN = 9
  #  At the water's top: no higher after this many ticks of holding jump
  #  (a player there bobs; 0.05 is under what it rises in a tick)
  RISEN = 10
  RISE = 0.05
  #  Nothing gained: less than 0.05 blocks nearer in this many ticks of
  #  pushing into something (the agent's own, swimming)
  STUCK = 40
  #  Afloat over a place in the water: this near it, across
  OVER = 0.45
  #  What it perceives with: itself alone, no blocks around it
  LOOK = (0, 0, 0)
  #  Laid level, swimming as 1.13 has it: its own box under this high
  LEVEL = 1.0
  #  The steepest it looks up or down as it steers, in degrees
  STEEP = 60.0
  #  A game with no such swimming: its box still tall after this many
  #  ticks of sprint and forward in water
  NONE = 60
  #  At a place under water: this near it, across and up and down
  THERE = 0.8
  #  Pushing into something this many perceptions running, laid level:
  #  the bank, or the water's end. It goes on upright, up and over
  PUSHING = 5

  #  Fallback Variables

  #  Private Variables
  __body__: Any = None
  #  The keys it holds down
  __held__: set = None
  #  The tick it last perceived, and the one it last pressed jump at
  __now__: int = 0
  __jumped__: int = None
  #  How many of its last swim's perceptions found it laid level
  __level__: int = 0

  #  Public Variables
  body = Field()
  level = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @body.GET
  def _getBody(self) -> Any:
    """The body it plays."""
    return self.__body__

  @level.GET
  def _getLevel(self) -> int:
    """How many of its last swim's perceptions found it laid level."""
    return self.__level__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: Any) -> None:
    """The swimmer of 'body': a player's means (perceive, keyDown, keyUp,
    look, ticks)."""
    BaseObject.__init__(self)
    self.__body__ = body
    self.__held__ = set()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def letGo(self) -> None:
    """Every key it holds, let go. In water, it sinks then."""
    for key in sorted(self.__held__):
      self.__body__.keyUp(key)
    self.__held__.clear()

  def surface(self, ticks: Optional[int] = None) -> Perception:
    """
    Up to the water's top, when it is under it: jump held until it is
    out of the water, or no higher after RISEN ticks of holding. It
    returns afloat, jump still held. Not in water, it does nothing. What
    it perceives then.

    Parameters
    ----------
    ticks : int, optional
      The step's tick budget; 300, left out.

    Raises
    ------
    TesttimeError
      The budget is spent and it is still rising or still under.
    """
    budget = 300 if ticks is None else ticks
    if budget <= 0:
      raise ValueError('a tick budget is above 0, not %r' % budget)
    seen = self._see()
    if not seen.inWater:
      return seen
    first = seen.tick
    heights = []
    try:
      while seen.inWater:
        if seen.tick - first > budget:
          infoSpec = """still under water after %d ticks of holding jump
          (the budget), at %s"""
          info = infoSpec % (seen.tick - first, where(seen.pos))
          raise TesttimeError('surface', seen, ' '.join(info.split()))
        self._hold('key.jump', True)
        if 'key.jump' in self.__held__:
          heights.append((seen.tick, seen.pos.y))
          before = [y for tick, y in heights
                    if seen.tick - tick >= self.RISEN]
          if before and seen.pos.y - before[-1] < self.RISE:
            break
        self.__body__.ticks(1)
        seen = self._see()
    except BaseException:
      self.letGo()
      raise
    return seen

  def swim(self, place: Union[Vec3, BlockPos],
           ticks: Optional[int] = None) -> Perception:
    """
    To 'place', swimming as 1.13 has it: sprint and forward held, laid
    level and 0.6 high, going where it looks, which is at the place.
    That swimming begins with its eyes under water: jump is let go, so
    from the water's top it sinks under by itself. A place under water
    it is done at, every key let go. At a bank, or where the water ends,
    it goes on upright (paddle), up and out onto the ground. 'level'
    says how much of it was swum level. What it perceives then.

    Parameters
    ----------
    place : Vec3 or BlockPos
      Where its feet are to be; a BlockPos is its floor's middle.
    ticks : int, optional
      The step's tick budget; 100 and 20 a block, left out.

    Raises
    ------
    TesttimeError
      Its box is still tall after NONE ticks of sprint and forward in
      water (the game has no such swimming: paddle instead); nothing
      gained; or the budget spent.
    """
    place = self._place('swim', place, ticks)
    seen = self._see()
    first = seen.tick
    if ticks is None:
      ticks = 100 + int(math.ceil(20 * math.dist(
        (place.x, place.y, place.z),
        (seen.pos.x, seen.pos.y, seen.pos.z))))
    self.__level__ = 0
    swum, hits, tall = False, 0, None
    try:
      while True:
        across = math.hypot(place.x - seen.pos.x, place.z - seen.pos.z)
        far = math.hypot(across, place.y - seen.pos.y)
        level = seen.box.maxY - seen.box.minY < self.LEVEL
        swum = swum or seen.inWater
        self.__level__ += 1 if level else 0
        if far < self.THERE or (seen.onGround and not seen.inWater and
                                not level and across < self.OVER):
          self.letGo()
          return seen
        spent = seen.tick - first
        if spent > ticks:
          infoSpec = """the tick budget (%d) is spent, %.2f blocks short,
          at %s"""
          info = infoSpec % (ticks, far, where(seen.pos))
          raise TesttimeError('swim', seen, ' '.join(info.split()))
        hits = hits + 1 if seen.collidedHorizontally else 0
        if swum and (hits >= self.PUSHING or
                     not (seen.inWater or level)):
          #  the bank, or the water's end: on upright, up and over
          self._hold('key.sprint', False)
          return self.paddle(place, max(1, ticks - spent))
        if seen.inWater and not level:
          tall = seen.tick if tall is None else tall
          if seen.tick - tall > self.NONE:
            infoSpec = """its box is still %.1f high after %d ticks of
            sprint and forward in water: this game has no swimming as
            1.13 has it (paddle instead)"""
            info = infoSpec % (seen.box.maxY - seen.box.minY,
                               seen.tick - tall)
            raise TesttimeError('swim', seen, ' '.join(info.split()))
        else:
          tall = None
        self._hold('key.jump', False)
        self._hold('key.sprint', True)
        self._hold('key.forward', True)
        self._aim(seen, place, across)
        seen = self._see()
    except BaseException:
      self.letGo()
      raise

  def paddle(self, place: Union[Vec3, BlockPos],
             ticks: Optional[int] = None) -> Perception:
    """
    Towards 'place', upright and afloat, as every version swims: jump
    held while it is in the water or under the place's level, forward
    held, turned to the place as it goes. It is done when it stands on
    ground out of the water, having been in it, with every key let go;
    or when it is afloat over the place, forward let go and jump still
    held. What it perceives then.

    Parameters
    ----------
    place : Vec3 or BlockPos
      Where to; a BlockPos is its floor's middle.
    ticks : int, optional
      The step's tick budget; 100 and 25 a block across, left out.

    Raises
    ------
    TesttimeError
      Pushing into something with nothing gained for STUCK ticks, or the
      budget spent.
    """
    place = self._place('paddle', place, ticks)
    seen = self._see()
    first = seen.tick
    if ticks is None:
      ticks = 100 + int(math.ceil(25 * math.hypot(place.x - seen.pos.x,
                                                 place.z - seen.pos.z)))
    swum = False
    pushed = []
    try:
      while True:
        across = math.hypot(place.x - seen.pos.x, place.z - seen.pos.z)
        swum = swum or seen.inWater
        if seen.onGround and not seen.inWater and (
            swum or across < self.OVER):
          self.letGo()
          return seen
        if seen.inWater and across < self.OVER:
          self._hold('key.forward', False)
          self._hold('key.jump', True)
          return seen
        if seen.tick - first > ticks:
          infoSpec = """the tick budget (%d) is spent, %.2f blocks short,
          at %s"""
          info = infoSpec % (ticks, across, where(seen.pos))
          raise TesttimeError('paddle', seen, ' '.join(info.split()))
        pushed.append((seen.tick, across))
        self._stuck(seen, across, pushed, first)
        self._hold('key.sprint', False)
        self._hold('key.jump', seen.inWater or
                   seen.pos.y < place.y - 0.05)
        self._hold('key.forward', True)
        self._face(seen, place)
        seen = self._see()
    except BaseException:
      self.letGo()
      raise

  @staticmethod
  def _place(step: str, place: Any, ticks: Optional[int]) -> Vec3:
    """The place as a Vec3; the step's arguments refused when wrong."""
    if isinstance(place, BlockPos):
      place = place.center()
    if not isinstance(place, Vec3):
      raise TypeError('%s goes towards a Vec3 or a BlockPos, not %r' % (
        step, place))
    if ticks is not None and ticks <= 0:
      raise ValueError('a tick budget is above 0, not %r' % ticks)
    return place

  def _see(self) -> Perception:
    """What the body perceives now: itself, no blocks around it."""
    seen = self.__body__.perceive(*self.LOOK)
    self.__now__ = seen.tick
    return seen

  def _hold(self, key: str, down: bool) -> None:
    """
    The key held down or let go, unless it is so already. Jump isn't
    pressed again within JUMP_AGAIN ticks of its last press (a creative
    player would fly): not yet, it is left up.
    """
    if down and key not in self.__held__:
      if key == 'key.jump':
        if (self.__jumped__ is not None and
            self.__now__ - self.__jumped__ < self.JUMP_AGAIN):
          return
        self.__jumped__ = self.__now__
      self.__body__.keyDown(key)
      self.__held__.add(key)
    elif not down and key in self.__held__:
      self.__body__.keyUp(key)
      self.__held__.discard(key)

  def _face(self, seen: Perception, place: Vec3) -> None:
    """Turns towards the place if it isn't, else lets a tick pass."""
    yaw = math.degrees(math.atan2(-(place.x - seen.pos.x),
                                  place.z - seen.pos.z))
    if _turn(seen.look.yaw, yaw) > 1.0:
      self.__body__.look(yaw, seen.look.pitch)
    else:
      self.__body__.ticks(1)

  def _aim(self, seen: Perception, place: Vec3, across: float) -> None:
    """
    Looks where it is to swim: at the place, STEEP up or down at most. A
    tick passes when it looks there already.
    """
    yaw = seen.look.yaw
    if across > 0.2:
      yaw = math.degrees(math.atan2(-(place.x - seen.pos.x),
                                    place.z - seen.pos.z))
    pitch = math.degrees(math.atan2(-(place.y - seen.pos.y), across))
    pitch = max(-self.STEEP, min(self.STEEP, pitch))
    if _turn(seen.look.yaw, yaw) > 1.0 or abs(
        seen.look.pitch - pitch) > 1.0:
      self.__body__.look(yaw, pitch)
    else:
      self.__body__.ticks(1)

  def _stuck(self, seen: Perception, across: float, pushed: list,
             first: int) -> None:
    """TesttimeError when pushing on has gained nothing for STUCK ticks."""
    if not seen.collidedHorizontally:
      return
    before = [was for tick, was in pushed if seen.tick - tick >= self.STUCK]
    if not before or before[-1] - across >= 0.05:
      return
    infoSpec = """nothing gained in %d ticks of pushing on, %.2f blocks
    short, at %s, after %d ticks"""
    info = infoSpec % (self.STUCK, across, where(seen.pos),
                       seen.tick - first)
    raise TesttimeError('paddle', seen, ' '.join(info.split()))
