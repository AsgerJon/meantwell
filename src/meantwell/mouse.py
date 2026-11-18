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
And while a walking key is held it sets the look outright, as the body
does: the agent's walk counts on its look being there at once, and
walked in rings round a waypoint when it wasn't.
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
  The mouse of one body. 'look' is a turn; every other member is the
  body's own.

    agent = Agent(Mouse(game), frames)   # every step of it turns so
    Mouse(body).look(90.0, 0.0)          # some eight looks, then there
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
    turns from where it left the look last (the first time, from where
    the body perceives it looks): a look turned by anything else is
    found again by its last request, which is the look itself.

    Raises
    ------
    TypeError
      A look that isn't two numbers.
    ValueError
      A pitch beyond straight up or straight down.
    """
    for each in (yaw, pitch):
      if isinstance(each, bool) or not isinstance(each, (int, float)):
        raise TypeError('a look is its yaw and its pitch in degrees, not '
                        '%r' % (each,))
    if not -90.0 <= pitch <= 90.0:
      raise ValueError('a pitch is from -90 to 90, not %r' % (pitch,))
    body = self.__body__
    if self.__at__ is None:
      now = body.perceive(0, 0, 0).look
      self.__at__ = now.yaw, now.pitch
    atYaw, atPitch = self.__at__
    self.__at__ = float(yaw), float(pitch)
    leftYaw = (yaw - atYaw + 180.0) % 360.0 - 180.0
    leftPitch = pitch - atPitch
    left = math.hypot(leftYaw, leftPitch)
    if left == 0.0:
      return
    if left <= self.SMALL or self.__walking__:
      body.look(yaw, pitch)
      return
    #  along the straight line from where it looks to where it is to
    wayYaw, wayPitch = leftYaw / left, leftPitch / left
    speed, summed, gone = 0.0, 0.0, 0.0
    while True:
      still = left - gone
      summed += still
      want = self.KP * still + self.KI * summed - self.KD * speed
      speed = min(max(want, self.SLOWEST), speed + self.QUICKEN,
                  self.FASTEST)
      if speed >= still:
        break
      gone += speed
      body.look(self._wrapped(atYaw + wayYaw * gone),
                atPitch + wayPitch * gone)
    #  the last of it: the look itself, to the hair
    body.look(yaw, pitch)

  @staticmethod
  def _wrapped(yaw: float) -> float:
    """The yaw from -180 to 180."""
    return (yaw + 180.0) % 360.0 - 180.0
