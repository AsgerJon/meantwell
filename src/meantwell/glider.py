"""
Glider: the elytra, a routine (SPEC.md 21.17). It opens its wings, and
glides to a place: turned to it, its pitch chosen by flying the model of
how an elytra flies (glide.py) ahead, and it comes down there softly.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import Field

from unittas.errors import TesttimeError
from unittas.values import BlockPos, Vec3

from . import glide
from .routine import Routine
from .words import where

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union

  from unittas.perception import Perception


class Glider(Routine):
  """
  The glider of one body. It plays the body directly, by four of a
  player's means and no others: perceive, keyDown, keyUp and look (it
  waits by perceiving). Gliding is steered by the look alone; the keys
  are jump, to open its wings, and forward as it jumps where it stands.

    glider = Glider(body)
    glider.takeOff()
    glider.glide(Vec3(240.5, 64.0, -80.5))
    glider.miss, glider.sink  # how far off it came down, and how fast
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  How long its wings have to open in after the press, in ticks
  OPENING = 10
  #  Low down a degree of its look is blocks on the ground: it asks for
  #  the look it chose unless it has it to this, in degrees
  TURN = 0.2
  #  The knobs below (STEEP, FLARE, FLARE_PITCH, HARD, LOW, HOLD and
  #  COMMIT) were found by search on the scorecard of modelled flights
  #  (tests/practice/glides.py; SPEC.md 21.17), not set by hand
  #  The pitches it flies ahead to choose among, in degrees (down is
  #  above 0): the one it holds, and a spread; then each degree about
  #  the best of those, and each quarter of a degree about that
  PITCHES = tuple(range(-5, 76, 5))
  FINER = tuple(range(-4, 5))
  FINEST = (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75)
  #  Coming in steeper than STEEP it comes down hard, so near the ground
  #  it levels off: within FLARE ticks of the place's level, at the rate
  #  it sinks, it looks FLARE_PITCH. (Looking up there would lift it
  #  away again at speed, and it would skim on and off to the place.)
  #  Coming in at STEEP or flatter it comes down softly as it is, and
  #  steers all the way down
  STEEP = 34.0
  FLARE = 13.0
  FLARE_PITCH = 11.5
  #  It chooses at every look once it is this near the place's level
  LOW = 28.0
  #  What coming down hard counts for as it chooses: this many blocks
  #  off, for each block a tick faster than soft
  HARD = 65.0
  #  How many looks it holds a choice for, high up; low, it chooses at
  #  every look
  HOLD = 2
  #  About to come down, within this many ticks at the rate it sinks,
  #  it holds its look: one asked for then is flown too late to help
  COMMIT = 4
  #  How many ticks it still flies as it looked before, once it asks for
  #  a look: the first of the request's two. Measured in the practice
  #  game, not a knob
  LAG = 1
  #  How many ticks it flies the model ahead at most
  AHEAD = 1500
  #  At the place: this near it across, come to rest
  NEAR = 3.0
  #  At rest: on the ground, and slower across than this, in blocks a
  #  tick; and how many looks it has to come to rest in, once it is down
  STILL = 0.003
  RESTING = 100

  #  Fallback Variables

  #  Private Variables
  #  How far across from the place it came to rest, at its last glide;
  #  how fast downward and how fast across it was then, as last
  #  perceived in the air; and where it was first perceived down
  __miss__: float = None
  __sink__: float = None
  __down__: Vec3 = None
  __speed__: float = None

  #  Public Variables
  miss = Field()
  sink = Field()
  down = Field()
  speed = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @miss.GET
  def _getMiss(self) -> float:
    """How far across from the place its last glide came to rest."""
    return self.__miss__

  @sink.GET
  def _getSink(self) -> float:
    """How fast downward its last glide came down, in blocks a tick: as
    last perceived in the air, its wings open."""
    return self.__sink__

  @down.GET
  def _getDown(self) -> Vec3:
    """Where its last glide was first perceived down."""
    return self.__down__

  @speed.GET
  def _getSpeed(self) -> float:
    """How fast across its last glide was as it came down, in blocks a
    tick."""
    return self.__speed__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: Any) -> None:
    """The glider of 'body': a player's means (it asks perceive,
    keyDown, keyUp and look)."""
    Routine.__init__(self, body)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def takeOff(self, ticks: Optional[int] = None) -> Perception:
    """
    Opens its wings: one press of jump as it falls. Standing, it jumps
    first, forward held so that it leaves where it stood, and presses
    again once it falls, JUMP_AGAIN ticks on at the soonest (sooner, a
    creative player would fly instead). Done when its own box lies
    level; every key is let go then. Gliding already, it does nothing.
    What it perceives then.

    Parameters
    ----------
    ticks : int, optional
      The step's tick budget; 80, left out.

    Raises
    ------
    TesttimeError
      Its box is still tall OPENING ticks after the press as it fell (it
      has no wings to open, or was down again first), or the budget is
      spent.
    """
    budget = 80 if ticks is None else ticks
    if budget <= 0:
      raise ValueError('a tick budget is above 0, not %r' % budget)
    seen = self._see()
    if self._level(seen):
      return seen
    first, pressed = seen.tick, None
    try:
      if seen.onGround:
        self._hold('key.forward', True)
        self._hold('key.jump', True)
      while True:
        seen = self._see()
        if self._level(seen):
          self.letGo()
          return seen
        if pressed is not None and seen.tick - pressed > self.OPENING:
          infoSpec = """it has no wings to open: jump was pressed as it
          fell, %d ticks ago, and its box is still %.1f high, at %s"""
          info = infoSpec % (seen.tick - pressed,
                             seen.box.maxY - seen.box.minY, where(seen.pos))
          raise TesttimeError('takeOff', seen, ' '.join(info.split()))
        if seen.tick - first > budget:
          infoSpec = """its wings aren't open after %d ticks (the budget):
          it %s, at %s"""
          how = 'stands' if seen.onGround else 'never fell'
          info = infoSpec % (seen.tick - first, how, where(seen.pos))
          raise TesttimeError('takeOff', seen, ' '.join(info.split()))
        if pressed is None and not seen.onGround and seen.motion.y < 0.0:
          self._hold('key.jump', False)
          self._hold('key.jump', True)
          if self.holds('key.jump'):
            pressed = seen.tick
    except BaseException:
      self.letGo()
      raise

  def glide(self, place: Union[Vec3, BlockPos],
            ticks: Optional[int] = None) -> Perception:
    """
    Glides to 'place' and comes down there: turned to it, its pitch
    chosen by flying the model ahead (for each of PITCHES, a steep one
    levelled off near the ground, where would it come to rest, and how
    hard does it come down?). Down, it lets itself come to rest. 'miss'
    is then how far across from the place it is; 'sink' and 'speed' are
    how fast downward and across it came down, as last perceived in the
    air. What it perceives then.

    Parameters
    ----------
    place : Vec3 or BlockPos
      Where to come down; a BlockPos is its floor's middle.
    ticks : int, optional
      The step's tick budget; 3000, left out.

    Raises
    ------
    TesttimeError
      It stands with its wings shut (falling, it opens them itself); it
      came to rest further than NEAR from the place (short of it or
      beyond, said); it isn't at rest RESTING looks after it was down;
      or the budget is spent.
    """
    if isinstance(place, BlockPos):
      place = place.center()
    if not isinstance(place, Vec3):
      raise TypeError('glide goes to a Vec3 or a BlockPos, not %r' % (
        place,))
    budget = 3000 if ticks is None else ticks
    if budget <= 0:
      raise ValueError('a tick budget is above 0, not %r' % budget)
    seen = self._see()
    if not self._level(seen) and not seen.onGround:
      #  falling with its wings shut: it opens them
      seen = self.takeOff()
    if not self._level(seen):
      infoSpec = """its wings aren't open and it stands (its box is %.1f
      high, at %s): takeOff comes first"""
      info = infoSpec % (seen.box.maxY - seen.box.minY, where(seen.pos))
      raise TesttimeError('glide', seen, ' '.join(info.split()))
    first, start = seen.tick, seen.pos
    air, held, chosen = seen, 0, None
    #  down is on the ground, or its wings folded: the tick after they
    #  fold its feet aren't on the ground, in the game
    while not seen.onGround and self._level(seen):
      if seen.tick - first > budget:
        infoSpec = """the tick budget (%d) is spent, still in the air, at
        %s"""
        info = infoSpec % (budget, where(seen.pos))
        raise TesttimeError('glide', seen, ' '.join(info.split()))
      high = seen.pos.y - place.y
      if high >= self.COMMIT * -seen.motion.y:
        if chosen is None or held >= self.HOLD or high < self.LOW:
          before = None if chosen is None else chosen[1]
          chosen, held = self._choose(seen, place, before), 0
        yaw, pitch = chosen
        if pitch > self.STEEP and high < self.FLARE * -seen.motion.y:
          pitch = self.FLARE_PITCH
        if self._off(seen, yaw, pitch):
          self.body.look(yaw, pitch)
        held += 1
      air = seen
      seen = self._see()
    self.__sink__ = max(0.0, -air.motion.y)
    self.__speed__ = math.hypot(air.motion.x, air.motion.z)
    self.__down__ = seen.pos
    for _ in range(self.RESTING):
      if seen.onGround and math.hypot(seen.motion.x,
                                      seen.motion.z) < self.STILL:
        break
      seen = self._see()
    else:
      infoSpec = """it isn't at rest %d looks after it was down: at %s,
      %.2f blocks a tick across, %s the ground"""
      info = infoSpec % (self.RESTING, where(seen.pos), math.hypot(
        seen.motion.x, seen.motion.z), 'on' if seen.onGround else 'off')
      raise TesttimeError('glide', seen, ' '.join(info.split()))
    self.__miss__ = math.hypot(place.x - seen.pos.x, place.z - seen.pos.z)
    if self.__miss__ > self.NEAR:
      flown = math.hypot(seen.pos.x - start.x, seen.pos.z - start.z)
      whole = math.hypot(place.x - start.x, place.z - start.z)
      infoSpec = """came down %.1f blocks %s %s, at %s, having come
      down at %.2f blocks a tick downward"""
      info = infoSpec % (self.__miss__,
                         'short of' if flown < whole else 'beyond',
                         where(place), where(seen.pos), self.__sink__)
      raise TesttimeError('glide', seen, ' '.join(info.split()))
    return seen

  def _choose(self, seen: Perception, place: Vec3,
              held: Optional[float] = None) -> tuple:
    """
    Where to look now: (yaw, pitch). The yaw is the place's; the pitch
    the one whose flight ahead comes down nearest the place, coming down
    hard counted against it: among 'held' (the pitch chosen before,
    flown ahead first, so that it is kept unless another is better) and
    PITCHES, then FINER about the best of those, then FINEST about that.
    """
    across = math.hypot(place.x - seen.pos.x, place.z - seen.pos.z)
    yaw = seen.look.yaw
    if across > 1.0:
      yaw = math.degrees(math.atan2(-(place.x - seen.pos.x),
                                    place.z - seen.pos.z))
    first = tuple(float(each) for each in self.PITCHES)
    if held is not None:
      first = (held,) + first
    best, least = first[0], math.inf
    for spread in (first, self.FINER, self.FINEST):
      about = 0.0 if spread is first else best
      for step in spread:
        cost = self._flown(seen, place, yaw, about + step)
        if cost < least:
          best, least = about + step, cost
    return yaw, best

  def _flown(self, seen: Perception, place: Vec3, yaw: float,
             pitch: float) -> float:
    """
    What a pitch is worth: the model flown ahead from here, LAG ticks
    as it looks now and then looking 'yaw' and 'pitch' (a pitch steeper
    than STEEP until FLARE ticks off the place's level, and FLARE_PITCH
    from there), down to that level, and slid on from there to rest as
    the game slides (glide.slide). How far across from the place it
    comes to rest, and HARD for each block a tick it comes down faster
    than soft. A flight not down within AHEAD ticks is the worst there
    is.
    """
    x, y, z = seen.pos.x, seen.pos.y, seen.pos.z
    vx, vy, vz = seen.motion.x, seen.motion.y, seen.motion.z
    flares = pitch > self.STEEP
    for at in range(self.AHEAD):
      if at < self.LAG:
        looks = seen.look.yaw, seen.look.pitch
      elif flares and y - place.y < self.FLARE * -vy:
        looks = yaw, self.FLARE_PITCH
      else:
        looks = yaw, pitch
      vx, vy, vz = glide.ahead(vx, vy, vz, *looks)
      x, y, z = x + vx, y + vy, z + vz
      if y <= place.y:
        dx, dz = glide.slide(vx, vz, *looks)
        return math.hypot(place.x - x - dx, place.z - z - dz) + (
          self.HARD * max(0.0, -vy - glide.SOFT))
    return math.inf
