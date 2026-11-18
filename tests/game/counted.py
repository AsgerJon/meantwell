"""
Counted: the agent with its looks and walks counted (not a test module
itself), for the game tests of what stands above perceive and walkTo
(SPEC.md 21.12): how many of each a trip took, and how many of the
game's ticks went by.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any, Optional


class Counted:
  """
  The agent's perceive and walkTo, passed on as they are. 'looks' and
  'legs' count them; 'failed' counts the walks the agent couldn't
  complete; 'ticks' is how many of the game's ticks went by from the
  first perception to the last.
  """

  def __init__(self, agent: Any) -> None:
    self.agent = agent
    self.looks = 0
    self.legs = 0
    self.failed = 0
    self.first = None
    self.last = None

  @property
  def ticks(self) -> int:
    """The game's ticks from the first perception to the last."""
    return 0 if self.first is None else self.last - self.first

  def _seen(self, seen: Any) -> Any:
    if self.first is None:
      self.first = seen.tick
    self.last = seen.tick
    return seen

  def perceive(self, *look: int) -> Any:
    self.looks += 1
    return self._seen(self.agent.perceive(*look))

  def walkTo(self, place: Any, within: float = 0.25,
             ticks: Optional[int] = None) -> Any:
    self.legs += 1
    try:
      return self._seen(self.agent.walkTo(place, within, ticks))
    except Exception:
      self.failed += 1
      raise
