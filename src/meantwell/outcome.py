"""
Outcome: what came of an instruction (SPEC.md 21.3, 21.7 step 3): done,
with what the agent saw; or not done, with the step, what it did and
what it saw. It is never done for a step the agent didn't complete.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.ezdata import EZData, EZField


class Outcome(EZData):
  """
  An outcome: the 'instruction'; whether it was 'done'; the line 'said'
  of it; its 'value', what the agent's step gave (what it perceived, the
  container, what moved, an examination's answer; each step's outcome
  for a series or a conditional), or None; and its 'error', the agent's
  TesttimeError when it wasn't done, or None.
  """

  instruction = EZField[object](None)
  done = EZField[bool](False)
  said = EZField[str]('')
  value = EZField[object](None)
  error = EZField[object](None)
