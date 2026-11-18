"""
The glider (SPEC.md 21.17), without a game, on a body in the sky that
flies as the model has it (skybody.py), which the practice game
confirmed. Falling, one press of jump opens its wings; standing, it
jumps and presses again as it falls, 9 ticks on, never flying as a
creative player does; with no wings worn it says so. Gliding, it turns
to the place and chooses its pitch by flying the model ahead, and comes
down at the place, softly. A place out of its reach it flies towards as
far as it can, and says how far short it came down. How it came down is
as it was last seen in the air. It asks four of the body's five means
(it waits by perceiving, never by ticks) and no others.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from meantwell import glide
from meantwell.glider import Glider
from skybody import SkyBody
from unittas.errors import TesttimeError
from unittas.values import BlockPos, Vec3

HIGH = 40.0
TOWER = (0.5, 0.5, HIGH)
#  just off the tower's platform, walking south, falling
OFF_THE_TOWER, FALLING = Vec3(0.5, HIGH, 2.6), Vec3(0.0, -0.1, 0.2)
MEANS = {'perceive', 'keyDown', 'keyUp', 'look'}


def _far(place: Vec3, pos: Vec3) -> float:
  return math.hypot(place.x - pos.x, place.z - pos.z)


class Told(Glider):
  """A glider that keeps what it chose, and what it flew ahead for it:
  'told' holds each (the tick, the pitch held so far, the pitches flown
  ahead, the choice)."""

  def _choose(self, seen: object, place: Vec3, held: float = None) -> tuple:
    self.flew = []
    choice = Glider._choose(self, seen, place, held)
    self.__dict__.setdefault('told', []).append(
      (seen.tick, held, self.flew, choice))
    return choice

  def _flown(self, seen: object, place: Vec3, yaw: float,
             pitch: float) -> float:
    self.__dict__.setdefault('flew', []).append(pitch)
    return Glider._flown(self, seen, place, yaw, pitch)


class GliderTests(unittest.TestCase):

  def falling(self, **body) -> SkyBody:
    return SkyBody(OFF_THE_TOWER, FALLING, tower=TOWER, **body)

  def assertNeverFlew(self, body: SkyBody) -> None:
    self.assertFalse(body.flew, 'jump pressed twice within 7 ticks')

  def flown(self, place: Vec3) -> tuple:
    """A glide from the tower to the place: (glider, body, what it saw)."""
    body = self.falling()
    glider = Glider(body)
    glider.takeOff()
    seen = glider.glide(place)
    return glider, body, seen

  def test_falling_one_press_opens_its_wings(self) -> None:
    body = self.falling()
    seen = Glider(body).takeOff()
    self.assertLess(seen.box.maxY - seen.box.minY, 1.0, 'its box level')
    self.assertTrue(body.gliding)
    self.assertEqual(1, len(body.presses))
    self.assertEqual(set(), body.keys, 'jump let go again')
    self.assertNeverFlew(body)

  def test_standing_it_jumps_and_opens_them_as_it_falls(self) -> None:
    body = SkyBody(Vec3(0.5, 0.0, 0.5))
    seen = Glider(body).takeOff()
    self.assertLess(seen.box.maxY - seen.box.minY, 1.0)
    jumps = [tick for tick, key in body.presses if key == 'key.jump']
    self.assertEqual(2, len(jumps), 'the jump, and the wings')
    self.assertGreaterEqual(jumps[1] - jumps[0], 9)
    self.assertNeverFlew(body)
    self.assertGreater(body.z, 1.0, 'forward as it jumped: off its spot')
    self.assertEqual(set(), body.keys, 'every key let go')

  def test_gliding_already_there_is_nothing_to_do(self) -> None:
    body = self.falling()
    glider = Glider(body)
    glider.takeOff()
    asked = len(body.asked)
    glider.takeOff()
    self.assertEqual(['perceive'], body.asked[asked:])

  def test_no_wings_to_open_is_said(self) -> None:
    body = self.falling(wings=False)
    with self.assertRaises(TesttimeError) as stopped:
      Glider(body).takeOff()
    self.assertEqual('takeOff', stopped.exception.step)
    self.assertIn('no wings to open', str(stopped.exception))
    self.assertEqual(set(), body.keys, 'every key let go')

  def test_it_comes_down_at_the_place_and_softly(self) -> None:
    for across in (80.0, 120.0, 200.0, 260.0):
      with self.subTest(across=across):
        place = Vec3(0.5, 0.0, across + 0.5)
        glider, body, seen = self.flown(place)
        self.assertTrue(seen.onGround)
        self.assertLessEqual(_far(place, seen.pos), Glider.NEAR)
        self.assertAlmostEqual(_far(place, seen.pos), glider.miss)
        _, where, motion = body.down
        self.assertGreater(motion.y, -glide.SOFT, 'softly')
        #  its own reckoning: as it was last perceived in the air
        self.assertLess(glider.sink, glide.SOFT)
        self.assertEqual(set(), body.keys)
        self.assertNeverFlew(body)

  def test_a_place_aside_is_turned_to(self) -> None:
    place = Vec3(140.5, 0.0, 140.5)
    glider, body, seen = self.flown(place)
    self.assertLessEqual(_far(place, seen.pos), Glider.NEAR)
    self.assertGreater(body.down[2].y, -glide.SOFT)

  def test_a_blockpos_is_its_floors_middle(self) -> None:
    glider, body, seen = self.flown(BlockPos(0, 0, 200))
    self.assertLessEqual(_far(Vec3(0.5, 0.0, 200.5), seen.pos), Glider.NEAR)

  def test_a_place_out_of_its_reach(self) -> None:
    #  from 40 up it glides some 290 blocks at best (the game: 283)
    place = Vec3(0.5, 0.0, 900.5)
    body = self.falling()
    glider = Glider(body)
    glider.takeOff()
    with self.assertRaises(TesttimeError) as stopped:
      glider.glide(place)
    self.assertEqual('glide', stopped.exception.step)
    self.assertIn('short', str(stopped.exception))
    self.assertGreater(body.z, 275.0, 'it flew as far as it could')
    self.assertGreater(glider.miss, 500.0)
    self.assertGreater(body.down[2].y, -glide.SOFT, 'and still softly')
    self.assertEqual(set(), body.keys)

  def test_falling_with_its_wings_shut_it_opens_them_itself(self) -> None:
    #  found in the game (SPEC.md 21.17): a jump where it stood opened
    #  them, the platform's edge shut them again, and it fell on
    place = Vec3(0.5, 0.0, 200.5)
    body = self.falling()
    glider = Glider(body)
    seen = glider.glide(place)
    self.assertLessEqual(_far(place, seen.pos), Glider.NEAR)
    self.assertEqual(1, len(body.presses), 'one press of jump')
    self.assertNeverFlew(body)

  def test_how_it_came_down_is_as_last_seen_in_the_air(self) -> None:
    for across in (80.0, 120.0, 200.0, 260.0):
      with self.subTest(across=across):
        glider, body, _ = self.flown(Vec3(0.5, 0.0, across + 0.5))
        air = [each for each in body.shown if not each.onGround and
               each.box.maxY - each.box.minY < 1.0][-1]
        self.assertEqual(max(0.0, -air.motion.y), glider.sink)
        self.assertEqual(math.hypot(air.motion.x, air.motion.z),
                         glider.speed)

  def test_down_between_two_looks_it_knows_how_it_came_down(self) -> None:
    #  found in the game (SPEC.md 21.17): the tick after its wings fold
    #  its feet aren't on the ground, and its motion down reads as one
    #  standing does, 0.08. Seen then, that was taken for how it came
    #  down. Here it is in the air at its first look, asks for another
    #  look (the place is far beyond its reach), and is next seen then
    body = SkyBody(Vec3(0.5, 0.25, 0.5), Vec3(0.0, -0.149492, 1.420991),
                   gliding=True)
    body.pitch = 20.0
    #  (one that doesn't hold its look as it comes down: the game's
    #  ticks aren't always the stand-in's)
    glider = type('Late', (Glider,), {'COMMIT': 0})(body)
    with self.assertRaises(TesttimeError) as stopped:
      glider.glide(Vec3(0.5, 0.0, 200.5))
    self.assertIn('short', str(stopped.exception))
    first, second = body.shown[:2]
    self.assertFalse(first.onGround)
    self.assertFalse(second.onGround, 'the tick its feet are off it')
    self.assertGreater(second.box.maxY - second.box.minY, 1.0)
    self.assertEqual(-first.motion.y, glider.sink)
    self.assertGreater(glider.sink, 0.15)
    self.assertEqual(math.hypot(first.motion.x, first.motion.z),
                     glider.speed)
    self.assertAlmostEqual(0.0, body.vz, delta=0.003, msg='at rest')

  def told(self, place: Vec3) -> tuple:
    """A glide from the tower to the place by a glider that keeps what
    it chose: (glider, body)."""
    body = self.falling()
    glider = Told(body)
    glider.takeOff()
    glider.glide(place)
    return glider, body

  def test_what_it_chose_before_is_flown_ahead_again(self) -> None:
    #  found on the scorecard: low down a degree is blocks, and a choice
    #  made anew from a few pitches lost the one it was flying by
    glider, body = self.told(Vec3(0.5, 0.0, 200.5))
    self.assertIsNone(glider.told[0][1], 'nothing held at first')
    for (_, _, _, before), (_, held, flew, _) in zip(glider.told,
                                                      glider.told[1:]):
      self.assertEqual(before[1], held)
      self.assertEqual(held, flew[0], 'first, so that a tie keeps it')

  def test_it_chooses_to_a_quarter_of_a_degree(self) -> None:
    glider, body = self.told(Vec3(0.5, 0.0, 200.5))
    parts = {pitch % 1.0 for _, _, _, (_, pitch) in glider.told}
    self.assertTrue(parts - {0.0}, 'finer than whole degrees')
    self.assertLessEqual(parts, {0.0, 0.25, 0.5, 0.75})

  def test_it_flies_the_look_it_chose(self) -> None:
    #  found on the scorecard: a look a degree off the choice was left
    #  as it was, and came down 12 blocks short
    glider, body = self.told(Vec3(0.5, 0.0, 200.5))
    checked = 0
    for tick, _, _, (yaw, pitch) in glider.told:
      after = [each for each in body.shown if each.tick > tick]
      if pitch > Glider.STEEP or not after or after[0].onGround:
        continue
      self.assertAlmostEqual(pitch, after[0].look.pitch,
                             delta=Glider.TURN)
      checked += 1
    self.assertGreater(checked, 20)
    self.assertLess(Glider.TURN, 0.25)

  def test_about_to_come_down_it_holds_its_look(self) -> None:
    #  a look takes two ticks to be the look it flies with: asked for
    #  as it comes down, it is no help, and found on the scorecard to
    #  bounce it along the ground
    for across in (80.0, 120.0, 200.0, 260.0):
      with self.subTest(across=across):
        glider, body, _ = self.flown(Vec3(0.5, 0.0, across + 0.5))
        down = body.down[0]
        late = [tick for tick, _, _ in body.looks
                if 0 <= down - tick < Glider.COMMIT - 1]
        self.assertEqual([], late)

  def test_its_wings_not_open_it_doesnt_glide(self) -> None:
    body = SkyBody(Vec3(0.5, 0.0, 0.5))
    with self.assertRaises(TesttimeError) as stopped:
      Glider(body).glide(Vec3(0.5, 0.0, 200.5))
    self.assertEqual('glide', stopped.exception.step)
    self.assertIn('wings', str(stopped.exception))
    self.assertEqual(['perceive'], body.asked)

  def test_it_asks_four_of_the_five_means_and_no_others(self) -> None:
    glider, body, _ = self.flown(Vec3(0.5, 0.0, 200.5))
    self.assertEqual(MEANS, set(body.asked))
    self.assertEqual({'key.jump'}, {key for _, key in body.presses})
    self.assertIs(body, glider.body)

  def test_made_wrong_it_is_refused(self) -> None:
    body = self.falling()
    glider = Glider(body)
    with self.assertRaises(TypeError):
      glider.glide('over there')
    with self.assertRaises(ValueError):
      glider.glide(Vec3(0.5, 0.0, 200.5), ticks=0)
    with self.assertRaises(ValueError):
      glider.takeOff(ticks=0)
    self.assertEqual([], body.asked)


if __name__ == '__main__':
  unittest.main()
