"""
CastMove: one move of a portal cast (SPEC.md 21.21): what it does, and
the block, the face or the spot it does it to. A value: the plan is a
row of these, and whoever plays it (the caster in a game, a world of
blocks in a test) is told the same.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.ezdata import EZData, EZField

from unittas.values import BlockPos, Vec3

from .castdoes import CastDoes
from .words import where

#  The faces of a block, as the crosshair's target names them
FACES = ('up', 'down', 'north', 'south', 'east', 'west')
#  What each kind of move is told: a block, a face of it, a spot
_BLOCK = (CastDoes.DIG, CastDoes.SCOOP_WATER, CastDoes.SCOOP_LAVA)
_FACE = (CastDoes.DIRT, CastDoes.POUR_WATER, CastDoes.POUR_LAVA,
         CastDoes.LIGHT)
_SPOT = (CastDoes.STAND, CastDoes.ENTER)
#  The sides it can lean over: a block's four, not its top or bottom
SIDES = ('north', 'south', 'east', 'west')


class CastMove(EZData, frozen=True):
  """
  A move: what it 'does'; the block 'pos' it digs, scoops from or
  clicks; the 'face' of that block it clicks (what it places lands in
  the cell beyond the face); or the 'spot' it stands at. Made with a
  part its kind lacks or can't have, it is refused at once.

    CastMove(CastDoes.DIG, BlockPos(11, 63, 20))
    CastMove(CastDoes.POUR_LAVA, BlockPos(11, 62, 20), 'up')
    CastMove(CastDoes.STAND, spot=Vec3(11.5, 64.0, 21.5))
    CastMove(CastDoes.FETCH_LAVA)

  Raises
  ------
  TypeError
    A part its kind needs is missing, or one it can't have is given.
  ValueError
    A face that is none of a block's six.
  """

  does = EZField[CastDoes](CastDoes.FETCH_LAVA)
  pos = EZField[object](None)
  face = EZField[str]('')
  spot = EZField[object](None)

  def __post_init__(self) -> None:
    does = self.does
    block = does in _BLOCK or does in _FACE
    if block != isinstance(self.pos, BlockPos):
      raise self._refused('names %s, not %r' % (
        'a block by a BlockPos' if block else 'no block', self.pos))
    faced = does in _FACE or does is CastDoes.LEAN
    if faced != bool(self.face):
      raise self._refused('names %s, not %r' % (
        'a face of its block' if does in _FACE else
        'a side to lean over' if faced else 'no face', self.face))
    if self.face and self.face not in FACES:
      raise ValueError('a block\'s faces are %s, not %r' % (
        ', '.join(FACES), self.face))
    if does is CastDoes.LEAN and self.face not in SIDES:
      raise ValueError('it leans over a side, %s, not %r' % (
        ', '.join(SIDES), self.face))
    if (does in _SPOT) != isinstance(self.spot, Vec3):
      raise self._refused('names %s, not %r' % (
        'a spot by a Vec3' if does in _SPOT else 'no spot', self.spot))

  def __str__(self) -> str:
    """The move as a person says it: 'dig the block at (11, 63, 20)'."""
    does = self.does
    if does in _SPOT:
      return '%s %s' % (does.value, where(self.spot))
    if does in (CastDoes.SCOOP_WATER, CastDoes.SCOOP_LAVA):
      return '%s %s' % (does.value, where(self.pos))
    if does is CastDoes.LEAN:
      return '%s the %s edge of what it stands on' % (does.value,
                                                      self.face)
    if does is CastDoes.DIG:
      return 'dig the block at %s' % where(self.pos)
    if does in _FACE:
      return '%s the %s face of the block at %s' % (
        does.value, self.face, where(self.pos))
    return does.value

  def _refused(self, why: str) -> TypeError:
    """The TypeError for a move its kind doesn't allow."""
    return TypeError('a move to %s %s' % (self.does.value, why))
