"""
How an elytra flies, as the model has it (SPEC.md 21.17; glide.py),
without a game: one tick of it against the game's formula worked by
hand, for a level look, a look upwards and one straight down; and that
the look's turn turns the flight with it. Whether the formula is the
game's is the game's to say (tests/game), not this page's; how far it
slides on once it is down is held against what the game measured.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from meantwell import glide
from unittas.values import Vec3


class GlideTests(unittest.TestCase):

  def assertMotion(self, expected: tuple, motion: Vec3) -> None:
    for name, wanted, got in zip('xyz', expected,
                                 (motion.x, motion.y, motion.z)):
      self.assertAlmostEqual(wanted, got, places=9, msg=name)

  def test_where_it_looks(self) -> None:
    #  yaw 0 is south (+z), pitch 90 straight down
    for yaw, pitch, expected in ((0.0, 0.0, (0.0, 0.0, 1.0)),
                                 (90.0, 0.0, (-1.0, 0.0, 0.0)),
                                 (-90.0, 0.0, (1.0, 0.0, 0.0)),
                                 (0.0, 90.0, (0.0, -1.0, 0.0)),
                                 (0.0, -30.0, (0.0, 0.5, math.sqrt(0.75)))):
      for wanted, got in zip(expected, glide.look(yaw, pitch)):
        self.assertAlmostEqual(wanted, got, places=9)

  def test_a_tick_looking_level(self) -> None:
    #  by hand: it sinks 0.02 (a quarter of gravity is left, level); a
    #  tenth of that fall goes forward and comes off the fall; its motion
    #  across turns a tenth towards its look; then 0.99 and 0.98 are kept
    after = glide.step(Vec3(0.0, 0.0, 1.0), 0.0, 0.0)
    self.assertMotion((0.0, -0.01764, 0.991782), after)

  def test_a_tick_looking_up(self) -> None:
    #  by hand, 30 degrees up: its speed across is spent on climbing
    after = glide.step(Vec3(0.0, 0.0, 1.0), 0.0, -30.0)
    self.assertMotion((0.0, 0.0309925, 0.974518875), after)
    self.assertGreater(after.y, 0.0, 'it climbs')

  def test_a_tick_looking_straight_down(self) -> None:
    #  no lift at all: gravity whole, 0.98 kept
    after = glide.step(Vec3(0.0, -1.0, 0.0), 0.0, 90.0)
    self.assertMotion((0.0, -1.0584, 0.0), after)

  def test_the_looks_turn_turns_the_flight(self) -> None:
    south = glide.step(Vec3(0.0, 0.0, 1.0), 0.0, 0.0)
    west = glide.step(Vec3(-1.0, 0.0, 0.0), 90.0, 0.0)
    self.assertMotion((-south.z, south.y, 0.0), west)

  def test_a_flight_is_its_ticks_one_after_another(self) -> None:
    pos, motion = Vec3(0.0, 100.0, 0.0), Vec3(0.0, 0.0, 0.5)
    flown = glide.flight(pos, motion, 0.0, 10.0, 3)
    self.assertEqual(3, len(flown))
    at, moving = pos, motion
    for there, then in flown:
      moving = glide.step(moving, 0.0, 10.0)
      at = Vec3(at.x + moving.x, at.y + moving.y, at.z + moving.z)
      self.assertMotion((at.x, at.y, at.z), there)
      self.assertMotion((moving.x, moving.y, moving.z), then)

  def test_held_level_it_settles_into_a_steady_glide(self) -> None:
    #  whatever it starts with, the same look ends in the same glide: by
    #  hand, looking level, sinking 0.01764 / 0.118 and about ten times
    #  that across
    slow = glide.flight(Vec3(0.0, 0.0, 0.0), Vec3(0.0, 0.0, 0.1), 0.0, 0.0,
                        3000)[-1][1]
    fast = glide.flight(Vec3(0.0, 0.0, 0.0), Vec3(0.0, -1.0, 2.0), 0.0, 0.0,
                        3000)[-1][1]
    self.assertMotion((slow.x, slow.y, slow.z), fast)
    self.assertAlmostEqual(-0.01764 / 0.118, slow.y, places=9)
    self.assertAlmostEqual(10.1, slow.z / -slow.y, places=1)

  def test_down_it_slides_on_as_the_game_measured(self) -> None:
    #  the practice game, 26.3, 2026-11-18 17:39 (SPEC.md 21.17): how
    #  fast across it reached the ground, its look's pitch, and how far
    #  on from there it came to rest
    for speed, pitch, measured in ((1.421883, 0.0, 5.1273),
                                   (1.596558, 15.0, 5.7572),
                                   (0.503353, -10.0, 1.8053),
                                   (1.614220, 0.0, 5.8200),
                                   (1.519403, 10.0, 5.4789)):
      with self.subTest(speed=speed, pitch=pitch):
        dx, dz = glide.slide(0.0, speed, 0.0, pitch)
        self.assertAlmostEqual(0.0, dx, places=9)
        self.assertAlmostEqual(measured, dz, delta=0.01)

  def test_it_slides_on_the_way_it_looks(self) -> None:
    south = glide.slide(0.0, 1.0, 0.0, 0.0)
    west = glide.slide(-1.0, 0.0, 90.0, 0.0)
    self.assertAlmostEqual(-south[1], west[0], places=9)
    self.assertAlmostEqual(0.0, west[1], places=9)


if __name__ == '__main__':
  unittest.main()
