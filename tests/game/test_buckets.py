"""
What a bucket does by a player's means, measured in a real game (SPEC.md
21.20), on the practice instance in a flat world played in survival: the
ground for a routine that builds a nether portal from a pool of lava.
Each test has a lane of its own, 12 blocks from the last, so that none
meets what another poured. In it, by command: a pool of lava, two by
two, sunk in the ground; a stone to stand on, out of the water's way;
the robot on it, a bucket and a water bucket in its hotbar. Then, by a
player's means alone (the look, the hotbar's keys, the use key), it
scoops lava, pours it out, pours water beside it, and scoops the water
back. What the game holds after each is read by command and noted under
the test's line: which block is where, tick by tick. The verdicts are
few: this page is here to find out.

  unittas run tests.game.test_buckets
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from mcdex import MCBlocks, MCItems

from unittas.scenario import ScenarioTestCase
from unittas.values import BlockPos, Item, Vec3

#  The pool, from the scene's origin: its four cells, sunk in the ground
POOL = ((3, -1, 4), (4, -1, 4), (3, -1, 5), (4, -1, 5))
#  Where it stands to work, and the hotbar: the bucket, the water
STAND = (3, 0, 2)
BUCKET, WATER = 1, 2


class BucketTests(ScenarioTestCase):

  #  a guard by the clock, never the verdict
  timeout_seconds = 300
  #  survival: a bucket is spent and filled as a speedrunner's is
  world = {'type': 'flat', 'game_mode': 'survival', 'cheats': True,
           'structures': False}

  def setUp(self) -> None:
    #  the test's own lane, by its number
    self.lane = 12 * (int(self._testMethodName.split('_')[1]) - 1)
    #  the setup, by command: the pool, the stone and the robot on it,
    #  the buckets in its hotbar
    for cell in POOL:
      self.scene.place(MCBlocks.Lava, at=self.shifted(cell))
    self.scene.place(MCBlocks.Stone, at=self.shifted(STAND))
    top = self.cell(STAND)
    self.game.teleport(Vec3(top.x + 0.5, top.y + 1.0, top.z + 0.5))
    #  survival by command too: the world asked for it and was made
    #  creative (found 2026-11-18: no hearts in the frame, and a bucket
    #  that filled without being spent)
    said = self.game.command('gamemode survival')
    self.scene.note('gamemode survival, by command: %s' % (
      '; '.join(said.lines) or 'nothing said'))
    self.game.setSlot('main.0', MCItems.Bucket)
    self.game.setSlot('main.1', MCItems.WaterBucket)
    self.game.setSlot('main.2', Item.EMPTY)
    self.agent.wait(10)
    self.body = self.agent.game

  def shifted(self, offset: tuple) -> tuple:
    """The offset in this test's lane."""
    return offset[0], offset[1], offset[2] + self.lane

  def cell(self, offset: tuple) -> BlockPos:
    """The place 'offset' from the origin, in this test's lane."""
    return self.scene.at(self.shifted(offset))

  def held(self) -> str:
    """What it knows it has, as names."""
    return ', '.join(sorted(each.name for each in self.agent.inventory()))

  def there(self, offset: tuple) -> str:
    """The block at the place, by command: its id and its level."""
    block = self.game.block(self.cell(offset))
    level = block.properties.get('level')
    return block.id.split(':')[-1] + ('' if level is None else '.' + level)

  def aimed(self, offset: tuple, up: float) -> None:
    """Its look turned to the cell's middle, 'up' above the cell's
    floor, by a player's means."""
    cell = self.cell(offset)
    eye = self.body.perceive(0, 0, 0).eye
    dx, dz = cell.x + 0.5 - eye.x, cell.z + 0.5 - eye.z
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(math.atan2(eye.y - (cell.y + up),
                                    math.hypot(dx, dz)))
    self.body.look(yaw, pitch)
    self.body.ticks(2)

  def used(self, slot: int, offset: tuple, up: float, what: str) -> None:
    """The hotbar's slot chosen by its key, the look turned, one press
    of the use key; then what is where, noted."""
    self.body.tap('key.hotbar.%d' % slot)
    self.aimed(offset, up)
    seen = self.body.perceive(0, 0, 0)
    self.body.tap('key.use')
    self.body.ticks(3)
    self.scene.note('%s: the crosshair was on %s; the block looked at '
                    'is now %s, and it holds %s' % (
                      what, seen.target.id or 'nothing',
                      self.there(offset), self.held()))

  def watched(self, what: str, cells: tuple, ticks: int, each: int) -> None:
    """What the cells hold, noted every 'each' ticks for 'ticks'."""
    for at in range(0, ticks + 1, each):
      self.scene.note('%s, %d ticks on: %s' % (what, at, ', '.join(
        '%s %s' % (cell, self.there(cell)) for cell in cells)))
      self.body.ticks(each)

  def test_1_lava_is_scooped_from_the_pool(self) -> None:
    self.used(BUCKET, POOL[0], 0.9, 'the bucket used on the pool')
    self.scene.note('the pool after: %s' % ', '.join(
      self.there(cell) for cell in POOL))
    self.assertIn('LavaBucket', self.held())

  def test_2_lava_poured_on_the_ground_runs(self) -> None:
    self.used(BUCKET, POOL[0], 0.9, 'the bucket used on the pool')
    #  onto the top of the ground, three cells from the pool's edge
    self.used(BUCKET, (1, -1, 4), 1.0, 'the lava poured on the ground')
    self.watched('the lava', ((1, 0, 4), (0, 0, 4), (1, 0, 3), (1, 0, 5),
                              (-1, 0, 4)), 90, 10)

  def test_3_water_beside_poured_lava(self) -> None:
    self.used(BUCKET, POOL[0], 0.9, 'the bucket used on the pool')
    self.used(BUCKET, (1, -1, 4), 1.0, 'the lava poured on the ground')
    self.used(WATER, (1, -1, 2), 1.0, 'the water poured two cells off')
    self.watched('the lava and the water', ((1, 0, 4), (1, 0, 3), (1, 0, 2),
                                            (0, 0, 4), (1, 0, 5)), 40, 5)
    self.used(WATER, (1, -1, 2), 1.2, 'the bucket used on the water')
    self.watched('after the water is scooped', ((1, 0, 4), (1, 0, 3),
                                                (1, 0, 2)), 40, 10)

  def test_4_lava_poured_where_water_runs(self) -> None:
    #  the lava first: the water will reach the pool
    self.used(BUCKET, POOL[0], 0.9, 'the bucket used on the pool')
    self.used(WATER, (1, -1, 2), 1.0, 'the water poured first')
    self.body.ticks(30)
    self.scene.note('the water run out: %s' % ', '.join(
      '%s %s' % (cell, self.there(cell)) for cell in (
        (1, 0, 2), (1, 0, 3), (1, 0, 4), (1, 0, 5), (0, 0, 4))))
    self.used(BUCKET, (1, -1, 4), 1.0, 'the lava poured where water runs')
    self.watched('the lava in the water', ((1, 0, 4), (1, 0, 3), (0, 0, 4),
                                           (1, 0, 5)), 20, 5)
