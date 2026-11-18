"""
CastBody: a body that shows what it is told to show and keeps what it is
asked (not a test module itself), for the caster's own checks (SPEC.md
21.21): its hotbar, what its crosshair meets after each look ('aim', a
function of the look), the blocks about it, and what a press of the use
key does to it ('onUse'). Whether a plan's clicks can be made at all is
castsim.py's to say, and the game's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any, Callable, Optional

from mcdex import MCItems

from unittas.perception import Perception
from unittas.target import Target
from unittas.values import Inventory, Item, Vec3

MEMBERS = {'minecraft:bucket': MCItems.Bucket,
           'minecraft:water_bucket': MCItems.WaterBucket,
           'minecraft:lava_bucket': MCItems.LavaBucket,
           'minecraft:dirt': MCItems.Dirt,
           'minecraft:flint_and_steel': MCItems.FlintAndSteel,
           'minecraft:iron_pickaxe': MCItems.IronPickaxe}


class CastBody:
  """
  The body, its eye at 'eye', with 'hotbar' ({slot: the game's id for
  what is in it}). 'asked' holds each request: (its name, its
  arguments).
  """

  def __init__(self, eye: Vec3, hotbar: dict, blocks: tuple = (),
               aim: Optional[Callable] = None,
               onUse: Optional[Callable] = None) -> None:
    self.eye = eye
    self.main = [Item.EMPTY] * 36
    for slot, name in hotbar.items():
      self.put(slot, name)
    self.selected = 0
    self.blocks = tuple(blocks)
    self.aim = aim
    self.onUse = onUse
    self.target = Target()
    self.asked = []
    self.tick = 0

  def put(self, slot: int, name: str) -> None:
    """The slot now holds one of what the game calls 'name'."""
    self.main[slot] = Item(name, 1)

  def named(self, name: str) -> list:
    """The arguments of each request of that name, in order."""
    return [args for asked, args in self.asked if asked == name]

  # ------------------------------------------------------------ the means

  def perceive(self, around: int = 2, below: int = 1,
               above: int = 1) -> Perception:
    self.asked.append(('perceive', (around, below, above)))
    self.tick += 1
    return Perception(tick=self.tick, eye=self.eye, blockReach=4.5,
                      pos=Vec3(self.eye.x, self.eye.y - 1.62, self.eye.z),
                      target=self.target, blocks=self.blocks)

  def look(self, yaw: float, pitch: float) -> None:
    self.asked.append(('look', (yaw, pitch)))
    self.tick += 2
    if self.aim is not None:
      self.target = self.aim(yaw, pitch)

  def tap(self, key: str) -> None:
    self.asked.append(('tap', (key,)))
    self.tick += 1
    if key.startswith('key.hotbar.'):
      self.selected = int(key.rsplit('.', 1)[-1]) - 1
    elif key == 'key.use' and self.onUse is not None:
      self.onUse(self)

  def ticks(self, n: int = 1) -> int:
    self.asked.append(('ticks', (n,)))
    self.tick += n
    return self.tick

  def keyDown(self, key: str) -> None:
    self.asked.append(('keyDown', (key,)))

  def keyUp(self, key: str) -> None:
    self.asked.append(('keyUp', (key,)))

  def inventory(self, side: Optional[str] = None) -> Inventory:
    self.asked.append(('inventory', ()))
    return Inventory(selected=self.selected, main=tuple(self.main))

  def membersOf(self, value: Any) -> frozenset:
    member = MEMBERS.get(getattr(value, 'id', None))
    return frozenset() if member is None else frozenset((member,))
