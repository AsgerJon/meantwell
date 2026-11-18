"""
StoppedAgent: an agent that perceives as the grid agent does and can't
walk at all (not a test module itself), for the traveller's test of a
leg the agent can't complete (SPEC.md 21.11, M1).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Optional

from gridworld import GridAgent
from unittas.errors import TesttimeError
from unittas.perception import Perception
from unittas.values import Vec3


class StoppedAgent:
  """The grid agent's perceive; a walkTo that is noted and then raises
  the agent's TesttimeError. 'asked' counts the walks asked for."""

  def __init__(self, grid: GridAgent) -> None:
    self.grid = grid
    self.asked = 0

  def perceive(self, *look: int) -> Perception:
    return self.grid.perceive(*look)

  def walkTo(self, place: Vec3, within: float = 0.25,
             ticks: Optional[int] = None) -> Perception:
    self.asked += 1
    raise TesttimeError('walkTo', self.grid.perceive(),
                        'blocked by something it can\'t see')
