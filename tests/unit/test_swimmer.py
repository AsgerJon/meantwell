"""
The swimmer (SPEC.md 21.16), without a game, on a body in a pool that
moves as a player does in water (poolbody.py), counted in water either
way a game counts it. Under water it comes up to the water's top and
stays afloat, jump held; it paddles to a bank and gets out onto it, or
stays afloat over a place in the water; let go, it sinks. In a modern
game it swims as 1.13 has it: laid level, 0.6 high, by sprint and its
look, faster than paddling, through a gap one block high, and out at a
bank; in 1.7.10 it says the game has no such swimming. Jump is never
pressed twice within 9 ticks (a creative player would fly). It asks the
body's five means and no others. Nothing gained, or its tick budget
spent, is a TesttimeError, with every key let go.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from meantwell.swimmer import Swimmer
from poolbody import PoolBody
from unittas.errors import TesttimeError
from unittas.values import BlockPos, Vec3

TOP, BED, BANK = 4.0, 1.0, 20.0
ON_THE_BED = Vec3(4.5, BED, 0.5)
ON_THE_BANK = Vec3(22.5, TOP, 0.5)
MEANS = {'perceive', 'keyDown', 'keyUp', 'look', 'ticks'}


class SwimmerTests(unittest.TestCase):

  def eachWay(self, **pool):
    """A body on the pool's bed, for each way of counting it in water."""
    for touching in (True, False):
      with self.subTest(touching=touching):
        yield PoolBody(ON_THE_BED, BANK, TOP, BED, touching=touching,
                       **pool)

  def assertNeverFlew(self, body: PoolBody) -> None:
    self.assertFalse(body.flew, 'jump pressed twice within 7 ticks')
    jumps = [tick for tick, key in body.presses if key == 'key.jump']
    for before, after in zip(jumps, jumps[1:]):
      self.assertGreaterEqual(after - before, 9)

  def test_from_the_bed_up_to_the_top_and_afloat(self) -> None:
    for body in self.eachWay():
      swimmer = Swimmer(body)
      seen = swimmer.surface()
      self.assertGreater(seen.pos.y, TOP - 0.8, 'at the water\'s top')
      self.assertEqual({'key.jump'}, body.keys, 'jump still held')
      body.mark()
      body.ticks(60)
      self.assertGreater(body.lowest, TOP - 0.9, 'afloat while held')
      self.assertNeverFlew(body)

  def test_let_go_it_sinks(self) -> None:
    for body in self.eachWay():
      swimmer = Swimmer(body)
      swimmer.surface()
      swimmer.letGo()
      self.assertEqual(set(), body.keys)
      body.ticks(80)
      self.assertLess(body.y, BED + 0.5, 'on the bed again')

  def test_not_under_water_there_is_nothing_to_do(self) -> None:
    body = PoolBody(ON_THE_BANK, BANK, TOP, BED)
    seen = Swimmer(body).surface()
    self.assertFalse(seen.inWater)
    self.assertEqual(['perceive'], body.asked)
    self.assertEqual([], body.presses)

  def test_from_the_bed_to_the_bank_and_out(self) -> None:
    for body in self.eachWay():
      swimmer = Swimmer(body)
      seen = swimmer.paddle(ON_THE_BANK)
      self.assertTrue(seen.onGround)
      self.assertFalse(seen.inWater)
      self.assertGreater(seen.pos.x + 0.3, BANK, 'on the bank')
      self.assertAlmostEqual(TOP, seen.pos.y)
      self.assertEqual(set(), body.keys, 'out, every key let go')
      self.assertNeverFlew(body)

  def test_afloat_over_a_place_in_the_water(self) -> None:
    place = Vec3(10.5, TOP, 0.5)
    for body in self.eachWay():
      seen = Swimmer(body).paddle(place)
      self.assertLess(math.hypot(place.x - seen.pos.x,
                                 place.z - seen.pos.z), 0.6)
      self.assertEqual({'key.jump'}, body.keys,
                       'afloat there: jump held, forward let go')
      body.mark()
      body.ticks(40)
      self.assertGreater(body.lowest, TOP - 0.9)

  def test_a_place_aside_is_turned_to(self) -> None:
    place = Vec3(10.5, TOP, 8.5)
    for body in self.eachWay():
      seen = Swimmer(body).paddle(place)
      self.assertLess(math.hypot(place.x - seen.pos.x,
                                 place.z - seen.pos.z), 0.6)

  def test_a_blockpos_is_its_floors_middle(self) -> None:
    body = PoolBody(ON_THE_BED, BANK, TOP, BED)
    seen = Swimmer(body).paddle(BlockPos(22, 4, 0))
    self.assertTrue(seen.onGround and not seen.inWater)

  def test_nothing_gained_is_an_error(self) -> None:
    #  a bank three over the water: no getting out
    for body in self.eachWay(lip=3.0):
      swimmer = Swimmer(body)
      with self.assertRaises(TesttimeError) as stopped:
        swimmer.paddle(Vec3(22.5, TOP + 3.0, 0.5), ticks=2000)
      self.assertEqual('paddle', stopped.exception.step)
      self.assertIn('nothing gained', str(stopped.exception))
      self.assertEqual(set(), body.keys, 'every key let go')

  def test_the_tick_budget_spent(self) -> None:
    for body in self.eachWay():
      with self.assertRaises(TesttimeError) as stopped:
        Swimmer(body).paddle(ON_THE_BANK, ticks=30)
      self.assertIn('the tick budget (30) is spent', str(stopped.exception))
      self.assertEqual(set(), body.keys)
    for body in self.eachWay():
      with self.assertRaises(TesttimeError) as stopped:
        Swimmer(body).surface(ticks=5)
      self.assertEqual('surface', stopped.exception.step)
      self.assertEqual(set(), body.keys)

  def test_jump_is_never_pressed_again_within_9_ticks(self) -> None:
    #  afloat over a place at once (jump pressed), let go, and asked up
    #  again straight away: the second press has to wait
    place = Vec3(10.5, TOP, 0.5)
    for touching in (True, False):
      with self.subTest(touching=touching):
        body = PoolBody(Vec3(10.5, TOP - 0.6, 0.5), BANK, TOP, BED,
                        touching=touching)
        swimmer = Swimmer(body)
        swimmer.paddle(place)
        swimmer.letGo()
        swimmer.surface()
        jumps = [tick for tick, key in body.presses if key == 'key.jump']
        self.assertEqual(2, len(jumps), 'pressed, let go, pressed again')
        self.assertLess(jumps[0], 5, 'the first press came at once')
        self.assertNeverFlew(body)
        swimmer.letGo()
        swimmer.paddle(ON_THE_BANK)
        self.assertNeverFlew(body)

  def test_it_asks_the_five_means_and_no_others(self) -> None:
    for body in self.eachWay():
      swimmer = Swimmer(body)
      swimmer.surface()
      swimmer.paddle(ON_THE_BANK)
      self.assertEqual(MEANS, set(body.asked))
      self.assertEqual({'key.jump', 'key.forward'},
                       {key for _, key in body.presses})
      self.assertIs(body, swimmer.body)

  def test_made_wrong_it_is_refused(self) -> None:
    body = PoolBody(ON_THE_BED, BANK, TOP, BED)
    swimmer = Swimmer(body)
    for step in (swimmer.paddle, swimmer.swim):
      with self.assertRaises(TypeError):
        step('the far bank')
      with self.assertRaises(ValueError):
        step(ON_THE_BANK, ticks=0)
    with self.assertRaises(ValueError):
      swimmer.surface(ticks=-1)
    self.assertEqual([], body.asked)

  # ------------------------------------------- swimming as 1.13 has it

  def test_under_water_it_swims_level_and_fast(self) -> None:
    place = Vec3(16.5, BED + 0.5, 0.5)
    body = PoolBody(ON_THE_BED, BANK, TOP, BED)
    swimmer = Swimmer(body)
    seen = swimmer.swim(place)
    self.assertLess(math.dist((place.x, place.y, place.z),
                              (seen.pos.x, seen.pos.y, seen.pos.z)), 0.8)
    self.assertEqual(set(), body.keys, 'there, every key let go')
    self.assertGreater(swimmer.level, 10, 'laid level as it went')
    self.assertGreater(body.level, 0.8 * body.tick,
                       'level nearly all the way')
    self.assertIn('key.sprint', {key for _, key in body.presses})
    self.assertNeverFlew(body)
    #  the same water paddled, upright at its top
    upright = PoolBody(ON_THE_BED, BANK, TOP, BED)
    Swimmer(upright).paddle(Vec3(16.5, TOP, 0.5))
    self.assertLess(body.tick, 0.8 * upright.tick, 'swimming is faster')

  def test_from_the_waters_top_it_sinks_under_and_swims(self) -> None:
    #  that swimming begins with its eyes under water: jump let go, it
    #  sinks there by itself; the place is no deeper than where it floats
    place = Vec3(16.5, TOP - 0.9, 0.5)
    body = PoolBody(Vec3(4.5, TOP - 0.5, 0.5), BANK, TOP, BED)
    swimmer = Swimmer(body)
    seen = swimmer.swim(place)
    self.assertLess(math.dist((place.x, place.y, place.z),
                              (seen.pos.x, seen.pos.y, seen.pos.z)), 0.8)
    self.assertGreater(swimmer.level, 10)

  def test_through_a_gap_one_block_high(self) -> None:
    #  stone from one block over the bed up, across four blocks of the
    #  pool: a player upright (1.8 high) doesn't fit under it
    roof = (9.0, 13.0, BED + 1.0)
    place = Vec3(16.5, BED + 0.1, 0.5)
    body = PoolBody(ON_THE_BED, BANK, TOP, BED, roof=roof)
    seen = Swimmer(body).swim(place)
    self.assertGreater(seen.pos.x, 13.0, 'through, and beyond it')
    self.assertLess(math.dist((place.x, place.y, place.z),
                              (seen.pos.x, seen.pos.y, seen.pos.z)), 0.8)
    upright = PoolBody(ON_THE_BED, BANK, TOP, BED, roof=roof)
    with self.assertRaises(TesttimeError) as stopped:
      Swimmer(upright).paddle(place, ticks=2000)
    self.assertIn('nothing gained', str(stopped.exception))
    self.assertLess(upright.x, 9.0, 'upright it is stopped at the gap')

  def test_swum_to_a_bank_it_gets_out(self) -> None:
    body = PoolBody(ON_THE_BED, BANK, TOP, BED)
    swimmer = Swimmer(body)
    seen = swimmer.swim(ON_THE_BANK)
    self.assertTrue(seen.onGround)
    self.assertFalse(seen.inWater)
    self.assertGreater(seen.pos.x + 0.3, BANK, 'on the bank')
    self.assertEqual(set(), body.keys)
    self.assertGreater(swimmer.level, 10, 'level across the water')
    self.assertNeverFlew(body)
    self.assertEqual(MEANS, set(body.asked))
    self.assertEqual({'key.jump', 'key.forward', 'key.sprint'},
                     {key for _, key in body.presses})

  def test_a_game_with_no_such_swimming_says_so(self) -> None:
    #  1.7.10: sprint and forward under water, and it stays upright
    body = PoolBody(ON_THE_BED, BANK, TOP, BED, touching=False)
    swimmer = Swimmer(body)
    with self.assertRaises(TesttimeError) as stopped:
      swimmer.swim(Vec3(16.5, BED + 0.5, 0.5))
    self.assertEqual('swim', stopped.exception.step)
    self.assertIn('no swimming as 1.13 has it', str(stopped.exception))
    self.assertEqual(0, swimmer.level)
    self.assertEqual(set(), body.keys, 'every key let go')

  def test_a_swims_tick_budget_spent(self) -> None:
    body = PoolBody(ON_THE_BED, BANK, TOP, BED)
    with self.assertRaises(TesttimeError) as stopped:
      Swimmer(body).swim(Vec3(16.5, BED + 0.5, 0.5), ticks=20)
    self.assertEqual('swim', stopped.exception.step)
    self.assertIn('the tick budget (20) is spent', str(stopped.exception))
    self.assertEqual(set(), body.keys)


if __name__ == '__main__':
  unittest.main()
