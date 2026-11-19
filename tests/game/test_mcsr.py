"""
The MCSR practice map opened in a real game (SPEC.md 21.20), on the
1.16.1 instance (mcsr.toml). The map is a save by Dibedy, with packs by
Mescht and Llama: it is their work, it stays in tmp/ (which git
ignores) and is opened from there, a fresh copy each run. This page is
here to find out: what the game shows once the map is open, where the
robot stands in it and what is around it; then what the map's portal
practice is, entered as a player enters it, by a line typed into the
chat ('/trigger portals': the chat's key, the line, Enter). Its pictures
are kept under the run's screenshots (mcsr-*.png): they are the finding.

  unittas run --instance mcsr.toml tests.game.test_mcsr
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from collections import Counter

from worktoy.desc import FixBox

from meantwell.mouse import Mouse
from unittas.agent import Agent
from unittas.run import Run
from unittas.scenario import ScenarioTestCase
from unittas.worldrun import World

#  Where the map is, from this module's folder
MAP = os.path.join('..', '..', 'tmp', 'MCSR.Practice.v2.0.0')


class McsrMap(World):
  """The practice map, as its authors saved it."""

  save = FixBox[str](MAP)


class McsrTests(ScenarioTestCase):

  #  a guard by the clock, never the verdict
  timeout_seconds = 300
  hub = McsrMap()

  def picture(self, name: str) -> None:
    """The frame as it is now, kept under the run's screenshots."""
    self.game.screenshot(os.path.join(
      Run.current.results, 'screenshots', 'mcsr-%s.png' % (name,)))

  def typed(self, line: str) -> None:
    """A line typed into the chat as a player types it: the chat's
    key, the line, Enter."""
    self.game.tap('key.chat')
    self.agent.wait(2)
    self.game.type(line)
    self.game.key('enter')

  def found(self, what: str) -> None:
    """Where it stands, what is around it and what it carries, noted;
    and a frame of each quarter about it, named by 'what'."""
    seen = self.agent.perceive(8, 3, 3)
    self.scene.note('it stands at (%.2f, %.2f, %.2f), looking %.1f and '
                    '%.1f, on the ground: %s' % (
                      seen.pos.x, seen.pos.y, seen.pos.z, seen.look.yaw,
                      seen.look.pitch, seen.onGround))
    kinds = Counter(near.id for near in seen.blocks)
    self.scene.note('%d blocks within 8: %s' % (len(seen.blocks), ', '.join(
      '%d %s' % (count, name) for name, count in kinds.most_common(16))))
    inventory = self.game.inventory()
    held = ['main.%d: %d %s' % (slot, stack.count, stack.id)
            for slot, stack in enumerate(inventory.main)
            if stack.id != 'minecraft:air']
    self.scene.note('its inventory: %s' % ('; '.join(held) or 'empty',))
    mouse = Mouse(self.game)
    for quarter in range(4):
      yaw = (seen.look.yaw + 90.0 * quarter + 180.0) % 360.0 - 180.0
      mouse.look(yaw, 10.0)
      self.agent.wait(5)
      self.picture('%s-%d' % (what, quarter))

  @hub
  def test_1_the_map_opens_and_the_robot_stands_in_it(self) -> None:
    self.picture('open')
    seen = self.agent.perceive(8, 3, 3)
    self.scene.note('it stands at (%.2f, %.2f, %.2f), looking %.1f and '
                    '%.1f, on the ground: %s' % (
                      seen.pos.x, seen.pos.y, seen.pos.z, seen.look.yaw,
                      seen.look.pitch, seen.onGround))
    kinds = Counter(near.id for near in seen.blocks)
    self.scene.note('%d blocks within 8: %s' % (len(seen.blocks), ', '.join(
      '%d %s' % (count, name) for name, count in kinds.most_common(16))))
    self.assertTrue(seen.blocks, 'something is around it')

  @hub
  def test_2_a_look_around_from_where_it_stands(self) -> None:
    #  the robot's own turn, by the mouse: a quarter at a time, a frame
    #  kept of each way
    mouse = Mouse(self.game)
    first = self.agent.perceive().look.yaw
    for quarter in range(4):
      yaw = (first + 90.0 * quarter + 180.0) % 360.0 - 180.0
      mouse.look(yaw, 0.0)
      self.agent.wait(5)
      self.picture('around-%d' % (quarter,))
    seen = self.agent.perceive(8, 3, 3)
    signs = [near for near in seen.blocks if 'sign' in near.id]
    self.scene.note('%d signs within 8: %s' % (len(signs), '; '.join(
      '%s at (%d, %d, %d)' % (near.id, near.pos.x, near.pos.y, near.pos.z)
      for near in signs[:24])))

  @hub
  def test_3_into_the_portal_practice_by_a_line_typed(self) -> None:
    #  the map's own trigger, which a player without cheats may use
    mark = self.game.mark()
    self.typed('/trigger portals')
    #  the map enables its pack and puts the player in it: given time
    self.agent.wait(100)
    self.picture('portal-practice')
    for line in self.game.chat(mark)[:12]:
      self.scene.note('the chat: %s' % (line.plain,))
    self.found('portal-practice')

  @hub
  def test_4_its_start_sign_used(self) -> None:
    #  in the practice's own place, the sign south of where it is put
    #  says Start (read in test 3's frames): used as a player uses it
    self.typed('/trigger portals')
    self.agent.wait(100)
    seen = self.agent.perceive(8, 3, 3)
    signs = [near.pos for near in seen.blocks
             if near.id == 'minecraft:oak_wall_sign' and
             near.pos.z > seen.pos.z]
    self.scene.note('the signs south of it: %s' % ('; '.join(
      '(%d, %d, %d)' % (pos.x, pos.y, pos.z) for pos in signs),))
    self.assertEqual(1, len(signs), 'one sign south of it, as seen')
    mark = self.game.mark()
    agent = Agent(Mouse(self.game),
                  os.path.join(Run.current.results, 'frames'))
    agent.use(signs[0])
    #  the level is built and the player put in it: given time
    self.agent.wait(120)
    self.picture('level')
    for line in self.game.chat(mark)[:12]:
      self.scene.note('the chat: %s' % (line.plain,))
    self.found('level')
