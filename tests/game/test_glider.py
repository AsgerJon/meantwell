"""
The glider in a real game (SPEC.md 21.17), on the practice instance: the
routine on the real player's body, by a player's means alone. The scene
is a tower built by command; the player is put on it wearing an elytra
(setup, by command). It is to open its wings, from a walk off the edge
and from a forward jump where it stands, and glide to a place on the
ground: straight ahead, and aside. Each glide's miss, how it came down,
and how far it slid on are noted under its line. Once it is at rest the
place's floor is made red wool (setup's means, by command) and it looks
at it, and the frame is kept (screenshots/rest-TEST.png), so that the
picture shows the miss.

  unittas run tests.game.test_glider
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os

from mcdex import MCBlocks, MCItems

from meantwell import glide
from meantwell.glider import Glider
from unittas.run import Run
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  The tower, from the scene's origin: its column, how high it stands,
#  and the platform on it, three by three
TOWER, HIGH = (0, 6), 40


class GliderTests(ScenarioTestCase):

  #  a flight is long by the clock too: a guard, never the verdict
  timeout_seconds = 300

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    #  the setup is by command, not the agent
    x, z = TOWER
    for up in range(HIGH):
      cls.scene.place(MCBlocks.Stone, at=(x, up, z))
    for dx in (-1, 0, 1):
      for dz in (-1, 0, 1):
        cls.scene.place(MCBlocks.Stone, at=(x + dx, HIGH, z + dz))

  def setUp(self) -> None:
    #  the setup, by command: the elytra worn, and up on the tower
    self.game.setSlot('armor.chest', MCItems.Elytra)
    top = self.scene.at((TOWER[0], HIGH + 1, TOWER[1]))
    self.game.teleport(Vec3(top.x + 0.5, float(top.y), top.z + 0.5))
    self.agent.wait(10)
    #  until the seam (SPEC.md 21.7 step 1) the body is the agent's game,
    #  of which the glider asks five members and no others
    self.glider = Glider(self.agent.game)
    self.addCleanup(self.glider.letGo)

  def place(self, offset: tuple) -> Vec3:
    """The floor's middle of the place 'offset' from the origin."""
    return self.scene.at(offset).center()

  def walkedOff(self) -> None:
    """Off the platform's south edge, by the forward key: falling."""
    body = self.agent.game
    body.look(0.0, 0.0)
    body.keyDown('key.forward')
    try:
      for _ in range(80):
        seen = body.perceive(0, 0, 0)
        if not seen.onGround and seen.motion.y < 0.0:
          return
      self.fail('it never walked off the tower: at %r' % (seen.pos,))
    finally:
      body.keyUp('key.forward')

  def glided(self, what: str, offset: tuple) -> None:
    """The glide from where it flies to the place 'offset' from the
    origin, noted, and the place shown; a FAIL when it is hard or
    wide."""
    place = self.place(offset)
    before = self.agent.perceive()
    glider = self.glider
    try:
      seen = glider.glide(place)
    finally:
      if glider.miss is not None:
        rest = self.agent.perceive()
        infoSpec = """%s: from (%.1f, %.1f, %.1f), %d ticks; it came to
        rest %.2f blocks from the place, at (%.1f, %.1f, %.1f); it came
        down at %.2f a tick downward and %.2f across, and was first
        seen down %.2f blocks before where it rests"""
        self.scene.note(' '.join((infoSpec % (
          what, before.pos.x, before.pos.y, before.pos.z,
          rest.tick - before.tick, glider.miss, rest.pos.x, rest.pos.y,
          rest.pos.z, glider.sink, glider.speed, math.hypot(
            rest.pos.x - glider.down.x, rest.pos.z - glider.down.z))
                                  ).split()))
        self.shown(offset, rest.pos)
    self.assertTrue(seen.onGround)
    self.assertLess(glider.sink, glide.SOFT, 'softly')
    self.assertLessEqual(glider.miss, Glider.NEAR)

  def shown(self, offset: tuple, eye: Vec3) -> None:
    """The place's floor made red wool (by command: it is the test's
    mark, not the robot's doing), and the robot's look turned to it from
    where it stands, for the frame."""
    dx, dy, dz = offset
    self.scene.place(MCBlocks.RedWool, at=(dx, dy - 1, dz))
    mark = self.place(offset)
    across = math.hypot(mark.x - eye.x, mark.z - eye.z)
    yaw = math.degrees(math.atan2(-(mark.x - eye.x), mark.z - eye.z))
    pitch = math.degrees(math.atan2(eye.y + 1.62 - mark.y, across))
    self.agent.game.look(yaw if across > 0.05 else 0.0, pitch)
    self.agent.wait(3)
    #  the frame, kept by the test (the watch's own pictures are taken
    #  every ten seconds, whatever is in front of it then)
    self.game.screenshot(os.path.join(
      Run.current.results, 'screenshots',
      'rest-%s.png' % self.id().rsplit('.', 1)[-1]))

  def test_1_walked_off_and_glided_200_ahead(self) -> None:
    self.walkedOff()
    opened = self.glider.takeOff()
    self.assertLess(opened.box.maxY - opened.box.minY, 1.0)
    self.glided('walked off, 200 ahead', (0, 0, 206))

  def test_2_a_forward_jump_where_it_stood_and_150_ahead(self) -> None:
    self.agent.game.look(0.0, 0.0)
    opened = self.glider.takeOff()
    self.scene.note('from standing: its wings open at (%.1f, %.1f, %.1f), '
                    'its box %.1f high' % (
                      opened.pos.x, opened.pos.y, opened.pos.z,
                      opened.box.maxY - opened.box.minY))
    self.glided('a forward jump, 150 ahead', (0, 0, 156))

  def test_3_a_place_aside(self) -> None:
    self.walkedOff()
    self.glider.takeOff()
    self.glided('walked off, 120 east and 120 south', (120, 0, 126))

  def test_4_a_place_near_and_steeply_down(self) -> None:
    self.walkedOff()
    self.glider.takeOff()
    self.glided('walked off, 70 ahead', (0, 0, 76))
