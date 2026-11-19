"""
LookBody: a body that keeps how its look turns, tick by tick (not a
test module itself), for the tests of the mouse (SPEC.md 21.22, 21.23
W6). Every request waits for the end of the next tick, as the probe runs
a step there; in each tick the look turns by the rate in force, as the
game turns it at every frame. A look set outright is there at that
tick's end and stops the rate; a rate asked is in force from the tick
after, and is answered with the bearing as it is before it acts.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any

from unittas.bearing import Bearing
from unittas.mouserate import MouseRate
from unittas.perception import Perception
from unittas.values import Look, Vec3


class LookBody:
  """The body, looking 'yaw' and 'pitch' to begin with. 'track' holds
  its look at each tick's end, 'looks' each look set outright, 'rates'
  each rate asked, 'asked' each request: (name, arguments)."""

  def __init__(self, yaw: float = 0.0, pitch: float = 0.0) -> None:
    self.yaw, self.pitch = yaw, pitch
    self.rate = 0.0, 0.0
    self.track = []
    self.looks = []
    self.rates = []
    self.asked = []
    self.tick = 0
    self.reach = 4.5

  def _tick(self) -> None:
    """A tick of the game: the look turned by the rate in force."""
    self.tick += 1
    self.yaw = (self.yaw + self.rate[0] + 180.0) % 360.0 - 180.0
    self.pitch = min(max(self.pitch + self.rate[1], -90.0), 90.0)
    self.track.append((self.yaw, self.pitch))

  def look(self, yaw: float, pitch: float) -> None:
    self.asked.append(('look', (yaw, pitch)))
    self._tick()
    self.yaw, self.pitch = yaw, pitch
    self.rate = 0.0, 0.0
    self.looks.append((yaw, pitch))
    self.track[-1] = yaw, pitch

  def mouseRate(self, yaw: float, pitch: float) -> Bearing:
    self.asked.append(('mouseRate', (yaw, pitch)))
    self._tick()
    self.rate = float(yaw), float(pitch)
    self.rates.append(self.rate)
    return Bearing(tick=self.tick, pos=Vec3(0.0, 0.0, 0.0),
                   look=Look(self.yaw, self.pitch),
                   motion=Vec3(0.0, 0.0, 0.0))

  def perceive(self, *args: Any) -> Perception:
    self.asked.append(('perceive', args))
    self._tick()
    return Perception(tick=self.tick, look=Look(self.yaw, self.pitch),
                      mouseRate=MouseRate(self.rate[0], self.rate[1], 0))

  def keyDown(self, key: str) -> None:
    self.asked.append(('keyDown', (key,)))
    self._tick()

  def keyUp(self, key: str) -> None:
    self.asked.append(('keyUp', (key,)))
    self._tick()

  def tap(self, key: str) -> None:
    self.asked.append(('tap', (key,)))
    self._tick()
