"""
A glide measured in a real game (SPEC.md 21.17), on the practice
instance: the check of the model of how an elytra flies (glide.py),
which was written down from memory. The scene is a tower built by
command. The player is put on it wearing an elytra (setup, by command);
then, by a player's means alone, it walks off, opens its wings with one
press of jump as it falls, holds one look, and is perceived until it is
down and has come to rest. Each flight is kept, look by look, in the
run's results (glide-NAME.json), for the model's flight to be laid
beside it, and for what the model doesn't have: how long a look asked
for takes to be the look it flies with, and how it slides on once down.

  unittas run tests.game.test_glide
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import os

from mcdex import MCBlocks, MCItems

from unittas.run import Run
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  The tower, from the scene's origin: its column, how high it stands,
#  and the platform on it, three by three
TOWER, HIGH = (0, 6), 40
#  How long a flight is perceived at most, in looks
LOOKS = 900


class GlideTests(ScenarioTestCase):

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

  def flown(self, pitch: float, changes: dict = None,
            name: str = '') -> list:
    """
    The flight from the tower with the look held at 'pitch', south: each
    perception of it from its wings' opening until it is down and at
    rest, kept in the run's results and summed up in a note. 'changes'
    asks for another pitch at some of its looks: {the look's number: the
    pitch}; each perception says what was asked for last.
    """
    changes = dict(changes or {})
    name = name or '%d' % pitch
    #  the setup, by command: the elytra worn, and up on the tower
    self.game.setSlot('armor.chest', MCItems.Elytra)
    top = self.scene.at((TOWER[0], HIGH + 1, TOWER[1]))
    self.game.teleport(Vec3(top.x + 0.5, float(top.y), top.z + 0.5))
    self.agent.wait(10)
    #  from here on a player's means alone: the look, two keys
    body = self.agent.game
    body.look(0.0, 0.0)
    body.keyDown('key.forward')
    try:
      for _ in range(80):
        seen = body.perceive(0, 0, 0)
        if not seen.onGround and seen.motion.y < 0.0:
          break
      else:
        self.fail('it never walked off the tower: at %r' % (seen.pos,))
      body.keyDown('key.jump')
    finally:
      body.keyUp('key.forward')
      body.keyUp('key.jump')
    body.look(0.0, pitch)
    flight, asked, rested = [], pitch, 0
    for at in range(LOOKS):
      if at in changes:
        asked = changes[at]
        body.look(0.0, asked)
      seen = body.perceive(0, 0, 0)
      flight.append({
        'tick': seen.tick, 'pos': [seen.pos.x, seen.pos.y, seen.pos.z],
        'motion': [seen.motion.x, seen.motion.y, seen.motion.z],
        'yaw': seen.look.yaw, 'pitch': seen.look.pitch, 'asked': asked,
        'high': seen.box.maxY - seen.box.minY, 'onGround': seen.onGround,
        'flying': seen.flying})
      if seen.onGround:
        #  on to rest: five looks running with no motion across
        still = abs(seen.motion.x) + abs(seen.motion.z) < 0.003
        rested = rested + 1 if still else 0
        if rested >= 5:
          break
    path = os.path.join(Run.current.results, 'glide-%s.json' % name)
    with open(path, 'w', encoding='utf-8') as file:
      json.dump(flight, file)
    level = [each for each in flight if each['high'] < 1.0]
    first, last = flight[0], flight[-1]
    air = [each for each in flight if not each['onGround']]
    infoSpec = """glide %s: %d looks over %d ticks, %d of them with its
    box level, %d in the air; from (%.1f, %.1f, %.1f) to rest at (%.1f,
    %.1f, %.1f); its last motion down in the air %.3f; kept in %s"""
    self.scene.note(' '.join((infoSpec % (
      name, len(flight), last['tick'] - first['tick'], len(level),
      len(air), first['pos'][0], first['pos'][1], first['pos'][2],
      last['pos'][0], last['pos'][1], last['pos'][2], air[-1]['motion'][1],
      os.path.basename(path))).split()))
    self.assertTrue(last['onGround'], 'down within %d looks' % LOOKS)
    self.assertGreater(len(level), 10, 'its wings opened: its box level')
    self.assertFalse(any(each['flying'] for each in flight),
                     'never flying as a creative player does')
    return flight

  def test_1_looking_level(self) -> None:
    self.flown(0.0)

  def test_2_looking_15_down(self) -> None:
    self.flown(15.0)

  def test_3_looking_10_up(self) -> None:
    self.flown(-10.0)

  def test_4_the_look_changed_as_it_flew(self) -> None:
    self.flown(0.0, {30: 15.0, 60: 0.0, 90: 20.0, 120: 5.0, 150: 30.0,
                     170: 0.0}, 'changed')

  def test_5_coming_in_steeply(self) -> None:
    self.flown(45.0, {35: 10.0}, 'steep')
