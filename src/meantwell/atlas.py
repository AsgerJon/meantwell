"""
Atlas: what the agent remembers of the ground (SPEC.md 21.11, M1). One
look shows the blocks around the player; the atlas keeps every look's,
so a way can be found across more ground than one look shows.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from unittas.perception import Perception

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional

  from unittas.values import Vec3

_EPS = 1e-6
_BESIDE = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Atlas(BaseObject):
  """
  The ground as the agent was shown it, look by look. A look shows the
  blocks that aren't air within 'around' columns of the player's, from
  'below' blocks under its feet's block to 'above' over its head's
  (unitTAS's player.perceive): those blocks are remembered, and the rest
  of that box is known to be air. A later look replaces an earlier
  one's, cell by cell; what it doesn't show stays as it was remembered.
  A column is known once any of it was shown.

  What it remembers around a place is given as one perception, so
  unittas's own Terrain says what a player can walk there. A column not
  yet shown holds nothing, so it is no way: the edge of what was shown
  is where to go and look further.

    atlas = Atlas()
    atlas.note(agent.perceive(8, 3, 3), 8, 3, 3)
    terrain = Terrain(atlas.ground(seen.pos, 24), 24, 0, 0)
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  #  Each remembered block that isn't air, a NearBlock, by its (x, y, z)
  __blocks__: dict = None
  #  The heights shown of each known column, by its (x, z)
  __known__: dict = None
  #  How many looks were noted
  __looks__: int = 0

  #  Public Variables
  looks = Field()
  columns = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @looks.GET
  def _getLooks(self) -> int:
    """How many looks were noted."""
    return self.__looks__

  @columns.GET
  def _getColumns(self) -> int:
    """How many columns are known."""
    return len(self.__known__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self) -> None:
    """An atlas with nothing remembered."""
    BaseObject.__init__(self)
    self.__blocks__ = {}
    self.__known__ = {}

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def note(self, seen: Perception, around: int, below: int,
           above: int) -> None:
    """
    Remembers a look: 'seen', as it was perceived with 'around', 'below'
    and 'above'.

    Raises
    ------
    TypeError
      'seen' is no perception.
    ValueError
      A reach below 0.
    """
    if not isinstance(seen, Perception):
      raise TypeError('an atlas notes a Perception, not %r' % (seen,))
    for name, reach in (('around', around), ('below', below),
                        ('above', above)):
      if reach < 0:
        raise ValueError('a look\'s %s is 0 or more, not %r' % (name, reach))
    fx, fz = math.floor(seen.pos.x), math.floor(seen.pos.z)
    feet = math.floor(seen.pos.y + _EPS)
    heights = range(feet - below, feet + 1 + above + 1)
    shown = {(near.pos.x, near.pos.y, near.pos.z): near
             for near in seen.blocks}
    for x in range(fx - around, fx + around + 1):
      for z in range(fz - around, fz + around + 1):
        self.__known__.setdefault((x, z), set()).update(heights)
        for y in heights:
          if (x, y, z) not in shown:
            self.__blocks__.pop((x, y, z), None)
    #  every block shown, one outside the box as reckoned here too
    for (x, y, z), near in shown.items():
      self.__blocks__[(x, y, z)] = near
      self.__known__.setdefault((x, z), set()).add(y)
    self.__looks__ += 1

  def knows(self, x: int, z: int) -> bool:
    """Whether any of the column (x, z) was shown."""
    return (x, z) in self.__known__

  def known(self, x: int, y: int, z: int) -> bool:
    """Whether the cell (x, y, z) was shown: a block, or air."""
    return y in self.__known__.get((x, z), ())

  def block(self, x: int, y: int, z: int) -> Optional[Any]:
    """The block remembered at (x, y, z), a NearBlock; None for air, or
    for a cell not shown ('known' says which)."""
    return self.__blocks__.get((x, y, z))

  def ground(self, pos: Vec3, around: int) -> Perception:
    """
    What is remembered within 'around' columns of 'pos', as one
    perception from there: its blocks, whatever their height.
    """
    cx, cz = math.floor(pos.x), math.floor(pos.z)
    blocks = tuple(near for (x, _, z), near in self.__blocks__.items()
                   if abs(x - cx) <= around and abs(z - cz) <= around)
    return Perception(pos=pos, blocks=blocks)

  def edges(self, x: int, z: int, around: int) -> tuple:
    """
    The known columns within 'around' of (x, z) that have a column not
    known beside them: where what was shown ends. Each (x, z), in order.
    """
    known = self.__known__
    return tuple(sorted(
      (kx, kz) for kx, kz in known
      if abs(kx - x) <= around and abs(kz - z) <= around and
      any((kx + dx, kz + dz) not in known for dx, dz in _BESIDE)))
