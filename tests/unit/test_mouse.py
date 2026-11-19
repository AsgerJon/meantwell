"""
The look turned as a hand turns a mouse (SPEC.md 21.22, 21.23 W6;
mouse.py), without a game, on a body that keeps how its look turns tick
by tick (lookbody.py). The mouse gives a rate each tick and the game
turns by it: a turn quickens, runs no faster than its fastest, slows as
it comes near, never goes past, and ends on the look asked for to the
hair, with no rate left in force. Both ways turn together, the short
way round. A small turn is one look set. The same turn is turned the
same way each time. With a walking key held 'look' sets the look
outright. Everything else of the body it hands on untouched.

And 'toward': one tick's rate of that turn, for the one who turns while
it walks. Asked each tick it is the same turn; it follows a look that
moves, goes on from how fast it turns already, and is never set
outright, a walking key held or not. 'ahead' reckons the looks it will
have, 'rest' stops the rate, 'bearing' is the last answer.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from lookbody import LookBody
from meantwell.mouse import Mouse


def _turns(body: LookBody, yaw: float = 0.0, pitch: float = 0.0) -> list:
  """How far each tick turned the look, in degrees."""
  turned, at = [], (yaw, pitch)
  for look in body.track:
    turned.append(math.hypot((look[0] - at[0] + 180.0) % 360.0 - 180.0,
                             look[1] - at[1]))
    at = look
  return turned


def _names(body: LookBody) -> list:
  """The name of each request it was asked."""
  return [name for name, _ in body.asked]


class MouseTests(unittest.TestCase):

  def test_a_turn_is_spread_over_many_ticks_and_ends_there(self) -> None:
    body = LookBody()
    Mouse(body).look(90.0, 0.0)
    self.assertEqual((90.0, 0.0), (body.yaw, body.pitch))
    turning = [turn for turn in _turns(body) if turn > 0.0]
    self.assertGreaterEqual(len(turning), 8)
    self.assertLessEqual(len(turning), 20, 'a second at the most')
    self.assertLessEqual(max(turning), Mouse.FASTEST + 1e-9)
    self.assertEqual((0.0, 0.0), body.rate, 'no rate left in force')

  def test_it_quickens_and_then_slows(self) -> None:
    body = LookBody()
    Mouse(body).look(90.0, 0.0)
    turns = [turn for turn in _turns(body) if turn > 1e-9]
    fastest = turns.index(max(turns))
    self.assertLessEqual(turns[0], Mouse.QUICKEN + 1e-9)
    self.assertLess(turns[0], max(turns), 'it starts slower than it runs')
    self.assertLess(turns[-1], max(turns), 'and ends slower')
    for before, after in zip([0.0] + turns, turns):
      self.assertLessEqual(after - before, Mouse.QUICKEN + 1e-9)
    slowing = turns[fastest:]
    self.assertEqual(sorted(slowing, reverse=True), slowing,
                     'no second wind')

  def test_it_never_goes_past(self) -> None:
    for yaw, pitch in ((90.0, 0.0), (-170.0, 40.0), (12.0, -60.0),
                       (3.5, 2.0), (179.0, 89.0)):
      with self.subTest(yaw=yaw, pitch=pitch):
        body = LookBody()
        Mouse(body).look(yaw, pitch)
        left = [math.hypot((yaw - at[0] + 180.0) % 360.0 - 180.0,
                           pitch - at[1]) for at in body.track]
        for before, after in zip(left, left[1:]):
          self.assertLessEqual(after, before + 1e-9)
        self.assertEqual(0.0, left[-1])

  def test_both_ways_turn_together_straight_across(self) -> None:
    body = LookBody()
    Mouse(body).look(40.0, 30.0)
    for yaw, pitch in body.track:
      self.assertAlmostEqual(yaw * 30.0 / 40.0, pitch, places=9)

  def test_the_short_way_round(self) -> None:
    body = LookBody(170.0, 0.0)
    Mouse(body).look(-170.0, 0.0)
    self.assertAlmostEqual(20.0, sum(_turns(body, 170.0)), places=6)
    for yaw, _ in body.track:
      self.assertTrue(yaw >= 170.0 or yaw <= -170.0, yaw)

  def test_a_small_turn_is_one_look(self) -> None:
    body = LookBody()
    Mouse(body).look(2.0, 1.0)
    self.assertEqual([(2.0, 1.0)], body.looks)
    self.assertEqual([], body.rates)

  def test_looking_there_already_it_asks_nothing(self) -> None:
    body = LookBody(40.0, 5.0)
    Mouse(body).look(40.0, 5.0)
    self.assertEqual(['perceive'], _names(body), 'but to know its look')

  def test_it_turns_on_from_where_it_left_the_look(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    mouse.look(90.0, 0.0)
    before = len(body.asked)
    mouse.look(0.0, 0.0)
    self.assertNotIn('perceive', _names(body)[before:])
    self.assertEqual((0.0, 0.0), (body.yaw, body.pitch))
    mouse.look(1.0, 0.0)
    self.assertEqual((1.0, 0.0), body.looks[-1], 'a small turn from it')

  def test_the_same_turn_is_turned_the_same_way(self) -> None:
    first, second = LookBody(), LookBody()
    Mouse(first).look(-135.0, 25.0)
    Mouse(second).look(-135.0, 25.0)
    self.assertEqual(first.track, second.track)

  def test_a_look_no_head_can_take_is_refused(self) -> None:
    body = LookBody()
    with self.assertRaises(ValueError):
      Mouse(body).look(0.0, 91.0)
    with self.assertRaises(TypeError):
      Mouse(body).look('north', 0.0)
    self.assertEqual([], body.asked)

  def test_walking_its_look_is_set_outright(self) -> None:
    #  found in the game: the agent's walk counts on its look being
    #  there at once; turned over many requests, it walked in rings
    #  round a waypoint until its budget was spent
    for key in Mouse.WALKS:
      with self.subTest(key=key):
        body = LookBody()
        mouse = Mouse(body)
        mouse.keyDown(key)
        mouse.look(90.0, 0.0)
        self.assertEqual([(90.0, 0.0)], body.looks)
        self.assertEqual([], body.rates)
        mouse.keyUp(key)
        mouse.look(0.0, 0.0)
        self.assertGreater(len(body.rates), 5, 'standing, it turns')

  def test_all_else_of_the_body_is_handed_on(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    mouse.tap('key.use')
    self.assertEqual(4.5, mouse.reach)
    self.assertEqual(body.perceive().tick, mouse.perceive().tick - 1)
    self.assertEqual(('tap', ('key.use',)), body.asked[0])
    self.assertIs(body, mouse.body)
    with self.assertRaises(AttributeError):
      mouse.flap()

  def test_toward_is_one_ticks_rate(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    self.assertFalse(mouse.toward(90.0, 0.0), 'not there yet')
    self.assertEqual(['perceive', 'mouseRate'], _names(body))
    self.assertFalse(mouse.toward(90.0, 0.0))
    self.assertEqual(['perceive', 'mouseRate', 'mouseRate'], _names(body))
    self.assertAlmostEqual(Mouse.QUICKEN, body.rates[0][0])
    self.assertAlmostEqual(2 * Mouse.QUICKEN, body.rates[1][0],
                           msg='it goes on from how fast it turns already')
    self.assertEqual([], body.looks, 'never set outright')

  def test_toward_asked_each_tick_is_the_turn_look_makes(self) -> None:
    for yaw, pitch in ((90.0, 0.0), (-170.0, 40.0), (12.0, -60.0)):
      with self.subTest(yaw=yaw, pitch=pitch):
        whole, parts = LookBody(), LookBody()
        Mouse(whole).look(yaw, pitch)
        mouse = Mouse(parts)
        while not mouse.toward(yaw, pitch):
          self.assertLess(len(parts.track), 40)
        for one, other in zip(whole.track, parts.track):
          self.assertAlmostEqual(one[0], other[0], places=9)
          self.assertAlmostEqual(one[1], other[1], places=9)
        self.assertAlmostEqual(yaw, parts.yaw, places=9)
        self.assertAlmostEqual(pitch, parts.pitch, places=9)
        self.assertEqual((0.0, 0.0), parts.rate)

  def test_toward_there_already_says_so_and_is_still_a_tick(self) -> None:
    #  it is its asker's clock: a rate of nothing is asked all the same
    body = LookBody(40.0, 5.0)
    mouse = Mouse(body)
    self.assertTrue(mouse.toward(40.0, 5.0))
    self.assertEqual([(0.0, 0.0)], body.rates)
    self.assertEqual((40.0, 5.0), (body.yaw, body.pitch))

  def test_toward_follows_a_look_that_moves(self) -> None:
    #  where it is to look moves on each tick, as a walker's does
    body = LookBody()
    mouse = Mouse(body)
    wanted = [30.0 + 2.0 * at for at in range(40)]
    for yaw in wanted:
      mouse.toward(yaw, 0.0)
      self.assertLessEqual(body.yaw, yaw + 1e-9, 'never past it')
    turns = _turns(body)
    self.assertLessEqual(max(turns), Mouse.FASTEST + 1e-9)
    for before, after in zip([0.0] + turns, turns):
      self.assertLessEqual(after - before, Mouse.QUICKEN + 1e-9)
    self.assertLess(wanted[-1] - body.yaw, 8.0, 'it keeps up')

  def test_toward_turned_back_begins_from_rest(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    for _ in range(3):
      mouse.toward(170.0, 0.0)
    self.assertAlmostEqual(Mouse.FASTEST, body.rates[-1][0])
    mouse.toward(-90.0, 0.0)
    self.assertAlmostEqual(-Mouse.QUICKEN, body.rates[-1][0])

  def test_toward_turns_with_a_walking_key_held(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    mouse.keyDown('key.forward')
    self.assertFalse(mouse.toward(90.0, 0.0))
    self.assertEqual([(Mouse.QUICKEN, 0.0)], body.rates)
    self.assertEqual([], body.looks)

  def test_rest_stops_the_rate(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    mouse.toward(90.0, 0.0)
    mouse.toward(90.0, 0.0)
    mouse.rest()
    self.assertEqual((0.0, 0.0), body.rate)
    at = body.yaw
    body.perceive()
    self.assertEqual(at, body.yaw, 'and it turns no more')
    before = len(body.asked)
    mouse.rest()
    self.assertEqual(before, len(body.asked), 'at rest, nothing is asked')
    mouse.look(at + 1.0, 0.0)
    self.assertEqual((at + 1.0, 0.0), body.looks[-1], 'it knows its look')

  def test_ahead_reckons_the_looks_it_will_have(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    mouse.toward(120.0, 20.0)
    mouse.toward(120.0, 20.0)
    before = len(body.asked)
    reckoned = mouse.ahead(120.0, 20.0, 8)
    self.assertEqual(before, len(body.asked), 'nothing is asked')
    had = [(body.yaw, body.pitch)]
    for _ in range(7):
      mouse.toward(120.0, 20.0)
      had.append((body.yaw, body.pitch))
    self.assertEqual(8, len(reckoned))
    for one, other in zip(reckoned, had):
      self.assertAlmostEqual(one[0], other[0], places=9)
      self.assertAlmostEqual(one[1], other[1], places=9)

  def test_its_bearing_is_the_last_answer(self) -> None:
    body = LookBody()
    mouse = Mouse(body)
    self.assertIsNone(mouse.bearing)
    mouse.toward(90.0, 0.0)
    self.assertEqual(body.tick, mouse.bearing.tick)
    self.assertEqual(body.yaw, mouse.bearing.look.yaw)

  def test_a_rate_found_in_force_is_gone_on_from(self) -> None:
    body = LookBody()
    body.rate = 10.0, 0.0
    mouse = Mouse(body)
    mouse.toward(170.0, 0.0)
    self.assertAlmostEqual(Mouse.FASTEST, body.rates[0][0],
                           msg='10 already, and no more than 6 faster')

  def test_toward_refuses_a_look_no_head_can_take(self) -> None:
    body = LookBody()
    with self.assertRaises(ValueError):
      Mouse(body).toward(0.0, -91.0)
    with self.assertRaises(TypeError):
      Mouse(body).toward(0.0, None)
    self.assertEqual([], body.asked)


if __name__ == '__main__':
  unittest.main()
