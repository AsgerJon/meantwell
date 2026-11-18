"""
Swimming in a real game (SPEC.md 21.16), on the practice instance: the
swimmer on the real player's body, by five of its means alone. The scene
is a pool dug and filled by command, as a scenario's setup is: three
wide, sixteen long, three deep, its water's top a little under the
ground's. Put on its bed by command (setup, not the agent), it is to
come up, stay afloat and paddle out. From one bank it is to paddle to
the other. And the walk that sank (SPEC.md 21.14) is done on purpose,
and the swimmer is to save it. Then swimming as 1.13 has it: laid level
under water from end to end, out at the bank, and through a gap one
block high that is built for it. What each took is noted under its line.

  unittas run tests.game.test_swim
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from mcdex import MCBlocks

from meantwell.swimmer import Swimmer
from unittas.errors import TesttimeError
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  The pool, from the scene's origin (the block the run's start stands
#  in): its columns, and how far down its water goes
POOL_X, POOL_Z, DEEP = range(3, 6), range(4, 20), (-1, -2, -3)
#  Its middle column, the ground before its near end and after its far
MIDDLE, NEAR_BANK, FAR_BANK = (4, 0, 11), (4, 0, 2), (4, 0, 21)
#  Columns near its two ends, in the water
NEAR_END, FAR_END = (4, 0, 5), (4, 0, 18)
#  The gap: stone in the two upper layers across these columns' rows,
#  the lowest layer left water, one block high
GAP_Z, GAP_DOWN = range(10, 13), (-1, -2)


class SwimTests(ScenarioTestCase):

  #  a swim is long by the clock too: a guard, never the verdict
  timeout_seconds = 300

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    #  the setup is by command, not the agent
    for x in POOL_X:
      for z in POOL_Z:
        for down in DEEP:
          cls.scene.place(MCBlocks.Water, at=(x, down, z))

  def setUp(self) -> None:
    #  until the seam (SPEC.md 21.7 step 1) the body is the agent's game,
    #  of which the swimmer asks five members and no others
    self.swimmer = Swimmer(self.agent.game)
    self.addCleanup(self.swimmer.letGo)
    #  the ground's level, and the water's top just under it
    self.ground = float(self.scene.origin.y)

  def place(self, offset: tuple) -> Vec3:
    """The floor's middle of the place 'offset' from the origin."""
    return self.scene.at(offset).center()

  def assertOut(self, seen) -> None:
    """On the ground beyond the pool's far end, out of the water."""
    self.assertTrue(seen.onGround, seen.pos)
    self.assertFalse(seen.inWater, seen.pos)
    self.assertGreater(seen.pos.z, self.scene.at(FAR_BANK).z - 1.5)
    self.assertAlmostEqual(self.ground, seen.pos.y, delta=0.1)

  def swumOut(self, what: str) -> None:
    """The swim to the far bank from where it is, noted."""
    before = self.agent.perceive()
    seen = self.swimmer.paddle(self.place(FAR_BANK))
    self.scene.note('%s: swam %.1f blocks and out in %d ticks, to (%.1f, '
                    '%.1f, %.1f)' % (what, seen.pos.z - before.pos.z,
                                     seen.tick - before.tick, seen.pos.x,
                                     seen.pos.y, seen.pos.z))
    self.assertOut(seen)

  def onTheBed(self, offset: tuple) -> Vec3:
    """Put on the pool's bed in the column 'offset', by command: the
    setup, not the agent. Where it stands then."""
    column = self.scene.at(offset)
    bed = Vec3(column.x + 0.5, self.ground + min(DEEP), column.z + 0.5)
    self.game.teleport(bed)
    self.agent.wait(10)
    return bed

  def swum(self, what: str, place: Vec3):
    """The swim as 1.13 has it, from where it is to 'place', noted."""
    before = self.agent.perceive()
    seen = self.swimmer.swim(place)
    blocks = math.dist((before.pos.x, before.pos.y, before.pos.z),
                       (seen.pos.x, seen.pos.y, seen.pos.z))
    ticks = seen.tick - before.tick
    self.scene.note('%s: swam %.1f blocks in %d ticks (%.2f a tick), laid '
                    'level at %d of its looks, to (%.1f, %.1f, %.1f)' % (
                      what, blocks, ticks, blocks / max(1, ticks),
                      self.swimmer.level, seen.pos.x, seen.pos.y,
                      seen.pos.z))
    self.assertGreater(self.swimmer.level, 5, 'laid level, one block high')
    return seen

  def test_1_from_the_bed_up_afloat_and_out(self) -> None:
    middle = self.scene.at(MIDDLE)
    bed = Vec3(middle.x + 0.5, self.ground + min(DEEP), middle.z + 0.5)
    self.game.teleport(bed)
    self.agent.wait(10)
    under = self.agent.perceive()
    self.assertTrue(under.inWater, under.pos)
    self.assertLess(under.pos.y, self.ground - 2.0, 'on the bed')
    up = self.swimmer.surface()
    self.scene.note('surfaced: from y %.2f to y %.2f in %d ticks (the '
                    'ground is at %.2f)' % (under.pos.y, up.pos.y,
                                            up.tick - under.tick,
                                            self.ground))
    self.assertGreater(up.pos.y, self.ground - 1.0, 'at the water\'s top')
    lowest = up.pos.y
    for _ in range(12):
      self.agent.wait(5)
      lowest = min(lowest, self.agent.perceive().pos.y)
    self.scene.note('afloat 60 ticks, jump held: never under y %.2f' % (
      lowest,))
    self.assertGreater(lowest, self.ground - 1.0, 'afloat')
    self.swumOut('from the middle')

  def test_2_from_bank_to_bank(self) -> None:
    self.agent.walkTo(self.place(NEAR_BANK))
    self.swumOut('from the near bank')

  def test_3_the_walk_that_sank_is_saved(self) -> None:
    try:
      self.agent.walkTo(self.place(MIDDLE))
      said = 'walkTo returned as arrived'
    except TesttimeError as error:
      said = 'walkTo raised: %s' % (error,)
    self.agent.wait(40)
    sunk = self.agent.perceive()
    self.scene.note('the walk to a place in water: %s; 40 ticks on it is at '
                    'y %.2f, in water: %s' % (said, sunk.pos.y,
                                             sunk.inWater))
    self.assertTrue(sunk.inWater, sunk.pos)
    up = self.swimmer.surface()
    self.scene.note('surfaced: from y %.2f to y %.2f in %d ticks' % (
      sunk.pos.y, up.pos.y, up.tick - sunk.tick))
    self.assertGreater(up.pos.y, self.ground - 1.0)
    self.swumOut('after the walk that sank')

  def test_4_swum_level_under_water_from_end_to_end(self) -> None:
    self.onTheBed(NEAR_END)
    far = self.scene.at(FAR_END)
    place = Vec3(far.x + 0.5, self.ground - 2.5, far.z + 0.5)
    seen = self.swum('under water', place)
    self.assertLess(math.dist((place.x, place.y, place.z),
                              (seen.pos.x, seen.pos.y, seen.pos.z)), 0.9)
    self.assertTrue(seen.inWater)

  def test_5_swum_to_the_bank_and_out(self) -> None:
    self.onTheBed(NEAR_END)
    self.assertOut(self.swum('to the bank', self.place(FAR_BANK)))

  def test_6_through_a_gap_one_block_high(self) -> None:
    #  the setup, by command: stone over the lowest layer of water
    for x in POOL_X:
      for z in GAP_Z:
        for down in GAP_DOWN:
          self.scene.place(MCBlocks.Stone, at=(x, down, z))
    self.onTheBed(NEAR_END)
    far = self.scene.at(FAR_END)
    place = Vec3(far.x + 0.5, self.ground + min(DEEP) + 0.1, far.z + 0.5)
    seen = self.swum('through the gap', place)
    self.assertGreater(seen.pos.z, self.scene.at((4, 0, max(GAP_Z))).z + 1)
