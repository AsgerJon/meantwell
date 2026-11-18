"""
LookBody: a body that keeps each look it is asked for (not a test module
itself), for the tests of how the look is turned (SPEC.md 21.22). A look
takes two ticks, as the practice game's does; every other request it is
asked is kept by name and takes one.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any

from unittas.perception import Perception
from unittas.values import Look


class LookBody:
  """The body, looking 'yaw' and 'pitch' to begin with. 'looks' holds
  each look asked for, 'asked' each other request: (name, arguments)."""

  def __init__(self, yaw: float = 0.0, pitch: float = 0.0) -> None:
    self.yaw, self.pitch = yaw, pitch
    self.looks = []
    self.asked = []
    self.tick = 0
    self.reach = 4.5

  def look(self, yaw: float, pitch: float) -> None:
    self.looks.append((yaw, pitch))
    self.asked.append(('look', (yaw, pitch)))
    self.yaw, self.pitch = yaw, pitch
    self.tick += 2

  def perceive(self, *args: Any) -> Perception:
    self.asked.append(('perceive', args))
    self.tick += 1
    return Perception(tick=self.tick, look=Look(self.yaw, self.pitch))

  def keyDown(self, key: str) -> None:
    self.asked.append(('keyDown', (key,)))
    self.tick += 1

  def keyUp(self, key: str) -> None:
    self.asked.append(('keyUp', (key,)))
    self.tick += 1

  def tap(self, key: str) -> None:
    self.asked.append(('tap', (key,)))
    self.tick += 1
