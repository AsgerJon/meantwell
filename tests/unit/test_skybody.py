"""
The body in the sky the glider's tests fly (skybody.py), held against
what the practice game measured (SPEC.md 21.17, 26.3, 2026-11-18 17:39):
what a request costs in ticks, from which tick a look asked for is the
look it flies with, and how it comes down, tick by tick. A stand-in the
game hasn't confirmed teaches the glider the stand-in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from meantwell import glide
from skybody import SkyBody
from unittas.values import Vec3

#  The level flight's last look in the air, in the game: how high above
#  the ground, and its motion; then each tick's (on the ground, how high
#  its box, its motion across, its motion downward, how far it has come)
ABOVE, MOTION = 0.096924, Vec3(0.0, -0.149492, 1.420991)
DOWN = ((True, 0.6, 1.421883, 0.0, 1.421883),
        (True, 0.6, 1.409446, 0.0, 2.831328),
        (False, 1.8, 0.769557, -0.0784, 4.240774),
        (True, 1.8, 0.700297, -0.0784, 5.010332),
        (True, 1.8, 0.382362, -0.0784, 5.710629),
        (True, 1.8, 0.208770, -0.0784, 6.092991))
REST = 6.5492


class SkyBodyTests(unittest.TestCase):

  def gliding(self, **body) -> SkyBody:
    return SkyBody(Vec3(0.0, ABOVE, 0.0), MOTION, gliding=True, **body)

  def test_a_perception_takes_a_tick_and_a_look_two(self) -> None:
    body = SkyBody(Vec3(0.0, 50.0, 0.0), Vec3(0.0, -0.1, 1.0),
                   gliding=True)
    first = body.perceive(0, 0, 0).tick
    self.assertEqual(1, body.perceive(0, 0, 0).tick - first)
    body.look(0.0, 10.0)
    self.assertEqual(3, body.perceive(0, 0, 0).tick - first - 1)

  def test_a_look_is_flown_from_its_second_tick(self) -> None:
    #  the game: after a look and a perception, one tick was flown as
    #  it looked before, and two as it was asked to
    body = SkyBody(Vec3(0.0, 50.0, 0.0), Vec3(0.0, -0.1, 1.0),
                   gliding=True)
    before = body.perceive(0, 0, 0)
    body.look(0.0, 30.0)
    after = body.perceive(0, 0, 0)
    motion = (before.motion.x, before.motion.y, before.motion.z)
    for pitch in (0.0, 30.0, 30.0):
      motion = glide.ahead(*motion, 0.0, pitch)
    self.assertEqual(30.0, after.look.pitch)
    for wanted, got in zip(motion, (after.motion.x, after.motion.y,
                                    after.motion.z)):
      self.assertAlmostEqual(wanted, got, places=12)

  def test_it_comes_down_tick_by_tick_as_the_game_measured(self) -> None:
    body = self.gliding()
    for at, (onGround, high, across, down, far) in enumerate(DOWN):
      with self.subTest(tick=at):
        seen = body.perceive(0, 0, 0)
        self.assertEqual(onGround, seen.onGround)
        self.assertAlmostEqual(high, seen.box.maxY - seen.box.minY)
        self.assertAlmostEqual(across, seen.motion.z, delta=2e-5)
        self.assertAlmostEqual(down, seen.motion.y, delta=2e-5)
        self.assertAlmostEqual(far, seen.pos.z, delta=5e-5)
        self.assertAlmostEqual(0.0, seen.pos.y)

  def test_it_comes_to_rest_where_the_game_did(self) -> None:
    body = self.gliding()
    for _ in range(60):
      seen = body.perceive(0, 0, 0)
    self.assertAlmostEqual(REST, seen.pos.z, delta=0.01)
    self.assertTrue(seen.onGround)

  def test_how_it_met_the_ground_is_kept(self) -> None:
    body = self.gliding()
    body.ticks(8)
    tick, where, motion = body.down
    self.assertEqual(1, tick)
    self.assertAlmostEqual(1.421883, where.z, delta=2e-5)
    self.assertLess(motion.y, -0.1, 'as it fell, not as the ground left it')

  def test_standing_it_stays_on_the_ground(self) -> None:
    body = SkyBody(Vec3(0.5, 0.0, 0.5))
    for _ in range(5):
      seen = body.perceive(0, 0, 0)
      self.assertTrue(seen.onGround)
      self.assertAlmostEqual(-0.0784, seen.motion.y)

  def test_what_it_showed_is_kept(self) -> None:
    body = self.gliding()
    shown = [body.perceive(0, 0, 0) for _ in range(3)]
    self.assertEqual(shown, body.shown)

  def test_a_request_can_be_late(self) -> None:
    #  the game doesn't wait for the one who asks: a request sent late
    #  is run a tick on. 'late' says how many ticks each waits first
    waits = iter((0, 1, 2))
    body = SkyBody(Vec3(0.0, 50.0, 0.0), Vec3(0.0, -0.1, 1.0),
                   gliding=True, late=lambda: next(waits))
    self.assertEqual(1, body.perceive(0, 0, 0).tick)
    self.assertEqual(3, body.perceive(0, 0, 0).tick)
    body.look(0.0, 10.0)
    self.assertEqual(7, body.tick)
    self.assertEqual([(5, 0.0, 10.0)], body.looks)

  def test_each_look_asked_for_is_kept(self) -> None:
    body = SkyBody(Vec3(0.0, 50.0, 0.0), Vec3(0.0, -0.1, 1.0),
                   gliding=True)
    body.perceive(0, 0, 0)
    body.look(10.0, 20.0)
    body.look(0.0, 5.0)
    self.assertEqual([(1, 10.0, 20.0), (3, 0.0, 5.0)], body.looks)


if __name__ == '__main__':
  unittest.main()
