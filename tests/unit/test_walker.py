"""
A walk as a player walks (SPEC.md 21.23; walker.py), without a game, on
a body that moves as the ground has it and keeps every tick
(walkbody.py). What "not blocky" is, is read from that record, tick by
tick:

- the look never jumps: no tick turns it more than the mouse's fastest;
- the track has no corner: the way it moves turns no more than that;
- the feet don't stop on open ground between setting off and letting go;
- the stop is a stop: forward let go, a tap after it at most, a sneak
  only very near;
- it is there, within its margin, still, and looking where it was told;
- it is never off the ground the way goes on, nor against a wall.

The same record is read of the agent's own walkTo first: it arrives,
and it fails the first, the second and the fourth, which is what was
seen in the game.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import tempfile
import unittest

from meantwell import pace
from meantwell.mouse import Mouse
from meantwell.walker import Walker
from unittas.agent import Agent
from unittas.errors import TesttimeError
from unittas.values import Vec3
from walkbody import WalkBody

#  Open ground: the place ahead, beside, behind and aside, and near
OPEN = {'ahead': (0.5, 8.5), 'beside': (6.5, 0.5),
        'behind and aside': (-3.5, -5.5), 'near': (1.5, 2.5)}
#  A wall across the way, a hole in it: (the body's ground, the place)
ROUND = {
  'a wall': ({'walls': tuple((x, 3) for x in range(-3, 3))}, (0.5, 6.5)),
  'a hole': ({'holes': tuple((x, z) for x in range(0, 2)
                             for z in range(2, 5))}, (0.5, 6.5)),
  'a hole both sides': ({'holes': tuple(
    (x, z) for x in (-1, 0, 1, 3, 4, 5) for z in range(2, 7)) + tuple(
    (x, z) for x in range(-1, 6) for z in (8, 9))}, (2.5, 7.5)),
}


class WalkerTests(unittest.TestCase):

  # ---------------------------------------------------------- the record

  @staticmethod
  def lookJump(body: WalkBody) -> float:
    """The most a tick turned its look, in degrees."""
    yaws = [0.0] + [tick.yaw for tick in body.track]
    return max(abs(pace.turned(a, b)) for a, b in zip(yaws, yaws[1:]))

  @staticmethod
  def corner(body: WalkBody) -> float:
    """The most the way it moves turned from a tick to the next, of
    those it moved in, in degrees."""
    moved = [tick for tick in body.track if tick.speed > 0.05]
    return max([abs(pace.turned(a.heading, b.heading))
                for a, b in zip(moved, moved[1:])
                if b.tick == a.tick + 1] or [0.0])

  @staticmethod
  def presses(body: WalkBody, key: str) -> int:
    """How many times the key went down."""
    held = [False] + [key in tick.keys for tick in body.track]
    return sum(1 for a, b in zip(held, held[1:]) if b and not a)

  @staticmethod
  def sneaked(body: WalkBody, place: tuple) -> float:
    """The furthest from the place it sneaked; 0 when it never did."""
    return max([math.hypot(place[0] - tick.x, place[1] - tick.z)
                for tick in body.track if 'key.sneak' in tick.keys] or
               [0.0])

  @staticmethod
  def slowest(body: WalkBody) -> float:
    """Its least speed from its first tick at a walk's speed to the
    last tick forward was held."""
    track = body.track
    fast = [at for at, tick in enumerate(track)
            if tick.speed > 0.9 * pace.SPEED]
    held = [at for at, tick in enumerate(track)
            if 'key.forward' in tick.keys]
    return min(tick.speed for tick in track[fast[0]:held[-1] + 1])

  def assertThere(self, body: WalkBody, place: tuple,
                  within: float = 0.25) -> None:
    last = body.track[-1]
    self.assertLessEqual(math.hypot(place[0] - last.x, place[1] - last.z),
                         within)
    self.assertLess(last.speed, 0.01, 'still')
    self.assertEqual(set(), body.keys, 'every key let go')

  def assertOnGround(self, body: WalkBody) -> None:
    for tick in body.track:
      self.assertEqual(0.0, tick.y, 'never fell: %r' % (tick,))
      for dx in (-0.15, 0.15):
        for dz in (-0.15, 0.15):
          column = math.floor(tick.x + dx), math.floor(tick.z + dz)
          self.assertIn((column[0], -1, column[1]), body.blocks, tick)
          self.assertNotIn((column[0], 0, column[1]), body.blocks, tick)
    self.assertFalse(body.collided)

  def walked(self, place: tuple, **ground: tuple) -> WalkBody:
    """The body after the walker's walk to 'place'."""
    body = WalkBody(**ground)
    Walker(Mouse(body)).walk(Vec3(place[0], 0.0, place[1]))
    return body

  # ----------------------------------------------------- the agent's own

  def test_the_agents_own_walk_is_what_was_seen(self) -> None:
    #  it arrives; its look jumps, its track has a corner, and it ends
    #  sneaking from further off than a tap's
    for name in ('beside', 'behind and aside'):
      with self.subTest(place=name):
        place = OPEN[name]
        body = WalkBody()
        Agent(body, tempfile.gettempdir()).walkTo(
          Vec3(place[0], 0.0, place[1]))
        self.assertThere(body, place)
        self.assertGreater(self.lookJump(body), 2 * Mouse.FASTEST)
        self.assertGreater(self.corner(body), 2 * Mouse.FASTEST)
        self.assertGreater(self.sneaked(body, place), Walker.SNEAKS)

  # ------------------------------------------------------------ the walk

  def test_it_gets_there_and_stops(self) -> None:
    for name, place in OPEN.items():
      with self.subTest(place=name):
        self.assertThere(self.walked(place), place)

  def test_its_look_never_jumps(self) -> None:
    for name, place in OPEN.items():
      with self.subTest(place=name):
        self.assertLessEqual(self.lookJump(self.walked(place)),
                             Mouse.FASTEST + 1e-9)

  def test_its_track_has_no_corner(self) -> None:
    for name, place in OPEN.items():
      with self.subTest(place=name):
        self.assertLessEqual(self.corner(self.walked(place)),
                             Mouse.FASTEST + 1e-9)

  def test_its_feet_dont_stop_on_open_ground(self) -> None:
    for name in ('ahead', 'beside', 'behind and aside'):
      with self.subTest(place=name):
        self.assertGreater(self.slowest(self.walked(OPEN[name])),
                           pace.SPEED / 2)

  def test_its_stop_is_a_stop(self) -> None:
    for name, place in OPEN.items():
      with self.subTest(place=name):
        body = self.walked(place)
        self.assertLessEqual(self.presses(body, 'key.forward') +
                             self.presses(body, 'key.back'), 2)
        self.assertLess(self.sneaked(body, place), Walker.SNEAKS)

  def test_its_head_comes_round_before_its_feet_go(self) -> None:
    for name in ('beside', 'behind and aside'):
      with self.subTest(place=name):
        place = OPEN[name]
        body = self.walked(place)
        first = [tick for tick in body.track
                 if 'key.forward' in tick.keys][0]
        self.assertGreater(first.tick, 4, 'it turned first')
        self.assertLessEqual(abs(pace.turned(first.yaw, pace.bearing(
          first.x, first.z, *place))), Walker.WIDE + 1e-6)

  def test_round_what_is_in_the_way(self) -> None:
    for name, (ground, place) in ROUND.items():
      with self.subTest(round=name):
        body = self.walked(place, **ground)
        self.assertThere(body, place)
        self.assertOnGround(body)
        self.assertLessEqual(self.lookJump(body), Mouse.FASTEST + 1e-9)

  def test_a_narrow_margin_is_kept(self) -> None:
    for name, place in OPEN.items():
      with self.subTest(place=name):
        body = WalkBody()
        Walker(Mouse(body)).walk(Vec3(place[0], 0.0, place[1]), 0.08)
        self.assertThere(body, place, 0.08)

  def test_looking_where_it_was_told_once_there(self) -> None:
    body = WalkBody()
    seen = Walker(Mouse(body)).walk(Vec3(0.5, 0.0, 6.5),
                                    facing=Vec3(-2.5, 0.5, 6.5))
    self.assertThere(body, (0.5, 6.5))
    self.assertAlmostEqual(pace.bearing(seen.pos.x, seen.pos.z, -2.5, 6.5),
                           seen.look.yaw, delta=0.5)
    self.assertGreater(seen.look.pitch, 15.0, 'down at it')
    self.assertLessEqual(self.lookJump(body), Mouse.FASTEST + 1e-9)

  def test_it_keeps_the_way_it_took(self) -> None:
    body = WalkBody(walls=ROUND['a wall'][0]['walls'])
    walker = Walker(Mouse(body))
    walker.walk(Vec3(0.5, 0.0, 6.5))
    self.assertEqual((0.5, 0.5), walker.way[0])
    self.assertEqual((0.5, 6.5), walker.way[-1])
    self.assertGreater(len(walker.way), 2, 'round the wall')

  # ------------------------------------------------------ what it refuses

  def test_no_way_is_said(self) -> None:
    ring = tuple((x, z) for x in range(-1, 3) for z in range(-1, 3)
                 if (x, z) != (0, 0) and x in (-1, 0, 1) and z in (-1, 0, 1))
    body = WalkBody(walls=ring)
    with self.assertRaises(TesttimeError) as raised:
      Walker(Mouse(body)).walk(Vec3(0.5, 0.0, 6.5))
    self.assertIn('no way', str(raised.exception))
    self.assertEqual(set(), body.keys)

  def test_a_way_it_doesnt_walk_yet_is_said(self) -> None:
    steps = tuple((x, z) for x in range(-12, 13) for z in range(3, 9))
    body = WalkBody(steps=steps)
    with self.assertRaises(TesttimeError) as raised:
      Walker(Mouse(body)).walk(Vec3(0.5, 1.0, 6.5))
    self.assertIn('a jump', str(raised.exception))
    self.assertEqual(['perceive'], body.asked, 'before a key is pressed')

  def test_its_body_is_a_mouse(self) -> None:
    with self.assertRaises(TypeError):
      Walker(WalkBody())

  def test_what_it_is_asked_is_checked(self) -> None:
    walker = Walker(Mouse(WalkBody()))
    with self.assertRaises(TypeError):
      walker.walk((0.5, 0.0, 6.5))
    with self.assertRaises(TypeError):
      walker.walk(Vec3(0.5, 0.0, 6.5), facing=(1, 2, 3))
    with self.assertRaises(ValueError):
      walker.walk(Vec3(0.5, 0.0, 6.5), 0.01)
    with self.assertRaises(ValueError):
      walker.walk(Vec3(0.5, 0.0, 6.5), ticks=0)

  def test_a_spent_budget_is_said_with_every_key_let_go(self) -> None:
    body = WalkBody()
    with self.assertRaises(TesttimeError) as raised:
      Walker(Mouse(body)).walk(Vec3(0.5, 0.0, 8.5), ticks=10)
    self.assertIn('budget', str(raised.exception))
    self.assertEqual(set(), body.keys)

  def test_the_same_walk_is_walked_the_same_way(self) -> None:
    first = self.walked(OPEN['behind and aside'])
    second = self.walked(OPEN['behind and aside'])
    self.assertEqual(first.track, second.track)


if __name__ == '__main__':
  unittest.main()
