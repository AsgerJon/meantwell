"""
Trips across natural terrain in a real game (SPEC.md 21.11, 21.12), on
the practice instance: a world as the game makes it, from a fixed seed,
and the traveller sent 40 blocks each way from where the game put the
player, and 80 one way. This is practice: what real ground does to a
trip is what is wanted. A trip that arrives is ok; one the traveller
couldn't complete is the test's ERROR, with why, where it stood and the
picture the run takes there. Each trip's legs, looks and ticks are noted
either way.

  unittas run tests.game.test_wild
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from mcdex import MCBlocks

from meantwell.traveller import Traveller
from tests.game.counted import Counted
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  a whole number, as the game's version takes a seed
SEED = 20261118
#  how far from the column asked for a place to stand is looked for
NEAR = 6


class WildTests(ScenarioTestCase):

  #  a world of the class's own, as the game makes one from the seed
  world = {'type': 'default', 'seed': SEED}
  #  a trip is long by the clock too: a guard, never the verdict
  timeout_seconds = 300

  def trip(self, dx: int, dz: int) -> None:
    """
    The traveller's trip to the ground (dx, dz) columns from where it
    stands, noted. The place is the test's to pick, by command: on the
    top block there that stops a player. Skipped when that is water.
    """
    start = self.agent.perceive().pos
    found = self.ground(math.floor(start.x) + dx, math.floor(start.z) + dz)
    if found is None:
      self.skipTest('within %d columns of the place (%d, %d) columns off '
                    'there is only water and trees\' tops: no place to '
                    'stand' % (NEAR, dx, dz))
    ground, top = found
    goal = Vec3(ground.x + 0.5, ground.y + 1.0, ground.z + 0.5)
    counted = Counted(self.agent)
    try:
      Traveller(counted).travel(goal)
    finally:
      seen = self.agent.perceive()
      short = math.hypot(goal.x - seen.pos.x, goal.z - seen.pos.z)
      infoSpec = """trip to (%.1f, %.1f, %.1f) on %s, from (%.1f, %.1f,
      %.1f): %d legs (%d not completed), %d looks, %d ticks; it stands
      %.2f short, at (%.1f, %.1f, %.1f)"""
      self.scene.note(' '.join((infoSpec % (
        goal.x, goal.y, goal.z, top.id, start.x, start.y, start.z,
        counted.legs, counted.failed, counted.looks, counted.ticks, short,
        seen.pos.x, seen.pos.y, seen.pos.z)).split()))
    self.assertLessEqual(short, 0.25)

  def ground(self, x: int, z: int):
    """
    The ground a player can stand on at the column (x, z) or the nearest
    to it within NEAR, with the block there: (its place, the block). Its
    top block is no water and no tree's leaves (the game's height map
    gives a tree's top, where no walking player gets). None when there
    is none.
    """
    near = sorted(((dx, dz) for dx in range(-NEAR, NEAR + 1)
                   for dz in range(-NEAR, NEAR + 1)),
                  key=lambda each: (math.hypot(*each), each))
    for dx, dz in near:
      ground = self.game.ground(x + dx, z + dz)
      top = self.game.block(ground)
      members = self.game.membersOf(top)
      if MCBlocks.Water in members or any(
          each.name.endswith('Leaves') for each in members):
        continue
      return ground, top
    return None

  def test_1_south(self) -> None:
    self.trip(0, 40)

  def test_2_north(self) -> None:
    self.trip(0, -40)

  def test_3_east(self) -> None:
    self.trip(40, 0)

  def test_4_west(self) -> None:
    self.trip(-40, 0)

  def test_5_far_east(self) -> None:
    self.trip(80, 0)
