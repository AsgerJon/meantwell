"""
Steps: a series of instructions, followed in order (SPEC.md 21.7 step 3;
unitTAS's SPEC.md 15.1: "a series of abstractly defined actions"). The
series stops at the first step not done: the steps after it count on it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.ezdata import EZField

from .instruction import Instruction


class Steps(Instruction, frozen=True):
  """
  A series: its 'steps', one instruction or more, a series among them
  if need be.

    Steps((Action(Verb.OPEN, MCBlocks.Chest, chest),
           Action(Verb.TAKE, MCItems.PinkWool), Action(Verb.CLOSE)))

  Raises
  ------
  TypeError
    No steps, or one that is no instruction.
  """

  steps = EZField[tuple]()

  def __post_init__(self) -> None:
    if not self.steps:
      raise TypeError('a series has one step or more, not none')
    for each in self.steps:
      if not isinstance(each, Instruction):
        raise TypeError('a series\' steps are instructions, not %r' % (
          each,))

  def __str__(self) -> str:
    """The series as a person says it: '3 steps'."""
    return '%d step%s' % (len(self.steps), '' if len(self.steps) == 1
                          else 's')
