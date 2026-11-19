"""
Bearings: a game with each bearing a turning rate was answered with kept
(not a test module itself), for the game tests of the mouse and the
walker (SPEC.md 21.23 W6): how the look turned from tick to tick as the
game had it, and which answers came a tick late.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any


class Bearings:
  """
  The game's own members, passed on as they are. 'kept' holds each
  bearing a mouseRate was answered with, in turn.
  """

  def __init__(self, game: Any) -> None:
    self.game = game
    self.kept = []

  def __getattr__(self, name: str) -> Any:
    if name.startswith('__'):
      raise AttributeError(name)
    return getattr(self.game, name)

  def mouseRate(self, yaw: float, pitch: float) -> Any:
    bearing = self.game.mouseRate(yaw, pitch)
    self.kept.append(bearing)
    return bearing

  def turn(self) -> float:
    """The most the look turned in a tick between two answers, in
    degrees; 0 with fewer than two."""
    most = 0.0
    for before, after in zip(self.kept, self.kept[1:]):
      ticks = max(1, after.tick - before.tick)
      yaw = (after.look.yaw - before.look.yaw + 180.0) % 360.0 - 180.0
      pitch = after.look.pitch - before.look.pitch
      most = max(most, (yaw * yaw + pitch * pitch) ** 0.5 / ticks)
    return most

  def late(self) -> int:
    """How many answers came more than a tick after the one before."""
    return sum(1 for before, after in zip(self.kept, self.kept[1:])
               if after.tick - before.tick > 1)

  def lowest(self) -> float:
    """The least height its feet were at, of the answers kept."""
    return min(each.pos.y for each in self.kept)
