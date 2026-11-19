"""
How fast the robot's hand is, measured in a real game (SPEC.md 21.24
K1), on the practice instance in a flat world played in survival: a
portal cast in a lake of lava in under ten seconds is some 25 aims and
clicks in 200 ticks, and this page finds what an aim and its click cost.

By command: two holes one block deep in the ground, ground between
them, a set angle apart as seen from where the robot stands, lava in
the first; an empty bucket
in its hand. Then, by a player's means alone (the mouse's rate, the use
key): the lava scooped from one hole and poured into the other, there
and back, ten uses. Each lane is an angle and a mouse: the mouse as a
walk has it, and a quick one. What is read: the ticks ten uses took,
and by command, that the lava is where ten uses leave it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from mcdex import MCBlocks, MCItems

from meantwell.mouse import Mouse
from tests.game.quickmouse import QuickMouse
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  The two holes of each lane, from where the robot stands (x, z), and
#  how far apart they are seen from there, in degrees
PAIRS = {45: ((0, 2), (2, 2)), 53: ((-1, 2), (1, 2)),
         127: ((-2, 1), (2, 1))}
USES = 10
EYE = 1.62


class HandsTests(ScenarioTestCase):

  #  a guard by the clock, never the verdict
  timeout_seconds = 300
  world = {'type': 'flat', 'game_mode': 'survival', 'cheats': True,
           'structures': False}

  def played(self, lane: int, apart: int, mouse: type) -> None:
    """Ten uses between the two holes 'apart' degrees apart, in the
    lane 'lane', with a mouse of the class 'mouse'; noted."""
    shift = 12 * lane
    first, second = PAIRS[apart]
    holes = [self.scene.at((shift + x, -1, z)) for x, z in (first, second)]
    #  the setup, by command
    for hole in holes:
      self.game.setBlock(hole, MCBlocks.Air)
    self.game.setBlock(holes[0], MCBlocks.Lava)
    self.game.teleport(self.scene.at((shift, 0, 0)).center())
    self.game.setSlot('main.0', MCItems.Bucket)
    self.agent.wait(10)
    self.game.tap('key.hotbar.1')
    hand = mouse(self.game)
    seen = self.agent.perceive()
    eye = seen.pos.y + EYE
    aims = []
    for hole in holes:
      #  the hole's far wall, high on it: what a look down into a hole
      #  one deep comes to, over its near rim (its floor's middle is hid
      #  by the rim: the first run's crosshair lay on the grass before
      #  it). Lava poured on that wall is in the hole; a scoop's ray
      #  goes through the lava to it
      dx = hole.x + 0.5 - seen.pos.x
      dz = hole.z + 1.0 - seen.pos.z
      aims.append((math.degrees(math.atan2(-dx, dz)), math.degrees(
        math.atan2(eye - (hole.y + 0.7), math.hypot(dx, dz)))))
    hand.look(*aims[0])
    looks, presses = [], []
    for use in range(USES):
      #  scoop from one, pour into the other, and back; each look and
      #  each press timed by a perception before and after it (a tick
      #  each, taken off)
      before = self.agent.perceive().tick
      hand.look(*aims[(use + 1) // 2 % 2])
      between = self.agent.perceive().tick
      #  a press as two requests, down and up: a tick less than a tap
      self.game.keyDown('key.use')
      self.game.keyUp('key.use')
      presses.append(self.agent.perceive().tick - between - 1)
      looks.append(between - before - 1)
    self.agent.wait(10)
    held = self.game.inventory().main[0].id
    lava = [self.game.block(hole).id for hole in holes]
    whole = sum(looks) + sum(presses)
    self.scene.note(
      '%d degrees apart, %s: %d uses in %d ticks, %.1f a use (its looks '
      '%s, its presses %s); it holds %s; the holes hold %s and %s' % (
        apart, mouse.__name__, USES, whole, whole / USES, looks, presses,
        held, lava[0], lava[1]))
    #  ten uses: five scoops and five pours, the last a pour into the
    #  second hole
    self.assertEqual('minecraft:bucket', held)
    self.assertEqual(['minecraft:air', 'minecraft:lava'], lava)

  def test_1_the_holes_45_degrees_apart(self) -> None:
    self.played(0, 45, Mouse)
    self.played(1, 45, QuickMouse)

  def test_2_the_holes_53_degrees_apart(self) -> None:
    self.played(2, 53, Mouse)
    self.played(3, 53, QuickMouse)

  def test_3_the_holes_127_degrees_apart(self) -> None:
    self.played(4, 127, Mouse)
    self.played(5, 127, QuickMouse)
