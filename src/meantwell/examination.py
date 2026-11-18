"""
Examination: something the agent is asked about the world (SPEC.md 21.7
step 3), answered by its own means alone: what it knows of itself, what
an open screen shows it, what it sees. An examination by command is a
test's, in unitTAS's scenes, and never one of these (SPEC.md 21.4).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from mcdex import MCThing
from worktoy.ezdata import EZField

from unittas.values import BlockPos

from .instruction import Instruction
from .question import Question
from .words import named, where


class Examination(Instruction, frozen=True):
  """
  An examination: what it 'asks'; for what a block is, the block's
  'place' (a BlockPos) and the candidates it is told 'among' (mcdex
  members; none for every full cube the game's version has). Naming a
  few candidates gives the agent a significant advantage (unitTAS's
  Agent.identify).

    Examination(Question.INVENTORY)
    Examination(Question.IDENTIFY, BlockPos(3, 4, 6),
                (MCBlocks.Stone, MCBlocks.Bedrock))

  Raises
  ------
  TypeError
    A part its question needs is missing, one it can't have is given, or
    one is of the wrong kind.
  """

  asks = EZField[Question](Question.INVENTORY)
  place = EZField[object](None)
  among = EZField[tuple]()

  def __post_init__(self) -> None:
    if self.asks is not Question.IDENTIFY:
      if self.place is not None or self.among:
        raise self._refused('names no place and no candidates')
      return
    if not isinstance(self.place, BlockPos):
      raise self._refused('names its block\'s place by a BlockPos, not '
                          '%r' % (self.place,))
    for each in self.among:
      if not isinstance(each, MCThing):
        raise self._refused('names its candidates by mcdex members, not '
                            '%r' % (each,))

  def __str__(self) -> str:
    """The examination as a person says it: 'inventory'."""
    if self.asks is not Question.IDENTIFY:
      return self.asks.value
    said = 'identify the block at %s' % where(self.place)
    if self.among:
      said += ' among %s' % ', '.join(named(each) for each in self.among)
    return said

  def _refused(self, why: str) -> TypeError:
    """The TypeError for an examination its question doesn't allow."""
    return TypeError('the examination \'%s\' %s' % (self.asks.value, why))
