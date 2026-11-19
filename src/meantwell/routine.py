"""
Routine: what the routines that play the body share (SPEC.md 21.15,
21.16): the body itself, the keys held and let go, and jump guarded
against a creative player's double tap. A routine asks five of a
player's means and no others: perceive, keyDown, keyUp, look and ticks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

  from unittas.perception import Perception


class Routine(BaseObject):
  """
  A routine of one body: Swimmer, Glider. Until unitTAS's seam (SPEC.md
  21.7 step 1) the body it is handed in a game is the agent's game,
  which has the five members; from the seam on, the Body.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  Jump pressed again within 7 ticks makes a creative player fly (its
  #  double tap): it is pressed no sooner than this after its last press
  JUMP_AGAIN = 9
  #  What it perceives with: itself alone, no blocks around it
  LOOK = (0, 0, 0)
  #  Its own box under this high: laid level, swimming or gliding
  LEVEL = 1.0
  #  How far off its look may be before it asks for another, in degrees
  TURN = 1.0

  #  Fallback Variables

  #  Private Variables
  __body__: Any = None
  #  The keys it holds down
  __held__: set = None
  #  The tick it last perceived, and the one it last pressed jump at
  __now__: int = 0
  __jumped__: int = None

  #  Public Variables
  body = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @body.GET
  def _getBody(self) -> Any:
    """The body it plays."""
    return self.__body__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: Any) -> None:
    """The routine of 'body': a player's means (perceive, keyDown, keyUp,
    look, ticks)."""
    BaseObject.__init__(self)
    self.__body__ = body
    self.__held__ = set()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def letGo(self) -> None:
    """Every key it holds, let go."""
    for key in sorted(self.__held__):
      self.__body__.keyUp(key)
    self.__held__.clear()

  def holds(self, key: str) -> bool:
    """Whether it holds the key down."""
    return key in self.__held__

  def press(self, key: str) -> None:
    """
    One press of the key: down, and up again, two requests. A tick less
    than the body's own tap takes in the game (SPEC.md 21.24). A key it
    holds is let go first, so that the press is one.
    """
    if key in self.__held__:
      self.__body__.keyUp(key)
      self.__held__.discard(key)
    self.__body__.keyDown(key)
    self.__body__.keyUp(key)

  def _see(self) -> Perception:
    """What the body perceives now: itself, no blocks around it."""
    seen = self.__body__.perceive(*self.LOOK)
    self.__now__ = seen.tick
    return seen

  def _level(self, seen: Perception) -> bool:
    """Whether its own box lies level: swimming as 1.13 has it, or
    gliding."""
    return seen.box.maxY - seen.box.minY < self.LEVEL

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

  def _off(self, seen: Perception, yaw: float, pitch: float) -> bool:
    """Whether it looks another way than that, by more than TURN."""
    off = abs((yaw - seen.look.yaw + 180.0) % 360.0 - 180.0)
    return off > self.TURN or abs(seen.look.pitch - pitch) > self.TURN

  def _lookTo(self, seen: Perception, yaw: float, pitch: float) -> None:
    """Looks that way if it doesn't, within TURN; else lets a tick
    pass."""
    if self._off(seen, yaw, pitch):
      self.__body__.look(yaw, pitch)
    else:
      self.__body__.ticks(1)
