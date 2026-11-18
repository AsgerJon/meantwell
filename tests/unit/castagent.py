"""
CastAgent: an agent as far as the caster asks one (not a test module
itself; SPEC.md 21.21): its body, and the two steps the caster leaves to
it, walking to a spot and breaking a block, each kept as asked.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any

from castbody import CastBody
from unittas.perception import Perception
from unittas.values import Vec3


class CastAgent:
  """The agent of 'body'; 'asked' holds each step: (its name, its
  arguments)."""

  def __init__(self, body: CastBody) -> None:
    self.game = body
    self.asked = []

  def perceive(self, *args: Any) -> Perception:
    return self.game.perceive(*args)

  def walkTo(self, place: Any, within: float = 0.25) -> Perception:
    self.asked.append(('walkTo', (place, within)))
    self.game.eye = Vec3(place.x, place.y + 1.62, place.z)
    return self.game.perceive()

  def breakBlock(self, pos: Any) -> Perception:
    self.asked.append(('breakBlock', (pos,)))
    return self.game.perceive()
