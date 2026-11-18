"""
The look turned as a hand turns a mouse (SPEC.md 21.22; mouse.py),
without a game, on a body that keeps each look it is asked (lookbody.py).
A turn is many small looks: it quickens, runs no faster than its
fastest, slows as it comes near, never goes past, and ends on the look
asked for to the hair. Both ways turn together, the short way round. A
small turn is one look. The same turn is turned the same way each time.
With a walking key held the look is set outright. Everything else of
the body it hands on untouched.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from lookbody import LookBody
from meantwell.mouse import Mouse


def _steps(body: LookBody, yaw: float = 0.0, pitch: float = 0.0) -> list:
  """How far each look turned from the one before, in degrees."""
  turned, at = [], (yaw, pitch)
  for look in body.looks:
    turned.append(math.hypot((look[0] - at[0] + 180.0) % 360.0 - 180.0,
                             look[1] - at[1]))
    at = look
  return turned


class MouseTests(unittest.TestCase):

  def test_a_turn_is_many_small_looks_and_ends_where_asked(self) -> None:
    body = LookBody()
    Mouse(body).look(90.0, 0.0)
    self.assertGreaterEqual(len(body.looks), 5)
    self.assertLessEqual(len(body.looks), 12, 'a second at the most')
    self.assertEqual((90.0, 0.0), body.looks[-1])
    self.assertLessEqual(max(_steps(body)), Mouse.FASTEST + 1e-9)

  def test_it_quickens_and_then_slows(self) -> None:
    body = LookBody()
    Mouse(body).look(90.0, 0.0)
    steps = _steps(body)
    fastest = steps.index(max(steps))
    self.assertLessEqual(steps[0], Mouse.QUICKEN + 1e-9)
    self.assertLess(steps[0], max(steps), 'it starts slower than it runs')
    self.assertLess(steps[-1], max(steps), 'and ends slower')
    self.assertEqual(sorted(steps[:fastest + 1]), steps[:fastest + 1])
    self.assertEqual(sorted(steps[fastest:], reverse=True),
                     steps[fastest:], 'no second wind')

  def test_it_never_goes_past(self) -> None:
    for yaw, pitch in ((90.0, 0.0), (-170.0, 40.0), (12.0, -60.0),
                       (3.0, 2.0), (179.0, 89.0)):
      with self.subTest(yaw=yaw, pitch=pitch):
        body = LookBody()
        Mouse(body).look(yaw, pitch)
        left = [math.hypot((yaw - at[0] + 180.0) % 360.0 - 180.0,
                           pitch - at[1]) for at in body.looks]
        self.assertEqual(sorted(left, reverse=True), left)
        self.assertEqual(0.0, left[-1])

  def test_both_ways_turn_together_straight_across(self) -> None:
    body = LookBody()
    Mouse(body).look(60.0, 30.0)
    for yaw, pitch in body.looks:
      self.assertAlmostEqual(yaw / 2.0, pitch, places=9)

  def test_the_short_way_round(self) -> None:
    body = LookBody(yaw=170.0)
    Mouse(body).look(-170.0, 0.0)
    self.assertLessEqual(len(body.looks), 5, '20 degrees, not 340')
    for yaw, _ in body.looks:
      self.assertTrue(yaw >= 170.0 or yaw <= -170.0, yaw)
      self.assertTrue(-180.0 <= yaw <= 180.0, yaw)
    self.assertEqual((-170.0, 0.0), body.looks[-1])

  def test_a_small_turn_is_one_look(self) -> None:
    body = LookBody(yaw=30.0, pitch=10.0)
    Mouse(body).look(32.0, 9.0)
    self.assertEqual([(32.0, 9.0)], body.looks)

  def test_looking_there_already_it_asks_nothing(self) -> None:
    body = LookBody(yaw=30.0, pitch=10.0)
    Mouse(body).look(30.0, 10.0)
    self.assertEqual([], body.looks)

  def test_it_turns_on_from_where_it_left_the_look(self) -> None:
    #  it asks where it looks once, and no more: walking, the agent
    #  turns it every tick
    body = LookBody()
    mouse = Mouse(body)
    mouse.look(40.0, 0.0)
    mouse.look(41.0, 0.0)
    mouse.look(90.0, 10.0)
    self.assertEqual(1, [name for name, _ in body.asked].count('perceive'))
    self.assertEqual((90.0, 10.0), body.looks[-1])
    self.assertIn((41.0, 0.0), body.looks)

  def test_the_same_turn_is_turned_the_same_way(self) -> None:
    first, second = LookBody(), LookBody()
    Mouse(first).look(-135.0, 25.0)
    Mouse(second).look(-135.0, 25.0)
    self.assertEqual(first.looks, second.looks)

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
        mouse.keyUp(key)
        mouse.look(0.0, 0.0)
        self.assertGreater(len(body.looks), 5, 'standing, it turns')

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


if __name__ == '__main__':
  unittest.main()
