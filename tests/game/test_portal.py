"""
A nether portal cast beside a lake of lava, in a real game (SPEC.md
21.21), on the practice instance: a flat world played in survival. By
command (the setup): the lake the plan asks for, six by four and two
deep, sunk in the ground south of where it builds; survival and peace;
and in its hotbar a bucket of water, a flint and steel, a stack of dirt
and an iron pickaxe. Then the caster, by a player's means alone, as a
speedrunner casts one: trenches dug, a pillar of dirt, the water run
from its top, lava poured against it into the fall. It lights the portal
and walks into it. Each move it makes is noted under the test's line.
Before it walks in, the frame and its inside are read by command, and
pictures are kept as it goes (screenshots/portal-*.png).

  unittas run tests.game.test_portal
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os

from mcdex import MCBlocks, MCItems

from meantwell.mouse import Mouse
from meantwell.portalcast import PortalCast
from meantwell.portalcaster import PortalCaster
from unittas.agent import Agent
from unittas.run import Run
from unittas.scenario import ScenarioTestCase

#  From the scene's origin, the block the run's start stands in: where
#  the cast's own places are counted from. The frame stands just south
#  of the start, the lake beyond it: no lava between the two
ORIGIN = (-2, 0, 3)
#  The moves after which a picture is kept, by what they say
PICTURES = ('stand at', 'light', 'stand in the portal')


class PortalTests(ScenarioTestCase):

  #  a guard by the clock, never the verdict: some eighty moves
  timeout_seconds = 1500
  world = {'type': 'flat', 'game_mode': 'survival', 'cheats': True,
           'structures': False}

  def setUp(self) -> None:
    #  the setup, by command: survival (the world is made creative,
    #  SPEC.md 21.20), peace, the lake, and what it starts with
    for command in ('gamemode survival', 'difficulty peaceful',
                    'time set 1000'):
      said = self.game.command(command)
      self.scene.note('%s, by command: %s' % (command, '; '.join(
        said.lines) or 'nothing said'))
    self.cast = PortalCast(self.scene.at(ORIGIN))
    for cell in self.cast.lake:
      self.game.setBlock(cell, MCBlocks.Lava)
    self.game.setSlot('main.0', MCItems.WaterBucket)
    self.game.setSlot('main.1', MCItems.FlintAndSteel)
    self.game.setSlot('main.2', MCItems.Dirt, 64)
    self.game.setSlot('main.3', MCItems.IronPickaxe)
    self.agent.wait(10)
    self.pictures = 0
    self.read = None

  def kinds(self, cells: tuple) -> list:
    """What each cell holds, by command: the game's own names."""
    return [self.game.block(cell).id.split(':')[-1] for cell in cells]

  def said(self, line: str) -> None:
    """A move the caster made: noted; a picture kept after some; and
    once it is lit, before it walks in, the portal read by command."""
    self.scene.note(line)
    move = line.split(': ', 1)[-1]
    if 'light the' in move:
      self.agent.wait(10)
      self.read = (self.kinds(self.cast.frame),
                   self.kinds(self.cast.interior))
      self.scene.note('by command, once lit: its frame is %s; inside it '
                      'is %s' % (', '.join(self.read[0]),
                                 ', '.join(self.read[1])))
    if move.startswith(PICTURES):
      self.pictures += 1
      self.game.screenshot(os.path.join(
        Run.current.results, 'screenshots',
        'portal-%02d.png' % self.pictures))

  def test_it_casts_a_portal_from_the_lake_and_stands_in_it(self) -> None:
    #  an agent of its own, on a mouse: every look of it, walking and
    #  digging too, is turned and not jumped to (SPEC.md 21.22)
    agent = Agent(Mouse(self.game),
                  os.path.join(Run.current.results, 'frames'))
    caster = PortalCaster(agent, self.said)
    try:
      seen = caster.cast(self.cast.origin, self.cast.shore)
    finally:
      if self.read is None:
        self.scene.note('by command, as it stopped: its frame is %s; '
                        'inside it is %s' % (
                          ', '.join(self.kinds(self.cast.frame)),
                          ', '.join(self.kinds(self.cast.interior))))
        self.game.screenshot(os.path.join(
          Run.current.results, 'screenshots', 'portal-stopped.png'))
    frame, inside = self.read
    self.assertEqual(['obsidian'] * 10, frame)
    self.assertEqual(['nether_portal'] * 6, inside)
    spot = self.cast.inside
    self.assertLess(abs(seen.pos.x - spot.x) + abs(seen.pos.z - spot.z),
                    0.8, 'it stands in the portal')
