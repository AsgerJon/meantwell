"""
The walker in a real game (SPEC.md 21.23), on the practice instance in
a flat world, to be watched: 'unittas run --instance watch.toml
tests.game.test_walker'. Each test has a lane of its own, 20 blocks
from the last. In it, by command: the robot at the lane's start, and
what stands in its way (a wall, a hole). Then, by a player's means
alone (the keys, the mouse's rate), it walks: over open ground to a
place ahead, one beside and one behind; round a wall; round a hole.

What is read of each walk, from the bearings the game answered each
rate with: how many ticks it took, how far from the place it stopped,
the most its look turned in a tick, how many answers came late, and
that its feet never left the ground's level. Its pictures are kept
under the run's screenshots (walker-*.png).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os

from mcdex import MCBlocks

from meantwell.mouse import Mouse
from meantwell.walker import Walker
from tests.game.bearings import Bearings
from unittas.run import Run
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  How far a frame's share may put a tick's turn over the mouse's
#  fastest, in degrees
SHARE = 1.0


class WalkerTests(ScenarioTestCase):

  #  a guard by the clock, never the verdict
  timeout_seconds = 300
  world = {'type': 'flat', 'game_mode': 'survival', 'cheats': True,
           'structures': False}

  def setUp(self) -> None:
    #  the test's own lane, by its number; the setup is by command
    self.lane = 20 * (int(self._testMethodName.split('_')[1]) - 1)
    self.ground = float(self.scene.origin.y)
    self.game.teleport(self.spot(0, 0))
    self.agent.wait(10)
    self.body = Bearings(self.game)
    self.walker = Walker(Mouse(self.body))
    self.addCleanup(self.walker.letGo)

  def spot(self, x: int, z: int) -> Vec3:
    """The floor's middle of the lane's column (x, z)."""
    return self.scene.at((self.lane + x, 0, z)).center()

  def block(self, x: int, y: int, z: int, block: MCBlocks) -> None:
    """A block of the lane set, by command."""
    self.game.setBlock(self.scene.at((self.lane + x, y, z)), block)

  def picture(self, name: str) -> None:
    """The frame as it is now, kept under the run's screenshots."""
    self.game.screenshot(os.path.join(
      Run.current.results, 'screenshots', 'walker-%s.png' % (name,)))

  def walked(self, what: str, x: int, z: int) -> None:
    """The walk to the lane's column (x, z), noted and held to what a
    walk is."""
    place = self.spot(x, z)
    first = len(self.body.kept)
    before = self.agent.perceive()
    seen = self.walker.walk(place)
    short = math.hypot(place.x - seen.pos.x, place.z - seen.pos.z)
    kept = self.body.kept[first:]
    self.body.kept = kept
    self.scene.note(
      '%s: %d ticks, stopped %.2f from the place, at (%.2f, %.2f, %.2f); '
      'its look turned %.1f degrees in a tick at most, over %d rates, %d '
      'answered late; its way had %d stretches' % (
        what, seen.tick - before.tick, short, seen.pos.x, seen.pos.y,
        seen.pos.z, self.body.turn(), len(kept), self.body.late(),
        len(self.walker.way) - 1))
    self.assertLessEqual(short, 0.25, what)
    self.assertLessEqual(self.body.turn(), Mouse.FASTEST + SHARE, what)
    self.assertAlmostEqual(self.ground, self.body.lowest(), delta=0.01,
                           msg='%s: its feet left the ground' % (what,))
    self.assertTrue(seen.mouseRate.none, 'its look turns no more')

  def test_1_over_open_ground(self) -> None:
    self.walked('8 blocks ahead', 0, 8)
    self.walked('6 blocks beside', 6, 8)
    self.walked('behind and aside', 2, 1)
    self.picture('open')

  def test_2_round_a_wall(self) -> None:
    for x in range(-3, 3):
      for y in (0, 1):
        self.block(x, y, 4, MCBlocks.Stone)
    self.walked('round a wall', 0, 7)
    self.assertGreater(len(self.walker.way), 2, 'its way went round')
    self.picture('wall')

  def test_3_round_a_hole(self) -> None:
    for x in (0, 1):
      for z in (3, 4, 5):
        for y in (-1, -2, -3):
          self.block(x, y, z, MCBlocks.Air)
    self.walked('round a hole', 0, 8)
    self.assertGreater(len(self.walker.way), 2, 'its way went round')
    self.picture('hole')
