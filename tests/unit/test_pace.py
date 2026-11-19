"""
How a player walks on the ground, as the model has it (SPEC.md 21.23;
pace.py), without a game: what a held key adds in a tick, a tick of it
worked by hand, how far it goes on once the keys are let go, and where
it is on a way of straight stretches. Whether the reckoning is the
game's is the game's to say (tests/game), not this page's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from meantwell import pace

#  A way with one corner: 4 blocks south, then 3 east
WAY = ((0.0, 0.0), (0.0, 4.0), (3.0, 4.0))


class PaceTests(unittest.TestCase):

  def assertPair(self, expected: tuple, got: tuple) -> None:
    self.assertEqual(len(expected), len(got))
    for wanted, has in zip(expected, got):
      self.assertAlmostEqual(wanted, has, places=9)

  def walked(self, ticks: int, rest: int) -> tuple:
    """Where it is and how it moves after 'ticks' of forward looking
    south from rest, and 'rest' ticks more with no key: (z, vz)."""
    x, z, vx, vz = 0.0, 0.0, 0.0, 0.0
    for _ in range(ticks):
      x, z, vx, vz = pace.tick(x, z, vx, vz, *pace.push(0.0, 1, 0))
    for _ in range(rest):
      x, z, vx, vz = pace.tick(x, z, vx, vz, 0.0, 0.0)
    return z, vz

  def test_what_a_key_adds(self) -> None:
    #  yaw 0 is south (+z); looking south its left hand is east (+x)
    self.assertPair((0.0, 0.098), pace.push(0.0, 1, 0))
    self.assertPair((0.0, -0.098), pace.push(0.0, -1, 0))
    self.assertPair((0.098, 0.0), pace.push(0.0, 0, 1))
    self.assertPair((-0.098, 0.0), pace.push(0.0, 0, -1))
    self.assertPair((-0.098, 0.0), pace.push(90.0, 1, 0))
    self.assertPair((0.0, 0.0), pace.push(37.0, 0, 0))

  def test_two_keys_at_once_add_no_more_than_the_whole(self) -> None:
    ax, az = pace.push(0.0, 1, 1)
    self.assertAlmostEqual(0.1, math.hypot(ax, az), places=9)
    self.assertAlmostEqual(ax, az, places=9)

  def test_sneaking_adds_three_tenths(self) -> None:
    self.assertPair((0.0, 0.0294), pace.push(0.0, 1, 0, sneak=True))

  def test_a_tick_by_hand(self) -> None:
    #  the key adds to its motion, it moves by that, then 0.546 is kept
    self.assertPair((0.0, 0.098, 0.0, 0.098 * 0.546),
                    pace.tick(0.0, 0.0, 0.0, 0.0, 0.0, 0.098))
    self.assertPair((1.0 + 0.2, 2.0 + 0.148, 0.2 * 0.546, 0.148 * 0.546),
                    pace.tick(1.0, 2.0, 0.2, 0.05, 0.0, 0.098))

  def test_a_walk_settles_at_its_speed(self) -> None:
    before, _ = self.walked(60, 0)
    after, _ = self.walked(61, 0)
    self.assertAlmostEqual(pace.SPEED, after - before, places=9)
    self.assertAlmostEqual(0.098 / 0.454, pace.SPEED, places=9)

  def test_how_far_it_goes_on_with_the_keys_let_go(self) -> None:
    at, motion = self.walked(60, 0)
    rested, _ = self.walked(60, 200)
    self.assertAlmostEqual(rested - at, pace.coast(motion), places=9)
    self.assertAlmostEqual(0.0, pace.coast(0.0), places=9)

  def test_each_tick_held_is_as_far_in_the_end(self) -> None:
    for ticks in (1, 2, 5, 13):
      rested, _ = self.walked(ticks, 200)
      self.assertAlmostEqual(rested, pace.held(ticks), places=9)
    self.assertAlmostEqual(pace.SPEED, pace.held(1), places=9)

  def test_the_way_to_look_to_get_there(self) -> None:
    self.assertAlmostEqual(0.0, pace.bearing(0.0, 0.0, 0.0, 5.0))
    self.assertAlmostEqual(-90.0, pace.bearing(0.0, 0.0, 5.0, 0.0))
    self.assertAlmostEqual(90.0, pace.bearing(0.0, 0.0, -5.0, 0.0))
    self.assertAlmostEqual(180.0, abs(pace.bearing(0.0, 0.0, 0.0, -5.0)))
    self.assertAlmostEqual(-45.0, pace.bearing(1.0, 1.0, 3.0, 3.0))

  def test_a_turn_is_the_short_way_round(self) -> None:
    self.assertAlmostEqual(20.0, pace.turned(10.0, 30.0))
    self.assertAlmostEqual(-20.0, pace.turned(30.0, 10.0))
    self.assertAlmostEqual(20.0, pace.turned(170.0, -170.0))
    self.assertAlmostEqual(-20.0, pace.turned(-170.0, 170.0))
    self.assertAlmostEqual(-180.0, pace.turned(0.0, 180.0))

  def test_how_long_a_way_is(self) -> None:
    self.assertAlmostEqual(7.0, pace.length(WAY))
    self.assertAlmostEqual(0.0, pace.length(((2.0, 2.0),)))

  def test_the_point_so_far_along_a_way(self) -> None:
    self.assertPair((0.0, 0.0), pace.point(WAY, 0.0))
    self.assertPair((0.0, 2.5), pace.point(WAY, 2.5))
    self.assertPair((0.0, 4.0), pace.point(WAY, 4.0))
    self.assertPair((1.0, 4.0), pace.point(WAY, 5.0))
    #  never past its end, nor before its beginning
    self.assertPair((3.0, 4.0), pace.point(WAY, 9.0))
    self.assertPair((0.0, 0.0), pace.point(WAY, -1.0))
    self.assertPair((2.0, 2.0), pace.point(((2.0, 2.0),), 1.0))

  def test_where_on_a_way_it_is_abreast_of(self) -> None:
    #  (how far along, how far from it)
    self.assertPair((1.0, 0.2), pace.abreast(WAY, 0.2, 1.0))
    self.assertPair((1.0, 0.2), pace.abreast(WAY, -0.2, 1.0))
    self.assertPair((5.0, 0.3), pace.abreast(WAY, 1.0, 4.3))
    #  before its beginning and past its end
    self.assertPair((0.0, 1.0), pace.abreast(WAY, 0.0, -1.0))
    self.assertPair((7.0, 2.0), pace.abreast(WAY, 5.0, 4.0))
    #  as near to both stretches: the one further along
    self.assertPair((4.5, 0.5), pace.abreast(WAY, 0.5, 3.5))

  def test_abreast_never_goes_back_along_the_way(self) -> None:
    #  nearest to the first stretch, which is behind it by now
    along, off = pace.abreast(WAY, 0.1, 3.0, since=4.5)
    self.assertAlmostEqual(4.5, along, places=9)
    self.assertAlmostEqual(math.hypot(0.4, 1.0), off, places=9)
    #  'since' past the way's end is the end
    self.assertPair((7.0, 2.0), pace.abreast(WAY, 5.0, 4.0, since=9.0))

  def test_a_way_is_at_least_a_point(self) -> None:
    for call in (lambda: pace.length(()), lambda: pace.point((), 0.0),
                 lambda: pace.abreast((), 0.0, 0.0)):
      with self.assertRaises(ValueError):
        call()


if __name__ == '__main__':
  unittest.main()
