"""
When: an instruction that depends on what an examination finds (SPEC.md
21.7 step 3; unitTAS's SPEC.md 15.1: "actions, possibly conditional on
anything"). The agent is asked first; what follows depends on whether
the answer holds the thing named.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from mcdex import MCThing
from worktoy.ezdata import EZField

from .examination import Examination
from .instruction import Instruction
from .question import Question
from .words import named, where

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

#  The questions whose answers are mcdex members. An open container's
#  stacks are the game's own ids until the agent reads them back by
#  member, so 'contents' is not among them.
_BY_MEMBER = (Question.INVENTORY, Question.IDENTIFY)


class When(Instruction, frozen=True):
  """
  A conditional: the examination it 'asks' (the inventory, or what a
  block is); the mcdex member the answer 'holds' for it to be so (in the
  inventory; what the block is); the instruction followed 'then', and
  the one followed 'otherwise', or None for nothing.

    When(Examination(Question.INVENTORY), MCItems.PinkWool,
         Action(Verb.PUT, MCItems.PinkWool))

  Raises
  ------
  TypeError
    A part of the wrong kind, or an examination whose answer names no
    mcdex member.
  """

  asks = EZField[object](None)
  holds = EZField[object](None)
  then = EZField[object](None)
  otherwise = EZField[object](None)

  def __post_init__(self) -> None:
    if not isinstance(self.asks, Examination):
      raise TypeError('a conditional asks an examination, not %r' % (
        self.asks,))
    if self.asks.asks not in _BY_MEMBER:
      infoSpec = """a conditional asks the inventory or what a block is,
      whose answers are mcdex members, not '%s'"""
      raise TypeError(' '.join((infoSpec % (self.asks.asks.value,)).split()))
    if not isinstance(self.holds, MCThing):
      raise TypeError('a conditional\'s answer holds an mcdex member, not '
                      '%r' % (self.holds,))
    if not isinstance(self.then, Instruction):
      raise TypeError('what follows a conditional is an instruction, not '
                      '%r' % (self.then,))
    if not (self.otherwise is None or isinstance(self.otherwise,
                                                 Instruction)):
      raise TypeError('what follows a conditional otherwise is an '
                      'instruction or None, not %r' % (self.otherwise,))

  def __str__(self) -> str:
    """The conditional as a person says it, with what follows."""
    said = 'when %s: %s' % (self.condition, self.then)
    if self.otherwise is not None:
      said += '; otherwise: %s' % (self.otherwise,)
    return said

  @property
  def condition(self) -> str:
    """What must be so: 'its inventory holds MCItems.PinkWool'."""
    if self.asks.asks is Question.INVENTORY:
      return 'its inventory holds %s' % named(self.holds)
    return 'the block at %s is %s' % (where(self.asks.place),
                                      named(self.holds))

  def isSo(self, answer: Any) -> bool:
    """Whether the examination's answer holds the thing named."""
    if self.asks.asks is Question.INVENTORY:
      return self.holds in answer
    return answer is self.holds
