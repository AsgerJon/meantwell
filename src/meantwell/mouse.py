"""
Mouse: a body whose look is turned as a hand turns a mouse (SPEC.md
21.22, 21.23). A hand gives a mouse a speed, not a place: each tick the
mouse reckons how fast to turn and asks the body to turn at that rate
(unitTAS's mouse.rate), and the game turns the look by it at every
frame. Everything else of the body it hands on as it is, so an agent or
a routine made on Mouse(body) turns so in every step it has.

How fast it turns is reckoned each tick:

- KP times how far it still has to go;
- less KD times how fast it turns that way already.

It quickens by no more than QUICKEN a tick, never turns faster than
FASTEST nor slower than SLOWEST (it doesn't creep up on the last
degree), and never goes past: its last tick's rate is what is left.
Both ways turn together, so the look goes straight across the screen,
the short way round. The same turn is turned the same way every time:
nothing in it is random.

A rate asked now is in force after the tick its request waits for, and
is answered with the look as it is before it acts. So the mouse reckons
from where the look will be by then: the answer's look, and a tick more
of the rate in force. Each answer's look is taken as the truth, so
what a frame's share is off never adds up.

- look(yaw, pitch): the whole turn, then the look itself set, to the
  hair. A small turn is the look set at once.
- toward(yaw, pitch): one tick's rate of that turn, for a walk that
  knows it turns (the walker): asked each tick, with where to look
  then. It is its asker's clock: always a request, always a tick.
- ahead(yaw, pitch, ticks): the looks it would have, reckoned.
- rest(): the rate stopped. bearing: the last answer, with where the
  body is and how it moves.

While a walking key is held 'look' sets the look outright, as the body
does: the agent's walk counts on its look being there at once, and
walked in rings round a waypoint when it wasn't (found in the practice
game). 'toward' never does.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional

  from unittas.bearing import Bearing


class Mouse(BaseObject):
  """
  The mouse of one body. 'look' is a turn and 'toward' one tick of one;
  every other member is the body's own.

    agent = Agent(Mouse(game), frames)   # every step of it turns so
    Mouse(body).look(90.0, 0.0)          # some 14 ticks, then there
    while not mouse.toward(yaw, 0.0):    # a tick at a time, walking
      yaw = ...
    mouse.rest()
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  The turn's gains, by the tick: of how far it has to go, and of how
  #  fast it turns already
  KP, KD = 0.4, 0.1
  #  How much faster it may turn each tick, how fast at most and how
  #  slowly at least, in degrees a tick (15 is 300 a second)
  QUICKEN, FASTEST, SLOWEST = 6.0, 15.0, 1.0
  #  A turn of no more than this, from rest, is the look set at once
  SMALL = 3.0
  #  The keys that walk it: with one held, 'look' sets the look outright
  WALKS = ('key.forward', 'key.back', 'key.left', 'key.right')
  #  As near as two looks are counted the same, in degrees
  SAME = 1e-9

  #  Fallback Variables

  #  Private Variables
  __body__: Any = None
  #  The walking keys it holds down, as they went through it
  __walking__: set = None
  #  The look as its last answer had it: (yaw, pitch)
  __at__: tuple = None
  #  The rate in force, in degrees a tick: (yaw, pitch)
  __rate__: tuple = (0.0, 0.0)
  #  The last answer to a rate
  __bearing__: Any = None

  #  Public Variables
  body = Field()
  bearing = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @body.GET
  def _getBody(self) -> Any:
    """The body it turns."""
    return self.__body__

  @bearing.GET
  def _getBearing(self) -> Optional[Bearing]:
    """The body's bearing as the last rate asked was answered: its
    tick, where it is, its look and its motion. None before the first."""
    return self.__bearing__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: Any) -> None:
    """The mouse of 'body': a player's means, its look, its mouseRate
    and its perceive among them."""
    BaseObject.__init__(self)
    self.__body__ = body
    self.__walking__ = set()

  def __getattr__(self, name: str) -> Any:
    """Every member that isn't its own is the body's, as it is."""
    if name.startswith('__'):
      raise AttributeError(name)
    return getattr(self.__body__, name)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def keyDown(self, key: str) -> None:
    """The key held down on the body; a walking key is kept in mind."""
    self.__body__.keyDown(key)
    if key in self.WALKS:
      self.__walking__.add(key)

  def keyUp(self, key: str) -> None:
    """The key let go on the body."""
    self.__body__.keyUp(key)
    self.__walking__.discard(key)

  def look(self, yaw: float, pitch: float) -> None:
    """
    Turns the body's look to 'yaw' and 'pitch': a rate each tick until
    it is there, then the look itself, to the hair, with no rate left
    in force. Looking there already, it asks nothing. A small turn from
    rest is the look set at once; so is any turn with a walking key
    held.

    Raises
    ------
    TypeError
      A look that isn't two numbers.
    ValueError
      A pitch beyond straight up or straight down.
    """
    self._checked(yaw, pitch)
    self._known()
    left = self._off(self.__at__, yaw, pitch)[2]
    still = self.__rate__ == (0.0, 0.0)
    if self.__walking__ or (still and left <= self.SMALL):
      if left > 0.0 or not still:
        self._set(yaw, pitch)
      return
    while not self.toward(yaw, pitch):
      pass
    if self._off(self.__at__, yaw, pitch)[2] > 0.0:
      self._set(yaw, pitch)

  def toward(self, yaw: float, pitch: float) -> bool:
    """
    One tick's rate towards 'yaw' and 'pitch', going on from how fast it
    turns that way already. Whether it looks there once the request is
    answered. It is for the one who turns while it does something else,
    a walker: asked each tick, each time with where it is to look then.
    A rate is asked every time, of nothing when it is there, so that a
    tick passes and 'bearing' is that tick's. The look is never set
    outright, a walking key held or not.

    Raises
    ------
    TypeError
      A look that isn't two numbers.
    ValueError
      A pitch beyond straight up or straight down.
    """
    self._checked(yaw, pitch)
    self._known()
    rate, there = self._reckon(self.__at__, self.__rate__, yaw, pitch)
    self._ask(rate)
    return there

  def ahead(self, yaw: float, pitch: float, ticks: int) -> list:
    """
    The look it would have in each of the next 'ticks' ticks, were it
    asked 'toward' there each tick: (yaw, pitch) each, the first the
    look it has now. Reckoned; nothing is asked of the body but, the
    first time, its look.
    """
    self._checked(yaw, pitch)
    self._known()
    at, rate, looks = self.__at__, self.__rate__, []
    for _ in range(ticks):
      looks.append(at)
      asked, _ = self._reckon(at, rate, yaw, pitch)
      at, rate = self._turned(at, rate), asked
    return looks

  def rest(self) -> None:
    """The rate stopped: its look turns no more. At rest already, it
    asks nothing."""
    if self.__rate__ != (0.0, 0.0):
      self._ask((0.0, 0.0))

  def _ask(self, rate: tuple) -> None:
    """The rate asked of the body, and its answer kept."""
    bearing = self.__body__.mouseRate(*rate)
    self.__bearing__ = bearing
    self.__at__ = bearing.look.yaw, bearing.look.pitch
    self.__rate__ = rate

  def _set(self, yaw: float, pitch: float) -> None:
    """The look set outright, which stops any rate."""
    self.__body__.look(yaw, pitch)
    self.__at__ = float(yaw), float(pitch)
    self.__rate__ = 0.0, 0.0

  def _known(self) -> None:
    """Its look and the rate in force, perceived the first time."""
    if self.__at__ is None:
      seen = self.__body__.perceive(0, 0, 0)
      self.__at__ = seen.look.yaw, seen.look.pitch
      self.__rate__ = seen.mouseRate.yaw, seen.mouseRate.pitch

  def _reckon(self, at: tuple, rate: tuple, yaw: float,
              pitch: float) -> tuple:
    """
    The rate to ask now, looking 'at' with 'rate' in force, to look
    'yaw' and 'pitch': (the rate, whether it looks there once this
    request is answered). The rate asked acts from the tick after, so it
    is reckoned from where the look is by then.
    """
    leftYaw, leftPitch, left = self._off(self._turned(at, rate), yaw,
                                         pitch)
    if left <= self.SAME:
      return (0.0, 0.0), True
    #  along the straight line from where it looks to where it is to;
    #  of how fast it turns already, what goes that way is kept
    wayYaw, wayPitch = leftYaw / left, leftPitch / left
    speed = max(0.0, rate[0] * wayYaw + rate[1] * wayPitch)
    want = self.KP * left - self.KD * speed
    speed = min(max(want, self.SLOWEST), speed + self.QUICKEN,
                self.FASTEST, left)
    return (wayYaw * speed, wayPitch * speed), False

  @classmethod
  def _turned(cls, at: tuple, rate: tuple) -> tuple:
    """The look a tick on from 'at', turned by 'rate'."""
    return (cls._wrapped(at[0] + rate[0]),
            min(max(at[1] + rate[1], -90.0), 90.0))

  @staticmethod
  def _off(at: tuple, yaw: float, pitch: float) -> tuple:
    """How far it is from the look 'at' to 'yaw' and 'pitch': (the
    yaw's way, the short way round; the pitch's; both together)."""
    leftYaw = (yaw - at[0] + 180.0) % 360.0 - 180.0
    leftPitch = pitch - at[1]
    return leftYaw, leftPitch, math.hypot(leftYaw, leftPitch)

  @staticmethod
  def _checked(yaw: float, pitch: float) -> None:
    """Raises unless that is a look a head can take."""
    for each in (yaw, pitch):
      if isinstance(each, bool) or not isinstance(each, (int, float)):
        raise TypeError('a look is its yaw and its pitch in degrees, not '
                        '%r' % (each,))
    if not -90.0 <= pitch <= 90.0:
      raise ValueError('a pitch is from -90 to 90, not %r' % (pitch,))

  @staticmethod
  def _wrapped(yaw: float) -> float:
    """The yaw from -180 to 180."""
    return (yaw + 180.0) % 360.0 - 180.0
