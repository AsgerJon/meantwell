"""
Mouse: a body whose look is turned as a hand turns a mouse (SPEC.md
21.22): not in one request, but a part of the way each request, quickly
when it has far to go and slowly as it comes near. Everything else of
the body it hands on as it is, so an agent or a routine made on
Mouse(body) turns so in every step it has.

How fast it turns is a PID of sorts, reckoned each request:

- KP times how far it still has to go;
- less KD times how fast it turns already;
- and KI times all it has had left to go so far (0 as it stands:
  nothing is left over to work off, its last request is the look
  itself).

It quickens by no more than QUICKEN a request, never turns faster than
FASTEST nor slower than SLOWEST (it doesn't creep up on the last
degree), and it never goes past where it is going. Both ways turn
together, so the look goes straight across the screen, the short way
round. The same turn is turned the same way every time: nothing in it is
random.

Two things it isn't yet, both found in the practice game (SPEC.md
21.22). A request for a look takes two ticks, so a turn is a row of
some ten small jumps a second, not a hand's one movement: that needs
the probe to turn the look at every frame, which is asked of unitTAS.
And while a walking key is held 'look' sets the look outright, as the
body does: the agent's walk counts on its look being there at once, and
walked in rings round a waypoint when it wasn't.

'toward' is one request of a turn, for a walk that knows it turns (the
walker, SPEC.md 21.23): asked again and again with where to look then,
it turns as 'look' does and is never set outright.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Mouse(BaseObject):
  """
  The mouse of one body. 'look' is a turn and 'toward' one request of
  one; every other member is the body's own.

    agent = Agent(Mouse(game), frames)   # every step of it turns so
    Mouse(body).look(90.0, 0.0)          # some eight looks, then there
    while not mouse.toward(yaw, 0.0):    # a request at a time, walking
      yaw = ...
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  The turn's gains, by the request: of how far it has to go, of all
  #  it has had left so far, and of how fast it turns already
  KP, KI, KD = 0.7, 0.0, 0.1
  #  How much faster it may turn each request, how fast at most and how
  #  slowly at least, in degrees a request (a request is two ticks: 30
  #  is 300 a second)
  QUICKEN, FASTEST, SLOWEST = 12.0, 30.0, 2.0
  #  A turn of no more than this is one request, in degrees
  SMALL = 3.0
  #  The keys that walk it: with one held, a look is set outright
  WALKS = ('key.forward', 'key.back', 'key.left', 'key.right')

  #  Fallback Variables

  #  Private Variables
  __body__: Any = None
  #  The walking keys it holds down, as they went through it
  __walking__: set = None
  #  Where it left the look, once it has turned it: (yaw, pitch)
  __at__: tuple = None
  #  How far its last request turned it: (yaw, pitch), in degrees
  __rate__: tuple = (0.0, 0.0)

  #  Public Variables
  body = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @body.GET
  def _getBody(self) -> Any:
    """The body it turns."""
    return self.__body__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: Any) -> None:
    """The mouse of 'body': a player's means, its look and its perceive
    among them."""
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
    Turns the body's look to 'yaw' and 'pitch': a part of the way each
    request, the last one the look itself. Looking there already, it
    asks nothing. With a walking key held, the look is set outright. It
    turns from rest, from where it left the look last (the first time,
    from where the body perceives it looks): a look turned by anything
    else is found again by its last request, which is the look itself.

    Raises
    ------
    TypeError
      A look that isn't two numbers.
    ValueError
      A pitch beyond straight up or straight down.
    """
    self._checked(yaw, pitch)
    self.__rate__ = 0.0, 0.0
    if self.__walking__:
      if self._left(yaw, pitch)[2] > 0.0:
        self.__body__.look(yaw, pitch)
      self.__at__ = float(yaw), float(pitch)
      return
    while not self.toward(yaw, pitch):
      pass

  def toward(self, yaw: float, pitch: float) -> bool:
    """
    One request's turn towards 'yaw' and 'pitch': a part of the way, as
    'look' turns, going on from how fast it turns that way already.
    Whether it looks there now; looking there already it asks nothing.
    It is for the one who turns while it does something else, a walker:
    asked again and again, each time with where it is to look then. It
    is never set outright, a walking key held or not.

    Raises
    ------
    TypeError
      A look that isn't two numbers.
    ValueError
      A pitch beyond straight up or straight down.
    """
    self._checked(yaw, pitch)
    leftYaw, leftPitch, left = self._left(yaw, pitch)
    if left == 0.0:
      self.__rate__ = 0.0, 0.0
      return True
    atYaw, atPitch = self.__at__
    #  along the straight line from where it looks to where it is to;
    #  of how fast it turns already, what goes that way is kept
    wayYaw, wayPitch = leftYaw / left, leftPitch / left
    speed = max(0.0, self.__rate__[0] * wayYaw +
                self.__rate__[1] * wayPitch)
    want = self.KP * left - self.KD * speed
    speed = min(max(want, self.SLOWEST), speed + self.QUICKEN,
                self.FASTEST)
    if left <= self.SMALL or speed >= left:
      #  the last of it: the look itself, to the hair
      self.__body__.look(yaw, pitch)
      self.__at__ = float(yaw), float(pitch)
      self.__rate__ = leftYaw, leftPitch
      return True
    self.__at__ = (self._wrapped(atYaw + wayYaw * speed),
                   atPitch + wayPitch * speed)
    self.__rate__ = wayYaw * speed, wayPitch * speed
    self.__body__.look(*self.__at__)
    return False

  @staticmethod
  def _checked(yaw: float, pitch: float) -> None:
    """Raises unless that is a look a head can take."""
    for each in (yaw, pitch):
      if isinstance(each, bool) or not isinstance(each, (int, float)):
        raise TypeError('a look is its yaw and its pitch in degrees, not '
                        '%r' % (each,))
    if not -90.0 <= pitch <= 90.0:
      raise ValueError('a pitch is from -90 to 90, not %r' % (pitch,))

  def _left(self, yaw: float, pitch: float) -> tuple:
    """How far it is from where it left the look to 'yaw' and 'pitch':
    (the yaw's way, the short way round; the pitch's; both together).
    The first time, where it left the look is where the body looks."""
    if self.__at__ is None:
      now = self.__body__.perceive(0, 0, 0).look
      self.__at__ = now.yaw, now.pitch
    leftYaw = (yaw - self.__at__[0] + 180.0) % 360.0 - 180.0
    leftPitch = pitch - self.__at__[1]
    return leftYaw, leftPitch, math.hypot(leftYaw, leftPitch)

  @staticmethod
  def _wrapped(yaw: float) -> float:
    """The yaw from -180 to 180."""
    return (yaw + 180.0) % 360.0 - 180.0
