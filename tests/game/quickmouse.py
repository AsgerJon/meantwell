"""
QuickMouse: the mouse at a speedrunner's pace (not a test module
itself), for the game tests of how fast the robot's hand can be (SPEC.md
21.24 K1). A flick: it asks each tick for all that is left, as fast as
it may quicken, and so comes to its look in a tick or two once it is
within its fastest of it; where the mouse a walk is turned by slows down
all the way in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from meantwell.mouse import Mouse


class QuickMouse(Mouse):
  """The mouse, turning 40 degrees a tick at most and quickening by 20,
  with no slowing but what is left to turn."""

  KP, KD = 1.0, 0.0
  QUICKEN, FASTEST, SLOWEST = 20.0, 40.0, 2.0
