"""
Instruction: what the helper can be told (SPEC.md 21.7 step 3). An
instruction is a value: an action or an examination (unitTAS's SPEC.md
15.1), a series of them, or one that depends on an examination's answer.
Whoever gives it (a test, a person, a program) gives the same value.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.ezdata import EZData


class Instruction(EZData, frozen=True):
  """
  The base of every instruction: Action, Examination, Steps and When.
  It has no parts of its own, and the helper follows none that is only
  this.
  """
